### Phase 3.5 — Pilot (Page Migrator on samples)

**First dispatch:**
```
Pilot migration: migrate the sample pages to validate the full pipeline.

Blueprint: blueprint.json
da.live org/repo: {org}/{repo} (use the da-token vault for auth)
Preview base: https://main--{repo}--{org}.aem.page

Migrate these sample pages (one per archetype, from manifest.json archetypes[*].sampleUrls[0]):
{{sample_urls_list}}

For each page, follow the full per-page pipeline in your system prompt. Write status/{{url-hash}}.json for each page.
```

**Retry (Tier 2 failure):**
```
The Pilot Verifier found issues with the sample migration:

{{verifier_verdict_json}}

Fix the specific pages that failed. The blueprint and code are still in place. Re-upload corrected HTML to da.live and update the status files.
```
