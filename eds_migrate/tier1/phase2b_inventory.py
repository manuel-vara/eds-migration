"""Tier 1 validation script for Phase 2b — Block Inventory."""


def phase2b_inventory() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase2b","details":$msg}]'); }

if [ ! -f blueprint.json ]; then
  add_error "blueprint.json does not exist yet (expected partial after 2b)"
  echo "$ERRORS"; exit 1
fi

PALETTE_LEN=$(jq '.blockPalette | length' blueprint.json 2>/dev/null || echo 0)
[ "$PALETTE_LEN" -eq 0 ] && add_error "Block palette is empty"

# Check for duplicate block names
DUPE_BLOCKS=$(jq '[.blockPalette[].name] | group_by(.) | map(select(length > 1)) | length' blueprint.json)
[ "$DUPE_BLOCKS" -gt 0 ] && add_error "$DUPE_BLOCKS duplicate block names in palette"

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
