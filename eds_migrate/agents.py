"""Create and manage all CMA agents and environments for the EDS migration."""

from __future__ import annotations

import logging
import time
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
    session_id: str | None = None

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

    @property
    def all_agents(self) -> list[AgentRef]:
        agents = self.all_workers + self.all_verifiers
        if self.orchestrator:
            agents.append(self.orchestrator)
        return agents

    @property
    def all_env_ids(self) -> list[str]:
        return [e for e in [self.env_basic_id, self.env_npm_id, self.env_heavy_id] if e]


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
        params["extra_body"] = {"callable_agents": callable_agents}
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
AGENT_NAME_PREFIXES = (
    "Crawler-", "Analyzer-", "BlockDev-", "PageMigrator-", "Config-",
    "IntegrationQA-", "CrawlerVerifier-", "AnalyzerVerifier-",
    "BlockDevVerifier-", "PilotVerifier-", "Orchestrator-",
)


def cleanup_fleet(client: Anthropic, fleet: MigrationFleet) -> None:
    """Tear down every resource in the fleet: sessions, agents, environments."""
    cleaned = 0

    if fleet.session_id:
        cleaned += _stop_session(client, fleet.session_id)

    for agent in fleet.all_agents:
        cleaned += _archive_agent(client, agent.id, agent.name)

    for env_id in fleet.all_env_ids:
        cleaned += _archive_env(client, env_id)

    log.info("Cleanup complete — %d resource(s) torn down.", cleaned)


def cleanup_by_run_id(client: Anthropic, run_id: str) -> int:
    """
    Find and tear down orphaned resources matching a run ID.

    Searches for environments, agents, and their sessions by name suffix.
    Useful when the process crashed before normal cleanup ran.
    Returns the total number of resources cleaned up.
    """
    suffix = f"-{run_id}"
    cleaned = 0

    # Agents (and their sessions) first, then environments
    for agent in client.beta.agents.list():
        if any(agent.name.startswith(p) for p in AGENT_NAME_PREFIXES) and agent.name.endswith(suffix):
            for session in client.beta.sessions.list(agent_id=agent.id):
                cleaned += _stop_session(client, session.id)
            cleaned += _archive_agent(client, agent.id, agent.name)

    for env in client.beta.environments.list():
        if any(env.name.startswith(p) for p in ENV_NAME_PREFIXES) and env.name.endswith(suffix):
            cleaned += _archive_env(client, env.id)

    return cleaned


def _stop_session(client: Anthropic, session_id: str) -> int:
    """Interrupt a session, wait briefly for it to go idle, then delete it.

    A running CMA session that's mid-model-request may take a long time to
    process an interrupt. We give it 10 seconds, then move on — the session
    will eventually time out server-side. Agents and environments (the
    billable resources) are cleaned up independently.
    """
    try:
        client.beta.sessions.events.send(
            session_id,
            events=[{"type": "user.interrupt"}],
        )
        log.info("Sent interrupt to session %s", session_id)
    except Exception as e:
        log.debug("Interrupt send failed (session may already be idle): %s", e)

    for _ in range(3):
        time.sleep(3)
        try:
            session = client.beta.sessions.retrieve(session_id)
            if session.status != "running":
                log.info("Session %s is now %s", session_id, session.status)
                break
        except Exception:
            break
    else:
        log.info("Session %s still running — it will time out server-side", session_id)

    for action_name, action in [
        ("delete", lambda: client.beta.sessions.delete(session_id)),
        ("archive", lambda: client.beta.sessions.archive(session_id)),
    ]:
        try:
            action()
            log.info("%sd session %s", action_name.capitalize(), session_id)
            return 1
        except Exception:
            continue

    log.info("Session %s could not be deleted/archived (still running) — will expire on its own", session_id)
    return 0


def _archive_agent(client: Anthropic, agent_id: str, name: str = "") -> int:
    try:
        client.beta.agents.archive(agent_id)
        log.info("Archived agent %s (%s)", name or agent_id, agent_id)
        return 1
    except Exception as e:
        log.warning("Failed to archive agent %s: %s", agent_id, e)
        return 0


def _archive_env(client: Anthropic, env_id: str) -> int:
    try:
        client.beta.environments.archive(env_id)
        log.info("Archived environment %s", env_id)
        return 1
    except Exception as e:
        log.warning("Failed to archive environment %s: %s", env_id, e)
        return 0
