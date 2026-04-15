"""Deploy and teardown knowledge skills via the Anthropic Skills API.

During fleet setup each skill directory under ``knowledge/skills/`` is
uploaded as a custom skill.  The returned skill IDs are attached to every
agent in the fleet so the platform loads them on demand.  During teardown
the skills are deleted to keep the workspace clean.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic, APIConnectionError, APIStatusError
from anthropic._types import FileTypes

from eds_migrate.knowledge import get_skill_dirs

log = logging.getLogger(__name__)

_SKILLS_BETA = "skills-2025-10-02"
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2  # seconds; doubles each attempt
_SKIP_DIRS = {"node_modules", "__pycache__", ".git"}


def _collect_skill_files(directory: Path, relative_to: Path) -> list[FileTypes]:
    """Like ``files_from_dir`` but skips ``node_modules`` and similar."""
    files: list[FileTypes] = []
    for entry in sorted(directory.iterdir()):
        if entry.is_dir():
            if entry.name in _SKIP_DIRS:
                continue
            files.extend(_collect_skill_files(entry, relative_to))
        else:
            files.append((entry.relative_to(relative_to).as_posix(), entry.read_bytes()))
    return files


@dataclass
class DeployedSkill:
    """A skill that has been uploaded to the Anthropic Skills API."""
    skill_id: str
    name: str
    version: str


def _delete_skill(client: Anthropic, skill_id: str, display_title: str) -> None:
    """Delete all versions of a skill, then delete the skill itself."""
    for version in client.beta.skills.versions.list(skill_id, betas=[_SKILLS_BETA]):
        client.beta.skills.versions.delete(
            version.version, skill_id=skill_id, betas=[_SKILLS_BETA],
        )
    client.beta.skills.delete(skill_id, betas=[_SKILLS_BETA])
    log.info("Cleaned up stale skill %s (%s)", display_title, skill_id)


def _cleanup_stale_skills(client: Anthropic, names: set[str]) -> None:
    """Delete any previously-deployed skills whose display_title matches."""
    for skill in client.beta.skills.list(betas=[_SKILLS_BETA]):
        if skill.display_title in names:
            try:
                _delete_skill(client, skill.id, skill.display_title)
            except Exception as exc:
                log.warning("Failed to clean up skill %s: %s", skill.display_title, exc)


def deploy_all(client: Anthropic) -> list[DeployedSkill]:
    """Upload every knowledge skill and return their metadata."""
    skill_dirs = get_skill_dirs()
    names = {d.name for d in skill_dirs}

    _cleanup_stale_skills(client, names)

    deployed: list[DeployedSkill] = []
    for skill_dir in skill_dirs:
        name = skill_dir.name
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                files = _collect_skill_files(skill_dir, skill_dir.parent)
                log.debug("Skill %s: %d file(s)", name, len(files))
                skill = client.beta.skills.create(
                    display_title=name,
                    files=files,
                    betas=[_SKILLS_BETA],
                )
                ds = DeployedSkill(
                    skill_id=skill.id,
                    name=name,
                    version=str(skill.latest_version),
                )
                deployed.append(ds)
                log.info("Deployed skill %s (%s v%s)", name, skill.id, ds.version)
                break
            except (APIConnectionError, APIStatusError) as exc:
                last_exc = exc
                if isinstance(exc, APIStatusError) and exc.status_code < 500:
                    raise
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                log.warning("Retry %d/%d for skill %s (%s), waiting %.0fs...",
                            attempt, _MAX_RETRIES, name, exc, delay)
                time.sleep(delay)
            except Exception:
                log.exception("Failed to deploy skill %s", name)
                raise
        else:
            log.error("All %d retries exhausted for skill %s", _MAX_RETRIES, name)
            raise last_exc  # type: ignore[misc]

    log.info("Deployed %d skills.", len(deployed))
    return deployed


def teardown(client: Anthropic, skills: list[DeployedSkill]) -> None:
    """Delete all deployed skills (best-effort)."""
    for ds in skills:
        try:
            _delete_skill(client, ds.skill_id, ds.name)
        except Exception as exc:
            log.warning("Failed to delete skill %s (%s): %s", ds.name, ds.skill_id, exc)


def skill_params(skills: list[DeployedSkill]) -> list[dict]:
    """Build the ``skills`` list for ``agents.create()``."""
    return [
        {"type": "custom", "skill_id": ds.skill_id, "version": ds.version}
        for ds in skills
    ]
