# Harness Engineering Toolkit -- Design Spec

**Date:** 2026-04-15
**Status:** Draft
**Author:** ElvinOuyang + Claude

## Overview

A Claude Code plugin that provides mechanical enforcement for mandatory workflows. Prevents Claude from skipping workflow steps when running autonomously by providing hooks, scripts, slash commands, and living doc templates that gate progress on verified phase completion.

**Dependency:** superpowers plugin (writing-plans, executing-plans, brainstorming, verification-before-completion)

**Optional integration:** graphify (knowledge graph). When `graphify-out/` exists, the harness adds a PreToolUse hint for Glob/Grep and wires `/pre-feature` to run graphify queries. When absent, these are silently skipped.

## Problem

Claude systematically skips workflow steps when running autonomously -- missing specs, tests, doc updates, and verification. Users shouldn't have to babysit every step. The harness provides mechanical guardrails so gaps are caught automatically.

## Architecture

The harness is a state machine enforced by Claude Code hooks:

```
SessionStart          PreToolUse (Edit/Write)     PreToolUse (Bash)         PostToolUse (Bash)             Stop
     |                        |                         |                         |                         |
harness-init.sh        harness-debt.sh          harness-pr-check.sh       harness-commit-check.sh       harness-stop-gate.sh
     |                        |                         |                   harness-branch-check.sh             |
Create/reset            Inject remaining          Block push/PR if          After git commit:             Check phases,
.harness-state.json     phases as context         branch is behind          remind per-task review.       block if incomplete
                        before file edits         origin/trunk              After branch create:
                                                                            warn if trunk is stale.
```

### State file (.harness-state.json)

Session-scoped, gitignored. Single source of truth:

```json
{
  "branch": "feature/my-feature",
  "scope_override": null,
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
```

### Scopes

Inferred from git diff against trunk:

| Scope | Trigger | Required phases |
|-------|---------|-----------------|
| `feature` | New source files added | pre_feature_complete, graphify_queried, plan_created, plan_reviewed, execution_skill_active, per_task_reviews_done, smoke_tested, docs_synced, verified |
| `patch` | Source files modified (none added) | test_gate_passed, smoke_tested, docs_synced, verified |
| `design` | Only docs/ files changed | pre_feature_complete, graphify_queried, spec_written, docs_synced, verified |

Source file extensions (configurable): `.swift`, `.ts`, `.tsx`, `.py`, `.go`, `.rs`, `.java`, `.kt`, `.rb`, `.sql`

`scope_override` can narrow scope (feature->patch) but never widen (patch->feature).

### Stop hook loop detection

Critical pattern. Stop hooks that block create infinite loops (block -> user input -> Claude responds -> block again). Solution: hash-based loop detection.

```
Stop hook fires
  |
  v
Compute RESULT (missing phases for current scope)
  |
  +-- Empty: all phases complete -> exit 0
  |
  +-- Non-empty, first occurrence (new hash):
  |     Block with combined message
  |
  +-- Non-empty, same hash repeats within 120s:
        Auto-release: exit 0 (silence)
```

Key properties:
- Reason hashing via `cksum` -- counter only increments when exact same reason repeats
- Completing a phase changes the hash, resets the counter, gives fresh enforcement
- Persistent auto-release within cooldown (no noise during mid-session chat)
- Natural reset when cooldown expires (120s gap = new work unit)
- Repo-unique counter at `/tmp/harness-stop-{cksum of repo path}`

### Parameter model

The harness is parameterized at setup time. These values flow into scripts, commands, and docs:

| Parameter | Default | Where it's used |
|-----------|---------|-----------------|
| `trunk_branch` | `master` | All scripts (merge-base), commands (diff), CLAUDE.md |
| `source_extensions` | `.swift,.ts,.tsx,.py,.go,.rs,.java,.kt,.rb,.sql` | Stop gate scope inference, test-gate file matching |
| `living_docs` | (discovered at setup) | pre-feature, sync-docs, verify, audit-docs, CLAUDE.md |
| `test_command` | (asked at setup) | test-gate subagent prompt |
| `smoke_test_setup` | (asked at setup, may be "none") | smoke-test command |
| `project_name` | (from package.json/Cargo.toml/repo name) | HARNESS.md, doc headers |

Scripts use the trunk branch directly. Commands are generated with the actual living docs list. The stop gate uses source extensions for scope inference.

### Slash commands

| Command | What it does | Phase it marks |
|---------|-------------|----------------|
| `/pre-feature [name]` | Reads living docs (PRD, specs, constraints, registry, system design), optionally runs graphify query | `pre_feature_complete`, `graphify_queried` |
| `/evaluate-scope` | Checks conversation intent + git state, adjusts scope_override | Sets `scope_override` |
| `/test-gate` | Dispatches subagent for build, tests, code rules | `test_gate_passed` |
| `/smoke-test [feature]` | Runs smoke tests against behavior/regression spec | `smoke_tested` |
| `/sync-docs` | Checks all living docs for freshness, proposes updates | `docs_synced` |
| `/verify` | Dispatches adversarial subagent to cross-check all claimed phases | `verified` |
| `/audit-docs [scope]` | Read-only doc freshness audit | (none) |

### Phase marking paths

Each phase has a concrete marking mechanism. Phases are marked by the slash commands/skills that complete the corresponding workflow step:

| Phase | Marked by | Mechanism |
|-------|-----------|-----------|
| `pre_feature_complete` | `/pre-feature` command | After reading all living docs and summarizing |
| `graphify_queried` | `/pre-feature` command | After running graphify query (or skipped if graphify absent) |
| `plan_created` | `superpowers:writing-plans` skill | Skill updates state file after plan is written |
| `plan_reviewed` | `superpowers:executing-plans` or manual review | Marked after plan review iteration (Codex or peer) |
| `execution_skill_active` | `superpowers:executing-plans` skill | Marked when execution begins |
| `test_gate_passed` | `/test-gate` command | After subagent reports PASS |
| `per_task_reviews_done` | `/test-gate` command or manual | After per-task review evidence verified |
| `smoke_tested` | `/smoke-test` command | After smoke test passes against spec |
| `spec_written` | Manual (design scope only) | After spec file is written to docs/specs/ |
| `docs_synced` | `/sync-docs` command | After all living docs are confirmed fresh |
| `verified` | `/verify` command (only gate) | After adversarial subagent reports PASS |

For phases marked by superpowers skills: the generated CLAUDE.md workflow instructions tell Claude to update `.harness-state.json` after completing the step. The commands that depend on superpowers verify evidence (plan files exist, review commits exist) rather than trusting the phase boolean alone.

## Skills

### Skill 1: harness-setup

**Trigger:** "set up harness", "add workflow enforcement", "create harness system", "bootstrap harness", "enforce mandatory workflow"

**Purpose:** Bootstrap a complete harness enforcement system for any project.

**Phase 1 -- Living docs scaffold:**

Check for existing living docs. For any missing, generate from templates:

| Doc | Template contents |
|-----|-------------------|
| `docs/prd.md` | Version status table, shipped/planned sections, known bugs, personality/guardrails. Populated by reading codebase and git history. |
| `docs/system-design.md` | Architecture overview, data flow, services, tech stack, known limitations. Populated by exploring codebase structure. |
| `docs/component-registry.md` | Table of every reusable component, service, utility, hook with file paths. Built by scanning source files. |
| `docs/constraints.md` | Platform rules, recurring mistakes, workflow guardrails. Seeded with common gotchas for detected stack. |
| `docs/specs/README.md` | Index of feature specs with platform tags. |
| `docs/specs/[feature].md` | Per-feature behavior documentation. One per major feature area detected. |
| `docs/behavior-specs/README.md` | Index of regression checklists with ID prefixes. Created if testing against a local environment is relevant. |

For each missing doc: draft, show user, get approval, write. For existing docs: check format compatibility, offer to restructure.

**Phase 2 -- Harness infrastructure:**

Generate all scripts, hooks, commands, and documentation:

1. `.claude/scripts/harness-init.sh` -- SessionStart state file creation/reset
2. `.claude/scripts/harness-debt.sh` -- PreToolUse debt reminder injection
3. `.claude/scripts/harness-pr-check.sh` -- PreToolUse push/PR freshness block
4. `.claude/scripts/harness-commit-check.sh` -- PostToolUse commit review reminder
5. `.claude/scripts/harness-branch-check.sh` -- PostToolUse stale branch warning
6. `.claude/scripts/harness-stop-gate.sh` -- Stop gate with scope inference and loop detection
7. `.claude/commands/pre-feature.md` -- Preflight reading (wired to actual living docs list)
8. `.claude/commands/evaluate-scope.md` -- Scope override management
9. `.claude/commands/test-gate.md` -- Subagent-based code quality gate
10. `.claude/commands/smoke-test.md` -- Local environment smoke testing
11. `.claude/commands/sync-docs.md` -- Living doc freshness checks (wired to actual docs list)
12. `.claude/commands/verify.md` -- Adversarial verification subagent
13. `.claude/commands/audit-docs.md` -- Read-only doc audit
14. `.claude/HARNESS.md` -- Architecture documentation
15. `.claude/settings.json` -- Hook wiring (merged into existing if present)
16. `.gitignore` -- Add `.harness-state.json`
17. `CLAUDE.md` additions -- Living docs table, mandatory workflow sections

Commands are generated with the actual living doc list from phase 1 -- not hardcoded. If the project has no behavior specs, `/verify` won't check for them.

**Interview (3 questions):**
1. What living docs does your project have? (or "none, create them")
2. What's your trunk branch? (master/main/other)
3. Do you have a local testing setup for smoke testing? (describe it)

### Skill 2: harness-add-living-doc

**Trigger:** "add doc to harness", "harness doesn't check [X]", "integrate [doc] into enforcement", "add [doc] to harness", "harness is missing [doc]"

**Purpose:** Add a new living doc to every enforcement touchpoint in an existing harness.

**Steps:**
1. Ask: what doc, its path, its purpose, what triggers an update to it
2. Scan all enforcement touchpoints where doc families are enumerated:
   - `CLAUDE.md` -- step 1 read list (all workflows), step 9 sync list
   - `.claude/commands/pre-feature.md` -- read list
   - `.claude/commands/sync-docs.md` -- check items
   - `.claude/commands/verify.md` -- adversarial subagent prompt (`pre_feature_complete` and `docs_synced` checks)
   - `.claude/commands/audit-docs.md` -- scope examples and audit checklist
   - `.claude/HARNESS.md` -- command descriptions
3. Show diff preview of every file that needs updating
4. Apply on approval
5. Verify completeness: grep all harness files for other doc names and confirm the new doc appears everywhere they do

### Skill 3: harness-extend

**Trigger:** "add harness phase", "add new scope", "new enforcement hook", "add stop gate check", "add slash command to harness", "extend harness", "new harness hook"

**Purpose:** Add new enforcement infrastructure (phases, scopes, hooks, commands) to an existing harness.

**Operations:**

**Add a new phase:**
- Full update checklist (not just three places):
  1. `harness-init.sh` -- add to initial state JSON
  2. `harness-stop-gate.sh` -- add to REQUIRED dict for the right scope(s)
  3. `.claude/commands/verify.md` -- add to adversarial subagent's phase verification list
  4. `.claude/commands/evaluate-scope.md` -- update scope descriptions if phase changes scope semantics
  5. `.claude/HARNESS.md` -- add to phase documentation and command table
  6. The command that marks it -- create or update the slash command
- Ask: what scope(s) require this phase? What command marks it complete?
- If no existing command handles it, scaffold a new one

**Add a new scope:**
- Add to REQUIRED dict in stop gate with phase list
- Add scope inference rule (file patterns)
- Update narrowing-only override rule in stop gate
- Update `/evaluate-scope` command with new scope option
- Update scope-aware commands (`/test-gate`, `/smoke-test`) if they have scope-conditional behavior
- Update HARNESS.md scope table

**Add a new hook script:**
- Ask: hook point (SessionStart, PreToolUse, PostToolUse, Stop) and blocking vs advisory
- Generate script following correct pattern:

| Hook type | Output format | Rule |
|-----------|--------------|------|
| PreToolUse (block) | `{"decision": "block", "reason": "..."}` | Must have escape condition |
| PreToolUse (advisory) | `{"hookSpecificOutput": {"additionalContext": "..."}}` | Never blocks |
| PostToolUse (advisory) | Same as PreToolUse advisory | Fires after, never blocks |
| Stop (block) | Hash-based loop detection | MUST use three-line counter file pattern. Never block unconditionally. |

- Wire into `.claude/settings.json` with correct matcher

**Add a slash command:**
- Ask: what does it verify, what phase does it mark
- Generate `.claude/commands/[name].md` following patterns:
  - Subagent dispatch (like `/verify`, `/test-gate`): adversarial prompt template
  - Scan and report (like `/pre-feature`, `/audit-docs`): read-check-summarize pattern
  - Modify docs (like `/sync-docs`): diff-preview-then-apply pattern
- Update HARNESS.md command table

**After every operation:** Consistency check across all harness files.

### Skill 4: harness-troubleshoot

**Trigger:** "harness is stuck", "stop hook loop", "can't stop", "harness keeps blocking", "scope is wrong", "stale state file", "phases won't complete", "harness error"

**Purpose:** Diagnose and fix common harness problems.

**Decision tree:**

1. **Stop hook infinite loop** -- Same block message repeats endlessly
   - Check `/tmp/harness-stop-*` counter file
   - Verify hash-based detection: is hash changing (progress) or stuck (loop)?
   - Fix: ensure auto-release fires on repeat, check 120s cooldown

2. **Scope mismatch** -- Wrong phases required for the work being done
   - Run same scope inference as stop gate
   - Compare to `.harness-state.json` scope_override
   - Fix: set scope_override (narrowing only: feature->patch OK, patch->feature blocked)

3. **Stale state file** -- Wrong branch, phases from previous session
   - Compare state file branch to current `git rev-parse --abbrev-ref HEAD`
   - Fix: delete and let harness-init.sh recreate

4. **Phase won't mark complete** -- Command runs but phase stays false
   - Read the command file to understand its conditions
   - Usually: command found issues and reported without marking phase
   - Fix: address the issues the command reported, re-run

5. **Hook not firing** -- No enforcement, no reminders
   - Check `.claude/settings.json` for correct hook structure
   - Verify scripts are executable (`chmod +x`)
   - Test script manually
   - Fix: repair settings.json, chmod scripts, verify paths

**Reference section:** Includes the hash-based loop detection pattern as copyable template.

## Reference Templates

The skill carries reference copies of all generated scripts, commands, and doc templates. These are the proven patterns from the hive-mind project, generalized. Most of the real behavior lives in commands (not scripts), so command templates are critical.

**Scripts** (shell, parameterized with `{{trunk_branch}}` and `{{source_extensions}}`):
- `references/scripts/harness-init.sh` -- State file creation with configurable phases
- `references/scripts/harness-debt.sh` -- Debt reminder injection
- `references/scripts/harness-pr-check.sh` -- Push/PR freshness gate
- `references/scripts/harness-commit-check.sh` -- Post-commit review reminder
- `references/scripts/harness-branch-check.sh` -- Stale branch warning
- `references/scripts/harness-stop-gate.sh` -- Stop gate with loop detection (the critical one)

**Commands** (markdown, parameterized with `{{living_docs}}`, `{{trunk_branch}}`, `{{test_command}}`, `{{smoke_test_setup}}`):
- `references/commands/pre-feature.md` -- Preflight reading with living docs list
- `references/commands/evaluate-scope.md` -- Scope override management with scope definitions
- `references/commands/test-gate.md` -- Subagent code quality gate with test command
- `references/commands/smoke-test.md` -- Local environment smoke testing
- `references/commands/sync-docs.md` -- Living doc freshness checks with doc list
- `references/commands/verify.md` -- Adversarial verification subagent with full phase checklist
- `references/commands/audit-docs.md` -- Read-only doc audit with doc families

**Config:**
- `references/settings-hooks.json` -- Hook wiring template for `.claude/settings.json`
- `references/harness-doc.md` -- HARNESS.md template with architecture docs

**Living doc templates** (markdown skeletons populated by harness-setup):
- `references/docs/prd-template.md` -- Product roadmap
- `references/docs/system-design-template.md` -- Architecture
- `references/docs/component-registry-template.md` -- Component registry
- `references/docs/constraints-template.md` -- Platform constraints
- `references/docs/spec-template.md` -- Feature spec
- `references/docs/behavior-spec-template.md` -- Regression checklist

## What This Plugin Does NOT Do

- **Runtime enforcement** -- It doesn't run tests or builds. It ensures Claude runs them via the right skills/commands.
- **CI/CD** -- It enforces local workflow. CI is a separate concern.
- **Project-specific tools** -- It generates generic harness infrastructure. Project-specific hooks (like Xcode DerivedData cleanup) are added via `harness-extend`.
