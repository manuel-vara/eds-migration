# Phase 3 — Block Development Summary

## Overview
All 18 blocks for the Almac Group migration have been implemented, linted, and pushed to `main`. The code bus has all 49 EDS-relevant files synced (0 failures).

## Blocks

| Block | Purpose | Source | Variants |
|-------|---------|--------|----------|
| hero | Full-width banner with gradient overlay | block-collection (adapted) | default, carousel |
| cards | Content cards grid | block-collection (adapted) | default, news, resource, event, related, icon |
| columns | Media-text split layouts | block-collection (reused) | default, video |
| carousel | Sliding content panels | block-collection (reused) | default |
| video | Vimeo/YouTube playback | block-collection (reused) | inline, modal |
| embed | Third-party embed (iframes) | block-collection (reused) | default |
| accordion | Expandable FAQ/content sections | block-collection (reused) | default |
| tabs | Tabbed content panels | block-collection (reused) | default |
| table | Structured data tables | block-collection (reused) | default |
| fragment | Include reusable content fragments | block-collection (reused) | default |
| modal | Overlay dialogs | custom | default |
| hubspot-form | HubSpot form integration | custom | default |
| search | Site search with filtering | custom | default |
| content-filter | Dynamic content filtering by taxonomy | custom | default |
| stats | Animated statistics/counters | custom | default |
| profile | Team member profile cards | custom | default |
| quote | Blockquote/testimonial | custom | default |
| icon-grid | Grid of icons with labels | custom | default |
| breadcrumbs | Navigation breadcrumb trail | custom | default |

## Content Models

Each block uses a standard EDS table structure in authoring documents:

- **hero**: Row 1: [background image | heading (h1) + subtitle + CTA]
- **cards**: Each row = one card: [card image | heading + description + link]
- **columns**: Row 1: [image/video | heading + paragraphs + CTA]
- **carousel**: Each row = one slide (wraps hero or card content)
- **accordion**: Each row: [question heading | answer content]
- **tabs**: Row 1: tab labels; subsequent rows: tab content
- **hubspot-form**: Row 1: [HubSpot portal ID | form ID]
- **search**: Row 1: [placeholder text | index endpoint URL]
- **content-filter**: Row 1: [filter categories | content source URL]
- **stats**: Each row: [number value | description label]
- **profile**: Row 1: [photo | name + title + bio + social links]
- **quote**: Row 1: [quote text | attribution/author]
- **icon-grid**: Each row: [icon image | label + description]

## Global Styles (styles/styles.css)

- CSS custom properties for Almac brand colors, typography, spacing
- Mobile-first responsive breakpoints
- Default content styling (headings, paragraphs, links, images)
- Section-level layout utilities
- Button styling (primary/secondary variants)

## Scripts

- **scripts/aem.js**: Unmodified boilerplate — block loading, section decoration, eager/lazy/delayed phases
- **scripts/scripts.js**: Custom site initialization — font loading, header/footer decoration, metadata handling
- **scripts/delayed.js**: Deferred loading for analytics, third-party scripts

## head.html

- Content Security Policy meta tag (script-src with nonce)
- Viewport meta tag
- aem.js and scripts.js module script tags
- styles.css stylesheet link

## Configuration Files

- **fstab.yaml**: Content source pointing to `https://content.da.live/manuel-vara/eds-migration`
- **helix-query.yaml**: Query index with properties for title, description, image, dates, division, category, content type, event details, topic, expert, template
- **.hlxignore**: Excludes non-EDS files from code sync (Python files, node modules, dotfiles, markdown)
- **.eslintrc.js** / **.eslintignore**: ESLint configuration — lint passes with zero errors

## Known Issue: CDN Configuration

**Status**: All code is synced to the code bus (49 files, 0 failures) but CDN returns "Missing configuration."

**Root Cause**: The AEM Code Sync GitHub App (installation ID 34179329) does not have the `eds-migration` repository in its repository access list. The app is installed at the user level but has 0 repositories configured, preventing the AEM configuration service from initializing.

**Resolution**: The repo owner must visit https://github.com/apps/aem-code-sync/installations/new and add `manuel-vara/eds-migration` to the app's repository list. Once done, a push to `main` will trigger a webhook that properly initializes the configuration service and enables CDN serving.

See `.eds-migration/state/docs/code-sync-fix.md` for detailed instructions.
