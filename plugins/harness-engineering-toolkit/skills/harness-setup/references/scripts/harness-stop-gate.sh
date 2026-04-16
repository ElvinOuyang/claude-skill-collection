#!/bin/bash
# Stop gate: infer scope from git diff, check required phases, block if incomplete.
#
# Loop breaker: tracks consecutive identical blocks. Two tiers:
#   1. First block: combined message (missing phases + /evaluate-scope hint)
#   2. Repeat with no progress: auto-release (silence for mid-session chat)
STATE_FILE=".harness-state.json"
MAX_BLOCKS=1
COOLDOWN_SECS=120

# --- Configurable parameters (defaults work out of the box) ---
TRUNK="${TRUNK:-master}"
SOURCE_EXTS="${SOURCE_EXTS:-swift|ts|tsx|py|go|rs|java|kt|rb|sql}"

# --- Detect trunk branch ---
if ! git rev-parse --verify "$TRUNK" &>/dev/null; then
  # Fallback: try the other common trunk name
  if [ "$TRUNK" = "master" ]; then
    TRUNK="main"
  else
    TRUNK="master"
  fi
  if ! git rev-parse --verify "$TRUNK" &>/dev/null; then
    exit 0
  fi
fi

# Repo-unique loop counter (cksum of full repo path)
REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
LOOP_KEY="/tmp/harness-stop-$(printf '%s' "$REPO_PATH" | cksum | cut -d' ' -f1)"

# --- Scope inference ---
BASE=$(git merge-base HEAD "$TRUNK" 2>/dev/null) || { rm -f "$LOOP_KEY"; exit 0; }
CHANGED=$(git diff --name-only "$BASE"..HEAD 2>/dev/null) || { rm -f "$LOOP_KEY"; exit 0; }
if [ -z "$CHANGED" ]; then
  rm -f "$LOOP_KEY"
  exit 0
fi

# Build grep pattern from SOURCE_EXTS: "swift|ts|tsx" -> "\.(swift|ts|tsx)$"
SOURCE_PATTERN="\.(${SOURCE_EXTS})$"

HAS_NEW_SOURCE=$(git diff --diff-filter=A --name-only "$BASE"..HEAD 2>/dev/null | grep -cE "$SOURCE_PATTERN" || true)
HAS_MOD_SOURCE=$(printf '%s\n' "$CHANGED" | grep -cE '\.('"${SOURCE_EXTS}"'|sql|toml|yml|plist)$' || true)
HAS_DOCS=$(printf '%s\n' "$CHANGED" | grep -c '^docs/' || true)

# Scope override from state file (narrowing only: patch or design)
SCOPE_OVERRIDE=""
if [ -f "$STATE_FILE" ]; then
  SCOPE_OVERRIDE=$(python3 << 'PYEOF'
import json
try:
    with open(".harness-state.json") as f:
        v = json.load(f).get("scope_override", "")
    if v in ("patch", "design"):
        print(v, end="")
except Exception:
    pass
PYEOF
  )
fi

if [ -n "$SCOPE_OVERRIDE" ]; then
  SCOPE="$SCOPE_OVERRIDE"
elif [ "$HAS_NEW_SOURCE" -gt 0 ]; then
  SCOPE="feature"
elif [ "$HAS_MOD_SOURCE" -gt 0 ]; then
  SCOPE="patch"
elif [ "$HAS_DOCS" -gt 0 ]; then
  SCOPE="design"
else
  rm -f "$LOOP_KEY"
  exit 0
fi

# --- No state file: legacy doc check ---
if [ ! -f "$STATE_FILE" ]; then
  if { [ "$SCOPE" = "feature" ] || [ "$SCOPE" = "patch" ]; } && [ "$HAS_DOCS" -eq 0 ]; then
    echo '{"decision": "block", "reason": "Source files changed but no docs updated. Run /sync-docs before finishing. Consult CLAUDE.md Mandatory Workflow."}'
  fi
  exit 0
fi

# --- Check required phases (data via env vars, not string interpolation) ---
RESULT=$(SCOPE="$SCOPE" STATE_FILE="$STATE_FILE" python3 << 'PYEOF'
import json, os, sys

REQUIRED = {
    "feature": ["pre_feature_complete", "graphify_queried", "plan_created", "plan_reviewed",
                "execution_skill_active", "per_task_reviews_done", "smoke_tested",
                "docs_synced", "verified"],
    "design": ["pre_feature_complete", "graphify_queried", "spec_written",
               "docs_synced", "verified"],
    "patch": ["test_gate_passed", "smoke_tested", "docs_synced", "verified"],
}

scope = os.environ["SCOPE"]
state_file = os.environ["STATE_FILE"]
required = REQUIRED.get(scope, ["verified"])

try:
    with open(state_file) as f:
        state = json.load(f)
except Exception as e:
    # Fail closed: unreadable state file should block
    print("State file error: {}. Cannot verify phases.".format(e))
    sys.exit(0)

phases = state.get("phases", {})
missing = [p for p in required if not phases.get(p, False)]
if missing:
    print("Scope: {}. Incomplete: {}.".format(scope, ", ".join(missing)))
PYEOF
)

# All phases complete
if [ -z "$RESULT" ]; then
  rm -f "$LOOP_KEY"
  exit 0
fi

# --- Loop detection ---
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
  # Auto-release: same reason repeated without progress. Keep the counter
  # so subsequent stops within the cooldown also auto-release (no noise
  # during mid-session chat). Resets when: cooldown expires (120s gap),
  # or a phase is completed (hash changes).
  exit 0
fi

# Combined block: inform about missing phases + offer scope evaluation
ESCAPED=$(printf '%s' "$RESULT" | sed 's/"/\\"/g')
echo "{\"decision\": \"block\", \"reason\": \"${ESCAPED} Run /evaluate-scope if scope doesn't match session intent, or /verify when phases are complete.\"}"
