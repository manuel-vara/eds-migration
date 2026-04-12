### Phase 6 — Integration QA

**First dispatch:**
```
Run full integration QA on the completed migration.

Preview base: https://main--{repo}--{org}.aem.page
manifest.json has all source pages.
status/ has per-page migration results.
blueprint.json has archetype definitions.

Run all checks from your system prompt:
1. Visual regression across all archetypes
2. Lighthouse performance
3. Link checking
4. Content completeness spot-checks
5. Accessibility basics
6. Navigation verification
7. Redirect verification

Write qa-report.json with full results.
```
