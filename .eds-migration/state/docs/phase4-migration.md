# Phase 4 Migration Log — Chunk 1/4

**Worker:** PageMigrator-1b3ddcfa#chunk1  
**Run date:** 2026-05-12  
**Branch:** migration-state/1b3ddcfa

---

## Pages Processed

| URL | Archetype | EDS Path | Status |
|-----|-----------|----------|--------|
| https://www.almacgroup.com/ | homepage | / (index) | HTML generated; upload blocked (no EDS_TOKEN) |
| https://www.almacgroup.com/about/ | about | /about | HTML generated; upload blocked (no EDS_TOKEN) |
| https://www.almacgroup.com/contact-us/ | contact | /contact-us | HTML generated; upload blocked (no EDS_TOKEN) |

Additionally generated:
- `/nav` — standard EDS nav with logo + service nav + utility nav
- `/footer` — quick links, contact numbers, social links

---

## Archetype Matching

All three pages matched known archetypes from `blueprint.json`. No entries added to `pending-patterns.json`.

| Page | Blueprint Archetype | Sections Used |
|------|---------------------|---------------|
| Homepage | `homepage` | Carousel(hero), Stats(dark), Cards(services), Cards(news), full-width CTA, Fragment |
| About | `about` | Hero, Breadcrumbs, Columns(grey), Cards(sub-pages), Fragment |
| Contact Us | `contact` | Breadcrumbs, Columns(form+offices), Fragment |

---

## Generated HTML Files

Stored under `.eds-migration/state/migrated-html/`:

- `nav.html` — EDS nav document (logo + nav lists)
- `footer.html` — EDS footer document
- `index.html` — Homepage (carousel hero with 5 slides, stats block, service cards, 6 news cards, events placeholder, full-width CTA band, metadata)
- `about.html` — About page (hero with banner image, breadcrumbs, columns with text+video placeholder, 6 sub-page cards, metadata)
- `contact-us.html` — Contact page (breadcrumbs, columns with HubSpot form placeholder + 3 office locations with images, metadata)

---

## Content Fidelity Notes

### Homepage
- **Carousel hero:** 5 slides extracted from Slick slider — all with background images, headings, and CTA links ✓
- **Stats:** All 5 stats preserved (7800+ employees, 50% NMEs, 55+ years, top 25 biopharma, 18 facilities) ✓
- **Service cards:** 4 main service areas extracted (Discovery, Diagnostics, Pharma Dev, Galen) — images were lazy-loaded background divs without `<img>` tags, so cards have text-only ⚠️
- **News cards:** 6 news items with dates, titles, images, and links ✓
- **Events:** Section header present but event items not extracted (nested structure hidden under slick slider); defaulted to a section break ⚠️
- **Full-width CTA:** "Partnering to advance human health" band preserved ✓

### About Page
- **Hero:** Banner image from smush CDN preserved ✓
- **Breadcrumbs:** Raw breadcrumb HTML preserved ✓  
- **Columns:** Full text body (4 paragraphs) with corporate brochure PDF link; video panel was empty in source bundle → placeholder added ⚠️
- **Cards:** 6 sub-page cards; 3 have real images, 3 had `data:` placeholder images (lazy-loaded, not captured by crawler) ⚠️

### Contact Us
- **Form:** Gravity Forms removed (client-side only), replaced with `HubSpot Form` block placeholder ✓
- **Offices:** 3 office locations (UK, US, Asia Pacific) with background images, addresses, phone/email links ✓

---

## Issues & Resolutions

### Issue 1: EDS_TOKEN not available
- **Impact:** Cannot call `POST https://admin.da.live/source/...` or `POST https://admin.hlx.page/preview/...`
- **Resolution:** HTML files generated and committed to migration-state branch. Status files written with `"status": "failed"` and `"failureReason": "EDS_TOKEN not set; cannot upload to da.live"`. Upload helper scripts saved to `/home/claude/scratch/page-migrator/` for manual re-run once token is available.
- **Re-run command:** `EDS_TOKEN=<token> python3 /home/claude/scratch/page-migrator/da_upload.py`

### Issue 2: Lazy-loaded images with data: placeholder src
- **Impact:** Some card images show empty in output (the crawler captured the `data:image/gif` placeholder, not the loaded image)
- **Resolution:** Image src set to empty, card renders as text-only. Background-image style attributes were used for news panels and banners — these were correctly extracted.

### Issue 3: Events section on homepage
- **Impact:** Event items not fully extracted (nested inside duplicate Slick slider markup)  
- **Resolution:** Events section header preserved. In production, the `Cards (event)` block would be populated via a content-filter/query sheet once all pages are migrated.

### Issue 4: Galen Pharmaceuticals link has tracking params
- **Impact:** HubSpot tracking parameters (`__hstc`, `__hssc`) in the external link
- **Resolution:** Preserved as-is in card link. Can be cleaned manually during QA.

---

## Text / Image Fidelity Distribution

| Page | Est. Text Ratio | Est. Image Ratio | Notes |
|------|----------------|-----------------|-------|
| Homepage | ~75% | ~70% | Stats + news + CTA all present; events partial |
| About | ~85% | ~50% | Full text body; 3/6 card images missing (lazy-load) |
| Contact Us | ~80% | ~60% | Office info complete; form replaced with block |

*Note: Ratios are estimates based on content inspection, not Playwright screenshot diff — Playwright checks require a successful preview URL.*

---

## Pending Archetype Patterns

None added for this chunk. All 3 URLs matched known archetypes.

---

## Next Steps for Downstream Agents

1. Set `EDS_TOKEN` and re-run `da_upload.py` — it will upload and preview all 5 files (nav, footer, index, about, contact-us)
2. After preview succeeds, run Playwright self-check (text/image ratio validation)
3. For events on homepage: populate via `content-filter` query once events pages are migrated
4. For service card images: re-scrape with JavaScript execution to capture lazy-loaded images
