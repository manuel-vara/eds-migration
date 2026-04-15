### Phase 1 — Crawler

**First dispatch:**
```
Crawl the site: {site_url}

Write manifest.json to the working directory. Include every page, categorize by archetype, map navigation, and extract global assets.

Before starting, consult the **scrape-webpage** and **identify-page-structure** skills (attached to your agent).
```

**Retry (Tier 1 failure):**
```
Your manifest.json failed validation. Here are the errors:

{{tier1_errors}}

Fix these issues and write an updated manifest.json.
```

**Retry (Tier 2 failure):**
```
The Crawler Verifier found issues with your manifest.json:

{{verifier_verdict_json}}

Address the issues above and write an updated manifest.json. Do not re-crawl from scratch unless pages are missing — fix incrementally.
```
