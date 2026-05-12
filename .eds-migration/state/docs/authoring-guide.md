# Authoring Guide — Almac EDS Migration

## Content Source
All content is authored in **DA (Document Authoring)** at:
`https://da.live/edit#/manuel-vara/eds-migration/`

## Page Types (Archetypes)

### Standard Content Page
- Hero section (optional): image + heading + CTA
- Body content: headings, paragraphs, lists, images
- Optional sidebar section for related content
- CTA band or related cards at bottom

### Division Landing Page
- Carousel or hero block at top
- Stats block with key metrics
- Cards grid showcasing services/capabilities
- Quote/testimonial block
- CTA band with contact link

### Expert Profile Page
- Profile block with photo, name, title, credentials
- Body content with expertise description
- Related content cards at bottom

### Event/News Listing Page
- Content-filter block with appropriate source and filter fields
- Configured via block table with source path and facet fields

### Knowledge Library Page
- Content-filter block with category/topic/division filters
- Cards display with resource type indicators

## Block Usage Guide

### Hero
```
| Hero |                                |
|------|--------------------------------|
| (picture) | # Heading                |
|           | Description text          |
|           | **[CTA Text](url)**       |
```

### Cards
```
| Cards (variant) |                    |
|-----------------|---------------------|
| (picture)       | ### Card Title      |
|                 | Description         |
|                 | **[Read More](url)**|
| (picture)       | ### Card Title 2    |
|                 | Description 2       |
```
**Variants**: `news`, `event`, `resource`, `related`, `icon`

### Columns
```
| Columns |                             |
|---------|-------------------------------|
| (picture or content) | Content or picture |
```

### Carousel
```
| Carousel |                            |
|----------|-------------------------------|
| (image)  | ## Slide 1 Heading           |
|          | Description                   |
|          | **[CTA](url)**               |
| (image)  | ## Slide 2 Heading           |
|          | Description                   |
```

### HubSpot Form
```
| HubSpot Form |         |
|--------------|---------|
| Portal ID    | 123456  |
| Form ID      | abc-def |
```

### Content Filter
```
| Content Filter |            |
|---------------|-------------|
| Source         | news        |
| Category       | category   |
| Division       | division   |
```
Reads from `query-index.json`. Filter field names must match metadata properties.

### Breadcrumbs
Auto-generated from URL path. No authoring needed — the block is inserted automatically on all non-homepage pages.

### Video
```
| Video |                                      |
|-------|--------------------------------------|
| (thumbnail picture) | https://youtube.com/watch?v=xxx |
```

### Embed
```
| Embed |                                      |
|-------|--------------------------------------|
| (optional thumbnail) | https://youtube.com/watch?v=xxx |
```

### Stats
```
| Stats |              |
|-------|--------------|
| 50+   | Years Experience |
| 6000  | Employees    |
| 100+  | Countries    |
```

### Profile
```
| Profile |                              |
|---------|-------------------------------|
| (photo) | ## Dr. Jane Smith             |
|         | **Vice President, Research**   |
|         | Bio text...                    |
```

### Fragment
```
| Fragment |
|----------|
| /fragments/shared-cta |
```

### Quote
```
| Quote |                              |
|-------|------------------------------|
| "Quote text here..." |              |
| — Author Name, *Title, Company* |   |
```

### Accordion
```
| Accordion |                          |
|-----------|--------------------------|
| Question 1 | Answer text...          |
| Question 2 | Answer text...          |
```

### Tabs
```
| Tabs |                               |
|------|-------------------------------|
| Tab 1 Label | Tab 1 content...       |
| Tab 2 Label | Tab 2 content...       |
```

### Table
```
| Table |          |          |
|-------|----------|----------|
| Header 1 | Header 2 | Header 3 |
| Data 1   | Data 2   | Data 3   |
```
**Variants**: `striped`, `no-header`

### Modal
Modals are triggered programmatically. Create content at `/modals/your-modal-name` and link to it.

### Search
```
| Search |
|--------|
| /query-index.json |
```

### Icon Grid
```
| Icon Grid |                          |
|-----------|--------------------------|
| (icon)    | ### Title                 |
|           | Description text          |
| (icon)    | ### Title 2               |
```

## Section Styles
Add a **Section Metadata** table at the end of any section:

```
| Section Metadata |        |
|-----------------|---------|
| Style           | dark    |
```

Available styles:
- **`grey`** — Light grey background
- **`dark`** — Navy background, white text
- **`cta-band`** — Teal background, centered, white text
- **`full-width-image`** — Background image with navy overlay
- **`sidebar`** — Two-column layout (2fr + 1fr on desktop)
- **`highlight`** / **`light`** — Light grey background (alias)

## Image Guidelines
- **Hero images**: 1600×600px minimum, landscape orientation
- **Card images**: 750×563px (4:3 ratio) recommended
- **Profile photos**: 400×400px square, will be displayed as circle
- **Formats**: WebP preferred, JPEG/PNG accepted (auto-optimized)
- **Alt text**: Always provide descriptive alt text for accessibility

## Page Metadata
Add metadata at the bottom of every document:

```
| Metadata |                          |
|----------|--------------------------|
| Title    | Page Title               |
| Description | Page description      |
| Image    | /path/to/og-image.jpg    |
| Template | division-landing         |
| Division | Almac Discovery          |
| Category | News                     |
| Topic    | Drug Development         |
```

## Tips
- Use `**[Link Text](url)**` for primary buttons (bold link)
- Use `*[Link Text](url)*` for secondary buttons (italic link)
- Use `***[Link Text](url)***` for accent buttons (bold+italic)
- Separate sections with `---` (horizontal rule)
- Images are automatically optimized and served via CDN
