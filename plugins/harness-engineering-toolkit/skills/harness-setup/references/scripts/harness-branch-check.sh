#!/bin/bash
# PostToolUse (Bash): after branch creation, check that origin/{{TRUNK}} is fresh.
# Advisory only -- injects a warning if local trunk is behind remote.
TRUNK="${TRUNK:-master}"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only trigger on branch creation commands
if ! echo "$COMMAND" | grep -qE '(^|[;&|]\s*)git (checkout -b|branch |switch -c)'; then
  exit 0
fi

# Check if the new branch was based on origin/trunk
# Fetch silently to compare
git fetch origin "$TRUNK" --quiet 2>/dev/null || exit 0

LOCAL_TRUNK=$(git rev-parse "$TRUNK" 2>/dev/null || echo "none")
REMOTE_TRUNK=$(git rev-parse "origin/$TRUNK" 2>/dev/null || echo "none")

if [ "$LOCAL_TRUNK" = "none" ] || [ "$REMOTE_TRUNK" = "none" ]; then
  exit 0
fi

if [ "$LOCAL_TRUNK" != "$REMOTE_TRUNK" ]; then
  BEHIND=$(git rev-list --count "$TRUNK".."origin/$TRUNK" 2>/dev/null || echo "?")
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"HARNESS: local ${TRUNK} is ${BEHIND} commits behind origin/${TRUNK}. The new branch may be based on stale code. Run: git checkout ${TRUNK} && git pull origin ${TRUNK}, then recreate the branch from ${TRUNK}. See ~/.claude/CLAUDE.md Git Branching.\"}}"
fi
