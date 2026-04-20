## Your Specific Checks

You are verifying Phase 5 configuration. The previous migration
declared PASS on this phase while `/nav` and `/footer` on da.live were
empty documents — so every migrated page rendered with a collapsed
`<header></header>` and `<footer></footer>`. Your primary job is to
make sure that cannot happen again.

Follow your preamble's render, visual, and evidence rules. Source
ground truth lives in the Crawler's bundle at
`.eds-migration/state/source-bundle/`.

### GitHub and raw-file checks (raw HTTP is fine here)

1. **GitHub files exist on `main`**: Confirm via the GitHub API:
   - `GET /repos/{org}/{repo}/contents/helix-query.yaml?ref=main` → 200
   - `GET /repos/{org}/{repo}/contents/helix-sitemap.yaml?ref=main` → 200
   - `GET /repos/{org}/{repo}/contents/robots.txt?ref=main` → 200
2. **fstab.yaml still intact**: Fetch
   `https://raw.githubusercontent.com/{org}/{repo}/main/fstab.yaml`
   and confirm it still contains `https://content.da.live/{org}/{repo}`.
   Config work must not have overwritten it.
3. **YAML validity**: Fetch the raw `helix-query.yaml` and
   `helix-sitemap.yaml` from GitHub and parse them. Invalid YAML is
   a FAIL.

### Redirects

4. **Redirects are in da.live and correctly formatted**: Fetch
   `GET https://admin.da.live/source/{org}/{repo}/redirects` with
   `Authorization: Bearer $EDS_TOKEN`. Confirm:
   - 200 response and non-empty body.
   - Body is an HTML table (not JSON).
   - Table has `Source` and `Destination` column headers.
   - At least one redirect row exists.

### Nav and footer — the critical gate

5. **Nav and footer documents exist on da.live**: Fetch both
   `GET https://admin.da.live/source/{org}/{repo}/nav` and
   `.../footer` with `Authorization: Bearer $EDS_TOKEN`. Confirm 200
   and non-empty body. Then fetch the preview URLs
   `https://main--{repo}--{org}.aem.page/nav` and `.../footer`;
   confirm 200 and that the served HTML body contains real
   elements — not the shell
   `<body><header></header><main><div></div></main><footer></footer></body>`
   that the previous failed migration produced. If either document has
   a collapsed/empty `<main>`, that is an immediate high-severity FAIL.

6. **Rendered nav and footer have real content in context**: Render
   the migrated homepage
   `https://main--{repo}--{org}.aem.page/` in Playwright with a
   settle wait. In the rendered DOM:
   - The `<header>` element must contain at least one link.
   - The `<footer>` element must contain at least one link.
   - Screenshot the top strip (header band) and the bottom strip
     (footer band) of the rendered homepage. Commit them under
     `.eds-migration/verifier-results/config/screenshots/` as
     `home-header-<viewport>.png` and `home-footer-<viewport>.png`
     at both desktop (≥1280 px) and mobile (≤420 px).
   - Compare each strip against `source-bundle/chrome/header-desktop.png`
     and `source-bundle/chrome/footer-desktop.png` (plus mobile
     variants if the crawler captured them). Pick your scoring
     method; document method + threshold. Attach per-strip
     similarity evidence.
   - A wholly empty chrome band — or chrome that visually resembles
     nothing like the source — is an automatic high-severity FAIL.

7. **Nav/footer link coverage vs source chrome**: Compare the visible
   link text in the migrated nav/footer (from the in-context
   homepage render, not just the `/nav` and `/footer` docs) against
   `source-bundle/chrome/header.links.json` and
   `source-bundle/chrome/footer.links.json`. Cite a
   matched/unmatched list in the evidence. Fewer than ~60% of the
   source's nav links present (allowing for reasonable editorial
   consolidation) is a FAIL.
