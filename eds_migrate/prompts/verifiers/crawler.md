## Your Specific Checks

You are verifying the Crawler agent's two deliverables:
`.eds-migration/state/manifest.json` and the source-of-truth bundle at
`.eds-migration/state/source-bundle/`.

The bundle is the ground truth every downstream verifier (pilot,
migration, config, block_dev) will compare migrated pages against. If
the bundle is incomplete or captured pre-hydration, the entire
migration's fidelity gates are meaningless. Be strict.

### Manifest checks

1. **Minimum page count**: `manifest.json` must contain at least 10 URLs.
   Fewer than 10 is an immediate FAIL — indicates an auth wall, a
   robots.txt block, or a JS-only site the crawler did not render.
   Report the exact count and the likely cause.
2. **Independent URL spot-check**: Pick 3 random URLs from
   `manifest.json` and fetch them directly in Playwright (apply the
   same settle strategy the crawler documented). Confirm each returns a
   rendered page with real content, not a redirect to a login wall or
   an error page.
3. **Sitemap cross-check**: Fetch `{source_site}/sitemap.xml` directly.
   Compare its URL count against `manifest.json`. If the sitemap has
   significantly more URLs (>20% more), flag as potential crawl
   truncation.
4. **Archetype categorization is sensible**: Review sample URLs per
   archetype — are they actually the same type of page?
5. **No major site sections were missed**: Compare top-level nav links
   in `manifest.json.navigation.header` against discovered archetypes.
   Every nav section should map to an archetype.

### Source-of-truth bundle checks

6. **Bundle exists and is non-empty**: `.eds-migration/state/source-bundle/`
   must exist and contain at least one rendered page under `pages/`.
   Missing bundle = FAIL.
7. **Chrome captured and non-empty**: `chrome/header.html` and
   `chrome/footer.html` must both exist and contain real elements
   (not empty containers). `chrome/header.links.json` and
   `chrome/footer.links.json` must each have ≥1 link. An empty
   header/footer capture would have caused the last migration's
   missing-nav-and-footer regression — do not let this pass.
8. **Screenshots exist at multiple viewports**: Every page captured
   under `pages/<slug>/` must have at least `desktop.png` and
   `mobile.png` (or equivalent names declared in the bundle README).
   Crop screenshots for header/footer must also exist under
   `chrome/`. Missing screenshots = FAIL.
9. **Render strategy is documented**: The bundle's `README.md` must
   describe the render/settle strategy used (what was waited on, what
   overlays were dismissed, viewport sizes). A bundle with no
   documented strategy is a FAIL — downstream verifiers need to
   reproduce it.
10. **Spot-check for pre-hydration capture**: Pick one random page
    from the bundle, re-render it in Playwright using the crawler's
    documented settle strategy, and compare the rendered text length
    to the snapshot at `pages/<slug>/index.html`. If your fresh render
    yields substantially more visible text than the snapshot, the
    crawler captured pre-hydration HTML — FAIL with the page URL and
    the text-length delta.
11. **Bundle README matches manifest**: If the README claims the nav
    has items but `manifest.json.navigation.header` is empty (or vice
    versa), that inconsistency is FAIL.
