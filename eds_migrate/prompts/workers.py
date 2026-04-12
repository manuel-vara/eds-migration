"""System prompts for all worker agents, loaded from .md files."""

from eds_migrate.prompts import _load

CRAWLER = _load("workers/crawler.md")
ANALYZER = _load("workers/analyzer.md")
BLOCK_DEV = _load("workers/block_dev.md")
PAGE_MIGRATOR = _load("workers/page_migrator.md")
CONFIG = _load("workers/config.md")
INTEGRATION_QA = _load("workers/integration_qa.md")
