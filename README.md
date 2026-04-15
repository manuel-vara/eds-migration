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

Agents receive EDS domain knowledge through the [Anthropic Skills API](https://docs.anthropic.com/en/api/skills-guide). During setup, every skill directory under `eds_migrate/knowledge/skills/` is uploaded as a custom skill and attached to all agents in the fleet. The platform loads them on demand — agents discover and read skills automatically when relevant to their task, without consuming context until needed.

```
knowledge/
└── skills/                          16 custom skills
    ├── building-blocks/SKILL.md     creating and modifying EDS blocks
    ├── content-modeling/SKILL.md    David's Model, author-friendly structures
    ├── page-import/SKILL.md         end-to-end page import pipeline
    ├── eds-knowledge/               platform reference docs (markup, performance,
    │   ├── SKILL.md                 redirects, sitemaps, authoring, go-live, etc.)
    │   └── references/*.md
    └── ... (12 more skills)
```

Each `SKILL.md` follows the [agent skill specification](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills/overview) — self-describing with YAML frontmatter (`name`, `description`). Skills are uploaded at the start of a run and deleted during teardown.

## Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) with access to Claude Managed Agents (beta)
- A **GitHub Personal Access Token** with `repo` scope (see [Credentials](#credentials) below)
- A GitHub organization and repository set up with AEM Code Sync (see [Repository setup](#repository-setup) below)
- (Optional) An **Adobe EDS access token** for content authoring (see [Credentials](#credentials) below)

## Installation

### 1. Install Python 3.11+

The project requires Python 3.11+. On macOS the system Python is 3.9, so install a newer version via Homebrew:

```bash
brew install python@3.11
```

### 2. Create and activate a virtual environment

Use the full Homebrew path to ensure the venv is created with the right interpreter. If a `.venv` already exists from a previous attempt, delete it first:

```bash
rm -rf .venv
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
```

> On Windows use `.venv\Scripts\activate` instead.

Confirm the venv is using the right Python:

```bash
python3 --version  # should print 3.11.x
```

### 3. Upgrade pip

The bundled pip may be too old to handle `pyproject.toml`-based editable installs:

```bash
pip install --upgrade pip
```

### 4. Install the package

```bash
pip install -e .
```

To deactivate the environment when you're done:

```bash
deactivate
```

## Repository setup

Before running the migration, you need a GitHub repository connected to AEM Code Sync. This is a one-time manual step per repository.

### 1. Create an empty repository

Create a new repository in your GitHub organization (e.g. `my-org/my-site`). It can be public or private.

### 2. Install the AEM Code Sync GitHub App

1. Visit [github.com/apps/aem-code-sync/installations/new](https://github.com/apps/aem-code-sync/installations/new)
2. Select your organization
3. Under **Repository access**, choose **Only select repositories** and pick the repository you just created
4. Click **Save**

If the app is already installed on your org, go to its installation settings and add the new repository instead.

Once installed, any code pushed to the repository is automatically synced to the AEM code bus and becomes available at `https://main--{repo}--{org}.aem.page/`.

> This follows the same process as the [AEM developer tutorial](https://www.aem.live/developer/tutorial). The migration tool handles everything after this point — pushing boilerplate code, blocks, content, and configuration.

## Credentials

All credentials can be provided via CLI flags, environment variables, or a **`.env` file** in the project root. Copy the example to get started:

```bash
cp .env.example .env
```

Then fill in your values. The `.env` file is gitignored and will never be committed.

### GitHub Token (required)

A GitHub Personal Access Token (PAT) allows the agents to push code to the target repository.

**Classic token:**

1. Go to [github.com/settings/tokens](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Select the **`repo`** scope (full control of private repositories)
4. Click **Generate token** and copy it

**Fine-grained token** (alternative):

1. Go to [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)
2. Select the target repository
3. Grant **Contents: Read and write** permission
4. Generate and copy the token

### EDS Token (optional)

An Adobe EDS access token for [da.live](https://da.live) enables automated content authoring (creating pages, spreadsheets, and media in the EDS content repository). If omitted, the migration will push code to GitHub but skip content authoring — you can import content manually via the da.live UI afterward.

#### How to generate the token

1. Go to [Adobe Developer Console](https://developer.adobe.com/console/) and sign in
2. Create a new **Project** (or use an existing one)
3. Click **Add API** and select **Edge Delivery Services**
4. Choose **OAuth Server-to-Server** as the credential type
5. Select the appropriate product profiles and save
6. On the credential overview page, note your **Client ID**, **Client Secret**, and **Scopes**
7. Click **Generate access token** on the credential overview page, or generate one programmatically:

```bash
curl -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&grant_type=client_credentials&scope=YOUR_SCOPES'
```

The response contains your access token:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86399
}
```

Copy the `access_token` value and add it to your `.env` file or export it:

```bash
export EDS_TOKEN=eyJ...
```

> **Note:** Tokens expire after ~24 hours. For long migrations, regenerate and update the token as needed. Cache and reuse tokens — Adobe throttles excessive token generation.

## Usage

With a `.env` file (recommended):

```bash
# .env already has ANTHROPIC_API_KEY, GITHUB_TOKEN, EDS_TOKEN
eds-migrate --site https://example.com --org my-org --repo my-site
```

Or with environment variables:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
export EDS_TOKEN=eyJ...

eds-migrate --site https://example.com --org my-org --repo my-site
```

With all options:

```bash
eds-migrate \
  --site https://example.com \
  --org my-org \
  --repo my-site \
  --github-token ghp_... \
  --eds-token eyJ... \
  --verbose
```

### Options

| Flag | Description |
|---|---|
| `--site URL` | Source site URL to migrate (required) |
| `--org NAME` | GitHub organization (required) |
| `--repo NAME` | GitHub repository name (required) |
| `--github-token` | GitHub PAT (default: `$GITHUB_TOKEN` env var, **required**) |
| `--eds-token` | Adobe EDS access token (default: `$EDS_TOKEN` env var, optional) |
| `--verbose, -v` | Stream agent output to stdout |
| `--run-id ID` | Custom run ID (default: auto-generated) |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (default: `INFO`) |
| `--cleanup` | Tear down orphaned resources for a given `--run-id` (no migration) |

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
│   ├── __init__.py          Skill directory discovery
│   ├── deploy.py            Skills API upload/teardown (replaces GitHub bridge)
│   └── skills/              EDS skills (16 × SKILL.md), uploaded via Skills API
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
