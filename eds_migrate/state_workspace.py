"""
Local git-backed workspace the router uses to read/write migration state.

Every worker and verifier session operates against a dedicated branch
(``migration-state/{run_id}``) on the target GitHub repo and commits its
artifacts under ``.eds-migration/state/``.  The Python router keeps a
local clone of the same branch so it can:

- read artifacts (manifest, blueprint, verifier verdicts) when summarising
  worker runs back to the orchestrator;
- stamp a checkpoint and push it before the fleet is torn down.

All commits are local pushes to the remote branch so every new worker
session sees the latest state when it clones.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

STATE_BRANCH_PREFIX = "migration-state/"
STATE_DIR = ".eds-migration/state"
VERIFIER_DIR = ".eds-migration/verifier-results"


@dataclass
class StateWorkspace:
    """A local git clone that tracks the migration-state branch."""

    org: str
    repo: str
    run_id: str
    github_token: str
    root: Path  # local filesystem path to the clone

    # ---------- branch / remote info ----------

    @property
    def branch(self) -> str:
        return f"{STATE_BRANCH_PREFIX}{self.run_id}"

    @property
    def remote_url(self) -> str:
        return (
            f"https://x-access-token:{self.github_token}"
            f"@github.com/{self.org}/{self.repo}.git"
        )

    @property
    def display_remote(self) -> str:
        return f"https://github.com/{self.org}/{self.repo}.git"

    # ---------- lifecycle ----------

    def ensure(self) -> None:
        """Clone the repo and set up the state branch.  Idempotent."""
        if not (self.root / ".git").exists():
            self.root.parent.mkdir(parents=True, exist_ok=True)
            if self.root.exists():
                shutil.rmtree(self.root)
            log.info(
                "Cloning %s into %s for migration state",
                self.display_remote, self.root,
            )
            self._run(
                ["git", "clone", "--quiet", self.remote_url, str(self.root)],
                cwd=None,
            )
            self._run(
                ["git", "config", "user.email", "eds-migrate@automation.local"]
            )
            self._run(
                ["git", "config", "user.name", "EDS Migration Agent"]
            )

        self._run(["git", "fetch", "--quiet", "origin"])
        # Check out the state branch, creating it from main if it doesn't exist yet
        remote_ref = f"origin/{self.branch}"
        if self._run(
            ["git", "rev-parse", "--verify", "--quiet", remote_ref],
            check=False,
        ).returncode == 0:
            self._run(["git", "checkout", "-B", self.branch, remote_ref])
        else:
            # No remote branch yet — create it locally off the default HEAD
            self._run(["git", "checkout", "-B", self.branch])

        (self.root / STATE_DIR).mkdir(parents=True, exist_ok=True)
        (self.root / VERIFIER_DIR).mkdir(parents=True, exist_ok=True)

    def pull(self) -> None:
        """Fetch and fast-forward from the remote state branch.

        Called after a worker session goes idle so we can read whatever
        the worker committed.
        """
        self._run(["git", "fetch", "--quiet", "origin", self.branch], check=False)
        remote_ref = f"origin/{self.branch}"
        if self._run(
            ["git", "rev-parse", "--verify", "--quiet", remote_ref],
            check=False,
        ).returncode == 0:
            self._run(
                ["git", "reset", "--hard", remote_ref],
                check=False,
            )

    def push_checkpoint(self, phase: str, extra: dict[str, Any] | None = None) -> None:
        """Write a checkpoint and push it so subsequent workers see it."""
        data = {"phase": phase, "run_id": self.run_id}
        if extra:
            data.update(extra)
        (self.root / ".eds-migration" / "checkpoint.json").write_text(
            json.dumps(data, indent=2)
        )
        self._run(["git", "add", ".eds-migration/checkpoint.json"], check=False)
        if self._run(
            ["git", "diff", "--cached", "--quiet"],
            check=False,
        ).returncode != 0:
            self._run(
                ["git", "commit", "-m", f"checkpoint: {phase}"],
                check=False,
            )
            self._run(
                ["git", "push", "-u", "origin", self.branch],
                check=False,
            )

    # ---------- reads ----------

    def read_json(self, rel_path: str) -> Any | None:
        p = self.root / rel_path
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            log.warning("Failed to parse %s as JSON: %s", rel_path, exc)
            return None

    def read_text(self, rel_path: str) -> str | None:
        p = self.root / rel_path
        if not p.exists():
            return None
        return p.read_text()

    def manifest(self) -> dict | None:
        return self.read_json(f"{STATE_DIR}/manifest.json")

    def blueprint(self) -> dict | None:
        return self.read_json(f"{STATE_DIR}/blueprint.json")

    def verifier_result(self, phase: str) -> dict | None:
        """Read the verifier's JSON verdict for a phase, if it exists."""
        return self.read_json(f"{VERIFIER_DIR}/{phase}.json")

    def list_status_files(self) -> list[Path]:
        """Return all per-page status JSON files written by Page Migrator."""
        status_dir = self.root / STATE_DIR / "status"
        if not status_dir.exists():
            return []
        return sorted(status_dir.glob("*.json"))

    # ---------- internals ----------

    def _run(
        self,
        cmd: list[str],
        *,
        cwd: Path | None | str = "",
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a subprocess in the workspace root by default."""
        working_dir = self.root if cwd == "" else cwd
        env = os.environ.copy()
        # Avoid getting stuck on interactive prompts
        env.setdefault("GIT_TERMINAL_PROMPT", "0")
        result = subprocess.run(
            cmd,
            cwd=str(working_dir) if working_dir else None,
            capture_output=True,
            text=True,
            env=env,
        )
        if check and result.returncode != 0:
            raise RuntimeError(
                f"Command failed ({' '.join(cmd[:3])}): "
                f"exit={result.returncode}, stderr={result.stderr.strip()}"
            )
        return result


def create_workspace(
    org: str,
    repo: str,
    run_id: str,
    github_token: str,
    workspaces_root: Path | None = None,
) -> StateWorkspace:
    """Create and prepare the on-disk state workspace for a migration run."""
    root = workspaces_root or Path.cwd() / ".migration-workspaces"
    ws = StateWorkspace(
        org=org,
        repo=repo,
        run_id=run_id,
        github_token=github_token,
        root=(root / run_id),
    )
    ws.ensure()
    return ws
