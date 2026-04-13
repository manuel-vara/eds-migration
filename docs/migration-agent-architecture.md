# EDS Migration Agent Architecture

Automated website migration to Adobe Experience Manager Edge Delivery Services using a fleet of Claude Managed Agents.

## Overview

The input is a source site URL. A team of specialized agents crawls the site, analyzes its structure, builds the necessary block library, migrates every page to EDS-compatible HTML, configures site-level settings, and validates the result — all orchestrated by a single top-level agent.

The migration produces three outputs:

- **Code** → pushed to a GitHub repository (blocks, styles, scripts, config)
- **Content** → pushed to Document Authoring ([da.live](https://da.live)) via its Source API (HTML pages, media, JSON sheets)
- **Documentation** → pushed to the GitHub repository (`docs/`): per-phase reports, block reference, authoring guide, and a final migration report

Together these form a working EDS site, previewable immediately at `https://main--{repo}--{org}.aem.page/`.

Quality is enforced at every step through a two-tiered verification system. Tier 1 runs deterministic validation scripts (schema checks, file existence, linting, visual diff scoring) instantly and cheaply. Tier 2 dispatches a separate verifier agent for judgment calls that require reasoning. Workers and verifiers loop until the verifier is satisfied or retries are exhausted.

The system is designed to run **unattended**. When retries are exhausted, the system first attempts autonomous fallback (degrade gracefully, skip and continue, accept partial output) before escalating to a human as the last resort. The system always produces a usable result, even if imperfect.

## Agent Topology

```
┌──────────────────────────────────────────────────────────────────┐
│                      Migration Orchestrator                       │
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
 │              Tier 1: Deterministic Validation Scripts            │
 │  (runs after every worker step — fast, free, no LLM needed)    │
 └─────────────────────────────┬───────────────────────────────────┘
                               │ only if Tier 1 passes
                               ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │              Tier 2: Verifier Agents (judgment calls)           │
 │  Crawler │ Analyzer │ Block Dev │ Pilot │                       │
 │  Verifier│ Verifier │ Verifier  │ Vrfier│                       │
 └─────────────────────────────────────────────────────────────────┘
```

**Key:** Not every phase needs a Tier 2 verifier. Phase 5 (Configuration) and Phase 6 (Integration QA) are fully covered by deterministic scripts — QA is already the testing phase, so verifying the verifier adds cost without value. Phase 4 page threads run self-contained loops with Tier 1 scripts only (Playwright checks are scripted, not LLM-based).

---

## Two-Tiered Verification

Every phase produces output. Before that output is accepted, it passes through verification.

### Tier 1 — Deterministic Validation (Scripts)

Runs automatically after every worker step. No LLM involved.

- JSON/YAML schema validation
- File existence and structure checks
- Linting (`npm run lint`)
- Cross-referencing IDs (e.g., every manifest page has an archetype)
- Duplicate detection
- HTTP HEAD requests to verify URLs are reachable
- Counting (section counts match, redirect counts match manifest)
- **Visual diff scoring** (pixelmatch / SSIM against original screenshots — numeric threshold, not LLM judgment)

**Cost:** Near-zero. Runs in milliseconds.
**When it fails:** Worker gets structured error output and retries immediately. No verifier agent needed.

### Tier 2 — Judgment-Based Verification (Agents)

A separate Claude agent inspects the output for things scripts can't check.

- "Does this block palette make sense for this type of site?"
- "Is this content model author-friendly or developer-hostile?"
- "Is content complete, or was something garbled/lost?"
- "Do these blocks decorate correctly in the browser?"
- **Visual diffs in the ambiguous range** (Tier 1 visual diff score between 0.7–0.9 — clearly wrong pages are caught by Tier 1, clearly correct pages pass Tier 1, Tier 2 reviews the edge cases)

**Cost:** One LLM session per check. Used only where judgment is needed.
**When it fails:** Verifier returns structured feedback. Worker retries with that feedback. Loop until pass or max retries.

### The Loop

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

**Retry behavior:**

- On retry, the worker receives the **latest** Tier 1 errors + Tier 2 feedback, plus a **one-line summary** of each prior attempt. Not the full history — this prevents context window exhaustion.
- The worker must address every issue before returning.
- Verification re-checks all criteria on retry, not just previously failed ones (regression prevention).
- Max retries configurable per phase. If exceeded, the system tries autonomous fallback before escalating to human review.

### Why not just Tier 2 for everything?

Using an LLM agent to validate YAML syntax or check if a file exists is wasteful. Tier 1 catches ~80% of issues instantly and for free. Tier 2 agents focus their reasoning on the 20% that actually requires judgment. This makes loops faster, cheaper, and keeps verifier agents focused on what they're good at.

### Why not just Tier 1 for everything?

Scripts can't assess quality. "Does this content model respect David's Model?" is a judgment call. Tier 2 handles the subjective, holistic checks that determine whether the output is actually *good* — not just structurally valid.

---

## Operational Resilience

The system is designed to run for hours unattended on large sites. These mechanisms keep it alive and making progress.

### Checkpoint / Resume

The orchestrator writes a `migration-state.json` file to the environment filesystem after every phase transition and at regular intervals during Phase 4.

```json
{
  "phase": "4-migrate",
  "status": "in-progress",
  "siteUrl": "https://example.com",
  "config": { "org": "acme", "repo": "site", "daToken": "vault:da-token" },
  "completedPhases": ["1-discover", "2a-scrape", "2b-inventory", "2c-blueprint", "3-build", "3.5-pilot"],
  "totalRegressions": 1,
  "sessionCost": { "llmSessions": 47, "budget": 500 }
}
```

If the orchestrator session crashes, a new session reads this file and resumes from the current phase. Phase 4 resumes by checking per-page status files (see below) and only migrating pages still marked `pending`.

All operations are **idempotent**: re-running Phase 3 rebuilds only blocks that don't exist or failed. Re-running Phase 4 skips pages already marked `migrated`. Uploading to da.live overwrites — so re-POSTing a page is safe.

### Race-Free Shared State

`manifest.json` is written once by the Crawler and **never mutated** after that.

Page migration status is tracked in individual files: `status/{url-hash}.json`. Each thread writes only its own file. No locking, no race conditions. The orchestrator reads the full `status/` directory to get aggregate progress.

```json
// status/a7f3c2.json
{
  "url": "https://example.com/products/widget",
  "archetype": "product-detail",
  "status": "migrated",
  "daUrl": "https://da.live/edit#/acme/site/products/widget",
  "previewUrl": "https://main--site--acme.aem.page/products/widget",
  "attempts": 2,
  "visualDiffScore": 0.93
}
```

### Regression Circuit Breaker

The orchestrator tracks a `totalRegressions` counter. A regression is any time a later phase sends work back to an earlier phase (e.g., Pilot fails → back to Block Dev).

**Limit: 5 total regressions across the entire migration.** After that, the system accepts the best-effort output and moves forward. This prevents infinite oscillation between phases.

Each regression is logged with the reason, so the QA report explains what was attempted and what was accepted as-is.

### Cost Tracking

The orchestrator tracks `llmSessions` — a count of Tier 2 verifier invocations. A configurable budget (default: 500 sessions) acts as a circuit breaker.

When the budget is 80% consumed, the system degrades:

- Phase 4 page threads skip Tier 2 entirely, relying on Tier 1 scripts only
- Integration QA (Phase 6) spot-checks a sample of pages instead of all pages

When the budget is 100% consumed, all remaining Tier 2 checks are skipped. The QA report notes which pages were verified only by Tier 1.

This is a simple counter — not a billing integration. It prevents runaway costs from pathological retry spirals.

### Autonomous Fallback

When retries are exhausted for any phase, the system attempts autonomous fallback before escalating to a human. The principle: **always produce something usable, even if imperfect.**


| Phase              | Autonomous Fallback                                                                | Escalate to Human If...                              |
| ------------------ | ---------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1 — Discovery      | Accept partial manifest, flag low-confidence archetypes                            | Crawl returned < 10% of expected pages (vs. sitemap) |
| 2a — Scrape        | Skip failed pages, use remaining samples (if ≥ 1 per archetype)                    | An entire archetype has zero samples                 |
| 2b — Inventory     | Accept partial inventory, mark unmatched patterns as custom                        | Inventory is completely empty                        |
| 2c — Blueprint     | Use conservative defaults: fewer custom blocks, more default content               | Blueprint covers < 50% of archetypes                 |
| 3 — Block Dev      | Skip failing block, fall back to default content for sections that used it         | > 30% of palette blocks failed                       |
| 3.5 — Pilot        | Accept pilot with known issues logged, proceed with those pages flagged            | Visual diff < 0.5 on majority of pilot pages         |
| 4 — Migration      | Mark page as `failed`, continue with remaining pages                               | > 50% of pages fail                                  |
| 5 — Config         | Generate partial config (redirects + sitemap for migrated pages only)              | Redirect generation completely broken                |
| 6 — Integration QA | Accept report, flag issues by severity, mark migration as "complete with warnings" | Lighthouse average < 50                              |


Human escalation is the last resort — when the autonomous fallback itself determines the output is too degraded to be useful.

---

## Phase-Based Workflow

Migration proceeds through seven phases. The orchestrator gates each phase — the next phase does not begin until verification passes (or autonomous fallback accepts the output).

---

### Phase 1 — Discovery (Crawler Agent)

**Goal:** Build a complete inventory of every page on the source site.


| Responsibility            | Details                                                                              |
| ------------------------- | ------------------------------------------------------------------------------------ |
| Crawl the source site     | Follow `sitemap.xml`, internal links, or both. Use Playwright for JS-rendered pages. |
| Build page inventory      | URL, title, template type, depth, priority                                           |
| Identify page archetypes  | Homepage, PDP, PLP, blog post, landing page, etc.                                    |
| Extract site-level assets | Favicon, fonts, global images, social images                                         |
| Map navigation structure  | Header links, footer links, breadcrumb paths                                         |


**Output:** `manifest.json` — a structured page manifest on the environment filesystem.

**Documentation:** `docs/phase1-discovery.md` — page counts by archetype, navigation structure, site assets, crawl issues, archetype rationale.

**Tier 1 checks:**


| Check                                  | Method                                                   |
| -------------------------------------- | -------------------------------------------------------- |
| Manifest is valid JSON matching schema | JSON schema validation                                   |
| No duplicate URLs                      | Dedupe check on `pages[].url`                            |
| Every page has an assigned archetype   | Null check on `archetype` field                          |
| Archetypes have ≥ 1 sample URL         | Cross-reference `archetypes[].sampleUrls`                |
| Page count is plausible vs. sitemap    | Compare manifest count against `sitemap.xml` entry count |
| Navigation structure is non-empty      | Check `navigation.header` and `navigation.footer`        |


**Tier 2 checks (Crawler Verifier):**


| Check                                | Method                                                              |
| ------------------------------------ | ------------------------------------------------------------------- |
| Archetype categorization is sensible | Review sample URLs per archetype — are they actually the same type? |
| No major site sections were missed   | Compare top-level nav links against discovered archetypes           |
| Priority assignments are reasonable  | Homepage and main landing pages should be "high"                    |


**Manifest schema:**

```json
{
  "site": "https://example.com",
  "crawledAt": "2026-04-11T12:00:00Z",
  "pages": [
    {
      "url": "https://example.com/products/widget",
      "title": "Widget Pro",
      "archetype": "product-detail",
      "depth": 2,
      "priority": "high"
    }
  ],
  "archetypes": [
    {
      "name": "product-detail",
      "count": 48,
      "sampleUrls": [
        "https://example.com/products/widget",
        "https://example.com/products/gadget"
      ]
    }
  ],
  "navigation": { "header": [], "footer": [] },
  "assets": { "favicon": "https://example.com/favicon.ico", "fonts": [], "globalImages": [] }
}
```

---

### Phase 2 — Analysis (Analyzer Agent)

**Goal:** Understand the site's content patterns and produce a migration blueprint before any code is written.

Phase 2 is the most important phase. It's broken into three sub-steps, each with its own Tier 1 validation. Tier 2 (Analyzer Verifier) runs once at the end to assess the overall blueprint quality.

#### Phase 2a — Scrape Samples


| Responsibility                                | Details                                                                             |
| --------------------------------------------- | ----------------------------------------------------------------------------------- |
| Select 2–3 representative pages per archetype | Use sample URLs from manifest                                                       |
| Scrape each page                              | Screenshot, metadata, cleaned HTML, images (mirrors Adobe's `scrape-webpage` skill) |
| Store scrape artifacts                        | `analysis/{archetype}/{page}/` directories                                          |


**Tier 1 checks:**

- Every archetype has 2–3 scraped pages
- Each scrape directory contains `screenshot.png`, `metadata.json`, `cleaned.html`, `images/`
- `metadata.json` is valid and has non-empty `paths` and `metadata` fields
- `cleaned.html` is non-empty and contains at least one `<h1>`

#### Phase 2b — Build Block Inventory


| Responsibility                          | Details                                                                                                     |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Analyze structure of all scraped pages  | Identify sections, content sequences per section (mirrors `identify-page-structure` + `page-decomposition`) |
| Build global block inventory            | Which block patterns appear across the site                                                                 |
| Search Block Collection and Block Party | Match patterns to existing implementations                                                                  |
| Catalog available blocks                | Local blocks + Block Collection + Block Party matches                                                       |


**Tier 1 checks:**

- Every scraped page has a structure analysis with section count > 0
- Block inventory is non-empty
- Every block marked `source: "block-collection"` confirmed to exist (run search scripts)
- No duplicate block names with conflicting definitions

#### Phase 2c — Define Migration Blueprint


| Responsibility               | Details                                                    |
| ---------------------------- | ---------------------------------------------------------- |
| Decide block palette         | What to use from Block Collection vs. what to build custom |
| Define content models        | For each block, the author-facing table structure          |
| Map archetypes to blueprints | Which blocks and section styles each archetype uses        |
| Document site conventions    | Section styles, CTA patterns, image strategy               |


**Tier 1 checks:**

- Every archetype in the manifest has a corresponding blueprint
- Every block referenced in blueprints exists in the palette
- Every block in the palette has a `contentModel` type (standalone/collection/configuration/auto-blocked)
- `siteConventions` has non-empty values

**Tier 2 checks (Analyzer Verifier — runs once after 2c):**


| Check                                       | Method                                                                                              |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Content models follow David's Model         | Are they author-friendly? ≤ 4 cells per row? Semantic formatting?                                   |
| Block palette is minimal                    | Could any blocks be replaced with default content? Are there redundant blocks?                      |
| Archetype blueprints match the actual pages | Load sample screenshots and verify the blueprint sections align with visible content                |
| No over-blocking                            | Verify that content which could be simple headings/paragraphs isn't unnecessarily wrapped in blocks |
| Conventions are consistent                  | Section style names are reused sensibly, not one-off per archetype                                  |


**Output:** `blueprint.json` on the environment filesystem.

**Documentation:** `docs/phase2-analysis.md` — block palette with rationale, content model decisions, what was left as default content and why, site conventions, architecture decisions log.

```json
{
  "blockPalette": [
    {
      "name": "hero",
      "source": "block-collection",
      "contentModel": "standalone",
      "usedByArchetypes": ["homepage", "landing-page"],
      "variants": ["dark", "centered"]
    },
    {
      "name": "product-specs",
      "source": "custom",
      "contentModel": "collection",
      "usedByArchetypes": ["product-detail"],
      "variants": []
    }
  ],
  "archetypeBlueprints": {
    "product-detail": {
      "sections": [
        { "style": "light", "sequences": ["hero (standalone)", "product-specs (collection)"] },
        { "style": "grey", "sequences": ["default content", "cards (collection)"] }
      ]
    }
  },
  "siteConventions": {
    "sectionStyles": ["light", "grey", "dark", "accent"],
    "ctaPattern": "button-primary / button-secondary",
    "imageStrategy": "download-and-convert"
  }
}
```

---

### Phase 3 — Block Development (Block Dev Agent)

**Goal:** Produce a working codebase with all blocks implemented, tested, and linted.


| Responsibility                   | Details                                                                                         |
| -------------------------------- | ----------------------------------------------------------------------------------------------- |
| Set up project scaffolding       | Clone boilerplate, configure `head.html`, global styles, `scripts.js`                           |
| Match blocks to Block Collection | Prefer Adobe-vetted implementations; copy into project                                          |
| Build custom blocks              | For patterns with no existing match, follow content-modeling → building-blocks → testing-blocks |
| Test all blocks locally          | Ensure decoration works against sample content from Phase 2                                     |
| Run linting                      | `npm run lint` must pass                                                                        |


**Tier 1 checks:**


| Check                                            | Method                                      |
| ------------------------------------------------ | ------------------------------------------- |
| Every palette block has a directory in `blocks/` | `ls blocks/` vs. palette names              |
| Each block directory has `.js` and `.css` files  | File existence                              |
| `npm run lint` passes with zero errors           | Run linting, check exit code                |
| `aem.js` is unmodified                           | Checksum against boilerplate original       |
| `head.html` is valid HTML                        | HTML validation                             |
| No external framework imports                    | Grep for React, Vue, jQuery, Tailwind, etc. |


**Tier 2 checks (Block Dev Verifier):**


| Check                          | Method                                                                           |
| ------------------------------ | -------------------------------------------------------------------------------- |
| Each block decorates correctly | Start `aem up`, load test content, verify no JS console errors, take screenshots |
| CSS is properly scoped         | All selectors start with `.{block-name}`                                         |
| Blocks are responsive          | Screenshot at 375px, 768px, 1200px widths                                        |
| Code follows EDS patterns      | No build steps, ES6+ imports with `.js` extensions, vanilla JS only              |


**Documentation:** `docs/phase3-blocks.md` — block reference (name, purpose, content model, variants, screenshots), global styles, scripts, head.html contents, Block Collection dependencies. Also `docs/authoring-guide.md` — how to create each page type, use each block, apply section styles, and handle images.

**Output:** Code pushed to `github.com/{org}/{repo}`:

```
├── blocks/
│   ├── hero/
│   ├── cards/
│   ├── product-specs/    ← custom
│   └── ...
├── styles/
│   ├── styles.css
│   └── lazy-styles.css
├── scripts/
│   ├── aem.js
│   ├── scripts.js
│   └── delayed.js
├── head.html
├── fstab.yaml            ← points to da.live as content source
└── 404.html
```

The `fstab.yaml` is configured to use da.live:

```yaml
mountpoints:
  /: https://content.da.live/{org}/{repo}
```

---

### Phase 3.5 — Pilot Migration

**Goal:** Validate the entire page migration pipeline end-to-end with real content before scaling to all pages.

Takes the 2–3 sample pages per archetype scraped in Phase 2, runs them through the full migration pipeline, and uploads the result to da.live for real preview validation.


| Responsibility                | Details                                                                    |
| ----------------------------- | -------------------------------------------------------------------------- |
| Migrate sample pages          | Scrape → map to blueprint → generate HTML → upload to da.live              |
| Upload to da.live             | POST HTML + images via Source API. Verify response includes preview URL.   |
| Validate against real preview | Hit `https://main--{repo}--{org}.aem.page/{path}` — not a local dev server |
| Compare against originals     | Screenshot the live preview and compare to the Phase 2 original screenshot |


**Tier 1 checks:**


| Check                                             | Method                                                   |
| ------------------------------------------------- | -------------------------------------------------------- |
| da.live upload succeeded                          | HTTP 201 from Source API for each page and image         |
| Preview URL returns 200                           | HTTP GET on `aem.page` preview URL                       |
| Section count matches blueprint                   | Parse live HTML, count sections vs. archetype blueprint  |
| No truncated content                              | Grep for `...`, `<!-- more -->`, placeholder strings     |
| All block class names match `blocks/` directories | Extract class names from live HTML, cross-reference      |
| Metadata block present                            | Check last section                                       |
| Visual diff score ≥ 0.8                           | pixelmatch comparison of preview screenshot vs. original |


**Tier 2 checks (Pilot Verifier):**


| Check                                              | Method                                                                         |
| -------------------------------------------------- | ------------------------------------------------------------------------------ |
| Pages render without JS errors                     | Playwright: load preview URL, check console                                    |
| Visual diff scores in 0.7–0.9 range are acceptable | Review ambiguous-range pages — are the differences CSS tweaks or content loss? |
| Blocks decorate correctly                          | Visual inspection of decorated output vs. expected structure                   |
| Content is complete and faithful                   | Compare text content of preview vs. cleaned HTML from scrape                   |


**Why this phase exists:** Going from "blocks work against test content" to "migrate 500 pages in parallel" is a huge leap. The pilot catches pipeline issues — image path problems, da.live upload edge cases, blocks that work locally but break on preview — before you burn cycles on the full migration.

**If the pilot fails:** The feedback might require changes to blocks (back to Phase 3), the blueprint (back to Phase 2c), or just the migration pipeline. The orchestrator routes the fix to the appropriate phase, incrementing the regression counter.

---

### Phase 4 — Content Migration (Page Migrator Threads)

**Goal:** Migrate every page from the manifest into EDS-compatible HTML, uploaded to da.live.


| Responsibility                     | Details                                                      |
| ---------------------------------- | ------------------------------------------------------------ |
| Migrate pages in parallel          | Each thread handles one page using the established blueprint |
| Apply established block palette    | No new block/model decisions — use Phase 2 blueprint         |
| Upload to da.live                  | POST HTML + images via Source API per page                   |
| Self-contained Tier 1 verification | Each thread runs its own scripted checks — no LLM calls      |
| Track progress                     | Write per-page status file to `status/{url-hash}.json`       |
| Flag unknown patterns              | Pages that don't fit any archetype go to the feedback queue  |


**Migration strategy: archetype-by-archetype.** Migrate one archetype batch, verify the batch, then proceed. This catches archetype-specific issues early (e.g., all product pages are broken) before migrating the next archetype.

#### Per-Thread Pipeline

Each page migrator thread is self-contained. It runs scripted verification without LLM calls. The orchestrator only hears back when the page is done (migrated), failed (retries exhausted), or has an unknown pattern.

```
Thread N:
  1. Scrape page (screenshot, metadata, cleaned HTML, images)
  2. Map content to archetype blueprint
  3. Generate {path}.html with proper block tables
  4. Upload HTML + images to da.live via Source API
  5. Hit preview URL, take screenshot
  6. Tier 1 checks:
     - Upload succeeded (201 response)
     - Preview returns 200
     - Section count matches blueprint
     - No truncated content
     - Visual diff score ≥ 0.8 (pixelmatch vs. original)
     - No JS console errors on preview URL (Playwright)
     └─ FAIL → retry from step 3 (up to 3 times)
  7. Write status/{url-hash}.json → "migrated"
```

**Note on Phase 4 verification:** The Playwright checks (JS console errors, screenshot) and visual diff scoring are all **scripted Tier 1 checks**, not LLM calls. This keeps the per-page cost near-zero. No Tier 2 verifier runs during Phase 4 — quality judgment was front-loaded in the Pilot (Phase 3.5).

**If the page doesn't match any archetype:**
The thread writes the page URL and a description of the unmatched pattern to `pending-patterns.json`. It does not retry — the pattern is genuinely new, not a worker error.

#### Feedback Loop for Unknown Patterns

After the main migration batch completes, the orchestrator checks `pending-patterns.json`. If non-empty:

1. Orchestrator dispatches the Analyzer to examine the pending pages
2. Analyzer extends the blueprint with new archetypes/blocks if needed
3. If new blocks are needed, Block Dev builds them (regression counter increments)
4. Page Migrator threads retry the pending pages with the updated blueprint
5. If they still fail, they're marked `failed` and included in the QA report

**Documentation:** `docs/phase4-migration.md` — pages migrated per batch, pages that didn't match archetypes, issues encountered, visual diff score distribution.

**Concurrency:** 10–20 concurrent threads. Tune based on da.live Source API rate limits.

---

### Phase 5 — Configuration (Config Agent)

**Goal:** Set up all site-level configuration files and upload config sheets to da.live.


| Responsibility        | Details                                                                           |
| --------------------- | --------------------------------------------------------------------------------- |
| Generate redirects    | `redirects.json` mapping old URLs → new EDS paths, uploaded to da.live as a sheet |
| Build bulk metadata   | `metadata.json` with URL patterns for OG tags, descriptions, uploaded to da.live  |
| Configure query-index | `helix-query.yaml` committed to GitHub repo                                       |
| Set up sitemap        | `helix-sitemap.yaml` committed to GitHub repo                                     |
| Robots.txt            | `robots.txt` committed to GitHub repo                                             |
| Navigation documents  | `nav.html` and `footer.html` uploaded to da.live                                  |


**Tier 1 checks only (no Tier 2 verifier needed):**


| Check                                     | Method                                                                          |
| ----------------------------------------- | ------------------------------------------------------------------------------- |
| Every migrated page has a redirect entry  | Cross-reference status files (status = migrated) against redirect source column |
| No redirect loops or chains               | Walk each redirect, confirm single-hop resolution                               |
| `helix-query.yaml` is valid YAML          | YAML parse                                                                      |
| `helix-sitemap.yaml` is valid YAML        | YAML parse                                                                      |
| Sitemap covers all migrated pages         | Cross-reference paths                                                           |
| `robots.txt` doesn't block migrated paths | Parse directives, check against page paths                                      |
| Bulk metadata patterns don't conflict     | Check for overlapping URL globs with contradictory values                       |
| da.live uploads succeeded                 | HTTP 201 from Source API for sheets and nav documents                           |


Configuration is fully deterministic — the acceptance criteria are all objective and scriptable. No Tier 2 verifier needed.

**Documentation:** `docs/phase5-config.md` — redirects count and patterns, bulk metadata URL patterns, indexing configuration, sitemap structure, navigation hierarchy, robots.txt rationale.

**Output:** Config YAMLs committed to GitHub. Sheets and navigation documents uploaded to da.live.

---

### Phase 6 — Integration QA (Site-Wide)

**Goal:** Validate cross-cutting concerns that no individual phase can catch.

This is not a replacement for per-phase verification — it's an additional layer that checks how everything works *together* on the real preview URLs.

**Worker: Integration QA Agent**


| Responsibility         | Details                                                                     |
| ---------------------- | --------------------------------------------------------------------------- |
| Visual regression      | Compare preview screenshots vs. originals across all archetypes             |
| Performance validation | Lighthouse / PSI scores on preview URLs — target 100 on all four categories |
| Link checking          | Internal links resolve across the entire migrated site                      |
| Content completeness   | Spot-check pages per archetype for full content transfer                    |
| Accessibility          | Heading hierarchy, alt text, WCAG 2.1 AA basics                             |
| Navigation consistency | Header/footer links work and are consistent across pages                    |
| Redirect validation    | Hit old URLs, confirm they 301 to correct new pages                         |
| Generate QA report     | Pass/fail per page with actionable details and preview links                |


**Tier 1 checks:**


| Check                                | Method                       |
| ------------------------------------ | ---------------------------- |
| QA report exists and is valid JSON   | Schema validation            |
| All migrated pages have QA entries   | Cross-reference status files |
| No pages with zero Lighthouse scores | Null/zero check              |
| Average visual diff score ≥ 0.85     | Aggregate pixelmatch scores  |


**No Tier 2 verifier.** Integration QA is itself the final quality gate — adding a verifier agent on top would be testing the testing. The Tier 1 checks above are sufficient to validate the QA report structure and aggregate thresholds. The QA agent's judgment *is* the judgment layer.

#### Phase 6 Regression Path

If Integration QA discovers **systematic** issues (not individual page failures), it can tag findings with a `fixPhase` field:

```json
{
  "severity": "high",
  "criterion": "Lighthouse performance",
  "details": "All product pages score < 60 due to unoptimized hero images",
  "fixPhase": "3-build",
  "remediation": "Hero block should use loading=lazy for below-fold images"
}
```

The orchestrator routes these to the appropriate phase for a targeted fix. **Maximum 1 Phase 6 regression cycle** — after that, the issues are logged in the QA report for human review.

**Documentation:** `docs/phase6-qa-summary.md` — overall pass/fail/warning counts, Lighthouse score distribution, visual fidelity summary, broken links, accessibility findings, known issues, regressions found and their resolution status.

**QA report schema:**

```json
{
  "summary": {
    "totalPages": 127,
    "passed": 119,
    "warnings": 5,
    "failed": 3,
    "tier1Verified": 127
  },
  "pages": [
    {
      "url": "/products/widget",
      "status": "passed",
      "previewUrl": "https://main--site--acme.aem.page/products/widget",
      "daEditUrl": "https://da.live/edit#/acme/site/products/widget",
      "lighthouse": { "performance": 100, "accessibility": 98, "bestPractices": 100, "seo": 100 },
      "contentComplete": true,
      "brokenLinks": [],
      "visualDiffScore": 0.94
    }
  ],
  "degradations": [
    "Block 'product-specs' failed after 3 retries — sections using it fall back to default content (3 pages affected)"
  ],
  "regressions": [
    { "from": "3.5-pilot", "to": "3-build", "reason": "Hero block CSS scoping issue", "resolved": true }
  ]
}
```

---

## Output Delivery

The migration produces five deliverables:

### 1. GitHub Repository (Code)

```
github.com/{org}/{repo}
├── blocks/
├── styles/
├── scripts/
├── head.html
├── fstab.yaml       ← points to da.live
├── helix-query.yaml
├── helix-sitemap.yaml
├── robots.txt
└── 404.html
```

Pushed by Block Dev (Phase 3) and Config (Phase 5). The repo is the EDS code side — blocks, styles, scripts, and configuration. Connected to da.live via `fstab.yaml`.

### 2. da.live Content (Document Authoring)

```
da.live/{org}/{repo}
├── index.html
├── products/
│   ├── widget.html
│   └── ...
├── blog/
│   └── ...
├── nav.html
├── footer.html
├── metadata.json
├── redirects.json
└── (images are embedded in pages via da.live's media handling)
```

Uploaded by Page Migrators (Phase 4) and Config (Phase 5) via the da.live Source API. Each page is immediately previewable at `https://main--{repo}--{org}.aem.page/{path}`.

### 3. Documentation

```
github.com/{org}/{repo}
└── docs/
    ├── MIGRATION-REPORT.md     ← executive summary, compiled by Orchestrator
    ├── phase1-discovery.md
    ├── phase2-analysis.md
    ├── phase3-blocks.md
    ├── phase4-migration.md
    ├── phase5-config.md
    ├── phase6-qa-summary.md
    └── authoring-guide.md      ← how to author content for this site
```

Each worker writes its phase documentation as part of the job. The Orchestrator compiles `MIGRATION-REPORT.md` after all phases complete — it includes an executive summary, phase-by-phase results, architecture overview, known issues, and a maintenance guide. All pushed to GitHub alongside the code.

### 4. QA Report

A structured JSON report with per-page status, Lighthouse scores, visual diff scores, preview URLs, da.live edit URLs, and any degradations or issues. This is the primary artifact for human review.

### 5. Migration Log

Every Tier 2 verifier verdict (pass or fail), every regression, every autonomous fallback decision, and every cost checkpoint. Stored in the `verifier-history` memory store. Enables post-mortem analysis of why decisions were made.

---

## Shared State

### Environment Filesystem (Structured Data)

Structured artifacts live as files on the environment filesystem. These are the primary data exchange mechanism between phases.


| File                           | Written By                                                   | Read By                                |
| ------------------------------ | ------------------------------------------------------------ | -------------------------------------- |
| `manifest.json`                | Crawler (write once, never mutated)                          | All agents                             |
| `blueprint.json`               | Analyzer                                                     | Block Dev, Page Migrators, Config      |
| `analysis/{archetype}/{page}/` | Analyzer (scrape artifacts)                                  | Block Dev (test content), Pilot        |
| `status/{url-hash}.json`       | Page Migrators (one file per page, no races)                 | Orchestrator, Config, Integration QA   |
| `pending-patterns.json`        | Page Migrators                                               | Orchestrator, Analyzer (feedback loop) |
| `qa-report.json`               | Integration QA                                               | Orchestrator                           |
| `migration-state.json`         | Orchestrator (checkpoint for resume)                         | Orchestrator (on restart)              |
| `docs/*.md`                    | Workers (per-phase reports), Orchestrator (MIGRATION-REPORT) | Orchestrator, GitHub push              |


### Memory Stores (Soft Knowledge)

Memory stores hold decisions, conventions, and rationale — things that benefit from semantic search and persistence across sessions.


| Memory Store       | Purpose                                 | Example Entries                                                                                                                          |
| ------------------ | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `decisions-log`    | Authoring decisions and their rationale | "Chose cards over columns for product features because each item has an image, heading, and description — repeating structured pattern." |
| `conventions`      | Site-wide style and pattern conventions | "Section style 'accent' uses brand blue (#0055FF) background. CTA buttons always use 'button-primary' class."                            |
| `verifier-history` | Record of every Tier 2 verifier verdict | "Block Dev Verifier pass #2: hero block initially had scoping issue — fixed on retry. Cards block passed first attempt."                 |


Memory stores are not used for structured data like page inventories or QA reports. Those belong on the filesystem where they can be read, written, and cross-referenced efficiently.

---

## Knowledge Base

Agents need domain knowledge about how EDS works — markup structure, block patterns, content models, performance rules. This knowledge comes from two sources:

- **Skills** (from `adobe/helix-website`) — "how to build" patterns, workflows, and tools (15 skills)
- **Platform docs** (from `aem.live`) — "how the platform works" at the API/configuration level (14 docs)

Knowledge files live on the shared environment filesystem at `/knowledge/`, populated by the Orchestrator at session start:

```
/knowledge/
├── skills/
│   ├── building-blocks/SKILL.md
│   ├── content-modeling/SKILL.md
│   ├── page-import/SKILL.md
│   └── ... (15 skills)
└── docs/
    ├── developer-markup-sections-blocks.md
    ├── developer-keeping-it-100.md
    └── ... (14 docs)
```

**Progressive disclosure:** Skills follow the agent skill specification — each `SKILL.md` has a `description:` field. Agents discover available knowledge by listing the directory, scanning descriptions, and reading only the files relevant to their current task. No knowledge is injected into system prompts. This keeps context windows clean and ensures agents load the right information at the right time.

---

## Agent Specifications

### Migration Orchestrator

- **Model:** claude-opus-4-6
- **Role:** Top-level coordinator; gates phases, dispatches workers and verifiers, manages the feedback loop
- **Tools:** `agent_toolset_20260401` (bash, file ops, web)
- **Callable agents:** All workers and Tier 2 verifiers
- **Vaults:** `github-token` (repo access), `da-token` (da.live Source API auth)
- **Responsibilities:**
  - Accept site URL, org, and repo from user
  - Write and maintain `migration-state.json` checkpoint
  - Run Tier 1 scripts directly (they're just bash/node commands)
  - Dispatch Tier 2 verifiers only when Tier 1 passes
  - Enforce max retries and autonomous fallback per phase
  - Track regression counter and cost counter
  - Manage Phase 4 thread pool
  - Run feedback loop for unknown patterns
  - Verify each worker wrote its phase documentation to `docs/`
  - Compile `docs/MIGRATION-REPORT.md` after all phases
  - Push `docs/` to GitHub
  - Escalate to human only as last resort
  - Report progress between phases

### Worker Agents


| Agent          | Model             | Networking     | Packages                                   | Notes                                                                                                    |
| -------------- | ----------------- | -------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| Crawler        | claude-sonnet-4-6 | `unrestricted` | `npm` (playwright)                         | Playwright for JS-rendered pages                                                                         |
| Analyzer       | claude-opus-4-6   | `unrestricted` | —                                          | Block Collection/Party search scripts; runs across sub-steps 2a/2b/2c                                    |
| Block Dev      | claude-opus-4-6   | `unrestricted` | `npm` (aem-cli, playwright, vitest)        | Heaviest environment setup. Pushes to GitHub via vault token.                                            |
| Page Migrator  | claude-sonnet-4-6 | `unrestricted` | `npm` (playwright, pixelmatch)             | Spawned as threads; N concurrent; uploads to da.live via vault token. Tier 1 only — no LLM verification. |
| Config         | claude-sonnet-4-6 | `unrestricted` | —                                          | Commits to GitHub + uploads sheets/nav to da.live                                                        |
| Integration QA | claude-sonnet-4-6 | `unrestricted` | `npm` (playwright, lighthouse, pixelmatch) | Needs browser for screenshots/perf on preview URLs                                                       |


### Tier 2 Verifier Agents


| Agent              | Model             | Networking     | Notes                                                                                                        |
| ------------------ | ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------ |
| Crawler Verifier   | claude-sonnet-4-6 | `unrestricted` | Validates archetype categorization, coverage                                                                 |
| Analyzer Verifier  | claude-opus-4-6   | `unrestricted` | Assesses content model quality, David's Model adherence. Strongest verifier — blueprint quality is critical. |
| Block Dev Verifier | claude-sonnet-4-6 | `unrestricted` | Loads pages in Playwright, checks decoration, responsiveness                                                 |
| Pilot Verifier     | claude-sonnet-4-6 | `unrestricted` | Visual comparison of pilot preview URLs vs. originals                                                        |


**Not agents (Tier 1 only):** Config verification, per-page migration checks, and Integration QA validation are fully handled by scripts. QA is already the testing phase — verifying the verifier adds cost without value.

All Tier 2 verifiers share a common system prompt preamble that enforces:

- Binary PASS/FAIL verdicts (no "mostly okay")
- Structured issue format: `{ severity, criterion, details, remediation }`
- Mandatory evidence (file paths, screenshots, error logs) for every FAIL

---

## Worker/Verifier Loop Configuration


| Phase          | Max Retries | Tier 1 | Tier 2                    | Autonomous Fallback                   | Escalate If...                 |
| -------------- | ----------- | ------ | ------------------------- | ------------------------------------- | ------------------------------ |
| 1 — Discovery  | 3           | Yes    | Yes                       | Accept partial manifest               | < 10% pages found              |
| 2a — Scrape    | 2           | Yes    | No                        | Use remaining samples                 | Zero samples for any archetype |
| 2b — Inventory | 2           | Yes    | No                        | Accept partial inventory              | Inventory empty                |
| 2c — Blueprint | 3           | Yes    | Yes                       | Conservative defaults                 | < 50% archetypes covered       |
| 3 — Block Dev  | 3           | Yes    | Yes                       | Skip failing blocks → default content | > 30% blocks failed            |
| 3.5 — Pilot    | 3           | Yes    | Yes                       | Accept with issues logged             | Visual diff < 0.5 on majority  |
| 4 — Migration  | 3 / page    | Yes    | No (scripts only)         | Mark page `failed`                    | > 50% pages fail               |
| 4 — Feedback   | 2           | Yes    | Yes                       | Mark pages `failed`                   | —                              |
| 5 — Config     | 3           | Yes    | No                        | Partial config                        | Redirect gen broken            |
| 6 — Int. QA    | 2           | Yes    | No (QA *is* the judgment) | Accept with warnings                  | Lighthouse avg < 50            |


**Global limits:**

- Regression circuit breaker: 5 total cross-phase regressions
- Cost circuit breaker: 500 LLM sessions (configurable)

---

## Design Principles

### Verify at the source, not at the end

Every phase has inline QA. Problems are caught and fixed in the same phase they're introduced, not discovered three phases later when the context is gone.

### Right-size the verification

Deterministic checks run as scripts (fast, free). Visual diffs use pixelmatch (fast, numeric). Judgment calls use verifier agents (powerful, expensive). Don't use an LLM to check if a file exists. Don't use a script to assess content model quality.

### Independent verification

Workers never self-review. Tier 2 verifiers are separate agents with different system prompts and explicit acceptance criteria. This eliminates blind spots.

### Always produce output

The system never halts silently. Every phase either passes, falls back to a degraded-but-usable result, or escalates with full context. A migration with 90% of pages and a list of issues is infinitely more valuable than a system that stopped at Phase 2c.

### Break big phases into verifiable sub-steps

Phase 2 (Analysis) is three sub-steps, each with its own Tier 1 gate. This means a content model error doesn't force re-scraping pages, and a scraping error doesn't invalidate the block inventory.

### Pilot before you scale

Phase 3.5 validates the entire pipeline with real content on real preview URLs at small scale before Phase 4 runs it 500 times in parallel. One fix here saves 500 fixes later.

### Handle the long tail

The feedback loop in Phase 4 catches pages that don't fit any archetype. Instead of treating them as failures, the system re-engages the Analyzer to learn the new pattern and retry. Only truly unresolvable pages reach the QA report.

### Validate on the real thing

Pilot and Migration verify against da.live preview URLs — not local dev servers. This catches issues that only surface in the real delivery pipeline (CDN behavior, content source integration, preview rendering).

### Consistency over creativity

The critical decisions (block palette, content models, styling conventions) are made once by the Analyzer in Phase 2, not independently per page. This prevents drift across a large migration.

### Document as you go

Documentation is a first-class deliverable, not an afterthought. Every phase writes its own report at completion time — when context is fresh. The Orchestrator compiles the final report, but never generates it from scratch.

### Survive failures gracefully

Checkpoint state for crash recovery. Per-page status files for race-free concurrency. Regression circuit breakers to prevent infinite loops. Cost tracking to prevent runaway spending. The system is designed to run for hours unsupervised.

---

## Getting Started

1. Set up credentials: GitHub token and da.live IMS token in Claude Managed Agents vaults
2. Implement Tier 1 validation scripts (reusable across all phases), including pixelmatch visual diff
3. Define the orchestrator agent with all callable agents, the worker/verifier loop logic, checkpoint/resume, and autonomous fallback
4. Build the Crawler worker; write Tier 1 scripts; build Crawler Verifier
5. Build the Analyzer worker (sub-steps 2a/2b/2c); write Tier 1 scripts; build Analyzer Verifier
6. Build the Block Dev worker; write Tier 1 scripts; build Block Dev Verifier; test GitHub push
7. Build the Pilot Migration pipeline with da.live uploads; build Pilot Verifier
8. Build the Page Migrator thread with self-contained Tier 1 verification and da.live upload
9. Build the Config worker with Tier 1 scripts, GitHub commit, and da.live sheet upload
10. Build the Integration QA worker with Tier 1 validation scripts
11. End-to-end test on a small site (< 20 pages)
12. Scale up to larger sites with tuned concurrency

