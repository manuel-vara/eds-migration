# Phase 2c — Migration Blueprint

**Site**: https://www.almacgroup.com  
**Total pages**: 3,605 across 27 archetypes  
**Blueprint version**: 2c-v1  
**Generated**: 2026-05-12

---

## Block Palette Summary

| # | Block | Source | Action | Complexity | Archetypes | Build Order |
|---|-------|--------|--------|-----------|------------|-------------|
| 1 | hero | Block Collection | adapt | simple | 16 archetypes | 1 |
| 2 | cards | Block Collection | adapt | medium | 14 archetypes (6 variants) | 2 |
| 3 | columns | Block Collection | reuse | simple | 7 archetypes | 3 |
| 4 | breadcrumbs | Block Collection | adapt (auto-blocked) | simple | 22 archetypes | 4 |
| 5 | fragment | Block Collection | reuse | simple | all | 4 |
| 6 | carousel | Block Collection | reuse | medium | 2 archetypes | 5 |
| 7 | video | Block Collection | reuse | simple | 5 archetypes | 6 |
| 8 | embed | Block Collection | reuse (autoblock) | simple | 4 archetypes | 7 |
| 9 | quote | Block Collection | reuse | simple | 3 archetypes | 8 |
| 10 | hubspot-form | **Custom** | build | medium | 25 archetypes (~3,500 pages) | 9 |
| 11 | stats | **Custom** | build | medium | 1 archetype (homepage) | 10 |
| 12 | profile | **Custom** | build | simple | 4 archetypes (141 pages) | 11 |
| 13 | accordion | Block Collection | reuse | simple | 3 archetypes | 12 |
| 14 | tabs | Block Collection | reuse | simple | 2 archetypes | 13 |
| 15 | search | Block Collection | adapt | medium | all (header) | 14 |
| 16 | content-filter | **Custom** | build | **complex** | 4 archetypes (2,330 pages) | 15 |
| 17 | modal | Block Collection | reuse (autoblock) | simple | 4 archetypes | 16 |
| 18 | table | Block Collection | reuse | simple | 2 archetypes | 17 |

**Totals**: 18 blocks (14 Block Collection, 4 custom), 5 section styles

---

## Eliminated Blocks (Palette Minimization)

| Original Block | Decision | Rationale |
|----------------|----------|-----------|
| contact-locations | **Compose** from columns + cards + fragment | Only 1 page (contact). Composition over custom block. |
| icon-grid | **Cards (icon) variant** | Only ~10 pages. CSS-only variant keeps palette minimal. |
| sidebar | **Section style** (`style: sidebar`) | CSS Grid layout, not a block. Authors use Section Metadata. |

---

## Content Model Decisions

### Why Fragment for site-wide HubSpot form
The 8-field HubSpot contact form appears on ~3,500 of 3,605 pages. Authoring it inline on every page would be unmaintainable. Instead:
- Author the form once at `/fragments/hubspot-cta`
- Each page includes `Fragment | /fragments/hubspot-cta`
- Changes to the form propagate to all pages automatically

### Why sidebar is a section style, not a block
EDS best practice: sidebars are layout concerns, not content blocks. Authors create two sections on the page — main content and sidebar content — then apply `Section Metadata | style: sidebar` to get the CSS Grid two-column layout. This is simpler to author and more flexible.

### Why cards has 6 variants instead of separate blocks
The source site uses cards in 6 distinct visual patterns (default link-box, news, resource, event, related, icon). All share the same fundamental structure: image + text + optional CTA. Using a single Cards block with variant classes (`cards (news)`, `cards (event)`, etc.) keeps the palette minimal while CSS handles visual differences.

### Why content-filter is custom despite Block Party reference
Block Party's Content Filter Hub provides architecture reference but needs significant adaptation for Almac's 3 distinct filter configurations (events, news, knowledge). Each has different filter fields and metadata. Custom build with Block Party as starting point, not direct reuse.

### Why breadcrumbs is auto-blocked
Breadcrumbs appear on 22 of 27 archetypes (all except homepage, blog-category, careers-resource, job-listing, contact). Auto-blocking via `scripts.js` means authors never need to add a breadcrumbs table — the block reads URL hierarchy and generates navigation automatically.

---

## Default Content Patterns

The following patterns use standard EDS default content (paragraphs, headings, lists, images) and do NOT require blocks:

| Pattern | Description | Archetypes |
|---------|-------------|------------|
| Body text | Paragraphs, headings (h2-h5), lists, inline images | All |
| CTA buttons | Bold links render as buttons (`**[Learn more](/path)**`) | All |
| Article content | News articles, career stories — bulk of page content | news-post, careers-story, knowledge-library, award |
| Bio text | Expert/team member biography paragraphs below profile block | knowledge-expert, expert-profile, bd-team-profile |
| Sidebar navigation | Links and categories in sidebar section | news-post, careers, api-chemical-product |
| Full-width image overlay | Heading + CTA over background (section style handles image) | clinical-services, commercial-services, pharma-drug |

---

## Site Conventions

### Section Styles
1. **sidebar** — CSS Grid `2fr 1fr` desktop, stack mobile. Used by 8 archetypes.
2. **full-width-image** — Background cover image with text overlay. 3 archetypes.
3. **cta-band** — Accent color background, centered heading + button. 3 archetypes.
4. **dark** — Dark background, light text for contrast sections. 3 archetypes.
5. **grey** — Light grey `#f5f5f5` alternating section contrast. 4 archetypes.

### CTA Pattern
Bold links = primary buttons. Almac CTAs: "Find out more", "Learn more", "Contact us", "Download", "Event Details", "View Resource". Authored as `**[CTA text](url)**` in EDS.

### Image Strategy
- **Download and convert**: Download all images from `wp-content/uploads` and `smushcdn.com` CDN
- **Format**: Convert to WebP where possible; preserve SVGs and animated GIFs
- **Alt text**: Preserve source alt attributes; flag empty alts for accessibility review
- **Naming**: Kebab-case slugs derived from original filenames

---

## Architecture Decisions Log

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| 18 blocks instead of 21 | Minimize palette per EDS philosophy | Slightly more complex CSS for composed patterns |
| Fragment for HubSpot form | DRY — one form, 3,500 pages | Extra Fragment page to maintain; changes have wide blast radius |
| Block Party reference for content-filter | Proven architecture for query-index filtering | Still needs significant custom work; not a drop-in solution |
| Auto-block breadcrumbs | Zero author effort; consistent across site | Less flexibility for custom breadcrumb text per page |
| 6 query-index sheets | Content-filter needs typed collections | More spreadsheet configuration; potential sync issues |
| careers-resource stub migration | Content is fully gated; no content to migrate | 36 pages need manual post-migration content review |
| Sidebar as section style | EDS convention; simpler than block | Authors must understand section boundaries in authoring |
| Preserve WP multisite URL paths | Avoid breaking external links; simpler redirect mapping | EDS folder structure mirrors WP multisite hierarchy |

---

## Migration Priority & Batches

| Batch | Name | Archetypes | Pages | Blocks Introduced |
|-------|------|------------|------:|-------------------|
| 1 | Foundation | homepage, about, award, contact, blog-category, client-portal | 69 | hero, cards, columns, breadcrumbs, hubspot-form, fragment, stats, video, embed |
| 2 | Division landing pages | 8 division sub-sites | 719 | quote, carousel, modal, table |
| 3 | Profile pages | knowledge-expert, expert-profile, bd-team-profile | 140 | profile |
| 4 | Article/detail pages | news-post, careers-story, careers, api-chemical-product, landing, job-listing | 1,003 | sidebar (section style) |
| 5 | Content collections | events, knowledge-library, knowledge, news | 1,651 | content-filter, search |
| 6 | Gated content | careers-resource | 36 | (none — stub migration) |

**Total**: 3,618 pages (some counted in multiple batches due to sub-page types)

---

## Risk Summary

| ID | Severity | Risk | Affected Pages | Mitigation |
|----|----------|------|---------------|-----------|
| RISK-001 | **Critical** | content-filter complexity | 2,330 | Block Party reference; iterative build; static fallback |
| RISK-002 | High | Gated careers-resource content | 36 | Stub migration; manual review |
| RISK-003 | High | HubSpot form dependency | 3,500 | Extract IDs; lazy-load; Fragment for DRY |
| RISK-004 | Medium | Slick.js → EDS carousel | 10 | Block Collection carousel; test transitions |
| RISK-005 | Medium | WP multisite URL structure | 3,000 | Preserve paths; redirect spreadsheet |
| RISK-006 | Medium | CJK URL encoding | 200 | Preserve encoded URLs; test routing |
| RISK-007 | Low | Sitemap 404 ghosts | Unknown | Skip + log + redirect |
| RISK-008 | Medium | Mega-menu navigation | 3,605 | Nested lists; custom header JS |
| RISK-009 | Low | External system embeds | 2 | Preserve iframes; manual setup |

---

## Files Written

| File | Description |
|------|-------------|
| `.eds-migration/state/blueprint.json` | Comprehensive migration blueprint (block palette, archetype blueprints, migration rules, config plan, risk register) |
| `.eds-migration/state/docs/phase2-analysis.md` | This document — Phase 2c analysis summary |
