"""Tier 1 validation script for Phase 6 — Integration QA."""


def phase6_qa() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase6","details":$msg}]'); }

# QA report exists and is valid
if [ ! -f qa-report.json ]; then
  add_error "qa-report.json does not exist"
  echo "$ERRORS"; exit 1
fi
jq empty qa-report.json 2>/dev/null || { add_error "qa-report.json is invalid JSON"; echo "$ERRORS"; exit 1; }

# Required fields
jq -e '.summary' qa-report.json >/dev/null 2>&1 || add_error "Missing summary in qa-report.json"
jq -e '.pages' qa-report.json >/dev/null 2>&1 || add_error "Missing pages array in qa-report.json"

# All migrated pages have QA entries
MIGRATED=$(find status/ -name '*.json' -type f -exec jq -r 'select(.status=="migrated") | .url' {} \; 2>/dev/null | wc -l)
QA_ENTRIES=$(jq '.pages | length' qa-report.json)
[ "$QA_ENTRIES" -lt "$MIGRATED" ] && add_error "QA report has $QA_ENTRIES entries but $MIGRATED pages were migrated"

# No zero Lighthouse scores
ZERO_LH=$(jq '[.pages[] | select(.lighthouse.performance == 0 or .lighthouse.performance == null)] | length' qa-report.json 2>/dev/null || echo 0)
[ "$ZERO_LH" -gt 0 ] && add_error "$ZERO_LH pages have zero/null Lighthouse performance"

# Average visual diff
AVG_DIFF=$(jq '[.pages[].visualDiffScore // 0] | add / length' qa-report.json 2>/dev/null || echo 0)
BELOW=$(echo "$AVG_DIFF < 0.85" | bc -l 2>/dev/null || echo 0)
[ "$BELOW" = "1" ] && add_error "Average visual diff score is $AVG_DIFF (below 0.85)"

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
