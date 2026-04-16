"""
Session management — starting, streaming, and interacting with CMA sessions.

This module provides the core loop that the orchestrator uses to drive the
migration. It creates a session for the orchestrator agent, sends the initial
task message, and streams events back to the caller.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import threading
import time
from dataclasses import dataclass

import httpx
from anthropic import Anthropic

from eds_migrate.agents import MigrationFleet

log = logging.getLogger(__name__)

# CMA orchestrator turns can take 30+ minutes when the model is planning,
# running tools, and dispatching sub-agents.  The default Anthropic SDK
# timeout (600 s) is far too short for the SSE read leg.
_STREAM_TIMEOUT = httpx.Timeout(
    connect=30.0,
    read=1800.0,   # 30 minutes between SSE chunks
    write=30.0,
    pool=30.0,
)

MAX_RECONNECTS = 5
RECONNECT_BACKOFF_BASE = 2.0


@dataclass
class SessionResult:
    """Outcome of a completed session."""
    session_id: str
    status: str
    duration_s: float
    events_received: int


def run_migration(
    client: Anthropic,
    fleet: MigrationFleet,
    site_url: str,
    org: str,
    repo: str,
    *,
    github_token: str,
    eds_token: str | None = None,
    verbose: bool = False,
) -> SessionResult:
    """
    Launch the orchestrator session and stream it to completion.

    The orchestrator agent handles all phase gating, worker dispatch,
    Tier 1/Tier 2 verification loops, feedback loops, and fallback
    logic internally — it's all encoded in its system prompt and the
    callable_agents it has access to.

    This function creates the session, sends the initial user message
    containing the migration task, and streams events until the session
    goes idle.  If the SSE stream disconnects prematurely (timeout or
    network blip), we reconnect up to MAX_RECONNECTS times.
    """
    log.info("Creating orchestrator session...")
    session = client.beta.sessions.create(
        agent=fleet.orchestrator.id,
        environment_id=fleet.env_id,
        title=f"EDS Migration: {site_url}",
    )
    fleet.session_id = session.id
    log.info("Session created: %s", session.id)

    task_message = _build_task_message(
        site_url, org, repo, fleet,
        github_token=github_token,
        eds_token=eds_token,
    )

    events_count = 0
    reached_idle = False
    start = time.monotonic()
    event_logger = EventLogger(fleet, verbose=verbose)

    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": task_message}],
        }],
    )
    log.info("Task message sent. Streaming events...")

    reconnects = 0

    while not reached_idle:
        try:
            if reconnects:
                log.info("Reconnecting to stream (attempt %d/%d)...",
                         reconnects, MAX_RECONNECTS)

            with client.beta.sessions.events.stream(
                session.id,
                timeout=_STREAM_TIMEOUT,
            ) as stream:
                for event in stream:
                    events_count += 1
                    event_logger.handle(event)

                    if event.type == "session.status_idle":
                        log.info("Session reached idle state.")
                        reached_idle = True
                        break

        except (httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ReadError) as exc:
            reconnects += 1
            if reconnects > MAX_RECONNECTS:
                log.error("Stream disconnected after %d reconnect attempts — giving up.", MAX_RECONNECTS)
                raise
            backoff = RECONNECT_BACKOFF_BASE ** reconnects
            log.warning("Stream interrupted (%s), reconnecting in %.0fs... (%d/%d)",
                        type(exc).__name__, backoff, reconnects, MAX_RECONNECTS)
            time.sleep(backoff)
            replayed = _catch_up(client, session.id, event_logger)
            events_count += replayed
            if replayed:
                log.info("Replayed %d missed events.", replayed)
            event_logger.reset_heartbeat()
            continue

        if not reached_idle:
            reconnects += 1
            if reconnects > MAX_RECONNECTS:
                break
            backoff = RECONNECT_BACKOFF_BASE ** reconnects
            log.warning("Stream ended without idle state, reconnecting in %.0fs... (%d/%d)",
                        backoff, reconnects, MAX_RECONNECTS)
            time.sleep(backoff)
            replayed = _catch_up(client, session.id, event_logger)
            events_count += replayed
            if replayed:
                log.info("Replayed %d missed events.", replayed)
            event_logger.reset_heartbeat()

    event_logger.stop()
    elapsed = time.monotonic() - start

    if not reached_idle:
        log.error(
            "Session %s stream ended after %.1fs (%d events) WITHOUT reaching idle state. "
            "The migration did not complete successfully.",
            session.id, elapsed, events_count,
        )
        raise RuntimeError(
            f"Session {session.id} never reached idle state after {events_count} events "
            f"and {reconnects} reconnect attempts. The orchestrator may have stalled or "
            f"the stream timed out. Check the session in the Anthropic dashboard."
        )

    log.info("Session %s completed in %.1fs (%d events)", session.id, elapsed, events_count)

    return SessionResult(
        session_id=session.id,
        status="completed",
        duration_s=elapsed,
        events_received=events_count,
    )


def _build_task_message(
    site_url: str,
    org: str,
    repo: str,
    fleet: MigrationFleet,
    *,
    github_token: str,
    eds_token: str | None = None,
) -> str:
    """Build the initial user message that kicks off the migration."""
    from eds_migrate.tier1 import TIER1_SCRIPTS

    tier1_block = ""
    for phase_key, script_fn in TIER1_SCRIPTS.items():
        tier1_block += f"\n### Tier 1 script for {phase_key}\n"
        tier1_block += f"Save this to `tier1/{phase_key}.sh` and run with `bash tier1/{phase_key}.sh`:\n"
        tier1_block += f"```bash\n{script_fn()}\n```\n"

    eds_token_block = ""
    if eds_token:
        eds_token_block = f"""\
export EDS_TOKEN="{eds_token}"
echo "EDS access token configured." """
    else:
        eds_token_block = """\
echo "WARNING: No EDS token provided — content authoring steps will use fallback (manual import)." """

    from eds_migrate.prompts import _load

    template = _load("templates/lead-task.md")
    return template.format(
        site_url=site_url,
        org=org,
        repo=repo,
        github_token=github_token,
        eds_token_block=eds_token_block,
        tier1_block=tier1_block,
        workers=", ".join(a.name for a in fleet.all_workers),
        verifiers=", ".join(a.name for a in fleet.all_verifiers),
    )


_TOOL_OUTPUT_LIMIT = 2000
_AGENT_MSG_LIMIT = 4000


def _catch_up(
    client: Anthropic,
    session_id: str,
    event_logger: "EventLogger",
) -> int:
    """Fetch historical events via list API and replay any missed ones.

    Returns the number of new events replayed.  The EventLogger's dedup
    set ensures we never process the same event twice, so it's safe to
    call this even if some events were already consumed from the stream.
    """
    new_count = 0
    try:
        for event in client.beta.sessions.events.list(
            session_id, order="asc", limit=100,
        ):
            eid = getattr(event, "id", None)
            if eid and eid not in event_logger._seen_ids:
                new_count += 1
                event_logger.handle(event)
    except Exception as exc:
        log.warning("Failed to catch up on missed events: %s", exc)
    return new_count


_HEARTBEAT_INTERVAL = 30  # seconds


class EventLogger:
    """Stateful event logger that tracks agent dispatch nesting and heartbeat."""

    def __init__(self, fleet: MigrationFleet, verbose: bool = False):
        self.verbose = verbose
        self._agent_stack: list[str] = ["Orchestrator"]
        self._pending_agent_calls: dict[str, str] = {}
        self._id_to_name: dict[str, str] = {}
        for agent in fleet.all_agents:
            self._id_to_name[agent.id] = agent.name

        self._seen_ids: set[str] = set()
        self._last_event_time = time.monotonic()
        self._in_model_request = False
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True,
        )
        self._heartbeat_thread.start()

    def stop(self):
        self._heartbeat_stop.set()

    def reset_heartbeat(self):
        """Reset heartbeat timer after reconnection so elapsed time restarts."""
        self._last_event_time = time.monotonic()
        self._in_model_request = False

    def _heartbeat_loop(self):
        while not self._heartbeat_stop.wait(_HEARTBEAT_INTERVAL):
            if self._in_model_request:
                elapsed = int(time.monotonic() - self._last_event_time)
                _status(f"{self._indent}[{self._who}] ⏳ model request running ({elapsed}s)")

    @property
    def _who(self) -> str:
        return self._agent_stack[-1] if self._agent_stack else "?"

    @property
    def _indent(self) -> str:
        depth = max(0, len(self._agent_stack) - 1)
        return "│ " * depth

    def handle(self, event) -> None:
        eid = getattr(event, "id", None)
        if eid:
            if eid in self._seen_ids:
                return
            self._seen_ids.add(eid)

        self._last_event_time = time.monotonic()
        etype = event.type

        # ── Session lifecycle ──
        if etype == "session.status_running":
            _status("[session] running")
        elif etype == "session.status_idle":
            _status("[session] idle — migration complete")
        elif etype == "session.status_terminated":
            _status("[session] TERMINATED")
        elif etype == "session.status_rescheduled":
            _status("[session] rescheduled (will resume)")

        # ── Errors ──
        elif etype == "session.error":
            err = event.error
            msg = getattr(err, "message", str(err))
            err_type = getattr(err, "type", "unknown")
            _status(f"{self._indent}[ERROR] {err_type}: {msg}")

        # ── Agent messages ──
        elif etype == "agent.message":
            for block in event.content:
                if hasattr(block, "text"):
                    text = block.text.strip()
                    if not text:
                        continue
                    if self.verbose:
                        for line in text.split("\n"):
                            _status(f"{self._indent}[{self._who}] {line}")
                    else:
                        preview = text[:500]
                        if len(text) > 500:
                            preview += "..."
                        _status(f"{self._indent}[{self._who}] {preview}")

        # ── Thinking (progress signal, no content) ──
        elif etype == "agent.thinking":
            _status(f"{self._indent}[{self._who}] thinking...")

        # ── Built-in tool use ──
        elif etype == "agent.tool_use":
            tool = getattr(event, "name", "unknown")
            inp = getattr(event, "input", {})
            eid = getattr(event, "id", "")

            if tool == "agent":
                agent_id = str(inp.get("agent_id", ""))
                agent_name = self._id_to_name.get(agent_id, agent_id[:20])
                self._pending_agent_calls[eid] = agent_name
                msg_text = str(inp.get("message", ""))
                _status(f"{self._indent}┌─ DISPATCH {self._who} → {agent_name}")
                if self.verbose and msg_text:
                    for line in _redact(msg_text[:_AGENT_MSG_LIMIT]).split("\n"):
                        _status(f"{self._indent}│  {line}")
                elif msg_text:
                    preview = _redact(msg_text.strip()[:300])
                    _status(f"{self._indent}│  {preview}")
                self._agent_stack.append(agent_name)
            else:
                summary = _summarize_tool_input(tool, inp)
                tag = f"{self._indent}[{self._who}] {tool}"
                if summary:
                    _status(f"{tag} — {summary}")
                else:
                    _status(tag)

        # ── Built-in tool result ──
        elif etype == "agent.tool_result":
            is_error = getattr(event, "is_error", False)
            tool_use_id = getattr(event, "tool_use_id", "")

            if tool_use_id in self._pending_agent_calls:
                agent_name = self._pending_agent_calls.pop(tool_use_id)
                if self._agent_stack and self._agent_stack[-1] == agent_name:
                    self._agent_stack.pop()
                content = getattr(event, "content", None)
                text = _extract_text(content)
                status = "ERROR" if is_error else "done"
                _status(f"{self._indent}└─ RETURN {agent_name} ({status})")
                if text:
                    preview = _redact(text[:500 if not self.verbose else _AGENT_MSG_LIMIT])
                    for line in preview.split("\n")[:20]:
                        _status(f"{self._indent}   {line}")
                    if len(text) > (500 if not self.verbose else _AGENT_MSG_LIMIT):
                        _status(f"{self._indent}   ... ({len(text)} chars total)")
            else:
                prefix = f"{self._indent}[{self._who}] result"
                if is_error:
                    prefix += " ERROR"
                content = getattr(event, "content", None)
                text = _extract_text(content)
                if self.verbose:
                    if text:
                        truncated = _redact(text[:_TOOL_OUTPUT_LIMIT])
                        if len(text) > _TOOL_OUTPUT_LIMIT:
                            truncated += f"\n  ... ({len(text) - _TOOL_OUTPUT_LIMIT} chars truncated)"
                        _status(f"{prefix}\n{truncated}")
                    else:
                        _status(f"{prefix} (no text content)")
                else:
                    if text:
                        preview = _redact(text.strip()[:500])
                        _status(f"{prefix}\n{preview}")
                    elif is_error:
                        _status(f"{prefix} (no details)")

        # ── MCP tool use/result ──
        elif etype == "agent.mcp_tool_use":
            server = getattr(event, "server_name", "?")
            tool = getattr(event, "name", "unknown")
            _status(f"{self._indent}[{self._who}] mcp {server}/{tool}")
        elif etype == "agent.mcp_tool_result":
            is_error = getattr(event, "is_error", False)
            label = "mcp_result ERROR" if is_error else "mcp_result"
            if self.verbose:
                content = getattr(event, "content", None)
                text = _extract_text(content)
                _status(f"{self._indent}[{self._who}] {label}: {(text or '')[:500]}")

        # ── Model request spans ──
        elif etype == "span.model_request_start":
            self._in_model_request = True
            _status(f"{self._indent}[{self._who}] model request started")
        elif etype == "span.model_request_end":
            self._in_model_request = False
            usage = getattr(event, "model_usage", None)
            is_error = getattr(event, "is_error", False)
            if usage:
                inp = usage.input_tokens
                out = usage.output_tokens
                cached = usage.cache_read_input_tokens
                _status(f"{self._indent}[{self._who}] model — {inp} in / {out} out / {cached} cached"
                         + (" [ERROR]" if is_error else ""))
            elif is_error:
                _status(f"{self._indent}[{self._who}] model request failed")

        # ── Context compaction ──
        elif etype == "agent.thread_context_compacted":
            _status(f"{self._indent}[{self._who}] context compacted")

        # ── User events ──
        elif etype == "user.message":
            if self.verbose:
                _status("[user.message] (echo)")
        elif etype == "user.interrupt":
            _status("[user.interrupt]")

        # ── Catch-all ──
        else:
            _status(f"{self._indent}[event] {etype}")


_SECRET_PATTERN = re.compile(
    r'(ghp_\w{4})\w+|'           # GitHub PAT
    r'(eyJ[A-Za-z0-9_-]{4})[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|'  # JWT
    r'(x-access-token:)[^\s@"]+',  # git credential URL
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    """Mask tokens and secrets in log output."""
    def _repl(m):
        if m.group(1):
            return m.group(1) + "****"
        if m.group(2):
            return m.group(2) + "****"
        if m.group(3):
            return m.group(3) + "****"
        return "****"
    return _SECRET_PATTERN.sub(_repl, text)


def _summarize_tool_input(tool: str, inp: dict) -> str:
    """One-line summary of a tool invocation's input."""
    if tool == "bash" and "command" in inp:
        cmd = str(inp["command"]).strip()
        if len(cmd) > 200:
            cmd = cmd[:200] + "..."
        return _redact(cmd)
    if tool == "file" and "path" in inp:
        action = inp.get("action", "read")
        return f"{action} {inp['path']}"
    if tool == "agent" and "agent_id" in inp:
        msg = str(inp.get("message", ""))[:120]
        return f"→ {inp['agent_id'][:20]}... | {_redact(msg)}"
    return _redact(json.dumps(inp, default=str)[:200])


def _extract_text(content) -> str | None:
    """Pull text from a list of content blocks."""
    if not content:
        return None
    parts = []
    for block in content:
        if hasattr(block, "text") and block.text is not None:
            parts.append(block.text)
    return "\n".join(parts) if parts else None


def _status(msg: str) -> None:
    """Print a timestamped status line to stderr."""
    ts = time.strftime("%H:%M:%S")
    for i, line in enumerate(msg.split("\n")):
        prefix = f"  {ts} " if i == 0 else "         "
        print(f"{prefix}{line}", file=sys.stderr)
