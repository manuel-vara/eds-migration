"""
Tier 1 validation scripts for each phase.

These are the bash commands the orchestrator runs directly inside the
container after each worker step. They return structured error output
on failure.

Each function returns a shell script string that the orchestrator agent
should execute via its bash tool. Exit code 0 = pass, non-zero = fail.
The script prints JSON issues on failure.
"""

from eds_migrate.tier1.phase1_discovery import phase1_discovery
from eds_migrate.tier1.phase2a_scrape import phase2a_scrape
from eds_migrate.tier1.phase2b_inventory import phase2b_inventory
from eds_migrate.tier1.phase2c_blueprint import phase2c_blueprint
from eds_migrate.tier1.phase3_block_dev import phase3_block_dev
from eds_migrate.tier1.phase35_pilot import phase35_pilot
from eds_migrate.tier1.phase5_config import phase5_config
from eds_migrate.tier1.phase6_qa import phase6_qa

TIER1_SCRIPTS: dict[str, callable] = {
    "1-discover": phase1_discovery,
    "2a-scrape": phase2a_scrape,
    "2b-inventory": phase2b_inventory,
    "2c-blueprint": phase2c_blueprint,
    "3-build": phase3_block_dev,
    "3.5-pilot": phase35_pilot,
    "5-config": phase5_config,
    "6-qa": phase6_qa,
}
