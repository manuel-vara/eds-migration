"""
Dispatch router for the Orchestrator's custom tools.

The Orchestrator no longer uses multi-agent delegation (which is a gated
research-preview feature).  Instead it is given a suite of custom tools
— ``invoke_crawler``, ``verify_analyzer``, etc. — and this module is the
Python-side handler that:

1. Translates each tool call into a brand-new worker/verifier session
   (scoped to the same CMA environment).
2. Injects a git-bootstrap preamble so the worker clones the target
   repo, checks out the ``migration-state/{run_id}`` branch, and commits
   its artifacts under ``.eds-migration/state/`` before returning.
3. Streams the worker session to idle, collects its final text, and
   returns a ``user.custom_tool_result`` payload to the Orchestrator.
4. For verifiers, reads their structured JSON verdicts from the state
   branch (so the Orchestrator gets a machine-readable result even if
   the agent's final message is chatty).

The router is intentionally a pure dispatcher: it does not compute
verdicts, score parity, or otherwise second-guess the agents.  All
fidelity gates live in verifier prompts, which require per-page
screenshot pairs and cited visual-similarity evidence.

Concurrency: Phase 4 (content migration) is batched by the Orchestrator
through a single ``invoke_page_migrator`` call that carries a list of
URLs; the router splits the list into chunks and runs up to
``PHASE4_PARALLELISM`` worker sessions in parallel.
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable

import httpx
from anthropic import Anthropic

from eds_migrate.agents import AgentRef, MigrationFleet
from eds_migrate.state_workspace import StateWorkspace, STATE_DIR, VERIFIER_DIR

log = logging.getLogger(__name__)


PHASE4_PARALLELISM = 4
WORKER_SESSION_READ_TIMEOUT = 1800.0   # 30 minutes per worker turn
WORKER_SESSION_MAX_WALL = 3600.0       # 1 hour hard cap per worker session


# ---------------------------------------------------------------------------
# Custom tool registry


def build_custom_tools() -> list[dict]:
    """Return the list of custom-tool definitions attached to the Orchestrator.

    Names are stable identifiers the router matches on.
    """
    return [
        {
            "type": "custom",
            "name": "invoke_crawler",
            "description": (
                "Launch the Crawler worker to crawl the source site and write "
                "`.eds-migration/state/manifest.json` on the migration-state "
                "branch. Use this exactly once per run (Phase 1). Returns the "
                "worker's completion summary."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task instructions for the Crawler.",
                    },
                },
                "required": ["task"],
            },
        },
        {
            "type": "custom",
            "name": "invoke_analyzer",
            "description": (
                "Launch the Analyzer worker to execute one of phases 2a "
                "(sample scrape), 2b (block inventory), or 2c (blueprint). "
                "Reads from `.eds-migration/state/manifest.json` and writes "
                "into `.eds-migration/state/`."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": ["2a", "2b", "2c"],
                        "description": "Which Analyzer sub-phase to run.",
                    },
                    "task": {
                        "type": "string",
                        "description": "Task instructions for this sub-phase.",
                    },
                },
                "required": ["phase", "task"],
            },
        },
        {
            "type": "custom",
            "name": "invoke_block_dev",
            "description": (
                "Launch the Block Dev worker to scaffold the EDS codebase, "
                "build blocks from the blueprint, run `npm run lint`, and "
                "push to the main branch of the target GitHub repo."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                },
                "required": ["task"],
            },
        },
        {
            "type": "custom",
            "name": "invoke_page_migrator",
            "description": (
                "Launch one or more Page Migrator workers to migrate a batch "
                "of pages to da.live and trigger their previews.  Pass the "
                "full list of source URLs — the router will split them into "
                f"up to {PHASE4_PARALLELISM} parallel worker sessions and "
                "merge the results."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of source page URLs to migrate.",
                    },
                    "task": {
                        "type": "string",
                        "description": (
                            "Task template applied to every worker chunk. "
                            "The router appends the chunk's URL list."
                        ),
                    },
                },
                "required": ["urls", "task"],
            },
        },
        {
            "type": "custom",
            "name": "invoke_config",
            "description": (
                "Launch the Config worker to generate redirects, metadata, "
                "nav, footer, helix-query.yaml, helix-sitemap.yaml, and "
                "robots.txt."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                },
                "required": ["task"],
            },
        },
        {
            "type": "custom",
            "name": "invoke_integration_qa",
            "description": (
                "Launch the Integration QA worker to run the final quality "
                "gate: Lighthouse, visual regression, link checks, redirect "
                "validation, and produce `.eds-migration/state/qa-report.json`."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                },
                "required": ["task"],
            },
        },
        # ---- Verifiers ----
        *[
            {
                "type": "custom",
                "name": f"verify_{phase}",
                "description": desc,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "notes": {
                            "type": "string",
                            "description": (
                                "Optional extra instructions or focus areas "
                                "for the verifier."
                            ),
                        },
                    },
                },
            }
            for phase, desc in [
                ("crawler",    "Run the Crawler Verifier on the current manifest.json and source-bundle. Returns a structured verdict."),
                ("analyzer",   "Run the Analyzer Verifier on the current blueprint.json."),
                ("block_dev",  "Run the Block Dev Verifier against the pushed GitHub repo and compare archetype screenshots to the source bundle."),
                ("pilot",      "Run the Pilot Verifier on the pilot-migrated pages with source-vs-preview screenshot comparison."),
                ("migration",  "Run the Migration Verifier on the full Phase 4 batch with source-vs-preview screenshot comparison per archetype."),
                ("config",     "Run the Config Verifier on the Phase 5 outputs, including rendered nav/footer vs source chrome comparison."),
            ]
        ],
    ]


# ---------------------------------------------------------------------------
# Tool → (agent, phase, artifact) routing


_TOOL_TO_WORKER: dict[str, str] = {
    "invoke_crawler":        "crawler",
    "invoke_analyzer":       "analyzer",
    "invoke_block_dev":      "block_dev",
    "invoke_page_migrator":  "page_migrator",
    "invoke_config":         "config",
    "invoke_integration_qa": "integration_qa",
}

_TOOL_TO_VERIFIER: dict[str, str] = {
    "verify_crawler":   "crawler_verifier",
    "verify_analyzer":  "analyzer_verifier",
    "verify_block_dev": "block_dev_verifier",
    "verify_pilot":     "pilot_verifier",
    "verify_migration": "migration_verifier",
    "verify_config":    "config_verifier",
}

_VERIFIER_RESULT_FILE: dict[str, str] = {
    "verify_crawler":   f"{VERIFIER_DIR}/crawler.json",
    "verify_analyzer":  f"{VERIFIER_DIR}/analyzer.json",
    "verify_block_dev": f"{VERIFIER_DIR}/block_dev.json",
    "verify_pilot":     f"{VERIFIER_DIR}/pilot.json",
    "verify_migration": f"{VERIFIER_DIR}/migration.json",
    "verify_config":    f"{VERIFIER_DIR}/config.json",
}


def is_custom_tool(name: str) -> bool:
    return name in _TOOL_TO_WORKER or name in _TOOL_TO_VERIFIER


# ---------------------------------------------------------------------------
# Dispatch


@dataclass
class DispatchResult:
    text: str
    is_error: bool


def dispatch(
    client: Anthropic,
    fleet: MigrationFleet,
    workspace: StateWorkspace,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    eds_token: str | None = None,
    event_reporter: "Callable[[str], None]" = lambda msg: None,
) -> DispatchResult:
    """Handle a single custom-tool invocation from the Orchestrator."""
    try:
        if tool_name in _TOOL_TO_WORKER:
            return _dispatch_worker(
                client, fleet, workspace, tool_name, tool_input,
                eds_token=eds_token, event_reporter=event_reporter,
            )
        if tool_name in _TOOL_TO_VERIFIER:
            return _dispatch_verifier(
                client, fleet, workspace, tool_name, tool_input,
                eds_token=eds_token, event_reporter=event_reporter,
            )
    except Exception as exc:
        log.exception("Dispatch failed for %s", tool_name)
        return DispatchResult(
            text=f"Dispatch error for {tool_name}: {exc}",
            is_error=True,
        )

    return DispatchResult(
        text=f"Unknown custom tool: {tool_name}",
        is_error=True,
    )


# ---------------------------------------------------------------------------
# Worker dispatch


def _dispatch_worker(
    client: Anthropic,
    fleet: MigrationFleet,
    workspace: StateWorkspace,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    eds_token: str | None,
    event_reporter: Callable[[str], None],
) -> DispatchResult:
    worker_attr = _TOOL_TO_WORKER[tool_name]
    agent: AgentRef | None = getattr(fleet, worker_attr, None)
    if agent is None:
        return DispatchResult(
            text=f"No agent registered for {tool_name} ({worker_attr}).",
            is_error=True,
        )

    # Pull latest state before dispatching so the router-side view is fresh
    workspace.pull()

    if tool_name == "invoke_page_migrator":
        return _dispatch_page_migrator_batch(
            client, agent, workspace, tool_input,
            eds_token=eds_token, event_reporter=event_reporter,
        )

    task = str(tool_input.get("task", "")).strip() or "(no task provided)"
    if tool_name == "invoke_analyzer":
        phase = str(tool_input.get("phase", "2")).strip()
        task = f"Run Analyzer sub-phase {phase}.\n\n{task}"

    prompt = _build_worker_prompt(
        workspace=workspace,
        agent_name=agent.name,
        task=task,
        eds_token=eds_token,
        commit_summary=f"{worker_attr}: task",
    )

    event_reporter(f"[router] dispatching {tool_name} → session on {agent.name}")
    summary = _run_worker_session(
        client, agent, workspace=workspace, prompt=prompt,
        event_reporter=event_reporter,
    )
    workspace.pull()

    return DispatchResult(text=summary, is_error=False)


def _dispatch_page_migrator_batch(
    client: Anthropic,
    agent: AgentRef,
    workspace: StateWorkspace,
    tool_input: dict[str, Any],
    *,
    eds_token: str | None,
    event_reporter: Callable[[str], None],
) -> DispatchResult:
    """Split a URL list into parallel chunks and run Page Migrator workers."""
    urls = list(tool_input.get("urls") or [])
    base_task = str(tool_input.get("task", "")).strip() or (
        "Migrate the listed pages following your per-page pipeline."
    )
    if not urls:
        return DispatchResult(
            text="invoke_page_migrator called with no URLs.", is_error=True,
        )

    chunks = _split_chunks(urls, PHASE4_PARALLELISM)
    event_reporter(
        f"[router] invoke_page_migrator: {len(urls)} URLs split into "
        f"{len(chunks)} parallel chunks (up to {PHASE4_PARALLELISM})"
    )

    def run_chunk(idx: int, chunk: list[str]) -> str:
        chunk_task = (
            f"{base_task}\n\n"
            f"Pages to migrate in this worker session (chunk {idx+1}/{len(chunks)}):\n"
            + "\n".join(f"- {u}" for u in chunk)
        )
        prompt = _build_worker_prompt(
            workspace=workspace,
            agent_name=f"{agent.name}#chunk{idx+1}",
            task=chunk_task,
            eds_token=eds_token,
            commit_summary=f"page_migrator: chunk {idx+1}/{len(chunks)}",
        )
        try:
            return _run_worker_session(
                client, agent, workspace=workspace, prompt=prompt,
                event_reporter=event_reporter,
            )
        except Exception as exc:
            log.exception("Page Migrator chunk %d failed", idx + 1)
            return f"chunk {idx+1} FAILED: {exc}"

    results: list[str] = [""] * len(chunks)
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=PHASE4_PARALLELISM,
    ) as pool:
        futures = {
            pool.submit(run_chunk, i, chunk): i
            for i, chunk in enumerate(chunks)
        }
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()

    workspace.pull()

    combined = "\n\n".join(
        f"## Chunk {i+1}/{len(chunks)} ({len(chunks[i])} URLs)\n{results[i]}"
        for i in range(len(chunks))
    )
    return DispatchResult(text=combined, is_error=False)


# ---------------------------------------------------------------------------
# Verifier dispatch


def _dispatch_verifier(
    client: Anthropic,
    fleet: MigrationFleet,
    workspace: StateWorkspace,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    eds_token: str | None,
    event_reporter: Callable[[str], None],
) -> DispatchResult:
    verifier_attr = _TOOL_TO_VERIFIER[tool_name]
    agent: AgentRef | None = getattr(fleet, verifier_attr, None)
    if agent is None:
        return DispatchResult(
            text=f"No agent registered for {tool_name} ({verifier_attr}).",
            is_error=True,
        )

    workspace.pull()

    notes = str(tool_input.get("notes", "")).strip()
    phase = tool_name.removeprefix("verify_")
    task = (
        f"Verify Phase '{phase}' output using the checks in your system prompt. "
        f"All inputs live under `.eds-migration/state/` on the "
        f"`{workspace.branch}` branch of this repo. When you reach a "
        f"verdict, write a JSON document to `{_VERIFIER_RESULT_FILE[tool_name]}` "
        f"with shape {{verdict:'PASS'|'FAIL', issues:[...], summary:'...'}}, "
        f"then commit and push it."
    )
    if notes:
        task += f"\n\nOrchestrator notes:\n{notes}"

    prompt = _build_worker_prompt(
        workspace=workspace,
        agent_name=agent.name,
        task=task,
        eds_token=eds_token,
        commit_summary=f"{verifier_attr}: verdict",
    )

    event_reporter(f"[router] dispatching {tool_name} → session on {agent.name}")
    summary = _run_worker_session(
        client, agent, workspace=workspace, prompt=prompt,
        event_reporter=event_reporter,
    )
    workspace.pull()

    verdict = workspace.read_json(_VERIFIER_RESULT_FILE[tool_name]) or {}

    if verdict:
        return DispatchResult(
            text=json.dumps(verdict, indent=2, default=str)[:6000],
            is_error=(verdict.get("verdict") == "FAIL"),
        )

    # No structured verdict found — return the agent's prose instead.
    return DispatchResult(
        text=(
            f"Verifier {tool_name} finished but did not write "
            f"{_VERIFIER_RESULT_FILE[tool_name]}. Agent summary:\n\n{summary}"
        ),
        is_error=True,
    )


# ---------------------------------------------------------------------------
# Worker session plumbing


def _build_worker_prompt(
    *,
    workspace: StateWorkspace,
    agent_name: str,
    task: str,
    eds_token: str | None,
    commit_summary: str,
) -> str:
    """Render the git-bootstrap preamble + task instructions for a worker."""
    token_export = (
        f'export EDS_TOKEN="{eds_token}"\n' if eds_token else
        'echo "WARNING: no EDS_TOKEN provided — content authoring will fail"\n'
    )
    safe_commit = commit_summary.replace('"', "'")
    return f"""# Migration Task: {agent_name}

You are part of the EDS migration fleet. Before doing anything else, set up
your workspace on the shared migration-state branch. Then do your task. Then
commit and push your artifacts.

## Step 0 — Workspace bootstrap

Run these commands *exactly* in a single bash invocation before doing any
other work. If any command fails, stop and report the error verbatim.

```bash
set -e
mkdir -p /home/claude/migration-workspace
cd /home/claude/migration-workspace
if [ ! -d .git ]; then
  git clone --quiet "{workspace.remote_url}" .
fi
git config user.email "eds-migrate@automation.local"
git config user.name  "EDS Migration Agent"
git fetch --quiet origin
if git rev-parse --verify --quiet "origin/{workspace.branch}" >/dev/null; then
  git checkout -B "{workspace.branch}" "origin/{workspace.branch}"
else
  git checkout -B "{workspace.branch}"
fi
mkdir -p {STATE_DIR} {VERIFIER_DIR}
# Prevent ad-hoc helper scripts from being picked up by `git add -A` later.
# These are scratch artifacts (e.g. Playwright scrapers written by the worker
# itself) that must never land in the repo, because the boilerplate CI runs
# ESLint on every branch and will fail on them.
mkdir -p .git/info
cat > .git/info/exclude <<'GITEXCLUDE'
# worker scratch — never commit root-level helper scripts.
# `.git/info/exclude` only hides UNTRACKED files, so tracked boilerplate
# files like `.eslintrc.js` are unaffected.
/*.js
/*.mjs
/*.cjs
/*.ts
/scratch/
/tmp/
/*.scratch.*
GITEXCLUDE
# Workers should write their own Playwright/HTTP helper scripts under a
# scratch directory OUTSIDE the repo (e.g. /home/claude/scratch/<worker>/),
# NOT in the repo root — otherwise `git add -A` + boilerplate ESLint CI
# fails on the next push.
mkdir -p /home/claude/scratch
{token_export}
echo "workspace ready on branch {workspace.branch}"
```

All artifact paths below are **relative to
`/home/claude/migration-workspace`** unless explicitly noted otherwise:

- Manifest:        `{STATE_DIR}/manifest.json`
- Blueprint:       `{STATE_DIR}/blueprint.json`
- Per-page status: `{STATE_DIR}/status/<url-hash>.json`
- Pending:         `{STATE_DIR}/pending-patterns.json`
- Analysis dir:    `{STATE_DIR}/analysis/<archetype>/<slug>/...`
- QA report:       `{STATE_DIR}/qa-report.json`
- Phase docs:      `{STATE_DIR}/docs/phaseN-*.md`
- Verifier JSON:   `{VERIFIER_DIR}/<phase>.json`

Read what you need with `cat` / `jq`, write results to the same paths.

## Step 1 — Task

{task}

## Step 2 — Commit and push

When your task is finished, commit any files you created or modified and
push them so downstream agents can see them:

```bash
cd /home/claude/migration-workspace
git add -A
if ! git diff --cached --quiet; then
  git commit -m "{safe_commit}"
  git push -u origin "{workspace.branch}"
fi
```

## Step 3 — Final message

Reply with a concise (≤400 words) summary of what you did: artifacts
written, notable decisions, any issues hit. Do not paste large file
contents — the orchestrator can read them from the branch.
"""


def _run_worker_session(
    client: Anthropic,
    agent: AgentRef,
    *,
    workspace: StateWorkspace,
    prompt: str,
    event_reporter: Callable[[str], None],
) -> str:
    """Create a fresh session on the given agent, run it to idle, return text."""
    session = client.beta.sessions.create(
        agent=agent.id,
        environment_id=_resolve_env_id(workspace, client, agent),
        title=f"{agent.name} @ {workspace.run_id}",
    )
    log.info("worker session %s on %s created", session.id, agent.name)
    event_reporter(f"[router]   session {session.id} on {agent.name}")

    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [{"type": "text", "text": prompt}],
        }],
    )

    timeout = httpx.Timeout(
        connect=30.0, read=WORKER_SESSION_READ_TIMEOUT, write=30.0, pool=30.0,
    )
    start = time.monotonic()
    final_text_chunks: list[str] = []
    try:
        with client.beta.sessions.events.stream(
            session.id, timeout=timeout,
        ) as stream:
            for event in stream:
                etype = getattr(event, "type", "?")
                if etype == "agent.message":
                    for block in getattr(event, "content", []) or []:
                        if hasattr(block, "text") and block.text:
                            final_text_chunks.append(block.text)
                elif etype == "session.status_idle":
                    break
                if time.monotonic() - start > WORKER_SESSION_MAX_WALL:
                    raise TimeoutError(
                        f"worker session {session.id} exceeded "
                        f"{WORKER_SESSION_MAX_WALL}s wall clock"
                    )
    finally:
        _cleanup_worker_session(client, session.id)

    text = "\n".join(final_text_chunks).strip()
    return text or f"(worker {agent.name} produced no final message)"


def _resolve_env_id(workspace: StateWorkspace, client: Anthropic, agent: AgentRef) -> str:
    """Return the env_id to run the worker session in.  Stashed on workspace."""
    env_id = getattr(workspace, "_env_id", None)
    if env_id:
        return env_id
    raise RuntimeError(
        "env_id is not attached to workspace — call workspace.bind_env() "
        "after fleet creation"
    )


def bind_env(workspace: StateWorkspace, env_id: str) -> None:
    """Attach the CMA env_id to the workspace so dispatches use it."""
    setattr(workspace, "_env_id", env_id)


def _cleanup_worker_session(client: Anthropic, session_id: str) -> None:
    """Best-effort delete/archive of a finished worker session."""
    for action in (
        lambda: client.beta.sessions.delete(session_id),
        lambda: client.beta.sessions.archive(session_id),
    ):
        try:
            action()
            return
        except Exception:
            continue


# ---------------------------------------------------------------------------
# Utilities


def _split_chunks(urls: list[str], n: int) -> list[list[str]]:
    """Split a URL list into up to ``n`` roughly-equal chunks."""
    if n <= 1 or len(urls) <= 1:
        return [list(urls)]
    n = min(n, len(urls))
    chunk_size = (len(urls) + n - 1) // n
    return [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]
