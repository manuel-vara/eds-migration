### Phase 5 — Config

**First dispatch:**
```
Generate all site-level configuration for the migration.

Consult the **eds-knowledge** skill before starting — especially the docs on redirects, bulk metadata, indexing (helix-query.yaml), sitemaps (helix-sitemap.yaml), and spreadsheets.

Inputs:
- manifest.json (all pages and their URLs)
- status/ directory (migrated page statuses — use pages with status "migrated")
- blueprint.json (navigation structure, conventions)

GitHub repo: {org}/{repo} (use github-token vault)
da.live: {org}/{repo} (use $EDS_TOKEN for auth)

Generate and upload/commit:
1. redirects.json → da.live (as sheet)
2. metadata.json → da.live (as sheet)
3. helix-query.yaml → GitHub
4. helix-sitemap.yaml → GitHub
5. robots.txt → GitHub
6. nav.html + footer.html → da.live
```
