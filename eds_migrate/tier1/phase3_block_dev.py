"""Tier 1 validation script for Phase 3 — Block Development."""


def phase3_block_dev() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

ERRORS='[]'
add_error() { ERRORS=$(echo "$ERRORS" | jq --arg msg "$1" '. + [{"severity":"high","criterion":"phase3","details":$msg}]'); }

# Every palette block has a directory
PALETTE_BLOCKS=$(jq -r '.blockPalette[].name' blueprint.json)
for block in $PALETTE_BLOCKS; do
  [ -d "blocks/$block" ] || add_error "Missing blocks/$block/ directory"
  [ -f "blocks/$block/$block.js" ] || [ -f "blocks/$block/${block}.js" ] || add_error "Missing JS for block $block"
  [ -f "blocks/$block/$block.css" ] || [ -f "blocks/$block/${block}.css" ] || add_error "Missing CSS for block $block"
done

# Core files exist
for f in head.html fstab.yaml scripts/aem.js scripts/scripts.js styles/styles.css; do
  [ -f "$f" ] || add_error "Missing required file: $f"
done

# Lint
if [ -f package.json ] && jq -e '.scripts.lint' package.json >/dev/null 2>&1; then
  if ! npm run lint 2>&1; then
    add_error "npm run lint failed"
  fi
fi

# No framework imports
if grep -rE 'from\s+["\x27](react|vue|@angular|jquery|tailwind)' blocks/ scripts/ 2>/dev/null; then
  add_error "External framework imports detected"
fi

# fstab.yaml points to da.live
if [ -f fstab.yaml ]; then
  grep -q 'content.da.live' fstab.yaml || add_error "fstab.yaml does not point to da.live"
fi

if [ "$(echo "$ERRORS" | jq 'length')" -gt 0 ]; then
  echo "$ERRORS"; exit 1
fi
echo '{"verdict":"PASS","issues":[]}'; exit 0
"""
