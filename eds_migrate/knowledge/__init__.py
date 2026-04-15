"""
EDS knowledge base — skills for AEM Edge Delivery Services migration.

Directory layout:

    knowledge/
    └── skills/
        ├── scrape-webpage/SKILL.md
        ├── building-blocks/SKILL.md
        ├── eds-knowledge/SKILL.md + references/
        └── ...

Each skill directory contains a SKILL.md (and optional supporting files).
At deploy time, every skill is uploaded to the Anthropic Skills API and
attached to agents in the fleet.  The platform makes them available on
demand — agents discover and read them automatically.
"""

from __future__ import annotations

from pathlib import Path

_KNOWLEDGE_DIR = Path(__file__).parent
_SKILLS_DIR = _KNOWLEDGE_DIR / "skills"


def get_skill_dirs() -> list[Path]:
    """Return the absolute path of every skill directory.

    A valid skill directory contains a ``SKILL.md`` file.
    """
    dirs: list[Path] = []
    for child in sorted(_SKILLS_DIR.iterdir()):
        if child.is_dir() and (child / "SKILL.md").exists():
            dirs.append(child)
    return dirs
