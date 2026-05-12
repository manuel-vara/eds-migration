# Code Sync Fix — Required Manual Step

## Problem
The AEM CDN endpoints (`*.aem.page`, `*.aem.live`) return "Missing configuration" for all paths despite all 49 EDS code files being successfully synced to the AEM code bus.

## Root Cause
The AEM Code Sync GitHub App (installation ID `34179329`) is installed at the `manuel-vara` GitHub user level but has **0 repositories** in its repository access list. Without repo-level access:
1. GitHub does not deliver push webhooks to the AEM Code Sync app
2. The AEM configuration service never receives the initial registration event
3. The CDN cannot resolve site configuration → returns "Missing configuration"

## Evidence
- Individual code files have `code.status: 200` (e.g., `scripts/aem.js`, `fstab.yaml`, `head.html`)
- Manual code sync via `POST /code/manuel-vara/eds-migration/main` processes 49 files, 0 failures
- `GET /user/installations/34179329/repositories` returns `total_count: 0`
- `POST /config/manuel-vara/sites/eds-migration.json` returns 401 (no admin auth available)

## Fix Steps

### Step 1: Add Repository to AEM Code Sync App
The repo owner (`manuel-vara`) must:
1. Go to https://github.com/settings/installations/34179329
2. Under "Repository access", select "Only select repositories"
3. Add `eds-migration` to the list
4. Click "Save"

### Step 2: Trigger Code Sync
After adding the repo, push any commit to `main` (even an empty commit):
```bash
git commit --allow-empty -m "trigger code sync"
git push origin main
```

### Step 3: Verify
```bash
# Check CDN
curl -I "https://main--eds-migration--manuel-vara.aem.page/scripts/aem.js"
# Should return HTTP/2 200

# Check admin status
curl "https://admin.hlx.page/status/manuel-vara/eds-migration/main" | jq '.code.status'
# Should no longer return 400
```

## Alternative: Fresh Installation
If the existing installation cannot be modified:
1. Visit https://github.com/apps/aem-code-sync/installations/new
2. Select `manuel-vara` as the account
3. Choose "Only select repositories" → select `eds-migration`
4. Complete the installation

## What's Already Done
- `.hlxignore` added to exclude non-EDS files (Python, node, dotfiles)
- `fstab.yaml` verified correct: `mountpoints: /: https://content.da.live/manuel-vara/eds-migration`
- All 18 blocks, scripts, styles, head.html, 404.html are on `main` and synced to code bus
- ESLint passes with zero errors
