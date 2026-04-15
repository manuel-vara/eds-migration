"""
CLI entry point for the EDS Migration Agent.

Usage:
    eds-migrate --site https://example.com --org acme --repo site
    eds-migrate --site https://example.com --org acme --repo site --verbose
    eds-migrate --cleanup --run-id abc123

Credentials can be passed via CLI flags, environment variables, or a .env file:
    GITHUB_TOKEN   — GitHub PAT for pushing code (--github-token)
    EDS_TOKEN      — Adobe EDS access token for content authoring (--eds-token)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic

from eds_migrate.agents import create_fleet, cleanup_fleet, cleanup_by_run_id
from eds_migrate.knowledge.deploy import deploy_all, teardown as teardown_skills
from eds_migrate.session import run_migration


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="eds-migrate",
        description="Migrate a website to AEM Edge Delivery Services using Claude Managed Agents.",
    )
    parser.add_argument("--site", help="Source site URL to migrate")
    parser.add_argument("--org", help="GitHub organization")
    parser.add_argument("--repo", help="GitHub repository name")
    parser.add_argument("--run-id", default=None, help="Run ID (default: auto-generated)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Stream agent output to stdout")
    parser.add_argument("--cleanup", action="store_true", help="Only cleanup resources from a previous run")
    parser.add_argument(
        "--github-token", default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub PAT (default: $GITHUB_TOKEN)",
    )
    parser.add_argument(
        "--eds-token", default=os.environ.get("EDS_TOKEN"),
        help="Adobe EDS access token (default: $EDS_TOKEN)",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    log = logging.getLogger("eds_migrate")

    client = Anthropic()

    if args.cleanup:
        if not args.run_id:
            parser.error("--cleanup requires --run-id")
        log.info("Cleanup mode — tearing down resources for run %s", args.run_id)
        cleaned = cleanup_by_run_id(client, args.run_id)
        if cleaned:
            log.info("Cleaned up %d resource(s).", cleaned)
        else:
            log.info("No matching resources found for run ID %s.", args.run_id)
        return 0

    if not args.site or not args.org or not args.repo:
        parser.error("--site, --org, and --repo are required for migration")

    if not args.github_token:
        parser.error(
            "GitHub token required. Pass --github-token or set GITHUB_TOKEN env var."
        )
    if not args.eds_token:
        log.warning("No EDS token provided — content authoring steps will be skipped.")

    run_id = args.run_id or uuid.uuid4().hex[:8]

    log.info("=" * 60)
    log.info("EDS Migration Agent")
    log.info("=" * 60)
    log.info("Source site : %s", args.site)
    log.info("Target      : github.com/%s/%s", args.org, args.repo)
    log.info("Content     : da.live/%s/%s", args.org, args.repo)
    log.info("Preview     : https://main--%s--%s.aem.page/", args.repo, args.org)
    log.info("Run ID      : %s", run_id)
    log.info("GitHub token: %s...%s", args.github_token[:4], args.github_token[-4:])
    log.info("EDS token   : %s", "provided" if args.eds_token else "not provided")
    log.info("=" * 60)

    deployed_skills = None
    fleet = None
    try:
        log.info("Step 1/4 — Deploying knowledge skills...")
        deployed_skills = deploy_all(client)

        log.info("Step 2/4 — Creating agent fleet...")
        fleet = create_fleet(
            client, args.site, args.org, args.repo, run_id,
            deployed_skills=deployed_skills,
        )

        log.info("Step 3/4 — Launching orchestrator session...")
        result = run_migration(
            client, fleet, args.site, args.org, args.repo,
            github_token=args.github_token,
            eds_token=args.eds_token,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        log.warning("Interrupted by user.")
        return 130
    except Exception:
        log.exception("Migration failed")
        return 1
    finally:
        log.info("Step 4/4 — Cleaning up resources...")
        if deployed_skills:
            teardown_skills(client, deployed_skills)
        if fleet:
            cleanup_fleet(client, fleet)

    log.info("=" * 60)
    log.info("Migration complete!")
    log.info("Session  : %s", result.session_id)
    log.info("Duration : %.1f seconds", result.duration_s)
    log.info("Events   : %d", result.events_received)
    log.info("Preview  : https://main--%s--%s.aem.page/", args.repo, args.org)
    log.info("da.live  : https://da.live/edit#/%s/%s", args.org, args.repo)
    log.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
