---
name: harness-add-issue-led-workflow
description: >
  Convert a project's harness into an issue-led autonomous orchestration system where each GitHub Issue is one phase of work, and the agent picks up its current super-task from `gh issue view` + an orchestration plan instead of needing the user to re-explain context every session. Use when the user says "use github issues as long-running tasks", "issue-led workflow", "issue-driven harness", "make the harness pick up the next issue", "decompose the plan into issues", "one issue per phase", "epoch-based orchestration", "let the agent orchestrate itself across sessions", "stop having to re-explain the project at the start of every session", "wire issues into the harness", or wants the harness to derive its scope and required reading from a GitHub issue. Also use proactively when a project has a long linear implementation plan that's becoming hard to manage and would benefit from being decomposed into independently-shippable issues with worktrees. Requires an existing harness (run `harness-setup` first) and a GitHub remote with `gh` CLI authenticated.
---

# Harness Add Issue-Led Workflow

Wire an existing harness so each GitHub Issue is a long-running "super-task" the agent can pick up autonomously across sessions. The agent's current scope (which issue, which spec, which file boundaries) is derived from the branch name + `gh issue view` + an orchestration plan, not from user-supplied context.

This is the pattern the `pumpkin-space-organizer` project uses. Without this skill, you'd need to wire it across 6 files manually and it's easy to leave gaps that break autonomy (most commonly: the agent doesn't know which issue it's on, or `/pre-feature` doesn't load the orchestration plan, or `gh` calls trigger permission prompts mid-loop).

## When NOT to use

- Project has no GitHub remote, or `gh` CLI is not authenticated. Issue-led mode requires both.
- Project has fewer than ~5 distinct phases of work — overhead exceeds benefit.
- Project's work is reactive/exploratory (debugging, support, design exploration). Issue-led mode is for planned multi-phase delivery.
- No harness exists yet. Run `harness-setup` first; this skill extends it.

## Prerequisites

Verify all of:
- `.claude/scripts/harness-init.sh` exists (state file initialization)
- `.claude/scripts/harness-stop-gate.sh` exists (the stop gate)
- `.claude/HARNESS.md` exists
- `.claude/settings.json` exists with hook wiring
- `.claude/commands/pre-feature.md` exists
- `gh auth status` returns authenticated
- `git remote get-url origin` resolves to a GitHub repo

If any are missing, route the user to `harness-setup` first and stop.

## The autonomy loop (what you're enabling)

After this skill runs, a fresh agent session in the project does this without user intervention:

1. SessionStart fires `harness-init.sh`. If the current branch matches `^(feat|chore|docs)/issue-(\d+)-`, `issue_number` is auto-populated in `.harness-state.json`.
2. Agent reads `.harness-state.json`, sees `issue_number`, runs `gh issue view NN` for body + labels (no permission prompt — pre-allowlisted).
3. `/pre-feature` is gated on reading the orchestration plan, which gives the agent the dependency DAG, file-conflict policy, what's already shipped, and which spec file the issue's `area:*` label points to.
4. Standard harness phases run inside the issue's worktree until the PR closes the issue.
5. User runs `/start-issue NN+1` to bootstrap the next worktree, or the agent suggests the next unblocked issue from the orchestration plan.

The skill below installs the 6 coordinated changes that make this loop work.

## Step 1: Decide the orchestration plan path

Ask the user:
1. Do you already have an orchestration plan / decomposition doc? (a markdown file listing the issues, dependencies, file-conflict policy, version milestones)
2. If yes, what's its path? (e.g., `docs/superpowers/specs/YYYY-MM-DD-orchestration-plan.md`)
3. If no, offer to draft one. The plan should answer:
   - What are the issues? (list with one-line descriptions)
   - What's the dependency DAG? (which must ship before which)
   - Which issues touch overlapping files? (so parallel worktrees don't conflict)
   - What labels does each issue carry? (`version:vX`, `area:<domain>`, `phase`)

The plan path is the canonical artifact this skill wires into the harness. Hold onto it — you'll reference it in Steps 4, 5, and 7.

If drafting from scratch, model on the structure of an existing plan (decisions section, issue list table, parallelism analysis). Don't generate this skill's output — generate the project's own plan.

## Step 2: Add `issue_number` to harness state

Edit `.claude/scripts/harness-init.sh` so the state file carries an `issue_number` field, populated from either an env var or the branch name.

**Read `.claude/scripts/harness-init.sh` first.** The default `harness-setup` template uses a Python heredoc (`python3 << 'PYEOF' ... PYEOF`) that builds a `state = {...}` dict and atomically writes it via `os.replace`. If the script you're editing diverges from that shape (e.g. uses pure bash `jq`, or a Node script), adapt the snippet below to that structure rather than blindly inserting it. The semantic goal is: derive `issue_number` from `HARNESS_ISSUE_NUMBER` env var, falling back to branch-name parsing, and persist it into the state file alongside `branch`.

Insert this Python helper at the top of the `python3` block (before the `state = {...}` literal):

```python
def issue_number_from_branch(branch: str):
    """Parse `feat/issue-NN-<slug>` (or chore/docs equivalents) → NN; else None."""
    import re
    m = re.match(r"^(?:feat|chore|docs)/issue-(\d+)-", branch or "")
    return int(m.group(1)) if m else None

env_issue = os.environ.get("HARNESS_ISSUE_NUMBER", "").strip()
issue_number = (
    int(env_issue) if env_issue.isdigit()
    else issue_number_from_branch(os.environ["CURRENT_BRANCH"])
)
```

Then add `"issue_number": issue_number,` to the `state` dict, just below the `"branch":` line.

**Why both env var and branch parsing:** the env var path is for `/start-issue` (which knows the issue number explicitly); the branch parsing path is for resumed sessions and worktrees opened directly without going through `/start-issue`.

## Step 3: Create the `/start-issue NN` slash command

Create `.claude/commands/start-issue.md` with the recipe below. Replace `<TRUNK>` with the project's trunk branch (`main` or `master`) and `<ORCHESTRATION_PLAN_PATH>` with the path from Step 1.

```markdown
Bootstrap a worktree, branch, and harness state for a GitHub issue. Does NOT skip the brainstorm/plan workflow — it just sets up the workspace.

Usage: `/start-issue NN`

Steps:

1. **Fetch the issue.** Run `gh issue view "$ARGUMENTS" --json number,title,labels,body --jq '{number,title,labels:[.labels[].name],body}'`. If `gh` errors (issue not found, no auth, no remote), report the error verbatim and stop.

2. **Derive the branch name.**
   - Slug: lowercase the title, strip any leading `[v0.1]` / version markers, drop all punctuation, then split on whitespace and take the first 4 whitespace-delimited tokens, joined with `-`. Example: title `"[v0.2] Spaces tab: list + detail view"` → tokens `["spaces","tab","list","detail"]` → slug `spaces-tab-list-detail`.
   - Prefix: `feat/` by default. If the labels include `area:scaffold` use `chore/`; if labels include `area:docs` (and only `area:docs`) use `docs/`.
   - Final: `<prefix>issue-NN-<slug>` (e.g. `feat/issue-04-spaces-tab-list-detail`).
   - If a branch with that name already exists locally or on origin, report it and ask whether to resume (worktree onto existing branch) or pick a new slug.

3. **Confirm trunk freshness.** Run `git fetch origin <TRUNK>`. Verify the user's `<TRUNK>` is current. Abort with a clear message if `git fetch` fails (offline, no remote).

4. **Create the worktree.** Ensure the parent directory exists: `mkdir -p .claude/worktrees`. Then use the `superpowers:using-git-worktrees` skill — pass it the branch name above and worktree path `.claude/worktrees/issue-NN-<slug>`. The skill creates the branch from `origin/<TRUNK>`.

5. **Initialize harness state in the new worktree.** From the worktree directory, run:
   ```bash
   HARNESS_ISSUE_NUMBER=NN bash .claude/scripts/harness-init.sh
   ```
   This writes `.harness-state.json` with `issue_number=NN` and the new branch.

6. **Print the orientation block** for the user:
   - Worktree path
   - Branch name
   - Issue number, title, labels
   - The orchestration plan path (`<ORCHESTRATION_PLAN_PATH>`) and reminder that per-issue `/pre-feature` requires reading it
   - Next-step hint: "Open Claude Code in the new worktree and run `/pre-feature <slug>`."

7. **Do NOT mark any harness phase complete.** This command is workspace bootstrap, not workflow progression. The standard feature workflow runs inside the new worktree.

Edge cases:
- `$ARGUMENTS` empty or non-numeric: print "Usage: /start-issue NN" and stop.
- `gh` not authenticated: print "Run `gh auth login` first" and stop.
- Issue is closed: warn the user and ask before continuing (a closed issue may indicate the work was already done).
- Issue has no `version:*` label or no `area:*` label: warn the user — orchestration-plan-conformant issues should have both.
```

**Why no phase progression:** `/start-issue` is workspace bootstrap. The standard harness phases run inside the new worktree. If the command marked any phase, fresh worktrees would inherit progress they didn't earn.

## Step 4: Pre-allowlist `gh` in `settings.json`

Edit `.claude/settings.json` and add these to `permissions.allow` (create the array if it doesn't exist):

```json
"Bash(gh issue create:*)",
"Bash(gh issue list:*)",
"Bash(gh issue view:*)",
"Bash(gh issue edit:*)",
"Bash(gh issue comment:*)",
"Bash(gh issue close:*)",
"Bash(gh issue reopen:*)",
"Bash(gh label list:*)",
"Bash(gh label create:*)",
"Bash(gh api repos/:owner/:repo/milestones:*)",
"Bash(gh pr view:*)",
"Bash(gh pr list:*)"
```

**Why this matters for autonomy:** every `gh issue view` is something the agent does silently to load context. Without pre-allow, the agent stalls on permission prompts, breaking the autonomous loop. Pre-allow read + comment + label operations; never pre-allow `gh pr create` or `gh pr merge` (those are user-confirm actions).

Validate the JSON after editing:
```bash
python3 -c "import json; json.load(open('.claude/settings.json')); print('OK')"
```

## Step 5: Wire the orchestration plan as a living doc

The orchestration plan is a living doc — the agent must read it in `/pre-feature`, update it in `/sync-docs`, verify it in `/verify`, and audit it in `/audit-docs`.

**Delegate to `harness-add-living-doc`** for this step. Tell it:
- Path: the orchestration plan path from Step 1
- Purpose: "Decomposes implementation work into GitHub issues. Documents the dependency DAG, file-conflict policy, parallelism rules, and per-issue scope."
- Update trigger: "When an issue's scope shifts — file boundaries change, dependencies adjust, an issue is split/merged, or parallelism analysis changes."

Do not duplicate `harness-add-living-doc`'s checklist here. Its job is to ensure the plan is wired into every enforcement touchpoint (`pre-feature`, `sync-docs`, `verify`, `audit-docs`, `HARNESS.md`, `CLAUDE.md`).

After it runs, double-check that `/pre-feature` reads the orchestration plan as a **required** read (not optional), since per-issue work always depends on it.

## Step 6: Update `.claude/HARNESS.md` documentation

Add to `.claude/HARNESS.md`:

1. **State file section** — document `issue_number`:

   > `issue_number` is the GitHub issue this branch is shipping (per the orchestration plan), or `null` for sessions not tied to an issue (e.g. harness maintenance, the original orchestration session). Populated by `harness-init.sh` from `HARNESS_ISSUE_NUMBER` env var or by parsing a `feat|chore|docs/issue-NN-<slug>` branch name.

2. **Slash command table** — add a row for `/start-issue NN`. The backslash-pipes below (`\|`) are markdown-table escapes for a literal pipe character — copy them verbatim into HARNESS.md so the table renders correctly:

   > `/start-issue NN` | Bootstrap a GitHub-issue worktree: fetches the issue via `gh`, creates `feat\|chore\|docs/issue-NN-<slug>` from `origin/<TRUNK>`, opens a worktree at `.claude/worktrees/issue-NN-<slug>`, and writes `issue_number` into the new state file. Workspace bootstrap only — no phase progression. | none

3. **State file JSON example** — include `"issue_number": <number>,` in the example.

## Step 7: Verify the loop end-to-end

Run this checklist against the project. Each item must pass.

| # | Check | Command / expected |
|---|-------|--------------------|
| 1 | State file gains `issue_number` | `bash .claude/scripts/harness-init.sh && jq '.issue_number' .harness-state.json` (should be `null` on a non-issue branch) |
| 2 | Branch parsing works | `HARNESS_ISSUE_NUMBER= git checkout -b feat/issue-99-test-branch && bash .claude/scripts/harness-init.sh && jq '.issue_number' .harness-state.json` (should be `99`). Then delete the test branch. |
| 3 | Env var override works | `HARNESS_ISSUE_NUMBER=42 bash .claude/scripts/harness-init.sh && jq '.issue_number' .harness-state.json` (should be `42`) |
| 4 | `/start-issue` exists | `test -f .claude/commands/start-issue.md` |
| 5 | `gh` permissions wired | `python3 -c "import json; p=json.load(open('.claude/settings.json'))['permissions']['allow']; assert any('gh issue view' in x for x in p), 'missing gh permissions'"` |
| 6 | Orchestration plan referenced in pre-feature | `grep -l 'orchestration' .claude/commands/pre-feature.md` |
| 7 | Orchestration plan referenced in sync-docs | `grep -l 'orchestration' .claude/commands/sync-docs.md` |
| 8 | Orchestration plan referenced in verify | `grep -l 'orchestration' .claude/commands/verify.md` |
| 9 | HARNESS.md documents `issue_number` | `grep -l 'issue_number' .claude/HARNESS.md` |
| 10 | Settings JSON still valid | `python3 -c "import json; json.load(open('.claude/settings.json'))"` |

If any check fails, fix before declaring done. Failure modes are silent: a missing `gh` permission stalls the agent on the next session; a missing orchestration-plan reference in `/pre-feature` means the agent plans without knowing dependencies.

## Common mistakes

| Mistake | How to avoid |
|---------|-------------|
| Branch regex too loose (e.g. matches `feature/issue-...`) | Use exactly `^(feat\|chore\|docs)/issue-(\d+)-` so unrelated branches don't get an `issue_number` populated. |
| `/start-issue` marks `pre_feature_complete` | Never. Workspace bootstrap is not workflow progress. The new worktree must run its own `/pre-feature`. |
| Forgetting to pre-allow `gh issue comment` | The agent uses comments to leave audit trails ("plan reviewed by codex:rescue", etc.). Without pre-allow, this prompts the user mid-loop. |
| Orchestration plan added to `pre-feature` as optional | It must be a required read for any issue-scoped work. Otherwise the agent plans without knowing file boundaries and creates merge conflicts. |
| Pre-allowing `gh pr create` or `gh pr merge` | Don't. Those are user-confirm actions. Only pre-allow reads + comments + labels. |
| `harness-init.sh` overwrites `issue_number` on session resume | The script's existing branch-equality check protects this — same branch means existing state is preserved. Don't bypass that check. |
| Skipping `harness-add-living-doc` for the orchestration plan | The plan must be wired into all 6 enforcement touchpoints. Doing it manually misses one (usually `/audit-docs` or the `verify` adversarial check). |
| Issue numbers in branch but no orchestration plan | Half-implemented. The agent gets `issue_number` but has no doc to read for dependency context. Step 1 is mandatory, not optional. |

## Real-world reference

The `pumpkin-space-organizer` project uses this pattern in production. Reference artifacts:
- `.claude/commands/start-issue.md` — the slash command template
- `.claude/scripts/harness-init.sh` — the issue-number derivation
- `.claude/HARNESS.md` (state file section) — the `issue_number` documentation
- `docs/superpowers/specs/2026-04-28-orchestration-plan.md` — the orchestration plan
- `.claude/settings.json` (permissions.allow) — the `gh` allowlist

If your scaffolding diverges from these in structure, mirror the patterns rather than the literal paths.
