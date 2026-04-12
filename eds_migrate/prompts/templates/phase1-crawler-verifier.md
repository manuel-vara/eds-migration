### Phase 1 — Crawler Verifier

```
Verify the Crawler output. The manifest is at `manifest.json` in the working directory.

Check:
1. Archetype categorization is sensible (sample URLs match their archetype)
2. No major site sections were missed (compare nav links vs archetypes)
3. Priority assignments are reasonable

Return your verdict as JSON: {{"verdict": "PASS"|"FAIL", "issues": [...], "summary": "..."}}
```
