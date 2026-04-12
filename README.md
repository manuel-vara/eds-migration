# Agentic EDS Migration Process 

Automated migration of websites to [AEM Edge Delivery Services](https://www.aem.live/) using [Claude Managed Agents](https://platform.claude.com/docs/en/managed-agents/overview).

Given a source site URL, this tool spins up a fleet of specialized AI agents that crawl the site, analyze its content patterns, build EDS-compatible code, migrate every page, and validate the result — producing a fully previewable EDS site.

## How it works

The tool creates 11 agents on the Claude Managed Agents platform.

**Orchestrator** — the top-level coordinator. Dispatches workers, runs verification loops, gates phase transitions. The only agent that can call other agents.

### Workers

| Agent | Role |
|---|---|
| **Crawler** | Builds a complete page inventory from the source site |
| **Analyzer** | Scrapes samples, inventories block patterns, produces a migration blueprint |
| **Block Dev** | Implements all EDS blocks as vanilla JS/CSS, pushes code to GitHub |
| **Page Migrator** | Converts individual pages to EDS HTML and uploads to da.live |
| **Config** | Generates redirects, metadata, sitemaps, indexing, robots.txt |
| **Integration QA** | Validates the full migration: visual regression, Lighthouse, links, content |

### Verifiers

| Agent | Role |
|---|---|
| **Crawler Verifier** | Tier 2 judgment check on the Crawler's manifest |
| **Analyzer Verifier** | Tier 2 judgment check on the Analyzer's blueprint |
| **Block Dev Verifier** | Tier 2 judgment check on the Block Dev's code |
| **Pilot Verifier** | Tier 2 judgment check on pilot page migrations |

### Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      Migration Orchestrator                      │
│   (top-level agent — owns the session, gates phases, delegates)  │
└──┬────────┬──────────┬──────────┬─────────┬──────────┬───────────┘
   │        │          │          │         │          │
   ▼        ▼          ▼          ▼         ▼          ▼
Phase 1  Phase 2    Phase 3   Phase 3.5  Phase 4    Phase 5   Phase 6
Discover Analyze    Build     Pilot      Migrate    Configure Int. QA
   │     (3 subs)  Blocks    Migration  (threads)     │         │
   │        │          │          │         │          │         │
   ▼        ▼          ▼          ▼         ▼          ▼         ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │              Tier 1: Deterministic Validation Scripts           │
 │  (runs after every worker step — fast, free, no LLM needed)     │
 └─────────────────────────────┬───────────────────────────────────┘
                               │ only if Tier 1 passes
                               ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │              Tier 2: Verifier Agents (judgment calls)           │
 │  Crawler │ Analyzer │ Block Dev │ Pilot │                       │
 │  Verifier│ Verifier │ Verifier  │ Vrfier│                       │
 └─────────────────────────────────────────────────────────────────┘
```

Each phase follows a verification loop:

```
┌──────────────┐
│    Worker     │
│  (does work)  │
└──────┬───────┘
       │ output
       ▼
┌──────────────┐     FAIL: structured errors
│   Tier 1     │ ──────────────────────────────► Worker retries
│  (scripts)   │                                 (no LLM cost)
└──────┬───────┘
       │ PASS
       ▼
┌──────────────┐     FAIL: structured feedback
│   Tier 2     │ ──────────────────────────────► Worker retries
│  (verifier   │                                 (with feedback)
│   agent)     │
└──────┬───────┘
       │ PASS
       ▼
  Phase complete
  → Orchestrator advances
```

All communication flows through the Orchestrator in a star topology. Workers and verifiers cannot talk to each other directly. After max retries, the system degrades gracefully before escalating to a human.

## Knowledge base

Agents discover EDS domain knowledge at runtime from a shared filesystem at `/knowledge/`:

```
knowledge/
├── skills/          ← "how to build" (from adobe/helix-website)
│   ├── building-blocks/SKILL.md
│   ├── content-modeling/SKILL.md
│   ├── page-import/SKILL.md
│   └── ... (15 skills)
└── docs/            ← "how the platform works" (from aem.live)
    ├── developer-markup-sections-blocks.md
    ├── developer-keeping-it-100.md
    └── ... (14 docs)
```

Skills follow the [agent skill specification](https://github.com/anthropics/anthropic-cookbook/tree/main/misc/prompt_caching) — each `SKILL.md` is self-describing with a `description:` field. Agents list the directory, read descriptions, and pull only the skills relevant to their current task (progressive disclosure).

The codebase directory `eds_migrate/knowledge/` mirrors this runtime structure exactly.

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) with access to Claude Managed Agents (beta)
- A GitHub organization and empty repository for the migrated site
- A [da.live](https://da.live) workspace for content authoring

## Installation

```bash
pip install -e .
```

## Usage

```bash
export ANTHROPIC_API_KEY=sk-ant-...

eds-migrate --site https://example.com --org my-org --repo my-site
```

### Options

| Flag | Description |
|---|---|
| `--site URL` | Source site URL to migrate (required) |
| `--org NAME` | GitHub organization (required) |
| `--repo NAME` | GitHub repository name (required) |
| `--verbose, -v` | Stream agent output to stdout |
| `--run-id ID` | Custom run ID (default: auto-generated) |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (default: `INFO`) |
| `--cleanup` | Archive orphaned environments for a given `--run-id` (no migration) |

### What you get

| Output | Location |
|---|---|
| Code (blocks, styles, scripts) | `github.com/{org}/{repo}` |
| Content (pages, media, sheets) | `da.live/{org}/{repo}` |
| Documentation | `github.com/{org}/{repo}/docs/` |
| Preview | `https://main--{repo}--{org}.aem.page/` |
| QA report | `qa-report.json` in the agent environment |
| Migration log | Streamed to stderr during execution |

### Documentation output

Each phase produces a doc file, and a final report ties them together:

```
docs/
├── MIGRATION-REPORT.md      Executive summary, phase results, known issues, maintenance guide
├── phase1-discovery.md       Site inventory, archetype breakdown, navigation structure
├── phase2-analysis.md        Block palette, content models, architecture decisions
├── phase3-blocks.md          Block reference: purpose, content model, variants, screenshots
├── authoring-guide.md        For content authors: how to create pages, use blocks, add images
├── phase4-migration.md       Per-page migration status, visual diff scores, issues
├── phase5-config.md          Redirects, metadata, sitemaps, indexing, robots.txt
└── phase6-qa-summary.md      Lighthouse scores, visual fidelity, accessibility, known issues
```

These are pushed to the GitHub repo alongside the code, so they're always available to the team maintaining the site.

## Project structure

```
eds_migrate/
├── __main__.py              CLI entry point
├── agents.py                Fleet creation and cleanup (CMA API)
├── session.py               Orchestrator session lifecycle and event streaming
├── tier1/                   Deterministic validation scripts (bash)
│   ├── __init__.py          Re-exports TIER1_SCRIPTS lookup dict
│   ├── phase1_discovery.py  Phase 1 — manifest validation
│   ├── phase2a_scrape.py    Phase 2a — scrape artifact checks
│   ├── phase2b_inventory.py Phase 2b — block inventory checks
│   ├── phase2c_blueprint.py Phase 2c — blueprint schema validation
│   ├── phase3_block_dev.py  Phase 3 — block code, lint, framework checks
│   ├── phase35_pilot.py     Phase 3.5 — pilot page preview validation
│   ├── phase5_config.py     Phase 5 — YAML, redirects, robots.txt
│   └── phase6_qa.py         Phase 6 — QA report schema and thresholds
├── knowledge/
│   ├── __init__.py          Knowledge bundle builder (tar+gzip+base64)
│   ├── skills/              EDS development skills (15 × SKILL.md)
│   └── docs/                AEM platform documentation (14 × .md)
└── prompts/
    ├── orchestrator.md      Orchestrator system prompt
    ├── orchestrator.py      Prompt builder (assembles base + templates)
    ├── workers.py            Worker prompt loader
    ├── workers/              Worker system prompts (1 per agent)
    ├── verifiers.py          Verifier prompt loader
    ├── verifiers/            Verifier system prompts (preamble + 1 per agent)
    └── templates/            Dispatch templates (Orchestrator → subagent messages)
```

## Architecture documentation

See [`docs/migration-agent-architecture.md`](docs/migration-agent-architecture.md) for the full architecture specification, including shared state schemas, retry policies, fallback rules, and the verification matrix.

Open [`docs/migration-architecture-diagram.html`](docs/migration-architecture-diagram.html) in a browser for a visual diagram of the agent topology and phase pipeline.
