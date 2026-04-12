"""System prompt for the Migration Orchestrator agent.

Assembled from orchestrator.md (base instructions) plus all template
files in templates/ (dispatch messages for each phase).
"""

from pathlib import Path

from eds_migrate.prompts import _load

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_TEMPLATE_ORDER = [
    "phase1-crawler",
    "phase1-crawler-verifier",
    "phase2-analyzer",
    "phase2-analyzer-verifier",
    "phase3-block-dev",
    "phase3-block-dev-verifier",
    "phase3.5-pilot",
    "phase3.5-pilot-verifier",
    "phase4-migration",
    "phase5-config",
    "phase6-integration-qa",
    "generic-retry",
]


def _load_templates() -> str:
    sections = []
    for name in _TEMPLATE_ORDER:
        path = _TEMPLATES_DIR / f"{name}.md"
        sections.append(path.read_text(encoding="utf-8"))
    return "\n".join(sections)


_BASE = _load("orchestrator.md")
_TEMPLATES = _load_templates()

_FULL_TEMPLATE = (
    _BASE
    + "\n---\n\n"
    + "## Dispatch Templates\n\n"
    + "When you call a subagent, you send it a user message. "
    + "Use these templates to ensure each agent gets the context it needs. "
    + "Replace placeholders with actual values.\n\n"
    + _TEMPLATES
)


def build_orchestrator_prompt(site_url: str, org: str, repo: str) -> str:
    return _FULL_TEMPLATE.format(site_url=site_url, org=org, repo=repo)
