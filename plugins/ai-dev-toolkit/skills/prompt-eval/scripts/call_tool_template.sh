#!/usr/bin/env bash
# call_tool.sh — Mock tool caller for prompt evals.
#
# Usage: bash call_tool.sh <tool_name> '<compact_json_params>' [outputs_dir]
#
# Logs every call to tool_calls.jsonl (in outputs_dir) so the grader can
# verify which tools were called with which parameters. Returns a realistic
# fake success response so the model can continue naturally.
#
# HOW TO CUSTOMIZE:
# 1. Copy this file into your skill's scripts/ directory as call_tool.sh
# 2. Add case blocks for your tools under the "Return fake response" section
# 3. Keep params as compact single-line JSON (avoids multi-line log entries)

TOOL="$1"
PARAMS="$2"
OUTPUTS_DIR="${3:-./outputs}"

mkdir -p "$OUTPUTS_DIR"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Log the call (compact single line per entry)
printf '{"tool":"%s","params":%s,"timestamp":"%s"}\n' "$TOOL" "$PARAMS" "$TIMESTAMP" \
  >> "$OUTPUTS_DIR/tool_calls.jsonl"

# Return a fake response so the model can continue naturally.
# Replace these with responses realistic for your domain.
case "$TOOL" in
  # ── Add your tool responses here ──────────────────────────────
  create_task)
    echo '{"id":"task-001","status":"pending","created_at":"'"$TIMESTAMP"'"}'
    ;;
  update_task|complete_task|assign_task)
    echo '{"id":"task-001","status":"updated","updated_at":"'"$TIMESTAMP"'"}'
    ;;
  list_tasks)
    echo '{"tasks":[]}'
    ;;
  schedule_reminder)
    echo '{"id":"nudge-001","type":"reminder","status":"pending"}'
    ;;
  schedule_clarify)
    echo '{"id":"nudge-002","type":"clarification","status":"pending"}'
    ;;
  cancel_nudge)
    echo '{"id":"nudge-001","status":"dismissed"}'
    ;;
  # ── Fallback ───────────────────────────────────────────────────
  *)
    echo '{"ok":true}'
    ;;
esac
