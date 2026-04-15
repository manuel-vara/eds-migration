### Phase 4 — Content Migration (Page Migrator, batched)

**Dispatch (per batch of pages):**
```
Migrate the following pages to da.live:

Consult the **page-import** and **generate-import-html** skills if you haven't already.

Blueprint: blueprint.json
da.live: {org}/{repo} (use $EDS_TOKEN for auth)
Preview base: https://main--{repo}--{org}.aem.page

Pages to migrate:
{{batch_urls_list}}

For each page, follow your per-page pipeline. Write status/{{url-hash}}.json. If a page doesn't match any archetype, write it to pending-patterns.json — do NOT retry it.
```
