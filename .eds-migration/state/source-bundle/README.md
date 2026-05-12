# Source-of-Truth Bundle — almacgroup.com

## Overview

This bundle contains fully-rendered captures of representative pages from https://www.almacgroup.com,
taken on the crawl date recorded in `manifest.json`. Each page was captured using Playwright
(headless Chromium) after full JavaScript hydration and overlay dismissal.

## Render / Settle Strategy

- **Browser**: Playwright headless Chromium with `--ignore-certificate-errors` (site has a cert
  authority validation issue in automated environments)
- **Wait strategy**: `domcontentloaded` → `networkidle` (up to 15 s) → content stability check
  (body.innerText length measured twice 500 ms apart; accepted when non-zero and stable within 50 chars)
- **Overlay dismissal**: Attempted `#onetrust-accept-btn-handler` and common cookie-banner button
  selectors before final screenshot. The site uses OneTrust cookie consent.
- **Retries**: Up to 3 attempts per URL before recording failure.

## Viewports

| Label   | Dimensions |
|---------|------------|
| Desktop | 1440 × 900 |
| Mobile  | 390 × 844  |

## Pages Captured (25 total, 50 viewports)

| Slug | Archetype | URL |
|------|-----------|-----|
| homepage | homepage | https://www.almacgroup.com/ |
| about | about | https://www.almacgroup.com/about/ |
| contact-us | contact | https://www.almacgroup.com/contact-us/ |
| careers | careers | https://www.almacgroup.com/careers/ |
| careers-careers | job-listing | https://www.almacgroup.com/careers/careers/ |
| careers-news-almac-recognised-at-the-nus-2023-awards | news-post | https://www.almacgroup.com/careers/news/almac-recognised-at-the-nus-2023-awards/ |
| discovery | discovery | https://www.almacgroup.com/discovery/ |
| diagnostics | diagnostics | https://www.almacgroup.com/diagnostics/ |
| api-chemical-development | api-chemical | https://www.almacgroup.com/api-chemical-development/ |
| pharmaceutical-drug-product-development | pharma-drug | https://www.almacgroup.com/pharmaceutical-drug-product-development/ |
| analytical-solid-state | analytical | https://www.almacgroup.com/analytical-solid-state/ |
| clinical-services | clinical-services | https://www.almacgroup.com/clinical-services/ |
| clinical-technologies | clinical-technologies | https://www.almacgroup.com/clinical-technologies/ |
| commercial-services | commercial-services | https://www.almacgroup.com/commercial-services/ |
| knowledge | knowledge | https://www.almacgroup.com/knowledge/ |
| knowledge-library | knowledge-library | https://www.almacgroup.com/knowledge/library/ |
| knowledge-library-a-phase-ii-... | knowledge-library (404) | https://www.almacgroup.com/knowledge/library/a-phase-ii-study-... |
| knowledge-experts-abi-pesun | knowledge-expert | https://www.almacgroup.com/knowledge/experts/abi-pesun/ |
| knowledge-experts-adrian-collins | knowledge-expert | https://www.almacgroup.com/knowledge/experts/adrian-collins/ |
| events | events | https://www.almacgroup.com/events/ |
| news | news | https://www.almacgroup.com/news/ |
| business-development-team-aidan-kelly | bd-team-profile | https://www.almacgroup.com/business-development-team/aidan-kelly/ |
| almac-group-virtual-tour | landing | https://www.almacgroup.com/almac-group-virtual-tour/ |
| almac-clinical-technologies-response-... | landing | https://www.almacgroup.com/almac-clinical-technologies-response-to-coronavirus-covid-19-outbreak/ |
| clinical-services-news | news-section | https://www.almacgroup.com/clinical-services/news/ (partial capture — timed out on first attempt) |

## Chrome

`chrome/` contains:
- `header.html` — raw outerHTML of `<header>` element from homepage after render
- `footer.html` — raw outerHTML of `<footer>` element from homepage after render
- `header.links.json` — all `<a>` elements found in header (text + href)
- `footer.links.json` — all `<a>` elements found in footer (text + href)
- `header-desktop.png` — cropped screenshot of rendered header
- `footer-desktop.png` — cropped screenshot of rendered footer

## Partial Captures

| Page | Symptom |
|------|---------|
| `clinical-services-news` | Timed out on both desktop and mobile on first attempt (30 s timeout exceeded on `domcontentloaded`). Fallback directory exists but screenshots may be absent. |
| `knowledge-library/a-phase-ii-study-...` | Resolved to 404 ("Page not found - Almac") — the URL was in the sitemap but the content has been removed. |

## Site-Specific Quirks

1. **SSL certificate**: The site's certificate fails standard CA validation in headless Chrome without `--ignore-certificate-errors`.
2. **OneTrust cookie banner**: Present on first visit. Dismissed by clicking `#onetrust-accept-btn-handler` before screenshots.
3. **Large header nav**: 705 raw `<a>` tags in the header — the nav is a mega-menu with many sub-links. Deduped to ~60 meaningful links in manifest.
4. **Multi-site structure**: The domain hosts 11 distinct business-unit "sub-sites" (clinical-services, diagnostics, api-chemical-development, etc.), each with their own WordPress multisite install and separate sitemap indexes.
5. **Internationalised URLs**: Some pages have UTF-8 encoded slugs (Japanese/Chinese characters), particularly in the knowledge library and clinical-services sections. These are in-scope but lower priority.
6. **Events section is largest**: 928 pages — these are event listing/archive pages, not unique content.
