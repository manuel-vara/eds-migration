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
