### Phase 2 — Analyzer

**First dispatch (all sub-steps):**
```
Analyze the site for migration. The manifest is at `manifest.json`.

Execute all three sub-steps:

Phase 2a — Scrape Samples:
Select 2-3 representative pages per archetype from manifest.json.
For each, scrape with Playwright: screenshot, metadata, cleaned HTML, images.
Store in analysis/{{archetype}}/{{page-slug}}/.

Phase 2b — Build Block Inventory:
Analyze all scraped pages to identify sections and content sequences.
Build a global block inventory. Search Block Collection and Block Party for matches.

Phase 2c — Define Migration Blueprint:
Decide block palette (Block Collection vs custom). Define content models.
Map archetypes to section blueprints. Document site conventions.

Write blueprint.json to the working directory.
```

**Retry (Tier 1 failure on sub-step 2a/2b):**
```
Sub-step {{substep}} failed Tier 1 validation:

{{tier1_errors}}

Fix the issues. The existing analysis/ directory and manifest.json are still available.
```

**Retry (Tier 2 failure on blueprint):**
```
The Analyzer Verifier found issues with your blueprint.json:

{{verifier_verdict_json}}

Fix the blueprint. The analysis/ directory is still available for reference. Focus on the specific issues — don't redo the full analysis.
```
