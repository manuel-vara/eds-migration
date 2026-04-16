# EDS Migration Task

Migrate **{site_url}** to AEM Edge Delivery Services.

## Step 0 — Configure Credentials

**Before doing anything else**, run these commands to set up git credentials
and API tokens. All subsequent git operations and API calls depend on this.

```bash
# GitHub credentials — configures git to authenticate pushes
git config --global credential.helper store
echo "https://x-access-token:{github_token}@github.com" > ~/.git-credentials
git config --global user.email "eds-migrate@automation.local"
git config --global user.name "EDS Migration Agent"

# EDS access token — used for da.live content authoring API calls
{eds_token_block}

echo "Credentials configured."
```

**Verify** by running: `git ls-remote https://github.com/{org}/{repo}.git`
If this fails, stop and report the error.

## Knowledge

EDS skills are attached to every agent in this session. The platform loads
them on demand when relevant to the task — you and your workers do not need
to download or install anything. Skills cover block development, content
modeling, page import, code review, testing, web performance, and platform
reference documentation (the **eds-knowledge** skill).

## Configuration
- GitHub org: `{org}`
- GitHub repo: `{repo}`
- da.live path: `{org}/{repo}`
- Preview URL: `https://main--{repo}--{org}.aem.page/`

## Instructions

Execute the migration phases in order. For each phase:

1. First, save the Tier 1 validation script to `tier1/` and make it executable
2. Dispatch the appropriate worker agent with its task
3. Run the Tier 1 script: `bash tier1/<phase>.sh`
4. If Tier 1 fails, send the errors to the worker and have it retry
5. If Tier 1 passes and the phase has a Tier 2 verifier, dispatch it
6. If Tier 2 fails, send feedback to the worker (latest feedback only) and retry
7. If all retries exhausted, apply autonomous fallback per the rules in your system prompt
8. Verify the worker wrote its phase documentation to `docs/`
9. Write migration-state.json checkpoint after each phase

After all phases complete, write `docs/MIGRATION-REPORT.md` and push `docs/` to GitHub.

## Agent Roster
Workers: {workers}
Verifiers: {verifiers}

## Tier 1 Validation Scripts
{tier1_block}

Begin with Step 0 (credentials), then Phase 1 — Discovery. Good luck.
