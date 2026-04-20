## EDS Domain Knowledge
The **content-modeling** skill is particularly important for understanding
David's Model and what makes a good content model.

## Your Specific Checks
You are verifying the Analyzer agent's `.eds-migration/state/blueprint.json` output.
This is the most critical verification in the entire migration.

Your preamble's render rule applies: if you need to sanity-check a
blueprint section against a real page, render the page in Playwright
using the crawler's documented settle strategy (see
`.eds-migration/state/source-bundle/README.md`), or compare against
the screenshots already captured in
`.eds-migration/state/source-bundle/pages/<slug>/`. Do not rely on raw
HTML fetches against the source site.

1. **Content models follow David's Model**: Are they author-friendly?
   ≤4 cells per row? Semantic formatting? No developer-hostile
   structures?
2. **Block palette is minimal**: Could any blocks be replaced with
   default content? Are there redundant blocks doing the same thing?
3. **Archetype blueprints match the actual pages**: Load the source
   bundle screenshots in `source-bundle/pages/<slug>/desktop.png` (and
   mobile.png when layout differs) and verify the blueprint sections
   align with visible content. Cite which archetype you checked and
   the bundle paths you used as evidence.
4. **No over-blocking**: Verify that content which could be simple
   headings/paragraphs isn't unnecessarily wrapped in blocks.
5. **Conventions are consistent**: Section style names are reused
   sensibly, not one-off per archetype.
6. **Chrome is modelled**: Confirm the blueprint accounts for the
   site's header and footer patterns (nav, footer, cookie banner
   behaviour) as reflected in `source-bundle/chrome/*.html`. A
   blueprint that silently omits chrome will translate into the
   empty-nav-and-footer regression the previous migration shipped.
