---
name: harness-extend
description: >
  Add new enforcement infrastructure to an existing Claude Code harness -- phases, scopes, hooks, or slash commands. Use when the user says "add harness phase", "add new scope", "new enforcement hook", "add stop gate check", "add slash command to harness", "extend harness", "new harness hook", "add a new check", "new workflow step", or needs to modify the harness state machine. Also use when adding a blocking or advisory hook script, creating a new stop gate with loop detection, or changing which phases are required for a scope. This skill handles the multi-file update coordination that makes harness changes error-prone.
---

# Harness Extend

Add new enforcement infrastructure (phases, scopes, hooks, commands) to an existing harness. Each operation requires updating multiple files in coordination -- this skill provides the exhaustive checklists.

## Prerequisites

A harness system must already exist. Verify:
- `.claude/scripts/harness-stop-gate.sh` (the stop gate with REQUIRED dict)
- `.claude/scripts/harness-init.sh` (state file initialization)
- `.claude/HARNESS.md` (architecture docs)
- `.claude/settings.json` (hook wiring)

## Operation 1: Add a new phase

A phase is a boolean in `.harness-state.json` that a slash command or skill marks true after completing a workflow step.

**Ask:**
1. What does this phase verify? (e.g., "security review completed")
2. What scope(s) require it? (feature, patch, design, or multiple)
3. What command or skill marks it complete?

**Full update checklist:**

| # | File | Change |
|---|------|--------|
| 1 | `.claude/scripts/harness-init.sh` | Add `"new_phase": false` to the initial state JSON |
| 2 | `.claude/scripts/harness-stop-gate.sh` | Add `"new_phase"` to the REQUIRED list for the appropriate scope(s) in the Python block |
| 3 | `.claude/commands/verify.md` | Add the new phase to the adversarial subagent's phase verification list with verification criteria |
| 4 | `.claude/commands/evaluate-scope.md` | Update scope descriptions if the new phase changes what a scope means |
| 5 | `.claude/HARNESS.md` | Add to: state file example, scope table (required phases column), slash command table (if new command), "How phases get marked" section |
| 6 | `CLAUDE.md` | Update mandatory workflow steps if the new phase maps to a workflow step |
| 7 | Marking command | Create or update the slash command that sets this phase to true |

**After applying:** Verify the phase name is spelled identically in all 6 locations. A typo in one place means the phase is never checked or never marked.

## Operation 2: Add a new scope

A scope determines which phases are required based on what files changed on the branch.

**Ask:**
1. What triggers this scope? (what file patterns)
2. What phases does it require?
3. Can it be used as a scope_override? (only narrowing overrides are safe)

**Full update checklist:**

| # | File | Change |
|---|------|--------|
| 1 | `.claude/scripts/harness-stop-gate.sh` | Add to REQUIRED dict with phase list. Add scope inference rule (file pattern matching after existing scope checks). |
| 2 | `.claude/commands/evaluate-scope.md` | Add new scope as an option with description of when to use it |
| 3 | `.claude/commands/test-gate.md` | If the scope has different test requirements, add scope-conditional logic |
| 4 | `.claude/commands/smoke-test.md` | If the scope has different smoke test requirements, add scope-conditional logic |
| 5 | `.claude/HARNESS.md` | Add to scope table. Update scope override docs if the new scope is overrideable. |

**Scope inference order matters.** The stop gate checks scopes top-to-bottom: most specific first (feature), then broader (patch), then docs-only (design). Insert the new scope at the right position.

**Narrowing-only rule:** `scope_override` can narrow (feature -> patch) but never widen (patch -> feature). If the new scope should be overrideable, add it to the validation list in the stop gate.

## Operation 3: Add a new hook script

**Ask:**
1. Which hook point? (SessionStart, PreToolUse, PostToolUse, Stop)
2. Blocking or advisory?
3. What matcher? (for PreToolUse/PostToolUse: which tool names to match, e.g., "Edit|Write", "Bash")

**Hook patterns by type:**

### SessionStart (runs once when session begins)

```bash
#!/bin/bash
# SessionStart: [description]
# Runs once per session. Good for initialization, state setup, environment checks.

# Your initialization logic here
# Example: create a state file if it doesn't exist
STATE_FILE=".my-state.json"
if [ ! -f "$STATE_FILE" ]; then
  echo '{"initialized": true}' > "$STATE_FILE"
fi
```

SessionStart hooks have no input and no blocking capability. They run silently. Use for state file creation, environment validation, or one-time setup.

### PreToolUse -- Advisory (informational, never blocks)

```bash
#!/bin/bash
# PreToolUse: [description]
STATE_FILE=".harness-state.json"
if [ ! -f "$STATE_FILE" ]; then exit 0; fi

# Your check logic here
RESULT="your advisory message"

if [ -n "$RESULT" ]; then
  ESCAPED=$(echo "$RESULT" | sed 's/"/\\"/g')
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"additionalContext\":\"$ESCAPED\"}}"
fi
```

### PreToolUse -- Blocking (gates a specific action)

```bash
#!/bin/bash
# PreToolUse: [description]
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only trigger on specific commands
if ! echo "$COMMAND" | grep -qE 'pattern-to-match'; then exit 0; fi

# Your check logic -- MUST have an escape condition
if [ "$SHOULD_BLOCK" = "true" ]; then
  echo "{\"decision\": \"block\", \"reason\": \"Explain why and how to fix.\"}"
fi
```

**Rule:** Blocking PreToolUse hooks MUST have an escape condition. Never block unconditionally.

### PostToolUse -- Advisory (fires after, never blocks)

```bash
#!/bin/bash
# PostToolUse: [description]
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)

# Only trigger on specific commands
if ! echo "$COMMAND" | grep -qE 'pattern-to-match'; then exit 0; fi

# Your advisory logic
echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PostToolUse\",\"additionalContext\":\"Your message\"}}"
```

### Stop -- Blocking (MUST have loop detection)

**CRITICAL: Stop hooks that block MUST use hash-based loop detection.** A blocking stop hook without loop detection creates an infinite loop: block -> user input -> Claude responds -> stop fires again -> block -> ...

```bash
#!/bin/bash
# Stop: [description]
# Loop breaker: hash-based with auto-release on repeat
MAX_BLOCKS=1
COOLDOWN_SECS=120
REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
LOOP_KEY="/tmp/my-hook-$(printf '%s' "$REPO_PATH" | cksum | cut -d' ' -f1)"

# Your check logic -- compute RESULT (empty = pass, non-empty = block reason)
RESULT="your block reason or empty"

if [ -z "$RESULT" ]; then
  rm -f "$LOOP_KEY"
  exit 0
fi

# --- Loop detection (DO NOT MODIFY) ---
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
  exit 0  # Auto-release: same reason repeated without progress
fi
# --- End loop detection ---

ESCAPED=$(printf '%s' "$RESULT" | sed 's/"/\\"/g')
echo "{\"decision\": \"block\", \"reason\": \"${ESCAPED}\"}"
```

**After creating the script:**

| # | File | Change |
|---|------|--------|
| 1 | New script | Create at `.claude/scripts/[name].sh` and `chmod +x` |
| 2 | `.claude/settings.json` | Add hook entry under the appropriate hook point with correct matcher |
| 3 | `.claude/HARNESS.md` | Add to architecture diagram and hook documentation |

## Operation 4: Add a slash command

**Ask:**
1. What does the command do?
2. What phase does it mark complete? (or none for read-only commands)
3. What pattern? (subagent dispatch, scan-and-report, or diff-preview-apply)

**Command patterns:**

### Subagent dispatch (like `/verify`, `/test-gate`)

The command dispatches a fresh-context subagent with an adversarial prompt. The subagent has no session context, so the prompt must be self-contained with:
- What files to read
- What commands to run
- What criteria to check
- How to report (PASS/FAIL with evidence)

The command marks the phase only if the subagent reports PASS.

### Scan and report (like `/pre-feature`, `/audit-docs`)

The command reads files directly, summarizes findings, and reports. Good for preflight reading and audits.

### Diff-preview-apply (like `/sync-docs`)

The command analyzes what needs updating, shows a diff preview, waits for approval, then applies. Good for doc maintenance.

**After creating the command:**

| # | File | Change |
|---|------|--------|
| 1 | New command | Create at `.claude/commands/[name].md` |
| 2 | `.claude/HARNESS.md` | Add to slash command table |
| 3 | Phase (if applicable) | Ensure the phase exists in `harness-init.sh` and `harness-stop-gate.sh` |

## After every operation

Run a consistency check:

```bash
# Extract phase names from init (the canonical list)
INIT_PHASES=$(python3 -c "import json,re; t=open('.claude/scripts/harness-init.sh').read(); m=re.search(r'\{.*\}', t, re.DOTALL); d=json.loads(m.group()); print('\n'.join(sorted(d.get('phases',{}).keys())))")

# Extract phase names from stop gate REQUIRED dict
GATE_PHASES=$(python3 -c "
import re
t = open('.claude/scripts/harness-stop-gate.sh').read()
phases = set(re.findall(r'\"([a-z_]+)\"', t.split('REQUIRED')[1].split('scope = ')[0]))
print('\n'.join(sorted(phases)))
")

# Compare -- phases in gate but not in init are bugs
echo "=== In stop gate but NOT in init (will deadlock) ==="
comm -23 <(echo "$GATE_PHASES") <(echo "$INIT_PHASES")
echo "=== In init but NOT in stop gate (orphaned, harmless) ==="
comm -13 <(echo "$GATE_PHASES") <(echo "$INIT_PHASES")

# Check settings.json hook structure is valid JSON
python3 -c "import json; json.load(open('.claude/settings.json')); print('settings.json: Valid')"

# Check all scripts are executable
echo "=== Script permissions ==="
ls -la .claude/scripts/harness-*.sh | awk '{print $1, $NF}'
```

Report any inconsistencies found. Phases in the stop gate but not in init will cause a deadlock (phase can never be checked). Fix by adding the missing phase to `harness-init.sh`.
