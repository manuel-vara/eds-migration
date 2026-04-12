"""Tier 1 validation script for Phase 5 — Configuration."""


def phase5_config() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase5","details":$msg}]'); }

# YAML files are valid
for f in helix-query.yaml helix-sitemap.yaml; do
  if [ -f "$f" ]; then
    python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null || add_error "Invalid YAML: $f"
  else
    add_error "Missing $f"
  fi
done

# robots.txt exists
[ -f robots.txt ] || add_error "Missing robots.txt"

# Redirects exist
[ -f redirects.json ] || add_error "Missing redirects.json"
if [ -f redirects.json ]; then
  jq empty redirects.json 2>/dev/null || add_error "redirects.json is invalid JSON"
fi

# No redirect loops
if [ -f redirects.json ]; then
  LOOPS=$(jq '[.data[] | select(.source == .destination)] | length' redirects.json 2>/dev/null || echo 0)
  [ "$LOOPS" -gt 0 ] && add_error "$LOOPS redirect loops detected"
fi

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
