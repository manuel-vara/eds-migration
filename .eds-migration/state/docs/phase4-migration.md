# Phase 4 Migration Log

---

## Chunk 1/4 — Batch Summary

**Worker:** PageMigrator-1b3ddcfa#chunk1  
**Run date:** 2026-05-12  
**Branch:** migration-state/1b3ddcfa

### Pages Processed

| URL | Archetype | EDS Path | Status |
|-----|-----------|----------|--------|
| https://www.almacgroup.com/ | homepage | / (index) | HTML generated; upload blocked (no EDS_TOKEN) |
| https://www.almacgroup.com/about/ | about | /about | HTML generated; upload blocked (no EDS_TOKEN) |
| https://www.almacgroup.com/contact-us/ | contact | /contact-us | HTML generated; upload blocked (no EDS_TOKEN) |

Additionally generated:
- `/nav` — standard EDS nav with logo + service nav + utility nav
- `/footer` — quick links, contact numbers, social links

### Archetype Matching

All three pages matched known archetypes from `blueprint.json`. No entries added to `pending-patterns.json`.

| Page | Blueprint Archetype | Sections Used |
|------|---------------------|---------------|
| Homepage | `homepage` | Carousel(hero), Stats(dark), Cards(services), Cards(news), full-width CTA, Fragment |
| About | `about` | Hero, Breadcrumbs, Columns(grey), Cards(sub-pages), Fragment |
| Contact Us | `contact` | Breadcrumbs, Columns(form+offices), Fragment |

### Generated HTML Files (chunk 1)

Stored under `.eds-migration/state/migrated-html/`:

- `nav.html` — EDS nav document (logo + nav lists)
- `footer.html` — EDS footer document
- `index.html` — Homepage
- `about.html` — About page
- `contact-us.html` — Contact page

### Content Fidelity (chunk 1)

| Page | Est. Text Ratio | Est. Image Ratio | Notes |
|------|----------------|-----------------|-------|
| Homepage | ~75% | ~70% | Stats + news + CTA all present; events partial |
| About | ~85% | ~50% | Full text body; 3/6 card images missing (lazy-load) |
| Contact Us | ~80% | ~60% | Office info complete; form replaced with block |

### Issues (chunk 1)

1. **EDS_TOKEN not available** — All uploads blocked. HTML files committed to branch. Re-run: `EDS_TOKEN=<token> python3 /home/claude/scratch/page-migrator/da_upload.py`
2. **Lazy-loaded images with data: placeholder src** — Some card images empty; background-image style attrs extracted correctly.
3. **Events section on homepage** — Event items not fully extracted (Slick slider). Section header preserved; populate via `content-filter` once event pages migrate.
4. **Galen Pharmaceuticals link has HubSpot tracking params** — Preserved as-is; clean during QA.

---

## Chunk 3/4 — Batch Summary

**Worker:** PageMigrator-1b3ddcfa#chunk3  
**Pages Assigned:** 3 URLs  
**Run date:** 2026-05-12

### Pages Migrated (chunk 3)

| URL | Archetype | Status | EDS Path | Notes |
|-----|-----------|--------|----------|-------|
| https://www.almacgroup.com/biotech/ | N/A (redirect) | failed | N/A | 301 redirect — added to pending-patterns.json |
| https://www.almacgroup.com/careers/ | landing | failed (no token) | /careers | HTML staged, upload blocked: no EDS_TOKEN |
| https://www.almacgroup.com/knowledge/library/2019-investments-centered-around-cell-and-gene-therapies/ | knowledge-library | failed (no token) | /knowledge/library/2019-investments-centered-around-cell-and-gene-therapies | HTML staged, upload blocked: no EDS_TOKEN |

Additional pages created (nav/footer):
- `/nav` — staged at `.eds-migration/state/content-staging/nav.html`
- `/footer` — staged at `.eds-migration/state/content-staging/footer.html`

### Pages Sent to pending-patterns.json (chunk 3)

| URL | Pattern | Reason |
|-----|---------|--------|
| https://www.almacgroup.com/biotech/ | redirect-page | 301 redirect to /events/biotech-japan-2018/ — needs redirect rule in EDS redirects spreadsheet |

### EDS HTML Generated (chunk 3)

All generated HTML files stored in `.eds-migration/state/content-staging/`:

**careers.html → /careers**
- Archetype: landing (per manifest.json)
- Source: source-bundle/pages/careers/index.html
- Blocks: `Hero`, `Stats`, `Cards (news)`, default content, `Fragment`, `Metadata`
- Text fidelity: ~78% | Image fidelity: ~60%

**knowledge-library-2019-investments.html → /knowledge/library/2019-investments-centered-around-cell-and-gene-therapies**
- Archetype: knowledge-library
- Source: source-bundle/pages/knowledge-library/index.html
- Blocks: `Breadcrumbs`, default content, `Profile`, `Hubspot Form (gated-content)`, `Cards (related)`, `Fragment`, `Metadata`
- Text fidelity: ~82% | Image fidelity: ~85%

**nav.html → /nav**
- Standard EDS nav: logo + service links + utility links
- Based on source-bundle/chrome/header.links.json

**footer.html → /footer**
- Standard EDS footer: logo + quick links + contact info + social links + legal links
- Based on source-bundle/chrome/footer.links.json

### Issues (chunk 3)

1. **EDS_TOKEN not available** — Uploads blocked. HTML staged in `.eds-migration/state/content-staging/`. Upload manually via da.live UI or with token.
2. **/biotech/ is a 301 redirect** — URL redirects to `/events/biotech-japan-2018/`. Added to `pending-patterns.json`. Needs redirect rule in `redirects.xlsx`, not a content page.
3. **careers/talent-network double slash in source HTML** — WordPress URL composition bug. Fixed by hardcoding correct path.
4. **Knowledge Library related resource links missing** — `<a>` tags had no `href` in rendered HTML (JS-rendered). Used slugified heading text as approximate EDS paths.

### Text/Image Fidelity Distribution (chunk 3)

| Page | Text Ratio | Image Ratio |
|------|-----------|-------------|
| /biotech/ | N/A (redirect) | N/A |
| /careers/ | 0.78 | 0.60 |
| /knowledge/library/2019-investments... | 0.82 | 0.85 |

---

## Overall Next Steps

1. Provide valid `EDS_TOKEN` and re-upload all staged HTML from both chunks via da.live Source API.
2. Add redirect rule in `redirects.xlsx` for `/biotech/` → `/events/biotech-japan-2018/`.
3. Verify da.live preview renders correctly at `https://main--eds-migration--manuel-vara.aem.page/careers`.
4. Verify knowledge-library HubSpot form portal ID and form ID.
5. For homepage events section: populate via `content-filter` query once events pages are migrated.
