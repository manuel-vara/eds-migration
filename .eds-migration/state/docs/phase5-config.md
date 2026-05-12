# Phase 5 — Configuration

Generated: 2026-05-12

## Overview

Phase 5 generates all site-level configuration for the EDS migration of `https://www.almacgroup.com` (3,615 pages, 27 archetypes) to `manuel-vara/eds-migration`.

---

## Redirects

**File:** `.eds-migration/state/config/redirects.html`
**Format:** HTML table with `Source` / `Destination` columns — upload to `POST /source/{org}/{repo}/redirects`
**Total redirects:** 55

### Categories applied

| Category | Count | Rationale |
|---|---|---|
| Known 301 redirects from status files | 4 | `/biotech` → `/events/biotech-japan-2018`, `/pharma-services` → `/pharma-services-boston-workshop-april-2026` (both with trailing slash variants) |
| `careers-resource` → `/careers` | 37 | These 37 gated "day in the life" pages have no EDS equivalent; redirect to the careers hub to avoid 404s |
| `client-portal` → `/client-login` | 1 | `/client-login/almac-returns-waybill-generator/` requires auth — redirect to login page |
| `blog-category` → `/news` | 1 | `/category/uncategorized/` WordPress artefact → news hub |
| WP alias normalisation | 4 | `/about-us` → `/about`, `/our-locations` → `/about`, `?page_id=2251` → diagnostics page, `almac_journies/*` → `careers/stories/*` |
| Trailing slash variants | included above | EDS does not auto-append trailing slashes |

### Rules applied
- No redirect loops: all destinations are live EDS paths or external URLs
- No redirect chains: sources go directly to their final destination
- careers-resource pages redirect to `/careers` rather than `/careers/resources/` (no EDS sub-path exists for gated content)

---

## Bulk Metadata

**File:** `.eds-migration/state/config/metadata.html`
**Format:** HTML table — upload to `POST /source/{org}/{repo}/metadata`
**Total rows:** 3,607 (deduplicated by EDS path)

### Columns
| Column | Source | Notes |
|---|---|---|
| `URL` | manifest.json page paths | EDS-relative paths (e.g. `/about`, `/events/biotech-japan-2018`) |
| `Title` | `title` field, " - Almac" suffix stripped | Clean titles for EDS metadata |
| `Description` | `meta_description` field | Direct from manifest crawl |
| `Image` | `og:image` from sample-scrape.json | Available for ~32 scraped pages; empty for remainder (EDS will use first image found) |
| `Template` | Derived from archetype | Maps archetypes to EDS template names: `service`, `news-post`, `events`, `knowledge-library`, `profile`, `careers`, etc. |

### Archetype → Template mapping
- `diagnostics`, `clinical-services`, `clinical-technologies`, `commercial-services`, `api-chemical`, `pharma-drug`, `analytical`, `discovery` → `service`
- `api-chemical-product` → `product`
- `news-post`, `award` → `news-post`
- `knowledge-expert`, `bd-team-profile`, `expert-profile` → `profile`
- `careers-story` → `careers-story`
- `careers-resource` → `careers-resource`
- `blog-category` → `news`
- `client-portal` → `client-portal`

---

## Navigation (`/nav`)

**File:** `.eds-migration/state/config/nav.html`
**Source:** `source-bundle/chrome/header.html` + `header.links.json`

### Structure
1. **Logo** — `<p><a href="/"><img src="...logo-core.svg" alt="Almac Group"></a></p>`
2. **Main mega-menu** (`<ul>`) — 8 top-level business unit sections, each with 2–3 levels of nested `<ul>` submenus:
   - Diagnostic Services (35 sub-links, 3 levels)
   - API Services & Chemical Development (28 sub-links, 3 levels)
   - Pharmaceutical Development (15 sub-links, 2 levels)
   - Analytical & Solid State Services (18 sub-links, 2 levels)
   - Clinical Services (22 sub-links, 3 levels)
   - Clinical Technologies (18 sub-links, 2 levels)
   - Commercial Services (12 sub-links, 2 levels)
   - Discovery (4 sub-links, 1 level)
3. **Utility nav** (`<ul>`) — About, Sustainability, Careers, News, Events, Knowledge Centre, Contact us, Client login

**Link coverage:** ~148 unique nav links vs. 705 raw header links (705 includes heavy duplication — parent links repeated as first child). Coverage of unique visible hierarchy is ~80%.

**Decisions:**
- Language selector (JP/KR/US) omitted — not an EDS nav concern; handled by metadata/redirect layer
- Search icon omitted — EDS search block handles this via scripts.js
- WP query strings (`?__hstc=...`) stripped from all HubSpot tracking URLs
- Arran Chemical Company external link omitted (external sub-brand)

---

## Footer (`/footer`)

**File:** `.eds-migration/state/config/footer.html`
**Source:** `source-bundle/chrome/footer.html` + `footer.links.json`

### Structure
1. **Logo** — same as nav
2. **HubSpot Contact Form** (`div.hubspot-form`) — EDS `hubspot-form` block table with Portal ID `742105` and Form ID `61f11908-1f5a-47c0-b358-d1e2c3d076b2` (extracted from the live footer HTML). The source footer renders a full HS form in column 1; in EDS this becomes a `hubspot-form` block so the form loads via the lazy-loaded HS API.
3. **Quick Links** (h3 + `<ul>`) — 9 links: Careers, About Us, Our Locations, Latest News, Knowledge Centre, Almac Discovery, Almac Diagnostic Services, Privacy Policy, Galen Pharmaceuticals
4. **Get in Touch** (h3 + `<ul>`) — 3 regional phone numbers (European, North American, Asia Pacific)
5. **Social Links** (h3 + `<ul>`) — LinkedIn, YouTube, Vimeo
6. **Legal bar** (`<p>`) — copyright, Company Information, T&C, Privacy & Cookie Policy, Modern Slavery Statement links

**Footer link coverage:** 17 out of 18 footer links from `footer.links.json` (100% minus 1 HubSpot-tracked Galen URL, which is replaced with the clean `galen-pharma.com` URL).

---

## Indexing — `helix-query.yaml`

**Location:** `main` branch, `/helix-query.yaml`
**Pushed:** Yes, commit `config: add helix-sitemap.yaml, robots.txt; expand...`

### Changes from original
The original had a single `site` index with 13 properties. Added 3 **dedicated sub-indices** for the `content-filter` block:

| Index | Target JSON | Path pattern | Properties |
|---|---|---|---|
| `site` (existing) | `/query-index.json` | `/**` | 14 properties (all metadata) |
| `events` (new) | `/events-index.json` | `/events/**` | title, description, image, eventDate, eventLocation, eventType, division |
| `news` (new) | `/news-index.json` | `/news/**` | title, description, image, publishDate, division, category |
| `knowledge` (new) | `/knowledge-index.json` | `/knowledge/**` | title, description, image, contentType, topic, expert, division, publishDate |

**Rationale:** The `content-filter` block (used by events hub, news hub, knowledge centre) fetches from a dedicated sheet. Having path-scoped indices keeps the JSON payload small and fast. The 928 events + 679 news + 723 knowledge-library pages would otherwise bloat the main `query-index.json`.

---

## Sitemap — `helix-sitemap.yaml`

**Location:** `main` branch, `/helix-sitemap.yaml`
**Pushed:** Yes (same commit)

### Configuration
| Sitemap | Target | Coverage |
|---|---|---|
| `default` | `/sitemap.xml` | All `/**` except excluded paths |
| `events` | `/sitemap-events.xml` | `/events/**` |
| `news` | `/sitemap-news.xml` | `/news/**` |
| `knowledge` | `/sitemap-knowledge.xml` | `/knowledge/**` |

### Excluded from main sitemap
- `/client-login/**` — auth-gated portal
- `/careers/resources/**` — gated career resources (37 pages)
- `/category/**` — WordPress blog category artefacts
- `/drafts/**` — unpublished content
- `/nav`, `/footer`, `/fragments/**` — chrome/fragment documents (not indexable content)

**Total indexable pages estimate:** ~3,530 out of 3,615 (excludes 85 gated/system pages).

---

## `robots.txt`

**Location:** `main` branch, `/robots.txt`
**Pushed:** Yes (same commit)

```
User-agent: *
Allow: /

Disallow: /client-login/      # Auth-gated portal
Disallow: /careers/resources/ # Gated career content
Disallow: /category/          # WP artefacts
Disallow: /drafts/
Disallow: /fragments/
Disallow: /?s=                # WP search queries

Sitemap: /sitemap.xml (+ events, news, knowledge)
```

**Rationale:** All migrated content paths are open to crawlers. The four disallowed path groups are either auth-gated, transitional, or internal chrome documents that should never be indexed.

---

## Upload Status

EDS_TOKEN was not available in this run. All HTML config files are committed to `.eds-migration/state/config/` on the `migration-state/1b3ddcfa` branch. The following da.live uploads remain pending:

| Endpoint | File | Status |
|---|---|---|
| `POST /source/manuel-vara/eds-migration/redirects` | `config/redirects.html` | Pending — needs EDS_TOKEN |
| `POST /source/manuel-vara/eds-migration/metadata` | `config/metadata.html` | Pending — needs EDS_TOKEN |
| `POST /source/manuel-vara/eds-migration/nav` | `config/nav.html` | Pending — needs EDS_TOKEN |
| `POST /source/manuel-vara/eds-migration/footer` | `config/footer.html` | Pending — needs EDS_TOKEN |

The nav and footer in `.eds-migration/state/content-staging/` (previously staged by phase 4) have been superseded by the richer versions in `config/`.

Main branch files (helix-query.yaml, helix-sitemap.yaml, robots.txt) were successfully pushed.
