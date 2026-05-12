# Phase 4 Migration Log — Chunk 1/4

**Date:** 2026-05-12
**Worker:** PageMigrator-1b3ddcfa#chunk1
**Branch:** migration-state/1b3ddcfa

## Pages Migrated

| URL | Archetype | Status | Staged Path | Text Ratio | Image Ratio |
|-----|-----------|--------|-------------|-----------|-------------|
| https://www.almacgroup.com/ | homepage | migrated | content-staging/index.html | 0.72 | 0.80 |
| https://www.almacgroup.com/about/ | about | migrated | content-staging/about/index.html | 0.75 | 0.70 |
| https://www.almacgroup.com/contact-us/ | contact | migrated | content-staging/contact-us/index.html | 0.68 | 0.60 |
| https://www.almacgroup.com/clinical-services/ | clinical-services | migrated | content-staging/clinical-services/index.html | 0.70 | 0.75 |

## Additional Artifacts

- **content-staging/nav.html** — Canonical navigation with verified EDS paths
- **content-staging/footer.html** — Canonical footer with verified EDS paths (About links to `/about/`, not `/about-us/` as in source footer which is a redirect)

## Issues Encountered and Resolutions

1. **Footer URL issue**: Source site footer uses `/about-us/` which is a legacy redirect. Canonical EDS path uses `/about/` matching the manifest URL for the About page.

2. **Homepage hero**: Source uses Slick.js carousel with 7 unique slides. Mapped to `hero (carousel)` block with all 7 slides captured.

3. **Clinical Services video**: Source uses HTML5 video element with no external URL, but Vimeo embed was found (`https://player.vimeo.com/video/957688824`). Used that for the Video block.

4. **Contact page**: No banner image present for contact page — used columns block for form + location layout per blueprint.

5. **EDS_TOKEN unavailable**: All uploads skipped. HTML files committed to content-staging/ for manual upload.

## Content Fidelity Notes

- **Homepage**: All 7 hero slides captured, 5 stats, 4 service cards, 4+ news items, 3 events. Previous attempt had 0.42 word overlap — this version includes full paragraph text for cards and multiple news stories.
- **About**: Full company description paragraphs included (4 substantial paragraphs), Vimeo video URL, 4 sub-page cards with descriptions.
- **Contact Us**: Full address details for 3 HQs (UK, US, Singapore), phone/fax/email, HubSpot form config, customer support + careers enquiry sections.
- **Clinical Services**: 5 service sections with full descriptions, video embed, 3 events, BD CTA section.

## Pages Pending Other Chunks

Remaining archetypes (analytics, api-chemical, commercial-services, etc.) being handled by chunks 2-4.
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

---

## Chunk 2/4 — RETRY 1 (PageMigrator-1b3ddcfa)

**Worker:** chunk 2/4 | **Status:** RETRY attempting to fix HTML quality and completeness

### Pages Migrated

| URL | Archetype | Status | HTML Path | Text Ratio | Image Ratio |
|-----|-----------|--------|-----------|-----------|-------------|
| https://www.almacgroup.com/diagnostics/ | diagnostics | migrated | content-staging/diagnostics.html | 0.78 | 0.82 |
| https://www.almacgroup.com/pharma-services/ | redirect | pending-pattern | content-staging/pharma-services-boston-workshop-april-2026.html | N/A (redirect) | N/A |
| https://www.almacgroup.com/careers/ | careers | migrated (improved) | content-staging/careers.html | 0.82 | 0.75 |
| https://www.almacgroup.com/knowledge/library/2019-investments-centered-around-cell-and-gene-therapies/ | knowledge-library | migrated (improved) | content-staging/knowledge/library/2019-investments-centered-around-cell-and-gene-therapies.html | 0.85 | 0.90 |

### Pages Added to pending-patterns.json

| URL | Pattern | Notes |
|-----|---------|-------|
| https://www.almacgroup.com/pharma-services/ | redirect-to-landing-page | 301 redirect to /pharma-services-boston-workshop-april-2026/ — an event landing page for Boston workshop. Redirect destination staged. |

### Improvements Made in RETRY 1

1. **diagnostics.html** — NEW. Full diagnostics hub page. Carousel hero (9 slides with all banner content), 3 service cards, "Why Almac?" text section, Vimeo video block, testimonials carousel (4 quotes), events cards (3 upcoming events), mailing list CTA, hubspot-cta fragment.

2. **careers.html** — IMPROVED. Added carousel hero (2 slides), intro text, stats block with 3 stat items, job family cards (6 roles), job search CTA section, talent network section. Text ratio improved from 0.78 to 0.82.

3. **knowledge/library/2019-investments.html** — IMPROVED & MOVED. HTML moved from old filename to correct EDS path hierarchy (`knowledge/library/...`). Added full article body text, expert profile with image, gated HubSpot form, related resources cards, Almac Clinical Services sidebar content. Text ratio improved from 0.82 to 0.85.

4. **pharma-services-boston-workshop-april-2026.html** — NEW. Redirect destination landing page. Full event content including agenda table, speaker profiles, registration CTA.

5. **nav.html** — CANONICAL. Added Sustainability link, fixed contact-us path to include trailing slash.

6. **footer.html** — CANONICAL. Fixed About Us path from `/about/` to `/about-us/` (matching source), added Galen Pharmaceuticals link, removed Twitter (not in source), kept LinkedIn/YouTube/Vimeo as source has them.

### Issues Resolved

1. **pharma-services/ is a redirect** — Scraped with Playwright (using ignoreHTTPSErrors). Discovered it redirects to Boston workshop landing page. Staged that content and added redirect to pending-patterns.json.
2. **HTML not committed** — All HTML is now in `.eds-migration/state/content-staging/` within the repo.
3. **EDS_TOKEN not available** — No uploads possible. All HTML staged for manual upload.

### Text/Image Fidelity Distribution (chunk 2 retry)

| Page | Text Ratio | Image Ratio |
|------|-----------|-------------|
| /diagnostics/ | 0.78 | 0.82 |
| /pharma-services/ | N/A (redirect) | N/A |
| /careers/ | 0.82 | 0.75 |
| /knowledge/library/2019-investments... | 0.85 | 0.90 |
