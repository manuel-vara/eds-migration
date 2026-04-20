## Your Specific Checks

You are verifying the Phase 4 content migration against the Crawler's
source-of-truth bundle at `.eds-migration/state/source-bundle/`.

Write your own Playwright comparison script. Reuse the crawler's
documented settle strategy (`source-bundle/README.md`) so your
captures line up with the ground truth. Your preamble's render rule,
visual rule, and evidence rule apply in full here.

Do NOT read status files to determine pass/fail — verify externally.

1. **Coverage**: Count `.eds-migration/state/status/*.json` files with
   `"status": "migrated"`. This must be ≥ 90% of the total pages in
   `.eds-migration/state/manifest.json`. If below 90%, FAIL with the
   count and gap.
2. **Spot-check sample**: Select at least **one page per archetype**
   from the migrated status files (more if an archetype has many
   pages). These are the pages you compare in detail.
3. **Spot-check — da.live content present**: For each sample, hit
   `GET https://admin.da.live/source/{org}/{repo}/{path}` with
   `Authorization: Bearer $EDS_TOKEN`. Confirm 200 and non-empty
   HTML. Raw HTTP is fine here (da.live admin is not an SPA).
4. **Spot-check — preview accessible and rendered**: For each sample,
   render `https://main--{repo}--{org}.aem.page/{path}` in Playwright
   with your settle strategy. Confirm 200 and visible body content
   before you measure anything.
5. **Spot-check — visual comparison vs source (mandatory)**: For each
   sample, render at desktop (≥1280 px) and mobile (≤420 px),
   screenshot each after settle, and compare against
   `source-bundle/pages/<slug>/desktop.png` / `mobile.png`. Choose
   your scoring method (pHash, SSIM, template match, rendered-DOM
   tree diff); document the method and threshold. Commit the preview
   screenshots under
   `.eds-migration/verifier-results/migration/screenshots/`. Attach
   evidence per page with per-viewport similarity, method,
   threshold, pass/fail. Pages that visually resemble nothing like
   the source are automatic FAILs.
6. **Spot-check — content completeness**: Compare visible text on
   each rendered preview against the rendered source in
   `source-bundle/pages/<slug>/index.html`. Report per-page
   word-overlap and cite missing excerpts. A preview with < 50% of
   the source's rendered text is an automatic FAIL for that page.
7. **Spot-check — chrome is present**: For each rendered sample,
   confirm a non-empty header band and footer band. Empty chrome is
   a high-severity FAIL at the migration-phase level because it
   indicates a systemic regression across every page.
8. **Spot-check — no JS errors**: Check Playwright console for each
   sample page and cite any errors.
9. **Published**: At least the spot-checked pages must have
   `"published": true` in their status files. Flag any that are
   missing this.
