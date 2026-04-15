"""Upload and delete the knowledge archive via the GitHub Contents API.

During fleet setup the archive is pushed to a dotfile path in the target
repo so the orchestrator can ``curl`` it down without any data passing
through the LLM.  The file is removed during cleanup.
"""

from __future__ import annotations

import base64
import logging

import httpx

from eds_migrate.knowledge import build_archive

log = logging.getLogger(__name__)

REPO_PATH = ".eds-migrate/knowledge.tar.gz"
_API = "https://api.github.com"
_TIMEOUT = 30.0


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def upload(token: str, org: str, repo: str) -> str:
    """Push the knowledge archive to the repo.  Returns the blob SHA."""
    archive = build_archive()
    content_b64 = base64.b64encode(archive).decode("ascii")

    url = f"{_API}/repos/{org}/{repo}/contents/{REPO_PATH}"

    existing_sha = _get_existing_sha(token, org, repo)
    body: dict = {
        "message": "eds-migrate: add knowledge archive [skip ci]",
        "content": content_b64,
    }
    if existing_sha:
        body["sha"] = existing_sha

    resp = httpx.put(url, headers=_headers(token), json=body, timeout=_TIMEOUT)
    resp.raise_for_status()

    sha = resp.json()["content"]["sha"]
    log.info("Knowledge archive uploaded to %s/%s (%s)", org, repo, sha[:12])
    return sha


def delete(token: str, org: str, repo: str, sha: str) -> None:
    """Remove the knowledge archive from the repo."""
    url = f"{_API}/repos/{org}/{repo}/contents/{REPO_PATH}"
    body = {
        "message": "eds-migrate: remove knowledge archive [skip ci]",
        "sha": sha,
    }
    try:
        resp = httpx.delete(url, headers=_headers(token), json=body, timeout=_TIMEOUT)
        resp.raise_for_status()
        log.info("Knowledge archive deleted from %s/%s", org, repo)
    except Exception as exc:
        log.warning("Failed to delete knowledge archive: %s", exc)


def download_url(token: str, org: str, repo: str) -> str:
    """Return a curl command that downloads and extracts the archive."""
    raw = f"{_API}/repos/{org}/{repo}/contents/{REPO_PATH}"
    return (
        f'curl -fsSL -H "Authorization: token {token}" '
        f'-H "Accept: application/vnd.github.raw" '
        f'"{raw}" | tar xz -C /knowledge'
    )


def _get_existing_sha(token: str, org: str, repo: str) -> str | None:
    """Check if the file already exists and return its SHA (for updates)."""
    url = f"{_API}/repos/{org}/{repo}/contents/{REPO_PATH}"
    try:
        resp = httpx.get(url, headers=_headers(token), timeout=_TIMEOUT)
        if resp.status_code == 200:
            return resp.json()["sha"]
    except Exception:
        pass
    return None
