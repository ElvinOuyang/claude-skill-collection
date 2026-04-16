#!/bin/bash
# PreToolUse (Bash): before PR creation or push, verify branch is up-to-date
# with origin/{{TRUNK}}. Blocks if behind to prevent stale PRs.
TRUNK="${TRUNK:-master}"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only trigger on PR create or push commands
if ! echo "$COMMAND" | grep -qE '(^|[;&|]\s*)(gh pr create|git push)'; then
  exit 0
fi

# Don't block force-push (user explicitly chose it)
if echo "$COMMAND" | grep -qE 'git push.*(--force|-f)'; then
  exit 0
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Don't check when pushing trunk itself
if [ "$CURRENT_BRANCH" = "$TRUNK" ]; then
  exit 0
fi

# Fetch to get latest remote state
git fetch origin "$TRUNK" --quiet 2>/dev/null || exit 0

REMOTE_TRUNK=$(git rev-parse "origin/$TRUNK" 2>/dev/null) || exit 0
MERGE_BASE=$(git merge-base HEAD "origin/$TRUNK" 2>/dev/null) || exit 0

if [ "$MERGE_BASE" != "$REMOTE_TRUNK" ]; then
  BEHIND=$(git rev-list --count "$MERGE_BASE".."origin/$TRUNK" 2>/dev/null || echo "?")
  echo "{\"decision\": \"block\", \"reason\": \"Branch is ${BEHIND} commits behind origin/${TRUNK}. Rebase before pushing: git rebase origin/${TRUNK}. This prevents merge conflicts and stale PRs.\"}"
fi
