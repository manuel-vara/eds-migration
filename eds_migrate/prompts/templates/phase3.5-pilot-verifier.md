### Phase 3.5 — Pilot Verifier

```
Verify the Pilot Migration output. Sample pages have been uploaded to da.live and are previewable at https://main--{repo}--{org}.aem.page/.

Status files are in status/. The original screenshots are in analysis/.

Consult the **page-import** and **preview-import** skills to understand correct import structure and preview validation.

Check:
1. Pages render without JS errors (load preview URLs in Playwright)
2. Visual diff scores: review any page with score < 0.8
3. Blocks decorate correctly on live preview
4. Content is complete and faithful vs the original cleaned HTML

Return your verdict as JSON.
```
