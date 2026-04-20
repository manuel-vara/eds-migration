# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**EDS Migration Agent** — a multi-agent system that uses Claude Managed Agents (CMA) to migrate websites to Adobe AEM Edge Delivery Services. It spins up a fleet of 13 specialised AI agents (1 orchestrator, 6 workers, 6 verifiers) that produce code, content, and documentation.

Multi-agent delegation via `callable_agents` is a gated research-preview feature, so the orchestrator does NOT call the workers directly. Instead it runs with **only custom tools** (`invoke_crawler`, `verify_analyzer`, …) and a Python-side dispatch router in `eds_migrate/router.py` turns each tool call into a fresh worker/verifier session. Workers share state through a dedicated `migration-state/{run_id}` git branch under `.eds-migration/state/`.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # fill in ANTHROPIC_API_KEY, GITHUB_TOKEN, optionally EDS_TOKEN
```

## Running

```bash
eds-migrate --site https://example.com --org my-org --repo my-site
eds-migrate --cleanup --run-id abc123   # tear down a previous run
```

Key flags: `--verbose`, `--log-level DEBUG`, `--run-id` (resume/cleanup a specific run).

## Architecture

The entrypoint (`eds_migrate/__main__.py`) performs 4 sequential steps:

1. **Deploy skills** (`knowledge/deploy.py`) — uploads the `knowledge/skills/*/SKILL.md` files to the Anthropic Skills API and attaches them to agents
2. **Create fleet** (`agents.py`) — provisions 13 CMA agents and a cloud environment. The orchestrator is created with **custom tools only** (no bash / filesystem / web) so it physically cannot do the work itself.
3. **Run migration** (`session.py` + `router.py`) — creates a session for the orchestrator and streams SSE events. Whenever the orchestrator calls a custom tool (`invoke_*` / `verify_*`), the Python router spins up a fresh worker/verifier session, streams it to idle, and returns its summary as a `user.custom_tool_result` event.
4. **Cleanup** (`agents.py`) — deletes agents and environment; skills are also torn down. The `migration-state/{run_id}` git branch is left in place for post-hoc inspection.

### Agent Topology

```
Orchestrator                           (custom tools only — no bash/read/write/web)
├── Workers: crawler, analyzer, block_dev, page_migrator, config, integration_qa
└── Verifiers: crawler, analyzer, block_dev, pilot, migration, config
```

Each phase uses a **prompts-only verification loop**. Every verifier
agent writes its own site-appropriate comparison script (typically
Playwright-based), renders both the source and migrated pages with a
settle strategy, and produces a verdict with an `evidence` array that
cites source-vs-preview screenshot pairs per viewport. The router is a
pure dispatcher — it does not compute parity, score similarity, or
otherwise second-guess the agents. All fidelity gates live in the
prompts under `prompts/verifiers/`.

### State sharing

Worker sessions don't share a filesystem, so all intermediate artifacts
live in a dedicated **`migration-state/{run_id}` branch** of the target
GitHub repo. The router keeps a local clone at
`./.migration-workspaces/{run_id}/` so it can read verifier verdicts
when summarising them back to the orchestrator. Every worker session's
initial user message embeds a git bootstrap that clones the repo,
checks out the state branch, and at the end commits + pushes any
changes.

Artifact paths (all relative to the repo root on the state branch):

- `.eds-migration/state/manifest.json` — Phase 1 output
- `.eds-migration/state/source-bundle/` — Phase 1 rendered ground truth
  (per-page rendered HTML + multi-viewport screenshots + header/footer
  chrome). Every downstream verifier compares against this bundle.
- `.eds-migration/state/blueprint.json` — Phase 2c output
- `.eds-migration/state/analysis/{archetype}/{slug}/...` — Phase 2a output
- `.eds-migration/state/status/{url-hash}.json` — Phase 4 per-page results
- `.eds-migration/state/pending-patterns.json` — Phase 4 escapes
- `.eds-migration/state/qa-report.json` — Phase 6 output
- `.eds-migration/state/docs/phaseN-*.md` — per-phase docs
- `.eds-migration/verifier-results/{phase}.json` — Verifier verdicts
- `.eds-migration/verifier-results/{phase}/screenshots/` — Verifier-captured preview screenshots paired with bundle source screenshots
- `.eds-migration/checkpoint.json` — high-level run state

Block Dev and Config additionally push to `main` (EDS code, `fstab.yaml`, `helix-*.yaml`, `robots.txt`) via `git worktree` — see their worker prompts.

### Key Modules

| Module | Role |
|---|---|
| `eds_migrate/__main__.py` | CLI, env loading, top-level orchestration |
| `eds_migrate/agents.py` | CMA fleet create/cleanup, `AgentRef`/`MigrationFleet` dataclasses |
| `eds_migrate/session.py` | Orchestrator session, event streaming, dispatch loop |
| `eds_migrate/router.py` | Custom tool registry, worker/verifier dispatch, Phase-4 parallelism (4-way) |
| `eds_migrate/state_workspace.py` | Local git clone of the `migration-state/{run_id}` branch |
| `eds_migrate/knowledge/deploy.py` | Skills API upload/teardown |
| `eds_migrate/prompts/` | System prompts (orchestrator / workers / verifiers) + `templates/lead-task.md` |

### Prompts Structure

- `prompts/orchestrator.md` — base orchestrator system prompt (custom-tool workflow)
- `prompts/workers/*.md` — one per worker agent, all aware of the state branch layout
- `prompts/verifiers/*.md` + `preamble.md` — one per verifier agent
- `prompts/templates/lead-task.md` — kick-off message sent to the orchestrator on session create

### Skills

20 domain-specific EDS skills live in `knowledge/skills/*/SKILL.md`. Each is uploaded via the Skills API with a `skills-2025-10-02` beta header. Skills provide EDS-specific knowledge (block patterns, page structure, content modeling, etc.) to relevant agents.

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Claude API access |
| `GITHUB_TOKEN` | Yes | Push code to target GitHub repo |
| `EDS_TOKEN` | No | Push content to da.live authoring |
