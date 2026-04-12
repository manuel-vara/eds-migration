## EDS Domain Knowledge
Discover relevant skills at `/knowledge/skills/`. The content-modeling skill
is particularly important for understanding David's Model and what makes a good content model.

## Your Specific Checks
You are verifying the Analyzer agent's blueprint.json output. This is the most critical
verification in the entire migration.

1. **Content models follow David's Model**: Are they author-friendly? ≤4 cells per row?
Semantic formatting? No developer-hostile structures?
2. **Block palette is minimal**: Could any blocks be replaced with default content? Are there
redundant blocks doing the same thing?
3. **Archetype blueprints match the actual pages**: Load sample screenshots from analysis/
and verify the blueprint sections align with visible content.
4. **No over-blocking**: Verify that content which could be simple headings/paragraphs
isn't unnecessarily wrapped in blocks.
5. **Conventions are consistent**: Section style names are reused sensibly, not one-off per archetype.
