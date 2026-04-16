#!/bin/bash
# PreToolUse (Edit/Write): inject harness debt as additionalContext.
# Shows remaining phases and directs Claude to CLAUDE.md.
STATE_FILE=".harness-state.json"
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

DEBT=$(python3 -c "
import json, sys
with open('$STATE_FILE') as f:
    state = json.load(f)
phases = state.get('phases', {})
incomplete = [k for k, v in phases.items() if not v]
if not incomplete:
    sys.exit(0)
done = len(phases) - len(incomplete)
print(f'HARNESS: {done}/{len(phases)} phases complete. Remaining: {', '.join(incomplete)}. Consult CLAUDE.md Mandatory Workflow before proceeding.')
" 2>/dev/null)

if [ -n "$DEBT" ]; then
  ESCAPED=$(echo "$DEBT" | sed 's/"/\\"/g')
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"$ESCAPED\"}}"
fi
