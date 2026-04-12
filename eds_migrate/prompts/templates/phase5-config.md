### Phase 5 — Config

**First dispatch:**
```
Generate all site-level configuration for the migration.

Inputs:
- manifest.json (all pages and their URLs)
- status/ directory (migrated page statuses — use pages with status "migrated")
- blueprint.json (navigation structure, conventions)

GitHub repo: {org}/{repo} (use github-token vault)
da.live: {org}/{repo} (use da-token vault)

Generate and upload/commit:
1. redirects.json → da.live (as sheet)
2. metadata.json → da.live (as sheet)
3. helix-query.yaml → GitHub
4. helix-sitemap.yaml → GitHub
5. robots.txt → GitHub
6. nav.html + footer.html → da.live
```
