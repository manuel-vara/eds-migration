"""Tier 1 validation script for Phase 3.5 — Pilot Migration."""


def phase35_pilot() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase3.5","details":$msg}]'); }

# Check status files exist for pilot pages
PILOT_COUNT=$(find status/ -name '*.json' -type f 2>/dev/null | wc -l)
[ "$PILOT_COUNT" -eq 0 ] && add_error "No status files found for pilot pages"

# Check each status file
for f in status/*.json; do
  [ -f "$f" ] || continue
  STATUS=$(jq -r '.status' "$f" 2>/dev/null)
  URL=$(jq -r '.url' "$f" 2>/dev/null)
  PREVIEW=$(jq -r '.previewUrl' "$f" 2>/dev/null)
  DIFF=$(jq -r '.visualDiffScore // 0' "$f" 2>/dev/null)

  [ "$STATUS" = "migrated" ] || [ "$STATUS" = "pilot" ] || add_error "Pilot page $URL has status: $STATUS"
  if [ -n "$PREVIEW" ] && [ "$PREVIEW" != "null" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$PREVIEW" 2>/dev/null || echo "000")
    [ "$HTTP_CODE" = "200" ] || add_error "Preview URL for $URL returned HTTP $HTTP_CODE"
  fi
  BELOW=$(echo "$DIFF < 0.8" | bc -l 2>/dev/null || echo 0)
  [ "$BELOW" = "1" ] && add_error "Visual diff score for $URL is $DIFF (below 0.8 threshold)"
done

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
