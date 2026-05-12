# Authoring Guide — Almac Group EDS Migration

## Overview
This guide explains how content authors create pages and use blocks in the migrated Almac Group site on Adobe Edge Delivery Services (EDS). Content is authored on [da.live](https://da.live) and published to `https://main--eds-migration--manuel-vara.aem.live/`.

## Prerequisites
- Access to https://da.live (Dark Alley content editor)
- AEM Sidekick Chrome extension installed
- Familiarity with the block table structure

## Creating Pages

### Page Types (Archetypes)
Pages follow predefined archetypes. Create a new document in da.live under the appropriate folder:

| Archetype | Folder | Typical Blocks |
|-----------|--------|---------------|
| Homepage | `/` | hero (carousel), cards, stats, columns |
| About / Landing | `/about/`, `/landing/` | hero, columns, cards, accordion |
| Division pages | `/analytical/`, `/clinical-services/`, etc. | hero, cards, columns, video, tabs |
| Knowledge / News | `/knowledge/`, `/news/` | hero, cards, content-filter |
| Contact | `/contact/` | hero, hubspot-form, columns |
| Careers | `/careers/` | hero, cards, accordion |

### Page Metadata
Add a Metadata block at the bottom of every page:

| Metadata | |
|----------|--|
| title | Page Title |
| description | Page description for SEO |
| image | /path/to/og-image.jpg |
| template | archetype-name |
| division | Division Name |
| category | Category |

## Using Blocks

### Hero
Full-width banner with optional gradient overlay.

| Hero | |
|------|--|
| ![background image](/path/to/image.jpg) | # Heading<br>Subtitle text<br>**[CTA Button](/link)** |

**Carousel variant**: Use `Hero (carousel)` — each row becomes a slide.

### Cards
Grid of content cards. Each row = one card.

| Cards | |
|-------|--|
| ![card image](/path/to/img1.jpg) | ### Card Title<br>Description text<br>[Learn More](/link) |
| ![card image](/path/to/img2.jpg) | ### Card Title 2<br>Description text<br>[Learn More](/link2) |

**Variants**: `Cards (news)`, `Cards (resource)`, `Cards (event)`, `Cards (related)`, `Cards (icon)`

### Columns
Side-by-side media + text layout.

| Columns | |
|---------|--|
| ![image](/path/to/image.jpg) | ## Heading<br>Paragraph text<br>**[CTA Link](/page)** |

**Video variant**: Use `Columns (video)` with a video thumbnail.

### Accordion
Expandable sections for FAQs or detailed content.

| Accordion | |
|-----------|--|
| ### Question 1 | Answer content for question 1 |
| ### Question 2 | Answer content for question 2 |

### Tabs
Tabbed content panels.

| Tabs | |
|------|--|
| Tab 1 | Tab 2 | Tab 3 |
| Content for tab 1 | Content for tab 2 | Content for tab 3 |

### HubSpot Form
Embed a HubSpot form.

| HubSpot Form | |
|--------------|--|
| portal-id | form-id |

### Stats
Animated counters.

| Stats | |
|-------|--|
| 500+ | Global Employees |
| 30 | Years of Experience |
| 100+ | Countries Served |

### Quote
Testimonial or blockquote.

| Quote | |
|-------|--|
| "Quote text here" | — Author Name, Title |

### Profile
Team member card.

| Profile | |
|---------|--|
| ![photo](/path/to/photo.jpg) | **Name**<br>Job Title<br>Bio paragraph<br>[LinkedIn](https://linkedin.com/in/...) |

### Video
Inline or modal video playback.

| Video | |
|-------|--|
| https://vimeo.com/123456789 | |

### Embed
Third-party content embed.

| Embed | |
|-------|--|
| https://example.com/embed/content | |

### Icon Grid
Grid of icons with labels.

| Icon Grid | |
|-----------|--|
| ![icon](/icons/icon1.svg) | Label 1<br>Description |
| ![icon](/icons/icon2.svg) | Label 2<br>Description |

### Table
Structured data display.

| Table | | |
|-------|--|--|
| Header 1 | Header 2 | Header 3 |
| Data 1 | Data 2 | Data 3 |

### Search
Site search interface.

| Search | |
|--------|--|
| Search placeholder text | /query-index.json |

### Content Filter
Dynamic filtering by taxonomy.

| Content Filter | |
|----------------|--|
| division, category, content-type | /query-index.json |

### Breadcrumbs
Auto-generated from URL path. Add to page:

| Breadcrumbs | |
|-------------|--|

### Fragment
Include a shared content fragment.

| Fragment | |
|----------|--|
| /fragments/shared-content | |

### Modal
Overlay dialog (triggered by link with `#modal-id`).

| Modal | |
|-------|--|
| modal-id | Content for the modal dialog |

## Section Styles
Wrap content between horizontal rules (`---`) to create sections. Add section metadata:

| Section Metadata | |
|-----------------|--|
| style | dark |

Available styles: `dark`, `highlight`, `centered`, `narrow`

## Image Guidelines
- **Hero backgrounds**: 1920×800px minimum, JPEG or WebP
- **Card images**: 600×400px, consistent aspect ratio
- **Profile photos**: 400×400px square, JPEG
- **Icons**: SVG preferred, placed in `/icons/` folder
- Always include descriptive alt text
- Use WebP format when possible for performance
