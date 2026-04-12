"""System prompts for all Tier 2 verifier agents, loaded from .md files."""

from eds_migrate.prompts import _load

VERIFIER_PREAMBLE = _load("verifiers/preamble.md")

CRAWLER_VERIFIER = VERIFIER_PREAMBLE + "\n" + _load("verifiers/crawler.md")
ANALYZER_VERIFIER = VERIFIER_PREAMBLE + "\n" + _load("verifiers/analyzer.md")
BLOCK_DEV_VERIFIER = VERIFIER_PREAMBLE + "\n" + _load("verifiers/block_dev.md")
PILOT_VERIFIER = VERIFIER_PREAMBLE + "\n" + _load("verifiers/pilot.md")
