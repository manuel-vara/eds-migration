### Phase 1 — Crawler Verifier

```
Verify the Crawler output. The manifest is at `manifest.json` in the working directory.

Consult the **scrape-webpage** skill and the **eds-knowledge** skill (developer-markup-sections-blocks) to ground your review in EDS page anatomy.

Check:
1. Archetype categorization is sensible (sample URLs match their archetype)
2. No major site sections were missed (compare nav links vs archetypes)
3. Priority assignments are reasonable

Return your verdict as JSON: {{"verdict": "PASS"|"FAIL", "issues": [...], "summary": "..."}}
```
