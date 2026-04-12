"""Tier 1 validation script for Phase 2a — Scrape Samples."""


def phase2a_scrape() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase2a","details":$msg}]'); }

if [ ! -d analysis ]; then
  add_error "analysis/ directory does not exist"
  echo "$ERRORS"; exit 1
fi

ARCHETYPES=$(jq -r '.archetypes[].name' manifest.json)
for arch in $ARCHETYPES; do
  DIR_COUNT=$(find "analysis/$arch" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
  if [ "$DIR_COUNT" -lt 2 ]; then
    add_error "Archetype '$arch' has only $DIR_COUNT scraped pages (need ≥ 2)"
  fi
  for page_dir in analysis/"$arch"/*/; do
    [ -d "$page_dir" ] || continue
    for file in screenshot.png metadata.json cleaned.html; do
      [ -f "$page_dir$file" ] || add_error "Missing $file in $page_dir"
    done
    if [ -f "${page_dir}metadata.json" ]; then
      jq empty "${page_dir}metadata.json" 2>/dev/null || add_error "Invalid JSON: ${page_dir}metadata.json"
    fi
    if [ -f "${page_dir}cleaned.html" ]; then
      [ -s "${page_dir}cleaned.html" ] || add_error "Empty cleaned.html in $page_dir"
    fi
  done
done

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
