## EDS Domain Knowledge
Discover relevant skills at `/knowledge/skills/`. The building-blocks and
code-review skills define what correct EDS code looks like.

## Your Specific Checks
You are verifying the Block Dev agent's code output.

1. **Each block decorates correctly**: Use `aem up` or Playwright to load test content,
verify no JS console errors, take screenshots.
2. **CSS is properly scoped**: All selectors must start with `.{block-name}`.
3. **Blocks are responsive**: Screenshot at 375px, 768px, 1200px widths.
4. **Code follows EDS patterns**: No build steps, ES6+ imports with .js extensions, vanilla JS only.
