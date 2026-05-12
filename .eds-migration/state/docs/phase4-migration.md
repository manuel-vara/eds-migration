# Phase 4 — Pilot Migration Documentation

## Chunk 4/4 — Worker: PageMigrator-1b3ddcfa#chunk4

### Pages Processed

| URL | Archetype | Status | Notes |
|-----|-----------|--------|-------|
| https://www.almacgroup.com/news/almac-clinical-services-scoops-national-training-award/ | news-post | failed (no token) | HTML generated, upload blocked by missing EDS_TOKEN |
| https://www.almacgroup.com/knowledge/experts/abi-pesun/ | knowledge-expert | failed (no token) | HTML generated, upload blocked by missing EDS_TOKEN |

### Archetype Coverage

Both archetypes are new for this run:
- **news-post** — article with sidebar navigation layout; content from source-bundle `clinical-services-news/`
- **knowledge-expert** — expert profile with bio, sidebar, related articles; content from source-bundle `knowledge-experts-abi-pesun/`

### Source Bundle Usage

- `news/almac-clinical-services-scoops-national-training-award/` → NOT in bundle. Found via manifest slug `clinical-services-news` → bundle at `source-bundle/pages/clinical-services-news/`
- `knowledge/experts/abi-pesun/` → Found directly in bundle at `source-bundle/pages/knowledge-experts-abi-pesun/`

### HTML Structure Decisions

#### news-post (news-almac-clinical-services-scoops-national-training-award)
- **Section 1** (sidebar style): breadcrumbs + article body (h1, date, all body paragraphs)
- **Section 2**: Fragment block pointing to `/fragments/hubspot-cta`
- **Metadata**: title, description, publish-date, division, category
- All article body paragraphs retained; NOTES TO EDITORS section preserved as numbered list

#### knowledge-expert (abi-pesun)
- **Section 1**: Hero block with portrait image, name, title, division
- **Section 2**: Breadcrumbs nav
- **Section 3**: Profile (Expert) block — image + name/title/contact links in two-col table
- **Section 4**: Default content — bio paragraphs grouped under `<h2>` headings (Current Role, Previous Experience), Joined Almac year
- **Section 5**: Cards block — related articles with type label, image, title
- **Section 6**: Hubspot Form (gated-content) block — portal-id, form-id
- **Section 7**: Fragment block → `/fragments/hubspot-cta`
- **Metadata**: title, description, expert-name, expertise-area, division, og:image

### Issues Encountered

1. **No EDS_TOKEN** — The workspace bootstrap explicitly warned no token was provided. All DA upload attempts returned HTTP 401. Status files are written with `"status": "failed"` and `"failureReason"` explaining this. HTML artifacts are fully generated and available at `/home/claude/scratch/page-migrator/output/`.

2. **news article slug mismatch** — The manifest entry for the news article used slug `clinical-services-news` (not the full article slug). The source bundle stored it under `pages/clinical-services-news/`. This was cross-referenced via `meta.json` which confirmed the URL match.

3. **knowledge-expert expert section lazy-loading** — The `c-knowledge-expert` content section appeared sparse in initial scraping. Resolved by directly targeting the `s-cms` div within the expert section using BeautifulSoup class matching.

### Text/Image Fidelity

| Page | Source text length | Content captured | Estimate |
|------|--------------------|-----------------|----------|
| news-post | 14,084 chars | All article paragraphs + notes to editors | ~85% |
| knowledge-expert | 11,010 chars | Bio, role description, related articles | ~70% |

Image count: news article has no inline images (text-only article). Expert profile: 1 portrait + 2 related article thumbnails.

### Pending Patterns

None. Both URLs matched existing archetypes in blueprint.json.
