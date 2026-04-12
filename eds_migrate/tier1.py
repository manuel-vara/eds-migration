"""
Tier 1 validation scripts for each phase.

These are the bash commands the orchestrator runs directly inside the
container after each worker step. They return structured error output
on failure.

Each function returns a shell script string that the orchestrator agent
should execute via its bash tool. Exit code 0 = pass, non-zero = fail.
The script prints JSON issues on failure.
"""


def phase1_discovery() -> str:
    """Tier 1 checks for Phase 1 — Discovery."""
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


def phase2a_scrape() -> str:
    """Tier 1 checks for Phase 2a — Scrape Samples."""
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


def phase2b_inventory() -> str:
    """Tier 1 checks for Phase 2b — Block Inventory."""
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


def phase2c_blueprint() -> str:
    """Tier 1 checks for Phase 2c — Blueprint."""
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


def phase3_block_dev() -> str:
    """Tier 1 checks for Phase 3 — Block Development."""
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


def phase35_pilot() -> str:
    """Tier 1 checks for Phase 3.5 — Pilot Migration."""
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


def phase5_config() -> str:
    """Tier 1 checks for Phase 5 — Configuration."""
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


def phase6_qa() -> str:
    """Tier 1 checks for Phase 6 — Integration QA."""
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
