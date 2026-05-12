# Migration Report: almacgroup.com → EDS

**Source site:** https://www.almacgroup.com  
**Target repo:** https://github.com/manuel-vara/eds-migration  
**Preview URL:** https://main--eds-migration--manuel-vara.aem.page/  
**CDN URL:** https://main--eds-migration--manuel-vara.aem.live/  
**DA.live edit:** https://da.live/edit#/manuel-vara/eds-migration  
**Generated:** 2026-05-12  
**Migration run:** 1b3ddcfa  

---

## Executive Summary

Almac Group's corporate site (https://www.almacgroup.com) has been fully analysed, architected, and partially migrated to Adobe Edge Delivery Services. The site comprises **3,615 pages across 27 archetypes**, built on a WordPress Multisite installation with 11 sub-site sitemaps.

### What was completed

| Phase | Status | Key Output |
|-------|--------|-----------|
| 1 — Crawl & Discovery | ✅ Complete | manifest.json: 3,615 pages, 27 archetypes |
| 2 — Analysis & Blueprint | ✅ Complete | blueprint.json: 28 archetypes, 18-block palette |
| 3 — Block Development | ✅ Complete | 19 blocks on main, ESLint passing |
| 4 — Content Migration (pilot) | ✅ Complete | 16 pilot HTML pages staged |
| 5 — Configuration | ✅ Complete | nav, footer, redirects, metadata, sitemaps |
| 6 — Integration QA | ✅ Complete (deferred items) | qa-report.json, this report |

### What is blocked pending infrastructure
Two prerequisites block live validation and the remaining content migration:
1. **EDS_TOKEN** — da.live content upload API requires a bearer token; not available in this automation run
2. **AEM Code Sync GitHub App** — app must be configured by the repo owner to include the `eds-migration` repository

Once these are resolved, the 19-step **Activation Checklist** at the end of this document takes the site from "ready to go live" to "live."

---

## Phase-by-Phase Summary

### Phase 1 — Site Crawl & Discovery

**Status:** ✅ Complete  
**Retries:** 0  
**Fallbacks:** None  

Crawled the complete almacgroup.com sitemap tree (11 sub-site sitemaps, WordPress Multisite). Produced `manifest.json` with 3,615 pages classified into 27 archetypes. Also captured a 32-page `source-bundle` with rendered desktop/mobile screenshots, header/footer chrome, and cleaned HTML for migration reference.

**Key findings:**
- 3 archetypes dominate volume: events (928), knowledge-library (723), news-post (679) — together 64% of total pages
- WordPress Multisite creates 11 distinct sub-sites, each with its own URL prefix
- Navigation: mega-menu with 271 unique internal paths across 6 top-level sections
- Site uses HubSpot forms on ~3,500 pages (site-wide contact CTA pattern)

### Phase 2 — Content Analysis & Blueprint

**Status:** ✅ Complete  
**Retries:** 0  
**Fallbacks:** None

Produced `blueprint.json` defining:
- 18-block EDS palette (14 from Block Collection, 4 custom)
- 3 eliminated blocks (replaced with compositions or section styles)
- 5 section styles
- 6 query index sheets
- Content models for all 28 archetypes
- Risk register with 7 items

**Analyst verdict:** PASS

### Phase 3 — Block Development

**Status:** ✅ Complete  
**Retries:** 1 (lint fix — added `.eslintrc.js` and `.eslintignore`)  
**Fallbacks:** None

All 19 blocks scaffolded on `main` branch. ESLint (airbnb-base) passes with zero errors. AEM Code Sync code bus confirmed all 49 EDS-relevant files synced (code.status=200 for individual files).

**Note:** 19 blocks are present vs 18 in the blueprint. `icon-grid` was listed as "eliminated" in the blueprint (should be a `cards (icon)` variant) but was scaffolded as a standalone block. Both approaches work; the standalone block adds minor palette redundancy.

**Verifier verdict:** PASS (with low-severity notes)

### Phase 4 — Content Migration (Pilot)

**Status:** ✅ Staged; ⚠️ Not uploaded (no EDS_TOKEN)  
**Retries:** 0  
**Fallbacks:** Content staged locally; da.live upload skipped

16 pilot HTML pages covering 15 archetypes migrated to EDS table format and staged in `.eds-migration/state/content-staging/`. All use valid EDS block syntax, section dividers, and metadata tables.

**Pilot verifier verdict:** FAIL (infrastructure) — HTML quality assessed as GOOD independently

### Phase 5 — Configuration

**Status:** ✅ Complete (config files ready); ⚠️ Not uploaded (no EDS_TOKEN)  
**Retries:** 0  
**Fallbacks:** All config staged in `.eds-migration/state/config/`

All site-level configuration files generated and committed to the migration-state branch:
- `redirects.html` — 57 redirect rules
- `metadata.html` — 3,607 rows (full site metadata)
- `nav.html` — 296 links, 99.6% source coverage
- `footer.html` — 20 links, 100% source coverage
- `helix-query.yaml` — 4 query indices
- `helix-sitemap.yaml` — 4 sitemaps
- `robots.txt` — correct exclusions

**Config verifier verdict:** FAIL (infrastructure) — content quality PASS on all non-upload checks

### Phase 6 — Integration QA

**Status:** ✅ Static checks complete; 🔄 Live checks deferred  
**Retries:** 0

QA checks completed: code quality (PASS), config validity (PASS), redirect completeness (PASS), metadata coverage (PASS), nav coverage (PASS), footer coverage (PASS), HTML block format (PASS with warnings), link quality (3 broken WP post-ID links found), accessibility (4 heading hierarchy issues found).

Deferred: Lighthouse, visual regression, chrome check, live redirect verification.

---

## Architecture Overview

### Block Palette

| # | Block | Source | Variants | Volume |
|---|-------|--------|----------|--------|
| 1 | `hero` | Block Collection | default, carousel | 16 archetypes |
| 2 | `cards` | Block Collection | default, news, resource, event, related, icon | 14 archetypes |
| 3 | `columns` | Block Collection | default, video, sidebar | 7 archetypes |
| 4 | `breadcrumbs` | Block Collection | auto-blocked | 22 archetypes |
| 5 | `fragment` | Block Collection | — | all pages |
| 6 | `carousel` | Block Collection | — | 2 archetypes |
| 7 | `video` | Block Collection | inline, modal | 5 archetypes |
| 8 | `embed` | Block Collection | autoblock | 4 archetypes |
| 9 | `quote` | Block Collection | — | 3 archetypes |
| 10 | `accordion` | Block Collection | — | 3 archetypes |
| 11 | `tabs` | Block Collection | — | 2 archetypes |
| 12 | `table` | Block Collection | — | 2 archetypes |
| 13 | `modal` | Block Collection | autoblock | 4 archetypes |
| 14 | `search` | Block Collection | — | site-wide header |
| 15 | `hubspot-form` | **Custom** | default, gated-content, product-inquiry | ~3,500 pages |
| 16 | `stats` | **Custom** | — | homepage |
| 17 | `profile` | **Custom** | default, expert | 4 archetypes (141 pages) |
| 18 | `content-filter` | **Custom** | — | 4 archetypes (2,330 pages) |
| 19 | `icon-grid` | **Custom** | — | ~10 pages (see note below) |

**Note on icon-grid:** Blueprint specified eliminating this as a standalone block in favour of `cards (icon)` variant. Both are present. Recommend deprecating `icon-grid` in favour of `cards (icon)`.

### Eliminated Blocks (Palette Minimisation)

| Original Concept | Decision | Rationale |
|-----------------|----------|-----------|
| contact-locations | Compose from `columns` + `cards` + `fragment` | Only 1 page (contact). Composition over custom block. |
| icon-grid (standalone) | `cards (icon)` variant | ~10 pages. CSS-only variant keeps palette minimal. |
| sidebar | Section style `style: sidebar` | CSS Grid layout, not a content block. |

### Section Styles

| Style | Description | Usage |
|-------|-------------|-------|
| `sidebar` | CSS Grid 2fr/1fr — content left, nav right | 8 archetypes |
| `full-width-image` | Background cover with text overlay | 3 archetypes |
| `cta-band` | Accent colour background, centred CTA | 3 archetypes |
| `dark` | Dark background, light text | 3 archetypes |
| `grey` | Light grey `#f5f5f5` alternating sections | 4 archetypes |

### Content Models

**HubSpot form as Fragment (key decision)**  
The 8-field HubSpot contact CTA appears on ~3,500 of 3,615 pages. Authored once at `/fragments/hubspot-cta`. Each page includes: `Fragment | /fragments/hubspot-cta`. Changes propagate automatically. Avoids 3,500× content duplication.

**Breadcrumbs as auto-block (key decision)**  
Breadcrumbs appear on 22/27 archetypes. Auto-blocked via `scripts.js` reading URL hierarchy — authors never need to add a breadcrumbs table. URL hierarchy maps directly to navigation path for all archetypes.

**Content-filter for listing pages**  
Events (928), knowledge-library (723), and news-post (679) use a single `content-filter` block reading from query-index sheets. Each listing page authors one block row with the relevant index URL and filter fields. Block Party Content Filter Hub was used as architecture reference.

### Query Index Sheets

| Index | Path | Content | Key Fields |
|-------|------|---------|------------|
| site | `/query-index.json` | All pages | title, description, image, lastModified |
| events | `/events-index.json` | Events only | eventDate, eventLocation, eventType |
| news | `/news-index.json` | News only | publishDate, division, category |
| knowledge | `/knowledge-index.json` | Knowledge only | contentType, topic, expert |

### Navigation Architecture

The Almac mega-menu (271 unique paths, 6 top-level sections) is authored in a single `/nav` document using a nested unordered list structure. EDS's default `nav` decoration pattern handles the mega-menu rendering via CSS. Social media links and search are included in the nav document.

---

## Known Issues

### Deferred (Infrastructure)
| Issue | Impact | Resolution |
|-------|--------|-----------|
| EDS_TOKEN not provided | All 16 pilot pages not on da.live; preview returns 404 | Provide EDS_TOKEN; run activation checklist |
| GitHub App not configured | CDN returns "Missing configuration" | Owner adds repo to AEM Code Sync app |
| Lighthouse not run | Performance scores unknown | Run after activation |
| Visual regression not run | Pixel-level fidelity unknown | Run after activation against source-bundle screenshots |
| Live redirect verification | 301s unverified | Run after CDN activation |

### Content Issues (Fixable Before Activation)
| Issue | Pages Affected | Severity |
|-------|---------------|----------|
| Multiple H1 elements | diagnostics.html (9×H1), careers.html (2×H1) | High |
| Missing H1 | knowledge/experts/abi-pesun.html, knowledge/experts/doctor-rodney-brown.html | Medium |
| WordPress post-ID links (?p=) | diagnostics.html (3 links) | Medium |
| Block name case inconsistency | 3 issues across pilot pages | Low |
| 'Product Specifications' block not in palette | api-chemical-product page | Low |

### Scope Gaps (Not Regressions)
| Item | Notes |
|------|-------|
| 13 archetypes without pilot HTML | analytical, api-chemical, bd-team-profile, blog-category, careers-resource, client-portal, clinical-technologies, commercial-services, discovery, events, knowledge, news, pharma-drug |
| 3,591 non-pilot pages not migrated | Requires EDS_TOKEN and batch migration run |
| careers-resource pages (37) | Stubbed as redirects to /careers — no EDS content equivalent for gated pages |
| WordPress 404s in source sitemap | Some source URLs return 404 — flagged in manifest; not migrated |

---

## Maintenance Guide

### Adding New Pages

1. Author content at `https://da.live/edit#/manuel-vara/eds-migration/{path}`
2. Use block table format: `<table><tr><th>Block Name</th></tr><tr><td>content</td></tr></table>`
3. Add metadata table at page bottom with Title, Description, Template
4. Preview: `POST https://admin.hlx.page/preview/manuel-vara/eds-migration/main/{path}`
5. Publish: `POST https://admin.hlx.page/live/manuel-vara/eds-migration/main/{path}`

### Modifying Blocks

All block code lives at `https://github.com/manuel-vara/eds-migration/tree/main/blocks/`. Each block has a `.js` and `.css` file. Changes push automatically to the CDN via AEM Code Sync (once the GitHub App is configured).

**Block authoring pattern:**
```js
export default function decorate(block) {
  const rows = [...block.children];
  // process rows...
}
```

### Adding Redirects

Edit `/redirects` in da.live (HTML table with Source | Destination columns) and publish. CDN picks up changes within minutes.

### Updating Metadata

Edit `/metadata` in da.live (HTML table with URL | Title | Description | Image | Template columns) and publish. Affects all pages matching the URL pattern.

### Adding Query Index Fields

Edit `helix-query.yaml` on `main` branch and push. New fields will appear in the next index rebuild.

### Content Filter Pages (Events, News, Knowledge)

These listing pages auto-populate from the query index. To modify the filter fields or display, update `blocks/content-filter/content-filter.js` on `main`.

---

## Links

| Resource | URL |
|----------|-----|
| Preview (staging) | https://main--eds-migration--manuel-vara.aem.page/ |
| Live CDN | https://main--eds-migration--manuel-vara.aem.live/ |
| DA.live editor | https://da.live/edit#/manuel-vara/eds-migration |
| GitHub repository | https://github.com/manuel-vara/eds-migration |
| QA report | `.eds-migration/state/qa-report.json` on `migration-state/1b3ddcfa` |
| Phase docs | `.eds-migration/state/docs/` on `migration-state/1b3ddcfa` |
| Source bundle | `.eds-migration/state/source-bundle/` on `migration-state/1b3ddcfa` |

---

## Activation Checklist

Complete these steps in order to go live:

### Prerequisites
- [ ] **Repo owner** visits https://github.com/apps/aem-code-sync/installations and adds `eds-migration` to the app's repository access list
- [ ] **Obtain EDS_TOKEN** — da.live API bearer token for `manuel-vara` account (contact da.live support or check your da.live account settings)

### Content Upload
```bash
EDS_TOKEN="<your-token>"
BASE="https://admin.da.live/source/manuel-vara/eds-migration"
STATE=".eds-migration/state"

# Upload config
curl -X POST "$BASE/nav" -H "Authorization: Bearer $EDS_TOKEN" -H "Content-Type: text/html" --data-binary "@$STATE/config/nav.html"
curl -X POST "$BASE/footer" -H "Authorization: Bearer $EDS_TOKEN" -H "Content-Type: text/html" --data-binary "@$STATE/config/footer.html"
curl -X POST "$BASE/redirects" -H "Authorization: Bearer $EDS_TOKEN" -H "Content-Type: text/html" --data-binary "@$STATE/config/redirects.html"
curl -X POST "$BASE/metadata" -H "Authorization: Bearer $EDS_TOKEN" -H "Content-Type: text/html" --data-binary "@$STATE/config/metadata.html"

# Upload pilot pages (repeat for each page in content-staging/)
curl -X POST "$BASE/" -H "Authorization: Bearer $EDS_TOKEN" -H "Content-Type: text/html" --data-binary "@$STATE/content-staging/index.html"
# ... (see content-staging/ for full list)
```

### Activation
- [ ] Preview nav: `POST https://admin.hlx.page/preview/manuel-vara/eds-migration/main/nav`
- [ ] Preview footer: `POST https://admin.hlx.page/preview/manuel-vara/eds-migration/main/footer`
- [ ] Preview homepage: `POST https://admin.hlx.page/preview/manuel-vara/eds-migration/main/`
- [ ] Verify https://main--eds-migration--manuel-vara.aem.page/ renders with correct nav and footer

### Content Fixes (Before Publishing)
- [ ] Fix `diagnostics.html` — demote 9 service-section H1s to H2/H3
- [ ] Fix `careers.html` — demote duplicate H1 to H2
- [ ] Fix `knowledge/experts/abi-pesun.html` and `doctor-rodney-brown.html` — promote expert name to H1
- [ ] Fix 3 WordPress post-ID links in `diagnostics.html` — resolve `?p=` to canonical URLs
- [ ] Normalise block name casing — standardise `Cards (related)`, `HubSpot Form (gated-content)`, `Profile (expert)`

### Validation
- [ ] Run Lighthouse on preview URL — target 100/100/100/100
- [ ] Run visual regression against `source-bundle/pages/` screenshots
- [ ] Verify redirect 301s from CDN for all 57 redirect rules
- [ ] Verify nav/footer chrome matches `source-bundle/chrome/` screenshots

### Full Migration
- [ ] Generate pilot HTML for 13 remaining archetypes
- [ ] Batch-migrate all 3,591 non-pilot pages
- [ ] Publish all pages to live CDN

### DNS Cutover
- [ ] Configure custom domain `almacgroup.com` to point to EDS CDN (contact da.live support for CNAME/A record instructions)
- [ ] Update `robots.txt` Sitemap URLs to use `almacgroup.com` instead of `aem.live` domain
- [ ] Verify SSL certificate provisioned for custom domain

---

*Report generated by IntegrationQA-1b3ddcfa on 2026-05-12. QA details in `.eds-migration/state/qa-report.json` and `.eds-migration/state/docs/phase6-qa-summary.md` on branch `migration-state/1b3ddcfa`.*
