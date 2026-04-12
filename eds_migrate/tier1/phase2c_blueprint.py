"""Tier 1 validation script for Phase 2c — Blueprint."""


def phase2c_blueprint() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase2c","details":$msg}]'); }

if [ ! -f blueprint.json ]; then
  add_error "blueprint.json does not exist"
  echo "$ERRORS"; exit 1
fi
jq empty blueprint.json 2>/dev/null || { add_error "blueprint.json is invalid JSON"; echo "$ERRORS"; exit 1; }

# Every archetype in manifest has a blueprint
ARCHETYPES=$(jq -r '.archetypes[].name' manifest.json)
for arch in $ARCHETYPES; do
  HAS=$(jq -e --arg a "$arch" '.archetypeBlueprints[$a]' blueprint.json 2>/dev/null)
  [ -z "$HAS" ] || [ "$HAS" = "null" ] && add_error "Archetype '$arch' has no blueprint"
done

# Every block in blueprints exists in palette
PALETTE_NAMES=$(jq -r '[.blockPalette[].name] | .[]' blueprint.json)
BLUEPRINT_BLOCKS=$(jq -r '[.archetypeBlueprints[][].sections[].sequences[]] | map(split(" ")[0]) | unique | .[]' blueprint.json 2>/dev/null || true)
for block in $BLUEPRINT_BLOCKS; do
  [ "$block" = "default" ] && continue
  echo "$PALETTE_NAMES" | grep -q "^${block}$" || add_error "Block '$block' used in blueprint but not in palette"
done

# Every palette block has a contentModel
MISSING_MODEL=$(jq '[.blockPalette[] | select(.contentModel == null or .contentModel == "")] | length' blueprint.json)
[ "$MISSING_MODEL" -gt 0 ] && add_error "$MISSING_MODEL palette blocks missing contentModel"

# siteConventions exists
jq -e '.siteConventions' blueprint.json >/dev/null 2>&1 || add_error "Missing siteConventions"

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
