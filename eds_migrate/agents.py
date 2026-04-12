"""Create and manage all CMA agents and environments for the EDS migration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from anthropic import Anthropic

from eds_migrate.prompts import workers, verifiers
from eds_migrate.prompts.orchestrator import build_orchestrator_prompt

log = logging.getLogger(__name__)

TOOLSET = {"type": "agent_toolset_20260401"}


@dataclass
class AgentRef:
    """Pointer to a created agent."""
    id: str
    version: int
    name: str


@dataclass
class MigrationFleet:
    """All agents and environments needed for a migration run."""
    orchestrator: AgentRef | None = None
    crawler: AgentRef | None = None
    analyzer: AgentRef | None = None
    block_dev: AgentRef | None = None
    page_migrator: AgentRef | None = None
    config: AgentRef | None = None
    integration_qa: AgentRef | None = None
    crawler_verifier: AgentRef | None = None
    analyzer_verifier: AgentRef | None = None
    block_dev_verifier: AgentRef | None = None
    pilot_verifier: AgentRef | None = None
    env_basic_id: str | None = None
    env_npm_id: str | None = None
    env_heavy_id: str | None = None

    @property
    def all_workers(self) -> list[AgentRef]:
        return [a for a in [
            self.crawler, self.analyzer, self.block_dev,
            self.page_migrator, self.config, self.integration_qa,
        ] if a is not None]

    @property
    def all_verifiers(self) -> list[AgentRef]:
        return [a for a in [
            self.crawler_verifier, self.analyzer_verifier,
            self.block_dev_verifier, self.pilot_verifier,
        ] if a is not None]


def _create_agent(
    client: Anthropic, name: str, model: str, system: str,
    callable_agents: list[dict] | None = None,
) -> AgentRef:
    """Create a single CMA agent."""
    params: dict = {
        "name": name,
        "model": model,
        "system": system,
        "tools": [TOOLSET],
    }
    if callable_agents:
        params["callable_agents"] = callable_agents
    agent = client.beta.agents.create(**params)
    log.info("Created agent %s (%s v%d)", name, agent.id, agent.version)
    return AgentRef(id=agent.id, version=agent.version, name=name)


def _create_env(
    client: Anthropic, name: str, packages: dict[str, list[str]] | None = None,
) -> str:
    """Create a CMA environment. Returns the environment ID."""
    config: dict = {
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    }
    if packages:
        config["packages"] = packages
    env = client.beta.environments.create(name=name, config=config)
    log.info("Created environment %s (%s)", name, env.id)
    return env.id


def create_fleet(
    client: Anthropic,
    site_url: str,
    org: str,
    repo: str,
    run_id: str,
) -> MigrationFleet:
    """
    Create all agents and environments for a migration run.

    The run_id is appended to names to avoid collisions between concurrent runs.
    Each agent's system prompt points to /knowledge/ on the shared filesystem
    where EDS skills and platform docs are available for progressive discovery.
    The Orchestrator populates /knowledge/ at session start (Step 0).
    """
    fleet = MigrationFleet()
    suffix = f"-{run_id}"

    # ── Environments ──
    fleet.env_basic_id = _create_env(
        client, f"eds-basic{suffix}",
    )
    fleet.env_npm_id = _create_env(
        client, f"eds-npm{suffix}",
        packages={"npm": ["playwright", "pixelmatch", "pngjs"]},
    )
    fleet.env_heavy_id = _create_env(
        client, f"eds-heavy{suffix}",
        packages={"npm": [
            "@anthropic-ai/sdk", "playwright", "pixelmatch", "pngjs",
            "@adobe/aem-cli", "vitest",
        ]},
    )

    # ── Worker Agents ──
    fleet.crawler = _create_agent(
        client, f"Crawler{suffix}", "claude-sonnet-4-6",
        workers.CRAWLER,
    )
    fleet.analyzer = _create_agent(
        client, f"Analyzer{suffix}", "claude-opus-4-6",
        workers.ANALYZER,
    )
    fleet.block_dev = _create_agent(
        client, f"BlockDev{suffix}", "claude-opus-4-6",
        workers.BLOCK_DEV,
    )
    fleet.page_migrator = _create_agent(
        client, f"PageMigrator{suffix}", "claude-sonnet-4-6",
        workers.PAGE_MIGRATOR,
    )
    fleet.config = _create_agent(
        client, f"Config{suffix}", "claude-sonnet-4-6",
        workers.CONFIG,
    )
    fleet.integration_qa = _create_agent(
        client, f"IntegrationQA{suffix}", "claude-sonnet-4-6",
        workers.INTEGRATION_QA,
    )

    # ── Tier 2 Verifier Agents ──
    fleet.crawler_verifier = _create_agent(
        client, f"CrawlerVerifier{suffix}", "claude-sonnet-4-6",
        verifiers.CRAWLER_VERIFIER,
    )
    fleet.analyzer_verifier = _create_agent(
        client, f"AnalyzerVerifier{suffix}", "claude-opus-4-6",
        verifiers.ANALYZER_VERIFIER,
    )
    fleet.block_dev_verifier = _create_agent(
        client, f"BlockDevVerifier{suffix}", "claude-sonnet-4-6",
        verifiers.BLOCK_DEV_VERIFIER,
    )
    fleet.pilot_verifier = _create_agent(
        client, f"PilotVerifier{suffix}", "claude-sonnet-4-6",
        verifiers.PILOT_VERIFIER,
    )

    # ── Orchestrator ──
    callable = [
        {"type": "agent", "id": a.id, "version": a.version}
        for a in fleet.all_workers + fleet.all_verifiers
    ]
    fleet.orchestrator = _create_agent(
        client, f"Orchestrator{suffix}", "claude-opus-4-6",
        build_orchestrator_prompt(site_url, org, repo),
        callable_agents=callable,
    )

    log.info(
        "Fleet created: %d workers, %d verifiers, 1 orchestrator, 3 environments",
        len(fleet.all_workers), len(fleet.all_verifiers),
    )
    return fleet


ENV_NAME_PREFIXES = ("eds-basic-", "eds-npm-", "eds-heavy-")


def cleanup_fleet(client: Anthropic, fleet: MigrationFleet) -> None:
    """Archive all environments from an in-memory fleet."""
    for env_id in [fleet.env_basic_id, fleet.env_npm_id, fleet.env_heavy_id]:
        if env_id:
            _archive_env(client, env_id)


def cleanup_by_run_id(client: Anthropic, run_id: str) -> int:
    """
    Find and archive orphaned environments matching a run ID.

    Useful when the process crashed before the normal cleanup ran.
    Returns the number of environments archived.
    """
    suffix = f"-{run_id}"
    archived = 0

    envs = client.beta.environments.list()
    for env in envs:
        if any(env.name.startswith(p) for p in ENV_NAME_PREFIXES) and env.name.endswith(suffix):
            _archive_env(client, env.id)
            archived += 1

    return archived


def _archive_env(client: Anthropic, env_id: str) -> None:
    """Archive a single environment, logging success or failure."""
    try:
        client.beta.environments.archive(env_id)
        log.info("Archived environment %s", env_id)
    except Exception as e:
        log.warning("Failed to archive environment %s: %s", env_id, e)
