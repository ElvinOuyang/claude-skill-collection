# Claude Code Harness

Mechanical enforcement for the CLAUDE.md mandatory workflows. The harness prevents Claude from skipping workflow steps when running autonomously, without changing CLAUDE.md itself.

## Why this exists

Claude systematically skips workflow steps when running autonomously -- missing specs, tests, and doc updates. This harness provides mechanical guardrails so those gaps are caught automatically rather than relying on the user to notice.

## Architecture

```
SessionStart          PreToolUse (Edit/Write)     PreToolUse (Bash)         PostToolUse (Bash)             Stop
     |                        |                         |                         |                         |
harness-init.sh        harness-debt.sh          harness-pr-check.sh       harness-commit-check.sh       harness-stop-gate.sh
     |                        |                         |                   harness-branch-check.sh             |
Create/reset            Inject remaining          Block push/PR if          After git commit:             Check phases,
.harness-state.json     phases as context         branch is behind          remind per-task review.       block if incomplete
                        before file edits         origin/{{TRUNK}}          After branch create:
                                                                            warn if {{TRUNK}} is stale.
```

All hooks are configured in `.claude/settings.json`. State is tracked in `.harness-state.json` (gitignored, session-scoped).

## State file

`.harness-state.json` is the single source of truth for the current session:

```json
{
  "branch": "feature/my-feature",
  "scope_override": "patch",
  "phases": {
    "pre_feature_complete": false,
    "graphify_queried": false,
    "plan_created": false,
    "plan_reviewed": false,
    "execution_skill_active": false,
    "per_task_reviews_done": false,
    "smoke_tested": false,
    "spec_written": false,
    "docs_synced": false,
    "verified": false
  }
}
```

- Created by `harness-init.sh` on SessionStart
- Reset when the branch changes (different branch = new work)
- Preserved when resuming on the same branch
- `scope_override` is optional; set by `/evaluate-scope` when the inferred scope is wrong

## Scopes

The stop gate infers scope from the git diff against the trunk branch:

| Scope | Trigger | Required phases |
|-------|---------|-----------------|
| `feature` | New source files added | `pre_feature_complete`, `graphify_queried`, `plan_created`, `plan_reviewed`, `execution_skill_active`, `per_task_reviews_done`, `smoke_tested`, `docs_synced`, `verified` |
| `patch` | Source files modified (none added) | `docs_synced`, `verified` |
| `design` | Only doc files changed | `pre_feature_complete`, `graphify_queried`, `spec_written`, `docs_synced`, `verified` |
| (none) | No source or doc changes | No enforcement |

<!-- {{SCOPE_FILE_EXTENSIONS}}: customize the file extensions that trigger each scope.
Default: new .ts/.tsx/.swift/.py files = feature, modified source = patch, docs/ only = design.
-->

`scope_override` in the state file can narrow the scope (e.g., `feature` -> `patch` for a bug fix on a feature branch). Only `patch` and `design` are accepted as overrides -- this prevents accidental or malicious widening.

## Hooks

### SessionStart: `harness-init.sh`

Creates `.harness-state.json` with all phases false. If the file already exists for the same branch, leaves it alone (resumed session). If the branch changed, recreates it.

### PreToolUse (Edit/Write): `harness-debt.sh`

Before every file edit, injects remaining phases as `additionalContext`. Claude sees a reminder like: "HARNESS: 3/10 phases complete. Remaining: smoke_tested, docs_synced, verified." This is informational, not blocking.

### PreToolUse (Glob/Grep): graphify hint

Before file searches, reminds Claude that the knowledge graph exists at `graphify-out/` for faster lookups.

### PreToolUse (Bash): `harness-pr-check.sh`

Before `gh pr create` or `git push`, fetches origin/{{TRUNK}} and checks if the current branch's merge-base matches it. If the branch is behind, **blocks** with a rebase instruction. Skips force-push (intentional) and pushes from {{TRUNK}} itself.

### PostToolUse (Bash): `harness-commit-check.sh`

After any `git commit` command, injects a reminder about per-task review (CLAUDE.md step 7). Informational, not blocking.

### PostToolUse (Bash): `harness-branch-check.sh`

After `git checkout -b`, `git branch`, or `git switch -c`, fetches origin/{{TRUNK}} and compares it to local {{TRUNK}}. If local {{TRUNK}} is behind, **warns** (advisory, not blocking) that the new branch may be based on stale code.

### Stop: `harness-stop-gate.sh`

The enforcement gate. Blocks Claude from stopping if required phases are incomplete.

## Stop gate loop detection

Stop hooks have an inherent loop problem: a block message becomes user input, Claude responds, the hook fires again. Without mitigation, this creates an infinite loop.

The stop gate uses hash-based loop detection:

```
Stop hook fires
  |
  v
Compute RESULT (missing phases for current scope)
  |
  +-- Empty: all phases complete -> exit 0 (clean stop)
  |
  +-- Non-empty, first occurrence (new hash):
  |     Block with combined message:
  |     "Scope: X. Incomplete: Y.
  |      Run /evaluate-scope or /verify."
  |
  +-- Non-empty, same hash repeats within 120s:
        Auto-release: exit 0 (silence)
        Counter persists for continued silence.
```

Key properties:
- **Reason hashing**: the block reason is hashed with `cksum`. The counter only increments when the exact same reason repeats. Completing a phase changes the reason, resets the counter, and gives fresh enforcement.
- **Persistent auto-release**: the counter file is NOT deleted on auto-release. Subsequent stops within the 120s cooldown also auto-release silently. This prevents noise during mid-session chat.
- **Natural reset**: the counter resets when the hash changes (progress) or the cooldown expires (120s gap between stops = new work unit).
- **Repo-unique counter**: stored at `/tmp/harness-stop-{cksum of repo path}` to avoid collisions across repos.
- **Data via env vars**: scope and state file path are passed to Python via environment variables, not string interpolation, to prevent injection.
- **Fail closed**: if the state file is unreadable, the gate blocks with an error message rather than silently allowing.

## Slash commands

These commands interact with the harness state:

| Command | What it does | Phases it sets |
|---------|-------------|----------------|
| `/pre-feature [name]` | Reads living docs, runs graphify query. | `pre_feature_complete`, `graphify_queried` |
| `/evaluate-scope` | Checks conversation intent + git state, adjusts `scope_override` if the inferred scope is wrong for the session. | Sets `scope_override`; may mark phases for exploration sessions |
| `/test-gate` | Dispatches subagent for build, tests, code rules. | `per_task_reviews_done` |
| `/smoke-test [feature]` | Runs smoke tests against behavior spec. | `smoke_tested` |
| `/sync-docs` | Updates living docs to reflect implementation changes. | `docs_synced` |
| `/verify` | Dispatches adversarial subagent to cross-check all claimed phases. The only gate that sets verified. | `verified` |
| `/audit-docs [scope]` | Audits docs against source code. Read-only, does not modify state. | (none) |

## How phases get marked

Phases are marked true in `.harness-state.json` by the slash commands and skills that complete the corresponding workflow steps. The harness does NOT mark phases automatically -- the commands/skills do it after verifying the work is done.

## Modifying the harness

When changing hook scripts or adding new phases:

1. **Stop hooks that block must have loop detection.** Use the hash-based pattern: hash the block reason, track with a counter file, auto-release on repeat. Never create a Stop hook that blocks unconditionally.

2. **Scope changes require updating three places:** the `REQUIRED` dict in `harness-stop-gate.sh`, the scope inference logic in the same script, and this document.

3. **New phases require updating:** `harness-init.sh` (add to initial state), `harness-stop-gate.sh` (add to the appropriate scope's required list), the slash command that marks it, and this document.

4. **Test the full cycle** after changes: reset state, trigger block and auto-release, verify scope override works, verify progress resets the counter.

5. **State file is gitignored and session-scoped.** Don't store anything in it that needs to persist across sessions. Use memory or docs for that.
