#!/bin/bash
# PostToolUse (Bash): after git commit, inject per-task review reminder.
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

if ! echo "$COMMAND" | grep -qE '(^|[;&|]\s*)(git commit|git -\S+ commit)'; then
  exit 0
fi

STATE_FILE=".harness-state.json"
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

REMAINING=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
incomplete = [k for k, v in state.get('phases', {}).items() if not v]
if incomplete:
    print(', '.join(incomplete))
" 2>/dev/null)

if [ -n "$REMAINING" ]; then
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Commit created. If this completes a plan task, ensure per-task review per CLAUDE.md step 7 before starting the next task. Remaining phases: $REMAINING\"}}"
fi
