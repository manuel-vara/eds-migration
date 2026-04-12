"""
Session management — starting, streaming, and interacting with CMA sessions.

This module provides the core loop that the orchestrator uses to drive the
migration. It creates a session for the orchestrator agent, sends the initial
task message, and streams events back to the caller.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import dataclass

from anthropic import Anthropic

from eds_migrate.agents import MigrationFleet

log = logging.getLogger(__name__)


@dataclass
class SessionResult:
    """Outcome of a completed session."""
    session_id: str
    status: str
    duration_s: float
    events_received: int


def _pick_env(fleet: MigrationFleet, phase: str) -> str:
    """Select the right environment for a given phase."""
    heavy_phases = {"3-build"}
    npm_phases = {"1-discover", "3.5-pilot", "4-migrate", "6-qa"}
    if phase in heavy_phases:
        return fleet.env_heavy_id
    if phase in npm_phases:
        return fleet.env_npm_id
    return fleet.env_basic_id


def run_migration(
    client: Anthropic,
    fleet: MigrationFleet,
    site_url: str,
    org: str,
    repo: str,
    *,
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
    goes idle.
    """
    env_id = fleet.env_heavy_id

    log.info("Creating orchestrator session...")
    session = client.beta.sessions.create(
        agent=fleet.orchestrator.id,
        environment_id=env_id,
        title=f"EDS Migration: {site_url}",
    )
    log.info("Session created: %s", session.id)

    task_message = _build_task_message(site_url, org, repo, fleet)

    events_count = 0
    start = time.monotonic()

    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[{
                "type": "user.message",
                "content": [{"type": "text", "text": task_message}],
            }],
        )
        log.info("Task message sent. Streaming events...")

        for event in stream:
            events_count += 1
            _handle_event(event, verbose=verbose)

            if event.type == "session.status_idle":
                log.info("Session reached idle state.")
                break

    elapsed = time.monotonic() - start
    log.info("Session %s completed in %.1fs (%d events)", session.id, elapsed, events_count)

    return SessionResult(
        session_id=session.id,
        status="completed",
        duration_s=elapsed,
        events_received=events_count,
    )


def _build_task_message(
    site_url: str, org: str, repo: str, fleet: MigrationFleet,
) -> str:
    """Build the initial user message that kicks off the migration."""
    from eds_migrate.knowledge import build_setup_script
    from eds_migrate.tier1 import TIER1_SCRIPTS

    tier1_block = ""
    for phase_key, script_fn in TIER1_SCRIPTS.items():
        tier1_block += f"\n### Tier 1 script for {phase_key}\n"
        tier1_block += f"Save this to `tier1/{phase_key}.sh` and run with `bash tier1/{phase_key}.sh`:\n"
        tier1_block += f"```bash\n{script_fn()}\n```\n"

    knowledge_script = build_setup_script()

    return f"""\
# EDS Migration Task

Migrate **{site_url}** to AEM Edge Delivery Services.

## Step 0 — Set Up Knowledge Base

**Before doing anything else**, run this script to populate `/knowledge/`
with EDS skills and platform docs. All worker and verifier agents have
catalogs in their system prompts pointing to these files — they will read
them on demand during their tasks.

Save this to `setup-knowledge.sh` and run it:
```bash
{knowledge_script}
```

## Configuration
- GitHub org: `{org}`
- GitHub repo: `{repo}`
- da.live path: `{org}/{repo}`
- Preview URL: `https://main--{repo}--{org}.aem.page/`

## Credentials
- GitHub token: available via vault `github-token`
- da.live IMS token: available via vault `da-token`

## Instructions

Execute the migration phases in order. For each phase:

1. First, save the Tier 1 validation script to `tier1/` and make it executable
2. Dispatch the appropriate worker agent with its task
3. Run the Tier 1 script: `bash tier1/<phase>.sh`
4. If Tier 1 fails, send the errors to the worker and have it retry
5. If Tier 1 passes and the phase has a Tier 2 verifier, dispatch it
6. If Tier 2 fails, send feedback to the worker (latest feedback only) and retry
7. If all retries exhausted, apply autonomous fallback per the rules in your system prompt
8. Verify the worker wrote its phase documentation to `docs/`
9. Write migration-state.json checkpoint after each phase

After all phases complete, write `docs/MIGRATION-REPORT.md` and push `docs/` to GitHub.

## Agent Roster
Workers: {', '.join(a.name for a in fleet.all_workers)}
Verifiers: {', '.join(a.name for a in fleet.all_verifiers)}

## Tier 1 Validation Scripts
{tier1_block}

Begin with Step 0 (knowledge setup), then Phase 1 — Discovery. Good luck.
"""


def _handle_event(event, *, verbose: bool = False) -> None:
    """Process a single SSE event from the session stream."""
    etype = event.type

    if etype == "agent.message":
        for block in event.content:
            if hasattr(block, "text") and verbose:
                sys.stdout.write(block.text)
                sys.stdout.flush()
    elif etype == "agent.tool_use":
        tool = event.name if hasattr(event, "name") else "unknown"
        _print_status(f"[tool] {tool}")
    elif etype == "agent.agent_call":
        agent_name = getattr(event, "agent_name", "unknown")
        _print_status(f"[dispatch] → {agent_name}")
    elif etype == "agent.agent_return":
        agent_name = getattr(event, "agent_name", "unknown")
        _print_status(f"[return] ← {agent_name}")
    elif etype == "session.status_running":
        _print_status("[session] running")
    elif etype == "session.status_idle":
        _print_status("[session] idle — migration complete")
    elif verbose:
        _print_status(f"[event] {etype}")


def _print_status(msg: str) -> None:
    """Print a timestamped status line to stderr."""
    ts = time.strftime("%H:%M:%S")
    print(f"  {ts} {msg}", file=sys.stderr)
