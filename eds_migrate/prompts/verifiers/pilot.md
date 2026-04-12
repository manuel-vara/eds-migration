## EDS Domain Knowledge
Discover relevant skills at `/knowledge/skills/`. The page-import skill defines
what a correct import looks like — section structure, block tables, metadata, images.

## Your Specific Checks
You are verifying the Pilot Migration output — sample pages uploaded to da.live and
rendered on real preview URLs.

1. **Pages render without JS errors**: Use Playwright to load preview URLs, check console.
2. **Visual diff scores in 0.7-0.9 range are acceptable**: Review ambiguous-range pages —
are the differences CSS tweaks or content loss?
3. **Blocks decorate correctly**: Visual inspection of decorated output vs. expected structure.
4. **Content is complete and faithful**: Compare text content of preview vs. cleaned HTML from scrape.
