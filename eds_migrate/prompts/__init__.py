"""Agent prompt loaders. Prompts live in .md files for easy editing."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def _load(relative_path: str) -> str:
    """Read a prompt .md file relative to the prompts directory."""
    return (_PROMPTS_DIR / relative_path).read_text(encoding="utf-8")
