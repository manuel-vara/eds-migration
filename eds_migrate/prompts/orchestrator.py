"""System prompt for the Migration Orchestrator agent.

In the custom-tool design the orchestrator's prompt is lean: just the
base instructions with {site_url}/{org}/{repo} substituted.  The phase
dispatch is described via the custom-tool descriptions themselves (see
``router.build_custom_tools``) and by short phase-templates that live
next to the base prompt for reference.
"""

import re

from eds_migrate.prompts import _load


_BASE = _load("orchestrator.md")


def build_orchestrator_prompt(site_url: str, org: str, repo: str) -> str:
    values = {"site_url": site_url, "org": org, "repo": repo}
    result = _BASE
    for var, val in values.items():
        result = re.sub(r"(?<!\{)\{" + var + r"\}(?!\})", val, result)
    return result
