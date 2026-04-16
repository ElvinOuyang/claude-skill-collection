#!/bin/bash
# SessionStart: create or reset harness state file.
# - No file -> create with current branch
# - File exists, same branch -> leave alone (resumed session)
# - File exists, different branch -> recreate (new work)
STATE_FILE=".harness-state.json"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

create_state() {
  cat > "$STATE_FILE" << INIT
{
  "branch": "$CURRENT_BRANCH",
  "phases": {
    "pre_feature_complete": false,
    "graphify_queried": false,
    "plan_created": false,
    "plan_reviewed": false,
    "execution_skill_active": false,
    "test_gate_passed": false,
    "per_task_reviews_done": false,
    "smoke_tested": false,
    "spec_written": false,
    "docs_synced": false,
    "verified": false
  }
}
INIT
}

if [ ! -f "$STATE_FILE" ]; then
  create_state
else
  STORED_BRANCH=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('branch',''))" 2>/dev/null)
  if [ "$STORED_BRANCH" != "$CURRENT_BRANCH" ]; then
    create_state
  fi
fi
