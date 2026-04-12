"""Tier 1 validation script for Phase 1 — Discovery."""


def phase1_discovery() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase1","details":$msg}]'); }

# manifest.json exists and is valid JSON
if [ ! -f manifest.json ]; then
  add_error "manifest.json does not exist"
  echo "$ERRORS"; exit 1
fi
if ! jq empty manifest.json 2>/dev/null; then
  add_error "manifest.json is not valid JSON"
  echo "$ERRORS"; exit 1
fi

# Required top-level fields
for field in site pages archetypes navigation assets; do
  if ! jq -e ".$field" manifest.json >/dev/null 2>&1; then
    add_error "manifest.json missing required field: $field"
  fi
done

# No duplicate URLs
DUPES=$(jq '[.pages[].url] | group_by(.) | map(select(length > 1)) | length' manifest.json)
[ "$DUPES" -gt 0 ] && add_error "$DUPES duplicate URLs found"

# Every page has an archetype
NULL_ARCH=$(jq '[.pages[] | select(.archetype == null or .archetype == "")] | length' manifest.json)
[ "$NULL_ARCH" -gt 0 ] && add_error "$NULL_ARCH pages missing archetype"

# Every archetype has sample URLs
EMPTY_SAMPLES=$(jq '[.archetypes[] | select(.sampleUrls == null or (.sampleUrls | length) == 0)] | length' manifest.json)
[ "$EMPTY_SAMPLES" -gt 0 ] && add_error "$EMPTY_SAMPLES archetypes have no sample URLs"

# Navigation is non-empty
HEADER_LEN=$(jq '.navigation.header | length' manifest.json)
FOOTER_LEN=$(jq '.navigation.footer | length' manifest.json)
[ "$HEADER_LEN" -eq 0 ] && [ "$FOOTER_LEN" -eq 0 ] && add_error "Navigation is completely empty (no header or footer links)"

# Page count plausibility (just report it)
PAGE_COUNT=$(jq '.pages | length' manifest.json)
echo "INFO: $PAGE_COUNT pages discovered"

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
