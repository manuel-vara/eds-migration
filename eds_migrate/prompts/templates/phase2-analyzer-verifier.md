### Phase 2 — Analyzer Verifier

```
Verify the Analyzer output. The blueprint is at `blueprint.json`. Sample page analyses are in `analysis/`.

Consult the **content-modeling** skill (David's Model, author-friendly structures) before reviewing. Also consult the **eds-knowledge** skill (developer-block-collection).

Check:
1. Content models follow David's Model (author-friendly, ≤4 cells/row, semantic formatting)
2. Block palette is minimal (no unnecessary blocks, no redundancy)
3. Archetype blueprints match the actual scraped pages (compare against analysis/)
4. No over-blocking (content that could be default content shouldn't be in blocks)
5. Conventions are consistent

Return your verdict as JSON.
```
