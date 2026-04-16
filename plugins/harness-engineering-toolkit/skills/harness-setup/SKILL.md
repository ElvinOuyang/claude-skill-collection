---
name: harness-setup
description: >
  Bootstrap a complete Claude Code harness enforcement system for any project. Creates living doc templates, hook scripts, slash commands, and settings.json wiring that mechanically prevent Claude from skipping workflow steps. Use when the user says "set up harness", "add workflow enforcement", "create harness system", "bootstrap harness", "enforce mandatory workflow", "stop Claude from skipping steps", "add quality gates", or wants to enforce a mandatory workflow when Claude runs autonomously. Also use when starting a new project that needs living documentation and workflow enforcement from scratch. Requires the superpowers plugin.
---

# Harness Setup

Bootstrap a complete harness enforcement system for a project. The harness prevents Claude from skipping mandatory workflow steps (specs, tests, doc updates, verification) when running autonomously.

**Dependency:** superpowers plugin (writing-plans, executing-plans, brainstorming, verification-before-completion)

## What gets created

The harness consists of:
- **State file** (`.harness-state.json`) -- Session-scoped phase tracking (gitignored)
- **6 hook scripts** (`.claude/scripts/`) -- Mechanical enforcement via Claude Code hooks
- **7 slash commands** (`.claude/commands/`) -- Workflow step completion markers
- **Settings wiring** (`.claude/settings.json`) -- Hook configuration
- **Architecture docs** (`.claude/HARNESS.md`) -- How the system works
- **Living docs** (`docs/`) -- The documentation the harness enforces
- **CLAUDE.md updates** -- Mandatory workflow sections

## Phase 1: Interview

Ask these 3 questions before generating anything:

### Question 1: Living docs

> What living documentation does your project have? I'll check for these in your `docs/` directory:
>
> - **PRD / Product roadmap** -- version history, what's shipped vs planned
> - **System design** -- architecture, data flow, tech stack
> - **Component registry** -- reusable components, services, hooks, utilities
> - **Constraints** -- platform rules, recurring mistakes, gotchas
> - **Feature specs** -- per-feature behavior documentation
> - **Behavior specs** -- regression checklists for testing
>
> If you don't have any of these, I can create templates and populate them by reading your codebase. Which do you have, or should I create them all?

Scan `docs/` to pre-fill the answer. Show what exists and what's missing.

### Question 2: Trunk branch

> What's your trunk branch? (master/main/other)

Check `git remote show origin` or `git branch` to pre-fill.

### Question 3: Testing

> **Test command:** What runs your test suite? (e.g., `npm run test:run`, `pytest`, `cargo test`, `swift test`)
>
> **Smoke testing:** Do you have a local testing setup for smoke testing? Describe it briefly (e.g., "dev server at localhost:3000", "iOS simulator with local Supabase", "Docker compose stack"). If none, I'll generate a placeholder smoke-test command you can customize later.

Pre-fill the test command by checking `package.json` scripts, `Makefile`, `Cargo.toml`, `pyproject.toml`, etc.

## Phase 2: Living docs scaffold

For each missing doc, generate from the reference templates in this skill's `references/docs/` directory.

**Process for each missing doc:**
1. Read the template from `references/docs/[type]-template.md`
2. Populate placeholders by reading the codebase:
   - PRD: scan git log for version tags/milestones, read package.json/Cargo.toml for project name
   - System design: scan directory structure, find config files, identify tech stack
   - Component registry: scan source files for exported components/services/hooks
   - Constraints: detect platform (web/iOS/both) and seed with common gotchas
   - Feature specs: identify major feature areas from routes/views/modules
   - Behavior specs: create index file, individual specs come later
3. Show the draft to the user
4. Write on approval

For existing docs, check format compatibility. If a doc exists but lacks the expected structure (e.g., a PRD without a version status table), offer to restructure.

Create `docs/specs/README.md` as the spec index if it doesn't exist.

For feature specs specifically: identify major feature areas from routes, views, or modules (e.g., auth, chat, tasks, settings). Create one `docs/specs/[feature].md` per area using the spec template. Populate each with behaviors discovered by reading the corresponding source files.

## Phase 3: Generate harness infrastructure

### 3a: Scripts

Read each reference script from `references/scripts/` and customize:

| Script | Customization |
|--------|--------------|
| `harness-init.sh` | Set initial phase list (include `graphify_queried` only if graphify-out/ exists) |
| `harness-debt.sh` | No customization needed |
| `harness-pr-check.sh` | Set TRUNK variable to the user's trunk branch |
| `harness-commit-check.sh` | No customization needed |
| `harness-branch-check.sh` | Set TRUNK variable |
| `harness-stop-gate.sh` | Set TRUNK variable, set SOURCE_EXTS for the project's languages, set REQUIRED dict phase lists |

Write to `.claude/scripts/` and `chmod +x` all scripts.

### 3b: Commands

Read each reference command from `references/commands/` and customize with the actual living docs list:

| Command | Customization |
|---------|--------------|
| `pre-feature.md` | Insert the actual living doc paths into the read list. Include graphify query step only if graphify exists. |
| `evaluate-scope.md` | Set trunk branch in git commands. Set scope definitions matching the project. |
| `test-gate.md` | Insert the project's test command. Remove iOS-specific checks if not an iOS project. |
| `smoke-test.md` | Insert the user's smoke test setup description. |
| `sync-docs.md` | Insert the actual living doc list as numbered check items. |
| `verify.md` | Insert living docs into both pre_feature_complete and docs_synced verification. Insert project-specific verification criteria. |
| `audit-docs.md` | Insert living doc families into scope examples and audit checklist. |

Write to `.claude/commands/`.

### 3c: Settings

Read `references/settings-hooks.json` and merge into the project's existing `.claude/settings.json`:

- If no settings.json exists, write the template as-is
- If settings.json exists, merge the `hooks` key:
  - For each hook point (SessionStart, PreToolUse, PostToolUse, Stop), append harness hooks to existing hooks
  - Never overwrite existing hooks
  - If graphify is not present, omit the Glob|Grep graphify hint hook
- Show the merged result to the user before writing

### 3d: HARNESS.md

Read `references/harness-doc.md` and customize:
- Insert the actual phase list
- Insert the actual scope table with correct required phases
- Insert the actual command table
- Insert trunk branch name

Write to `.claude/HARNESS.md`.

### 3e: CLAUDE.md

Add to the project's CLAUDE.md (or create if absent):

1. **Living Docs table** -- list all living docs with paths and descriptions
2. **Mandatory Workflow: Feature Implementation** -- 9-step workflow referencing living docs and slash commands
3. **Mandatory Workflow: Product Design / Brainstorming** -- 8-step workflow

Match the project's existing CLAUDE.md style. If CLAUDE.md already has workflow sections, offer to replace or merge.

### 3f: Gitignore

Add `.harness-state.json` to `.gitignore`.

## Phase 4: Verify

After generating everything:

1. Verify all scripts are executable: `ls -la .claude/scripts/harness-*.sh`
2. Verify settings.json is valid JSON: `python3 -c "import json; json.load(open('.claude/settings.json'))"`
3. Verify state file can be created: `bash .claude/scripts/harness-init.sh && cat .harness-state.json`
4. Show the user a summary of everything created

## Scopes

The harness infers scope from git diff against trunk:

| Scope | Trigger | Required phases |
|-------|---------|-----------------|
| `feature` | New source files added | pre_feature_complete, graphify_queried (if graphify), plan_created, plan_reviewed, execution_skill_active, per_task_reviews_done, smoke_tested, docs_synced, verified |
| `patch` | Source files modified (none added) | test_gate_passed, smoke_tested, docs_synced, verified |
| `design` | Only docs/ files changed | pre_feature_complete, graphify_queried (if graphify), spec_written, docs_synced, verified |

## Architecture

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

**Stop hook loop detection** is the critical pattern. The stop gate uses hash-based loop detection to prevent infinite loops when blocking. See `references/scripts/harness-stop-gate.sh` for the battle-tested implementation. Never create a Stop hook that blocks without this pattern.
