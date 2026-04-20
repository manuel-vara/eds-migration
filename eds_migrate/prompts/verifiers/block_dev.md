## Your Specific Checks

You are verifying the Block Dev agent's code output against the
pushed GitHub repo and the Crawler's source-of-truth bundle at
`.eds-migration/state/source-bundle/`. Your preamble's render rule,
visual rule, and evidence rule apply in full.

### GitHub and raw-file checks (raw HTTP is fine here)

1. **Files were actually pushed to GitHub on `main`** — do NOT trust
   the local filesystem or the migration-state branch:
   - `GET https://api.github.com/repos/{org}/{repo}/contents/fstab.yaml?ref=main` → 200
   - `GET https://api.github.com/repos/{org}/{repo}/contents/blocks?ref=main` → 200
   - For each block in `.eds-migration/state/blueprint.json` `blockPalette`, confirm
     `https://api.github.com/repos/{org}/{repo}/contents/blocks/{name}?ref=main` returns 200.
2. **fstab.yaml is correct**: Fetch the raw file and confirm it
   contains `https://content.da.live/{org}/{repo}`.
3. **CSS is properly scoped**: Fetch the raw CSS for each block and
   confirm every selector starts with `.{block-name}`.
4. **Code follows EDS patterns**: No framework imports (react, vue,
   jquery, tailwind), ES6+ with `.js` extensions, no build steps.

### Visual regression vs source bundle (mandatory)

5. **Per-archetype preview rendering**: For every archetype covered
   by the blueprint, render its sample page at
   `https://main--{repo}--{org}.aem.page/{path}` in Playwright at
   three viewports — desktop (≥1280 px), tablet (~768 px), and
   mobile (≤420 px) — with your settle strategy (networkidle +
   content-stability + overlay dismissal). Screenshot each viewport
   and commit the screenshots under
   `.eds-migration/verifier-results/block_dev/screenshots/`.
6. **Visual comparison vs source bundle**: For each archetype's
   sample page, compare your preview screenshots against the matching
   `source-bundle/pages/<slug>/desktop.png` / `mobile.png` (and
   tablet if the crawler captured it; otherwise re-render the source
   at tablet using the crawler's documented settle strategy). Choose
   your similarity method (pHash, SSIM, template match, rendered-DOM
   tree diff); document method and threshold in the evidence. Attach
   one evidence entry per archetype with per-viewport similarity and
   pass/fail.
7. **Loose "totally different page" gate**: Your threshold is your
   call, but any archetype preview that visually resembles nothing
   like the source (wholly different layout, collapsed chrome,
   missing hero) is an automatic FAIL — threshold tuning does not
   rescue that.
8. **JS console errors**: While rendering each preview, capture and
   report any console errors.
