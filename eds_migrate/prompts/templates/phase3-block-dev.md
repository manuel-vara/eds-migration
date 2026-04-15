### Phase 3 — Block Dev

**First dispatch:**
```
Build the EDS codebase. The blueprint is at `blueprint.json`.

Before starting, consult the **building-blocks**, **content-driven-development**, and **testing-blocks** skills (attached to your agent). Also consult the **eds-knowledge** skill (developer-keeping-it-100) for performance requirements.

GitHub repo: {org}/{repo} (use the github-token vault for auth)
Content source fstab.yaml mount: https://content.da.live/{org}/{repo}

For each block in the palette:
- source: "block-collection" → copy from Block Collection repo
- source: "custom" → build from scratch following EDS patterns

After all blocks are built:
1. Run `npm run lint` — must pass with zero errors
2. Run `aem up` and verify blocks decorate on test content
3. Push all code to GitHub

The repo should contain: blocks/, styles/, scripts/, head.html, fstab.yaml, 404.html
```

**Retry (Tier 1 failure):**
```
The codebase failed Tier 1 validation:

{{tier1_errors}}

Fix the issues in the repo. Don't rebuild from scratch — fix incrementally. Run `npm run lint` before declaring done.
```

**Retry (Tier 2 failure):**
```
The Block Dev Verifier found issues:

{{verifier_verdict_json}}

Fix the specific issues above. Run `aem up` to verify blocks decorate, then `npm run lint`. Push fixes to GitHub.
```
