# Phase 1 — Discovery & Crawl

**Site**: https://www.almacgroup.com  
**Crawled**: See `manifest.json` → `crawledAt`  
**Total pages found**: 3,605  
**Sitemap sources**: 11 sub-site sitemap indexes (WordPress Multisite)

---

## Page Count by Archetype

| Archetype | Count | Description |
|-----------|------:|-------------|
| events | 928 | Conference/event listings and archive pages |
| knowledge-library | 721 | Whitepapers, publications, scientific resources |
| news-post | 677 | News articles across all business units |
| clinical-services | 210 | Clinical supply chain service pages |
| diagnostics | 175 | Diagnostic services + resource/type sub-pages |
| careers | 157 | Job listings, careers stories, resources |
| landing | 99 | Standalone landing pages (COVID responses, campaigns) |
| knowledge-expert | 96 | Expert profile pages in Knowledge Centre |
| clinical-technologies | 80 | Clinical technology service and article pages |
| api-chemical | 77 | API/chemical development service pages |
| api-chemical-product | 70 | Biocatalyst products and enzyme kits |
| award | 50 | Award recognition pages |
| commercial-services | 42 | Commercial/pharma manufacturing service pages |
| analytical | 39 | Analytical & solid-state service pages |
| careers-story | 39 | "Almac Journeys" employee stories |
| careers-resource | 36 | Careers resource articles |
| bd-team-profile | 32 | Business development team profiles |
| pharma-drug | 24 | Pharmaceutical drug product development pages |
| discovery | 20 | Discovery research/services pages |
| about | 15 | Company/corporate information pages |
| expert-profile | 12 | Expert profile pages (older URL pattern) |
| contact | 1 | Contact us page |
| homepage | 1 | Site homepage |
| knowledge | 1 | Knowledge Centre hub |
| news | 1 | News listing hub |
| blog-category | 1 | Blog category archive |
| client-portal | 1 | Client login portal |

**Total**: 3,605

---

## Archetype Rationale

- **events**: Separated from content pages because they follow a strict listing/archive pattern with date/location metadata and are likely candidates for structured data treatment in EDS.
- **knowledge-library**: High-value scientific content library with 721 items. Mixed types: PDFs, articles, whitepapers. Many have internationalised slugs.
- **news-post**: Individual news articles — standard blog-post archetype. Spans all business units.
- **business unit pages** (clinical-services, diagnostics, api-chemical, etc.): Each maps to a Almac sub-brand/business unit with its own WordPress multisite install. Treated as separate archetypes to reflect their distinct design and content patterns.
- **landing**: One-off campaign/response pages at root level. Short lifecycle content.
- **knowledge-expert / expert-profile**: Two URL patterns for expert profiles exist (`/knowledge/experts/` and `/expert/`). Separate archetypes to flag the older pattern for redirect mapping.
- **bd-team-profile**: Business development team member profiles — similar to expert profiles but different URL pattern and likely different template.
- **careers-story / careers-resource**: Sub-archetypes within the careers section with distinct templates.

---

## Navigation Structure

### Header
The site uses a **mega-menu navigation** rendered by JavaScript. Raw element count: 705 links in the header (after hydration). The main top-level items are:

- Services (with sub-menus per business unit)
- About
- Careers
- Contact Us
- Knowledge Centre

See `source-bundle/chrome/header.links.json` for full deduped link list.

### Footer
15 unique footer links including:
- Privacy Policy
- Cookie Policy
- Terms & Conditions
- Compliance Statement
- Social media links (LinkedIn, Twitter/X, YouTube)

See `source-bundle/chrome/footer.links.json`.

---

## Site Assets

| Asset | Location |
|-------|----------|
| Favicon | `/wp-content/themes/almac-theme/img/favicon.ico` |
| Fonts | Google Fonts + custom (detected in rendered HTML — see page index.html files) |
| Global images | Almac logo in header, background images per business unit |

---

## Crawl Issues

1. **SSL certificate**: Headless Chrome required `--ignore-certificate-errors` — the site's TLS cert doesn't validate against standard CA roots in this environment.
2. **`clinical-services/news/` timeout**: First load attempt timed out (30 s on `domcontentloaded`). The fallback news-post example was captured successfully from a different URL.
3. **`knowledge-library` 404**: One priority URL from the original sample (`/knowledge/library/a-phase-ii-study-...`) returned a 404. The sitemap contained stale/removed URLs — the library index (`/knowledge/library/`) was captured correctly instead.
4. **Internationalised URLs**: ~200 URLs use percent-encoded CJK characters. These are valid pages (localised content) but may need special handling in slug generation.
5. **Scale**: 3,605 URLs is too large for full-page screenshots. The 25-page source-truth bundle covers all major archetypes with 2 viewports each (50 total captures).

---

## Source-of-Truth Bundle

**Location**: `.eds-migration/state/source-bundle/`

| Coverage | Count |
|----------|------:|
| Pages with full HTML + screenshots | 25 |
| Desktop screenshots (1440×900) | 25 |
| Mobile screenshots (390×844) | 25 |
| Chrome captures (header + footer) | 1 set |
| Archetypes with ≥1 sample | 21 of 27 |

See `source-bundle/README.md` for render strategy, quirks, and partial capture notes.

---

## Files Written

| File | Description |
|------|-------------|
| `.eds-migration/state/manifest.json` | Full page inventory (3,605 pages) with archetypes, navigation, assets |
| `.eds-migration/state/source-bundle/pages/*/index.html` | Rendered DOM per captured page |
| `.eds-migration/state/source-bundle/pages/*/desktop.png` | Full-page desktop screenshot |
| `.eds-migration/state/source-bundle/pages/*/mobile.png` | Full-page mobile screenshot |
| `.eds-migration/state/source-bundle/pages/*/meta.json` | URL, title, archetype, capture metadata |
| `.eds-migration/state/source-bundle/chrome/header.html` | Rendered header outerHTML |
| `.eds-migration/state/source-bundle/chrome/footer.html` | Rendered footer outerHTML |
| `.eds-migration/state/source-bundle/chrome/header.links.json` | Header nav links |
| `.eds-migration/state/source-bundle/chrome/footer.links.json` | Footer links |
| `.eds-migration/state/source-bundle/chrome/header-desktop.png` | Header screenshot |
| `.eds-migration/state/source-bundle/chrome/footer-desktop.png` | Footer screenshot |
| `.eds-migration/state/source-bundle/README.md` | Bundle documentation |
