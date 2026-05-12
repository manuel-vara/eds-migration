# Phase 3 — Block Development Summary

## Overview
18 blocks + EDS boilerplate scaffolded on `main` branch of `manuel-vara/eds-migration`. All code passes `npm run lint` (eslint + stylelint) with zero errors.

### Retry 1 Fixes (2026-05-12)
- **Added `.eslintrc.js`** — standard AEM boilerplate config: `airbnb-base`, `@babel/eslint-parser`, `no-param-reassign` with `props: false` (standard for DOM manipulation)
- **Added `.eslintignore`** — excludes `eds_migrate/` (migration tooling), `.claude/` from lint scope
- **Confirmed AEM Code Sync** — bot installed (installationId: 34179329), code bus synced (all files at status 200)
- **DA content pending** — preview pages 404 until EDS_TOKEN is provided for content authoring on da.live

## Blocks

### Critical Priority

| Block | Purpose | Content Model | Variants | Source |
|-------|---------|---------------|----------|--------|
| **hero** | Full-width banner with background image, heading, CTA | Row: col1=picture, col2=heading+text+CTA | — | Custom (adapted from BC) |
| **cards** | Grid of content cards with image, heading, description | Rows of: col1=picture, col2=heading+text+link | default, news, event, resource, related, icon | Custom (adapted from BC) |
| **columns** | Media-text split layout | Row: col1=picture/content, col2=content | video | Adapted from BC |
| **carousel** | Rotating slide display | Multiple rows; each: col1=image, col2=heading+text+CTA | — | Adapted from BC |
| **hubspot-form** | Loads HubSpot form by portal/form ID | Config table: portal-id, form-id | — | Custom |
| **content-filter** | Filterable listings (events, news, resources) | Config table: source path + filter field names | — | Custom |
| **breadcrumbs** | Auto-generated from URL path | Auto-block (empty table) | — | Custom |

### High Priority

| Block | Purpose | Content Model | Variants | Source |
|-------|---------|---------------|----------|--------|
| **video** | Video embed (YouTube, Vimeo, MP4) with placeholder | Row: col1=placeholder picture, col2=video URL link | autoplay | Adapted from BC |
| **embed** | Generic embed (YouTube, Vimeo, iframe) | Row: optional picture + link URL | — | Adapted from BC |
| **stats** | Animated number counters | Rows: col1=number+suffix, col2=label text | — | Custom |
| **profile** | Expert profile with photo and bio | Row: col1=photo, col2=name+title+credentials | expert, bd-team | Custom |
| **fragment** | Load shared content fragments | Single cell with path/link to fragment | — | From BC |
| **quote** | Testimonial/quote display | Row1=quotation text, Row2=attribution | — | Adapted from BC |

### Medium Priority

| Block | Purpose | Content Model | Variants | Source |
|-------|---------|---------------|----------|--------|
| **accordion** | Expandable details/summary sections | Rows: col1=label, col2=body content | — | Adapted from BC |
| **tabs** | Tabbed content panels | Rows: col1=tab label, col2=panel content | — | Adapted from BC |
| **table** | Responsive data table | Standard table rows/columns | striped, no-header | Adapted from BC |
| **modal** | Modal/lightbox overlay | Triggered by fragment paths; programmatic API | — | Adapted from BC |

### Low Priority

| Block | Purpose | Content Model | Variants | Source |
|-------|---------|---------------|----------|--------|
| **search** | Site search via query-index.json | Single cell with optional index URL | — | Adapted from BC |
| **icon-grid** | Icon grid layout | Rows: col1=icon/image, col2=title+description | — | Custom |

## Global Styles (`styles/styles.css`)

### Design Tokens (CSS Custom Properties)
- **Colors**: `--color-navy` (#002855), `--color-teal` (#00857c), `--color-teal-light` (#00a89d), `--color-green` (#6cc24a)
- **Typography**: Open Sans (400, 600, 700) via Google Fonts, with system fallback
- **Breakpoints**: 600px (tablet), 900px (desktop)
- **Layout**: `--max-content-width: 1200px`

### Button Styles
- `.primary` — Teal background, white text
- `.secondary` — Teal outline, transparent background
- `.accent` — Navy background, white text

### Section Styles
| Style | Description |
|-------|-------------|
| `.grey` | Light grey (#f5f5f5) background |
| `.dark` | Navy background, white text, inverted buttons |
| `.cta-band` | Teal background, centered text, white CTAs |
| `.full-width-image` | Background image with navy gradient overlay |
| `.sidebar` | CSS Grid: 2fr + 1fr columns on desktop |

## Scripts

### `scripts/scripts.js`
- Standard EDS loading pipeline: loadEager → loadLazy → loadDelayed
- Auto-blocks: hero (from first h1+picture) and breadcrumbs (from URL path)
- Button decoration: strong=primary, em=secondary, strong+em=accent
- Font loading with session storage optimization

### `scripts/delayed.js`
- Loaded 3s after page load
- Placeholder for third-party scripts (analytics, etc.)

### `scripts/aem.js`
- Unmodified from aem-boilerplate v1.3.0

## head.html
- CSP meta tag with strict-dynamic
- Links to scripts/aem.js, scripts/scripts.js, styles/styles.css

## Configuration Files

### `fstab.yaml`
Points to `https://content.da.live/manuel-vara/eds-migration`

### `helix-query.yaml`
Defines `site` index with properties: title, description, image, lastModified, publishDate, division, category, contentType, eventDate, eventLocation, eventType, topic, expert, template

## Dependencies
- **Block Collection**: carousel, video, embed, fragment, quote, accordion, tabs, table, modal, search — all adapted with Almac brand styling
- **Custom blocks**: hero, cards, columns, breadcrumbs, hubspot-form, content-filter, stats, profile, icon-grid
- **No external JS dependencies** — all vanilla JS
- **HubSpot Forms**: loaded lazily on-demand via intersection observer in hubspot-form block
