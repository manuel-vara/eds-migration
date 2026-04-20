"""
Session management — starting, streaming, and interacting with CMA sessions.

This module runs the Orchestrator session and acts as the dispatch router
for its custom tools.  Multi-agent delegation via ``callable_agents`` is
a gated research-preview feature, so we replace it with a Python-side
fan-out: whenever the Orchestrator calls one of its custom ``invoke_*``
or ``verify_*`` tools, we spin up a brand-new worker/verifier session,
stream it to idle, and return its final text to the Orchestrator as a
``user.custom_tool_result`` event.  All worker sessions share state
through a common ``migration-state/{run_id}`` branch on the target
GitHub repo (see ``eds_migrate.state_workspace``).
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
from eds_migrate import router
from eds_migrate.state_workspace import StateWorkspace, create_workspace

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
    run_id: str,
    github_token: str,
    eds_token: str | None = None,
    verbose: bool = False,
) -> SessionResult:
    """Launch the Orchestrator session and drive it through custom tools.

    The Orchestrator has no bash/filesystem/web tools of its own — it
    delegates everything through custom tools that this function
    handles via the router, which spins up fresh worker/verifier
    sessions as needed.
    """
    log.info("Initialising migration-state workspace...")
    workspace = create_workspace(
        org=org, repo=repo, run_id=run_id, github_token=github_token,
    )
    router.bind_env(workspace, fleet.env_id)
    log.info(
        "Workspace ready at %s on branch %s", workspace.root, workspace.branch,
    )

    log.info("Creating orchestrator session...")
    session = client.beta.sessions.create(
        agent=fleet.orchestrator.id,
        environment_id=fleet.env_id,
        title=f"EDS Migration: {site_url}",
    )
    fleet.session_id = session.id
    log.info("Session created: %s", session.id)

    task_message = _build_task_message(
        site_url, org, repo, workspace, fleet,
        eds_token=eds_token,
    )

    events_count = 0
    start = time.monotonic()
    event_logger = EventLogger(fleet, verbose=verbose)

    # Pending custom tool calls we still owe the orchestrator a result for
    pending_tool_uses: dict[str, dict] = {}
    end_turn_reached = False
    retries_exhausted = False

    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": task_message}],
        }],
    )
    log.info("Task message sent. Streaming events...")

    reconnects = 0
    # When the orchestrator session goes idle with requires_action we service
    # the pending custom tools, send the results, and reopen the SSE stream.
    # That's the happy path, not a disconnect — so we don't count it as a
    # reconnect attempt.
    resume_after_tools = False

    while not end_turn_reached and not retries_exhausted:
        try:
            if reconnects:
                log.info("Reconnecting to stream (attempt %d/%d)...",
                         reconnects, MAX_RECONNECTS)
            elif resume_after_tools:
                log.info("Reopening stream after servicing custom tools.")

            resume_after_tools = False

            with client.beta.sessions.events.stream(
                session.id,
                timeout=_STREAM_TIMEOUT,
            ) as stream:
                stopped_for_action = False
                for event in stream:
                    events_count += 1
                    event_logger.handle(event)

                    etype = getattr(event, "type", "?")

                    if etype == "agent.custom_tool_use":
                        pending_tool_uses[event.id] = {
                            "name": event.name,
                            "input": dict(event.input or {}),
                        }

                    elif etype == "session.status_idle":
                        stop_reason = getattr(event, "stop_reason", None)
                        stop_type = getattr(stop_reason, "type", None)
                        if stop_type == "end_turn":
                            end_turn_reached = True
                            break
                        if stop_type == "retries_exhausted":
                            retries_exhausted = True
                            break
                        if stop_type == "requires_action":
                            expected_ids = list(
                                getattr(stop_reason, "event_ids", None) or []
                            )
                            _service_pending_tools(
                                client=client,
                                session_id=session.id,
                                fleet=fleet,
                                workspace=workspace,
                                pending=pending_tool_uses,
                                expected_ids=expected_ids,
                                eds_token=eds_token,
                                event_reporter=event_logger.report_router,
                            )
                            stopped_for_action = True
                            resume_after_tools = True
                            # The server closes the SSE stream when the
                            # session is idle.  Leave the inner loop and
                            # reopen in the next iteration of `while`.
                            break

                # If we broke out for end_turn / retries_exhausted / action,
                # skip the stream-ended reconnect path.
                if end_turn_reached or retries_exhausted or stopped_for_action:
                    reconnects = 0
                    event_logger.reset_heartbeat()
                    continue

        except (httpx.ReadTimeout, httpx.RemoteProtocolError, httpx.ReadError) as exc:
            reconnects += 1
            if reconnects > MAX_RECONNECTS:
                log.error("Stream disconnected after %d reconnect attempts — giving up.", MAX_RECONNECTS)
                raise
            backoff = RECONNECT_BACKOFF_BASE ** reconnects
            log.warning("Stream interrupted (%s), reconnecting in %.0fs... (%d/%d)",
                        type(exc).__name__, backoff, reconnects, MAX_RECONNECTS)
            time.sleep(backoff)
            replayed = _catch_up(client, session.id, event_logger, pending_tool_uses)
            events_count += replayed
            if replayed:
                log.info("Replayed %d missed events.", replayed)
            event_logger.reset_heartbeat()
            continue

        # Stream ended without end_turn AND we didn't stop for action — treat
        # as a transient disconnect and reconnect with backoff.
        reconnects += 1
        if reconnects > MAX_RECONNECTS:
            break
        backoff = RECONNECT_BACKOFF_BASE ** reconnects
        log.warning("Stream ended without end_turn, reconnecting in %.0fs... (%d/%d)",
                    backoff, reconnects, MAX_RECONNECTS)
        time.sleep(backoff)
        replayed = _catch_up(client, session.id, event_logger, pending_tool_uses)
        events_count += replayed
        if replayed:
            log.info("Replayed %d missed events.", replayed)
        event_logger.reset_heartbeat()

    event_logger.stop()
    elapsed = time.monotonic() - start

    # Best-effort final checkpoint — not fatal if it fails
    try:
        workspace.pull()
        workspace.push_checkpoint(
            "completed" if end_turn_reached else "interrupted",
            extra={"events": events_count, "duration_s": round(elapsed, 1)},
        )
    except Exception as exc:
        log.warning("Failed to write final checkpoint: %s", exc)

    if retries_exhausted:
        raise RuntimeError(
            f"Orchestrator session {session.id} ended with retries_exhausted."
        )
    if not end_turn_reached:
        log.error(
            "Session %s stream ended after %.1fs (%d events) WITHOUT end_turn.",
            session.id, elapsed, events_count,
        )
        raise RuntimeError(
            f"Session {session.id} never completed normally after "
            f"{events_count} events and {reconnects} reconnect attempts."
        )

    log.info("Session %s completed in %.1fs (%d events)", session.id, elapsed, events_count)

    return SessionResult(
        session_id=session.id,
        status="completed",
        duration_s=elapsed,
        events_received=events_count,
    )


# ---------------------------------------------------------------------------
# Dispatch-to-worker plumbing


def _service_pending_tools(
    *,
    client: Anthropic,
    session_id: str,
    fleet: MigrationFleet,
    workspace: StateWorkspace,
    pending: dict[str, dict],
    expected_ids: list[str],
    eds_token: str | None,
    event_reporter,
) -> None:
    """Dispatch every pending custom tool call and send results back."""
    # If the session tells us which IDs it's blocked on, service exactly those;
    # otherwise service everything we've seen.
    ids_to_service = expected_ids or list(pending.keys())
    if not ids_to_service:
        return

    for tool_use_id in ids_to_service:
        spec = pending.pop(tool_use_id, None)
        if spec is None:
            log.warning(
                "orchestrator blocked on unknown tool_use_id=%s; "
                "sending empty error result",
                tool_use_id,
            )
            _send_custom_tool_result(
                client, session_id, tool_use_id,
                text=f"router could not find pending spec for {tool_use_id}",
                is_error=True,
            )
            continue

        name = spec["name"]
        tinput = spec["input"]
        event_reporter(
            f"dispatching custom tool {name} (id={tool_use_id[:10]})"
        )

        if not router.is_custom_tool(name):
            _send_custom_tool_result(
                client, session_id, tool_use_id,
                text=f"unknown custom tool: {name}", is_error=True,
            )
            continue

        result = router.dispatch(
            client=client,
            fleet=fleet,
            workspace=workspace,
            tool_name=name,
            tool_input=tinput,
            eds_token=eds_token,
            event_reporter=event_reporter,
        )
        _send_custom_tool_result(
            client, session_id, tool_use_id,
            text=result.text, is_error=result.is_error,
        )


def _send_custom_tool_result(
    client: Anthropic,
    session_id: str,
    tool_use_id: str,
    *,
    text: str,
    is_error: bool,
) -> None:
    """Post a ``user.custom_tool_result`` event back to the orchestrator."""
    # Cap length to something the model can reasonably absorb
    capped = text if len(text) <= 16000 else (text[:16000] + "\n… [truncated]")
    client.beta.sessions.events.send(
        session_id,
        events=[{
            "type": "user.custom_tool_result",
            "custom_tool_use_id": tool_use_id,
            "content": [{"type": "text", "text": capped}],
            "is_error": is_error,
        }],
    )


# ---------------------------------------------------------------------------
# Initial task message


def _build_task_message(
    site_url: str,
    org: str,
    repo: str,
    workspace: StateWorkspace,
    fleet: MigrationFleet,
    *,
    eds_token: str | None = None,
) -> str:
    """Build the initial user message that kicks off the migration."""
    from eds_migrate.prompts import _load

    template = _load("templates/lead-task.md")
    return template.format(
        site_url=site_url,
        org=org,
        repo=repo,
        run_id=workspace.run_id,
        state_branch=workspace.branch,
        eds_token_status="provided" if eds_token else "NOT PROVIDED",
        workers=", ".join(a.name for a in fleet.all_workers),
        verifiers=", ".join(a.name for a in fleet.all_verifiers),
    )


# ---------------------------------------------------------------------------
# Event catch-up on reconnect


_TOOL_OUTPUT_LIMIT = 2000
_AGENT_MSG_LIMIT = 4000


def _catch_up(
    client: Anthropic,
    session_id: str,
    event_logger: "EventLogger",
    pending_tool_uses: dict[str, dict],
) -> int:
    """Fetch historical events via list API and replay any missed ones.

    Returns the number of new events replayed.
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
                if getattr(event, "type", None) == "agent.custom_tool_use":
                    pending_tool_uses[event.id] = {
                        "name": event.name,
                        "input": dict(event.input or {}),
                    }
    except Exception as exc:
        log.warning("Failed to catch up on missed events: %s", exc)
    return new_count


# ---------------------------------------------------------------------------
# Event logging


_HEARTBEAT_INTERVAL = 30  # seconds


class EventLogger:
    """Stateful event logger for the Orchestrator stream."""

    def __init__(self, fleet: MigrationFleet, verbose: bool = False):
        self.verbose = verbose
        self._id_to_name: dict[str, str] = {
            agent.id: agent.name for agent in fleet.all_agents
        }
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
        self._last_event_time = time.monotonic()
        self._in_model_request = False

    def _heartbeat_loop(self):
        while not self._heartbeat_stop.wait(_HEARTBEAT_INTERVAL):
            if self._in_model_request:
                elapsed = int(time.monotonic() - self._last_event_time)
                _status(f"[Orchestrator] ⏳ model request running ({elapsed}s)")

    def report_router(self, msg: str) -> None:
        """Bridge the router's progress messages into the status stream."""
        _status(f"[router] {msg}")

    def handle(self, event) -> None:
        eid = getattr(event, "id", None)
        if eid:
            if eid in self._seen_ids:
                return
            self._seen_ids.add(eid)

        self._last_event_time = time.monotonic()
        etype = event.type

        if etype == "session.status_running":
            _status("[session] running")
        elif etype == "session.status_idle":
            stop_reason = getattr(event, "stop_reason", None)
            stop_type = getattr(stop_reason, "type", "?")
            _status(f"[session] idle — stop_reason={stop_type}")
        elif etype == "session.status_terminated":
            _status("[session] TERMINATED")
        elif etype == "session.status_rescheduled":
            _status("[session] rescheduled (will resume)")

        elif etype == "session.error":
            err = event.error
            msg = getattr(err, "message", str(err))
            err_type = getattr(err, "type", "unknown")
            _status(f"[ERROR] {err_type}: {msg}")

        elif etype == "agent.message":
            for block in event.content:
                if hasattr(block, "text"):
                    text = block.text.strip()
                    if not text:
                        continue
                    if self.verbose:
                        for line in text.split("\n"):
                            _status(f"[Orchestrator] {line}")
                    else:
                        preview = text[:500]
                        if len(text) > 500:
                            preview += "..."
                        _status(f"[Orchestrator] {preview}")

        elif etype == "agent.thinking":
            _status("[Orchestrator] thinking...")

        elif etype == "agent.custom_tool_use":
            tool = getattr(event, "name", "unknown")
            tinput = getattr(event, "input", {}) or {}
            eid = getattr(event, "id", "")[:10]
            summary = _summarize_custom_tool_input(tool, tinput)
            _status(f"[Orchestrator] ▶ {tool} ({eid}) — {summary}")

        elif etype == "agent.tool_use":
            # Orchestrator has no built-in tools in the new design, but we
            # still log them defensively in case that changes.
            tool = getattr(event, "name", "unknown")
            tinput = getattr(event, "input", {}) or {}
            _status(f"[Orchestrator] (builtin) {tool} "
                    f"— {_redact(json.dumps(tinput, default=str)[:200])}")

        elif etype == "agent.tool_result":
            is_error = getattr(event, "is_error", False)
            label = "result ERROR" if is_error else "result"
            content = getattr(event, "content", None)
            text = _extract_text(content)
            if text:
                preview = _redact(text.strip()[:500])
                _status(f"[Orchestrator] {label}: {preview}")

        elif etype == "span.model_request_start":
            self._in_model_request = True
            _status("[Orchestrator] model request started")
        elif etype == "span.model_request_end":
            self._in_model_request = False
            usage = getattr(event, "model_usage", None)
            is_error = getattr(event, "is_error", False)
            if usage:
                inp = usage.input_tokens
                out = usage.output_tokens
                cached = usage.cache_read_input_tokens
                _status(
                    f"[Orchestrator] model — {inp} in / {out} out / "
                    f"{cached} cached" + (" [ERROR]" if is_error else "")
                )
            elif is_error:
                _status("[Orchestrator] model request failed")

        elif etype == "agent.thread_context_compacted":
            _status("[Orchestrator] context compacted")

        elif etype == "user.message":
            if self.verbose:
                _status("[user.message] (echo)")
        elif etype == "user.custom_tool_result":
            if self.verbose:
                tid = getattr(event, "custom_tool_use_id", "?")[:10]
                _status(f"[router→orchestrator] custom_tool_result ({tid})")
        elif etype == "user.interrupt":
            _status("[user.interrupt]")
        else:
            _status(f"[event] {etype}")


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


def _summarize_custom_tool_input(tool: str, inp: dict) -> str:
    """One-line summary of a custom tool invocation's input."""
    if tool == "invoke_page_migrator":
        urls = inp.get("urls") or []
        task = str(inp.get("task", ""))
        return f"{len(urls)} urls | {_redact(task[:120])}"
    if tool == "invoke_analyzer":
        phase = inp.get("phase", "?")
        task = str(inp.get("task", ""))
        return f"phase={phase} | {_redact(task[:120])}"
    if "task" in inp:
        return _redact(str(inp["task"])[:200])
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
