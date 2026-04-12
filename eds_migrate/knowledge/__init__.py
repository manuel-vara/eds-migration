"""
EDS knowledge base — skills and platform docs.

Directory layout mirrors the runtime filesystem at /knowledge/:

    knowledge/
    ├── skills/
    │   ├── scrape-webpage/SKILL.md
    │   ├── building-blocks/SKILL.md
    │   └── ...
    └── docs/
        ├── developer-markup-sections-blocks.md
        ├── developer-keeping-it-100.md
        └── ...

Skills (from adobe/helix-website) teach "how to build" — patterns, workflows,
tools. Each SKILL.md is self-describing via its description field.

Docs (from aem.live) teach "how the platform works" — markup, APIs,
configuration, performance.

At runtime, the Orchestrator unpacks a compressed archive of this directory
to /knowledge/ as Step 0. Worker and verifier agents discover and read
files on demand (progressive disclosure).
"""

from __future__ import annotations

import base64
import io
import tarfile
from pathlib import Path

_KNOWLEDGE_DIR = Path(__file__).parent
_SKILLS_DIR = _KNOWLEDGE_DIR / "skills"
_DOCS_DIR = _KNOWLEDGE_DIR / "docs"


def get_all_files() -> dict[str, str]:
    """
    Return {relative_path: content} for every knowledge file.

    Paths are relative to the knowledge root, e.g.:
      "skills/building-blocks/SKILL.md"
      "docs/developer-keeping-it-100.md"
    """
    files: dict[str, str] = {}

    for skill_dir in sorted(_SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        md = skill_dir / "SKILL.md"
        if md.exists():
            files[f"skills/{skill_dir.name}/SKILL.md"] = md.read_text(encoding="utf-8")

    for md in sorted(_DOCS_DIR.glob("*.md")):
        files[f"docs/{md.name}"] = md.read_text(encoding="utf-8")

    return files


def build_setup_script() -> str:
    """
    Return a bash script that unpacks the knowledge base to /knowledge/.

    Uses tar+gzip+base64 to minimize token usage in the task message.
    All workers and verifiers can then read individual files on demand.
    """
    all_files = get_all_files()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel_path, content in sorted(all_files.items()):
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=rel_path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))

    archive_b64 = base64.b64encode(buf.getvalue()).decode("ascii")

    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "mkdir -p /knowledge\n"
        f"echo '{archive_b64}' | base64 -d | tar xz -C /knowledge\n"
        "echo \"Knowledge base ready: $(find /knowledge -name '*.md' | wc -l) files.\"\n"
    )
