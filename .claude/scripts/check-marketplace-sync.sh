#!/bin/bash
# Marketplace sync Stop hook: nudge once per drift state between
# plugins/ on disk and .claude-plugin/marketplace.json.
# Spec: docs/superpowers/specs/2026-04-16-marketplace-sync-hook-design.md

# --- Tooling guards (advisory hook: never block on its own bugs) ---
if ! command -v jq >/dev/null 2>&1; then
  echo "[marketplace-sync] error: jq not found" >&2
  exit 0
fi
if [ ! -f ".claude-plugin/marketplace.json" ]; then
  echo "[marketplace-sync] error: .claude-plugin/marketplace.json not found" >&2
  exit 0
fi

# --- List on-disk plugins ---
on_disk=$(find plugins -mindepth 3 -maxdepth 3 \
  -path '*/.claude-plugin/plugin.json' -type f 2>/dev/null \
  | sed -E 's|^plugins/||; s|/\.claude-plugin/plugin\.json$||' \
  | sort -u)

# --- List registered plugins ---
registered=$(jq -r '.plugins[].name' .claude-plugin/marketplace.json 2>/dev/null | sort -u)

# --- Set diff with empty-input guard ---
diff_unique() {
  local left="$1" right="$2" flag="$3"
  if [ -z "$left" ]; then echo ""; return; fi
  comm "$flag" <(printf '%s\n' "$left") <(printf '%s\n' "${right:- }")
}
unregistered=$(diff_unique "$on_disk" "$registered" -23)
orphaned=$(diff_unique "$registered" "$on_disk" -23)

# --- Build single-line reason ---
RESULT=""
if [ -n "$unregistered" ] || [ -n "$orphaned" ]; then
  parts="[marketplace-sync] Drift between plugins/ and .claude-plugin/marketplace.json."
  [ -n "$unregistered" ] && parts="$parts Unregistered on disk: $(echo "$unregistered" | paste -sd, -)."
  [ -n "$orphaned" ]     && parts="$parts Orphaned in manifest: $(echo "$orphaned" | paste -sd, -)."
  parts="$parts Fix: edit .claude-plugin/marketplace.json (read plugins/<name>/.claude-plugin/plugin.json for metadata). One-time nudge per drift state."
  RESULT="$parts"
fi

# --- Harness loop-detection (verbatim from harness-extend reference) ---
MAX_BLOCKS=1
COOLDOWN_SECS=120
REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
LOOP_KEY="/tmp/marketplace-sync-$(printf '%s' "$REPO_PATH" | cksum | cut -d' ' -f1)"

if [ -z "$RESULT" ]; then
  rm -f "$LOOP_KEY"
  exit 0
fi

REASON_HASH=$(printf '%s' "$RESULT" | cksum | cut -d' ' -f1)
BLOCK_COUNT=0
if [ -f "$LOOP_KEY" ]; then
  STORED_HASH=$(sed -n '1p' "$LOOP_KEY" 2>/dev/null || echo "")
  STORED_COUNT=$(sed -n '2p' "$LOOP_KEY" 2>/dev/null || echo "0")
  STORED_TS=$(sed -n '3p' "$LOOP_KEY" 2>/dev/null || echo "0")
  NOW=$(date +%s)
  if [ "$REASON_HASH" = "$STORED_HASH" ] && [ $((NOW - STORED_TS)) -le "$COOLDOWN_SECS" ]; then
    BLOCK_COUNT=$STORED_COUNT
  fi
fi
BLOCK_COUNT=$((BLOCK_COUNT + 1))
printf '%s\n%s\n%s\n' "$REASON_HASH" "$BLOCK_COUNT" "$(date +%s)" > "$LOOP_KEY"
if [ "$BLOCK_COUNT" -gt "$MAX_BLOCKS" ]; then
  exit 0   # auto-release: same drift repeated within cooldown
fi

ESCAPED=$(printf '%s' "$RESULT" | sed 's/"/\\"/g')
echo "{\"decision\": \"block\", \"reason\": \"${ESCAPED}\"}"
