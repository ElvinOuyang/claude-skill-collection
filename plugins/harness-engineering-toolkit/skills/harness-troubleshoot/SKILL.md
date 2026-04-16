---
name: harness-troubleshoot
description: >
  Diagnose and fix Claude Code harness enforcement issues. Use when the harness is stuck, stop hook loops infinitely, scope is wrong, state file is stale, phases won't complete, or hooks aren't firing. Also use when the user says "can't stop", "harness keeps blocking", "harness error", "phases won't mark complete", "harness won't let me stop", "stuck in a loop", "wrong scope detected", or "hook not working". Use this skill proactively whenever a harness-related problem is encountered during development.
---

# Harness Troubleshoot

Diagnose and fix common harness enforcement problems via a structured decision tree.

## Prerequisites

A harness system must already exist in the project (`.claude/scripts/harness-*.sh`, `.claude/commands/`, `.harness-state.json`). If no harness exists, use `harness-setup` instead.

## Decision Tree

When invoked, determine which problem the user is experiencing and follow the corresponding diagnosis path.

### Problem 1: Stop hook infinite loop

**Symptoms:** Claude can't stop. Same block message repeats endlessly. Session is stuck.

**Diagnosis:**
```bash
# Check the loop counter file
REPO_PATH=$(git rev-parse --show-toplevel)
LOOP_KEY="/tmp/harness-stop-$(printf '%s' "$REPO_PATH" | cksum | cut -d' ' -f1)"
cat "$LOOP_KEY" 2>/dev/null || echo "No counter file"
```

The counter file has 3 lines: hash, count, timestamp. Check:
- Is the hash changing between stops? (progress is happening but phases aren't completing)
- Is the count > 1 but auto-release not firing? (loop detection is broken)
- Is the timestamp within 120s of now? (cooldown is active)

**Fixes:**
- If hash is stuck (same hash, count climbing): the stop gate is blocking on the same phases repeatedly. Run `/evaluate-scope` to check if scope is wrong, or complete the missing phases.
- If auto-release isn't firing: check `MAX_BLOCKS` in `harness-stop-gate.sh` (should be 1). Check that the `BLOCK_COUNT -gt MAX_BLOCKS` comparison uses `-gt` not `-ge`.
- If counter file doesn't exist: the stop gate script may be failing before reaching loop detection. Run it manually: `bash .claude/scripts/harness-stop-gate.sh`
- Nuclear option: `rm "$LOOP_KEY"` to reset the counter. This gives one fresh block, then auto-release resumes.

**The correct loop detection pattern** (for reference when fixing):
```bash
REASON_HASH=$(printf '%s' "$RESULT" | cksum | cut -d' ' -f1)
BLOCK_COUNT=0
if [ -f "$LOOP_KEY" ]; then
  STORED_HASH=$(sed -n '1p' "$LOOP_KEY")
  STORED_COUNT=$(sed -n '2p' "$LOOP_KEY" || echo "0")
  STORED_TS=$(sed -n '3p' "$LOOP_KEY" || echo "0")
  NOW=$(date +%s)
  if [ "$REASON_HASH" = "$STORED_HASH" ] && [ $((NOW - STORED_TS)) -le 120 ]; then
    BLOCK_COUNT=$STORED_COUNT
  fi
fi
BLOCK_COUNT=$((BLOCK_COUNT + 1))
printf '%s\n%s\n%s\n' "$REASON_HASH" "$BLOCK_COUNT" "$(date +%s)" > "$LOOP_KEY"
if [ "$BLOCK_COUNT" -gt 1 ]; then
  exit 0  # Auto-release
fi
```

### Problem 2: Scope mismatch

**Symptoms:** Harness demands feature-level phases for a bug fix. Or skips enforcement for a real feature.

**Diagnosis:**
```bash
# Read the project's configured trunk and source extensions from the stop gate
TRUNK=$(grep -oP 'TRUNK="\$\{TRUNK:-\K[^}]+' .claude/scripts/harness-stop-gate.sh 2>/dev/null || echo "master")
SOURCE_EXTS=$(grep -oP 'SOURCE_EXTS="\$\{SOURCE_EXTS:-\K[^}]+' .claude/scripts/harness-stop-gate.sh 2>/dev/null || echo "swift|ts|tsx|py|go|rs|java|kt|rb|sql")

# Run the same scope inference the stop gate uses
BASE=$(git merge-base HEAD "$TRUNK")
# New source files = feature scope
git diff --diff-filter=A --name-only "$BASE"..HEAD | grep -cE "\.($SOURCE_EXTS)$"
# Modified source files = patch scope
git diff --name-only "$BASE"..HEAD | grep -cE "\.($SOURCE_EXTS|sql|toml|yml|plist)$"
# Docs only = design scope
git diff --name-only "$BASE"..HEAD | grep -c '^docs/'
# Check current override
python3 -c "import json; print(json.load(open('.harness-state.json')).get('scope_override', 'none'))"
```

**Fixes:**
- Set `scope_override` in `.harness-state.json` to narrow the scope:
  ```python
  import json
  s = json.load(open('.harness-state.json'))
  s['scope_override'] = 'patch'  # or 'design'
  json.dump(s, open('.harness-state.json', 'w'), indent=2)
  ```
- Narrowing only: `feature` -> `patch` or `design` is allowed. Widening (`patch` -> `feature`) is blocked to prevent accidental enforcement bypass.
- If the inferred scope keeps being wrong, check that source file extensions in `harness-stop-gate.sh` match the project's language.

### Problem 3: Stale state file

**Symptoms:** State file references wrong branch. Phases from a previous session are carried over. Branch field doesn't match current branch.

**Diagnosis:**
```bash
python3 -c "import json; print(json.load(open('.harness-state.json')).get('branch', 'unknown'))"
git rev-parse --abbrev-ref HEAD
```

**Fixes:**
- Delete and let SessionStart recreate: `rm .harness-state.json`
- Or manually reset: run `bash .claude/scripts/harness-init.sh`
- If this keeps happening, check that the SessionStart hook is wired in `.claude/settings.json`

### Problem 4: Phase won't mark complete

**Symptoms:** Ran `/verify` but `verified` is still false. Or `/sync-docs` didn't set `docs_synced`.

**Diagnosis:**
```bash
# Check current phase state
python3 -c "import json; s=json.load(open('.harness-state.json')); [print(f'{k}: {v}') for k,v in s.get('phases',{}).items()]"
# Read the command that should mark it
cat .claude/commands/verify.md  # or whichever command
```

**Root causes:**
- The command found issues and reported them WITHOUT marking the phase. This is correct behavior -- the phase only gets marked when the check passes.
- The command's state file update failed (wrong path, JSON parse error).
- The command was never actually run (user thinks they ran it but didn't).

**Fixes:**
- Read the command's output to see what failed. Address the issues, re-run the command.
- If the command passed but didn't update state, check for JSON write errors in the command logic. Fix the marking path and re-run -- don't manually set phase booleans.
- For non-`verified` phases, manual marking is acceptable as a last resort if the marking command is genuinely broken:
  ```python
  import json
  s = json.load(open('.harness-state.json'))
  s['phases']['docs_synced'] = True  # Only for non-verified phases
  json.dump(s, open('.harness-state.json', 'w'), indent=2)
  ```
- **Never manually set `verified` to true.** The `/verify` command is the only gate for this phase. If it's not marking, fix the verify command itself.

### Problem 5: Hooks not firing

**Symptoms:** No debt reminders on edit. No stop gate. No enforcement at all.

**Diagnosis:**
```bash
# Check settings.json has hooks
cat .claude/settings.json | python3 -c "import json,sys; h=json.load(sys.stdin).get('hooks',{}); print(json.dumps(h, indent=2))"
# Check scripts exist and are executable
ls -la .claude/scripts/harness-*.sh
# Test a script manually
echo '{}' | bash .claude/scripts/harness-debt.sh
```

**Root causes:**
- `.claude/settings.json` missing or malformed hooks section
- Scripts not executable (missing `chmod +x`)
- Script paths wrong (relative vs absolute)
- Script fails silently (bash error before producing output)

**Fixes:**
- Fix settings.json hook structure (must match Claude Code hook schema)
- `chmod +x .claude/scripts/harness-*.sh`
- Test each script manually with sample input
- Add `set -e` temporarily to scripts to surface errors
