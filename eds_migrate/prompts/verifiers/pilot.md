## Your Specific Checks

You are verifying the Pilot Migration output — sample pages uploaded to
da.live and rendered on real preview URLs — against the Crawler's
source-of-truth bundle at `.eds-migration/state/source-bundle/`.

Write your own Playwright comparison script, adapted to this site's
render characteristics (see the crawler's `source-bundle/README.md`
for the settle strategy that was used for capture). Follow the global
render rule, visual rule, and evidence rule in your preamble — they
apply in full here.

For every pilot URL:

1. **Content is actually in da.live**: Fetch it from the Source API —
   `GET https://admin.da.live/source/{org}/{repo}/{path}` with
   `Authorization: Bearer $EDS_TOKEN`. Confirm 200 and non-empty HTML
   body. Raw HTTP here is fine (da.live admin is not an SPA). Do NOT
   rely on worker status files — verify independently.
2. **Preview is accessible and rendered**: Render
   `https://main--{repo}--{org}.aem.page/{path}` in Playwright with
   your settle strategy. Confirm 200 and visible body content.
3. **No JS errors**: Check the Playwright console for errors while
   rendering.
4. **Visual comparison vs source (mandatory)**: For each pilot URL,
   render the preview at desktop (≥1280 px) and mobile (≤420 px),
   screenshot each after settle, and compare against the matching
   `source-bundle/pages/<slug>/desktop.png` and `mobile.png`. Pick your
   similarity scoring method (pHash, SSIM, template match, rendered
   DOM-tree diff). Commit the preview screenshots under
   `.eds-migration/verifier-results/pilot/screenshots/`. Attach one
   evidence entry per URL with per-viewport scores, method, threshold,
   and pass/fail. Any viewport that visually resembles nothing like
   the source is an automatic FAIL for that page.
5. **Content-fidelity vs bundle**: Compare visible text on the rendered
   preview against the rendered source in
   `source-bundle/pages/<slug>/index.html`. Report per-page word-set
   overlap (or equivalent). Missing-from-preview excerpts should be
   cited in the evidence. A preview with < 50% of the source's
   rendered text length is an automatic FAIL for that page.
6. **Chrome is present on pilot pages**: While rendering each preview,
   confirm the page actually shows a non-empty header band and footer
   band (not the collapsed `<header></header>` / `<footer></footer>`
   that plagued the previous run). If either is empty, that is a
   high-severity FAIL — the pilot cannot pass without chrome.
7. **Blocks decorate correctly**: Sanity-check the decorated output
   against the expected block structure from
   `.eds-migration/state/blueprint.json`. This is support evidence,
   not a primary gate — blocks "rendering" on their own does not
   rescue a page that fails the visual or content-fidelity gates
   above.
