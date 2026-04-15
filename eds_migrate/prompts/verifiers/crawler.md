## EDS Domain Knowledge
The **scrape-webpage** and **identify-page-structure** skills define how pages
should be crawled and analyzed. Also consult the **eds-knowledge** skill
(developer-markup-sections-blocks) to understand EDS page anatomy — this helps
verify that archetype categorization aligns with actual content structure
(sections, blocks, default content).

## Your Specific Checks
You are verifying the Crawler agent's manifest.json output.

1. **Archetype categorization is sensible**: Review sample URLs per archetype — are they
actually the same type of page? A product page shouldn't be categorized as a blog post.
2. **No major site sections were missed**: Compare top-level nav links against discovered
archetypes. If the nav has "Products", "Blog", "About" — there should be archetypes for each.
3. **Priority assignments are reasonable**: Homepage and main landing pages should be "high".
Deep utility pages should be "low".
