---
name: env-health-check
description: >
  Unified diagnostic for the local development environment -- git, docker, Xcode, MCP servers, disk space, simulator state, and skill/plugin loading. Use when the user says "check to see if the git issues persist on this repo", "check and see if there's any problems with current git or current environment", "can you help me fix the hanging docker issue", "is something broken with my environment", "is git broken", "is docker stuck", "what's wrong with my environment", "env health check", "environment diagnostics", "debug my setup", "hung processes", "environment check", "check my dev environment", or otherwise asks whether the local toolchain is healthy. Use this skill proactively whenever Claude or the user notices environment-level friction (hung git, stalled docker, MCP timeouts, disk pressure, skill that won't load) before assuming the issue is in the project itself. This is meta-work about the environment, not feature work, so it is appropriate to run even when a harness scope-gate is engaged on the current branch -- mention this up front so the user understands the skill is intentionally cross-cutting.
---

# Env Health Check

A structured, end-to-end diagnostic that distinguishes **environment problems** (toolchain, daemons, caches, MCP servers) from **project problems** (the code under `git diff`). Run this before chasing a bug in application code when something feels off "below" the project layer.

## Why this skill exists

Real sessions kept hitting the same friction:

- "check to see if the git issues persist on this repo" -- a stuck `index.lock` from a crashed prior process.
- "check and see if there's any problems with current git or current environment" -- multiple things wrong at once (git lockfile + flaky docker + a failing MCP) and Claude needed a single pass that surfaces all of them with severity instead of fixing one and stopping.
- "can you help me fix the hanging docker issue?" -- `docker ps` hanging because the daemon socket was unresponsive.
- A worktree-based workflow where Xcode rebuilt the world because `DerivedData` was being shared with the main checkout's path -- silent, slow, demoralizing.
- The user disabled half their MCPs to get tokens back; pruning needed a deliberate, evidence-based pass (handled by the sibling `mcp-prune` skill, but `env-health-check` should *flag* MCP problems and recommend it).

The job here is to run all the cheap, safe diagnostics in one sweep, fix the obvious safe stuff automatically, and produce a punch list with severity for the rest. No surprises -- the user should never have to ask "did you also check X?".

## Scope note: this is meta-work

If the project has a harness with a scope gate, **do not** abandon this skill because the gate complains. This skill is about the local environment, not the feature scope of the current branch. When you start, briefly tell the user: "This is environment-level diagnostics, not feature work -- I'll be poking at git/docker/Xcode/MCP and may touch caches outside the repo. Tell me to stop if you'd rather keep the harness focused." Do **not** programmatically bypass any hook -- just be transparent about why the activity is legitimate.

## Workflow

Run the checks below in order. The order matters: git locks block almost everything else; docker probes can hang; Xcode and MCP checks are cheap and parallelizable.

For every section, classify findings as:

- `P0` -- broken, blocking work right now
- `P1` -- degraded, will bite soon (hung daemon, near-full disk)
- `P2` -- suboptimal but functional (worktree using wrong DerivedData, one MCP failing)
- `P3` -- cosmetic / housekeeping (stale simulator runtimes, old logs)

At the end, produce a single **Punch List** (template at the bottom of this file) showing what was auto-fixed and what needs the user.

### 1. Git health

Run from the current repo if there is one; otherwise note "no repo, skipping git checks".

```bash
# Inside the repo
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "Not a git repo"; }

# Hung git processes (a real recurring issue)
ps -eo pid,etime,command | grep -E '[g]it ' | awk '$2 ~ /[0-9]+:[0-9]+:[0-9]+/ || ($2 ~ /^[0-9]+:[0-9]+$/ && $2 > "05:00") { print }'

# Lock files left behind by crashed processes
ls -la "$REPO/.git"/{index.lock,HEAD.lock,config.lock,refs/heads/**/*.lock} 2>/dev/null

# Worktree consistency
git worktree list
git worktree prune --dry-run

# Repo integrity (cheap subset; full fsck is slow)
git fsck --no-dangling --no-reflogs 2>&1 | head -50

# Branch / remote reachability
git remote -v
git ls-remote --heads origin >/dev/null 2>&1 && echo "remote: reachable" || echo "remote: UNREACHABLE"

# Local vs remote drift on the current branch
git fetch --dry-run origin 2>&1 | head
```

**Auto-fix safely:**
- Delete `*.lock` files **only if** no `git` process owns them (check `lsof` or `ps`).
- Run `git worktree prune` if the dry-run shows only stale entries.

**Surface for user:**
- Hung git processes (don't kill without confirmation -- they may be holding work).
- `git fsck` errors.
- Unreachable remote (could be auth, VPN, or DNS).

### 2. Docker health

Docker probes hang when the daemon is wedged. Use timeouts religiously.

```bash
# Socket reachable? (don't let docker ps hang the whole skill)
timeout 3 docker info >/dev/null 2>&1 && echo "docker: ok" || echo "docker: NOT RESPONDING"

# Daemon process
pgrep -lf "Docker Desktop|dockerd|com.docker" | head

# Hung containers (only if daemon is responsive)
timeout 5 docker ps --filter status=exited --filter status=dead --format '{{.ID}} {{.Names}} {{.Status}}' 2>/dev/null
timeout 5 docker ps --format '{{.ID}} {{.Names}} {{.Status}}' 2>/dev/null | grep -iE 'unhealthy|restarting'

# Disk usage in docker
timeout 5 docker system df 2>/dev/null
```

**Auto-fix safely:**
- Nothing. Container/daemon restarts always require user confirmation.

**Surface for user:**
- "Docker daemon not responding -- restart Docker Desktop?" (P0/P1 depending on whether they need it now).
- Containers in unhealthy/restarting loops.
- Volume / image bloat over a sensible threshold (e.g., > 50 GB).

### 3. Xcode + iOS Simulator (skip cleanly if not on macOS or no Xcode)

```bash
xcode-select -p 2>/dev/null
xcodebuild -version 2>/dev/null | head

# DerivedData per worktree -- this is the gotcha
# In a worktree, the *main* checkout's DerivedData should NOT be the build target.
# Find the toplevel and see whether xcodebuild settings point inside or outside it.
TOPLEVEL=$(git rev-parse --show-toplevel 2>/dev/null)
GIT_COMMON=$(git rev-parse --git-common-dir 2>/dev/null)
if [ -n "$TOPLEVEL" ] && [ -n "$GIT_COMMON" ] && [ "$(cd "$GIT_COMMON/.." && pwd)" != "$TOPLEVEL" ]; then
  echo "In a git worktree. Main checkout: $(cd "$GIT_COMMON/.." && pwd). Worktree: $TOPLEVEL"
  echo "Recommended DerivedData: $TOPLEVEL/.derived-data (or any path unique to this worktree)"
fi
ls -la "$TOPLEVEL/.derived-data" 2>/dev/null
du -sh ~/Library/Developer/Xcode/DerivedData 2>/dev/null

# Simulator state
xcrun simctl list devices booted 2>/dev/null
# Stuck simulator processes
pgrep -lf "Simulator|CoreSimulator|launchd_sim" | head
```

**Auto-fix safely:**
- Nothing destructive on DerivedData. Recommend the worktree-local path; let the user opt in.

**Surface for user (worktree gotcha):**
> When in a git worktree, the worktree should have its own DerivedData (e.g., `<worktree>/.derived-data`) so it doesn't fight the main checkout's incremental build cache. If you keep getting full rebuilds across worktrees, this is almost always why.

Recommend setting per-scheme `DerivedDataPath` or shipping a project-local `xcconfig` that does this.

### 4. MCP servers

This is where token-cost and failure-rate problems live. We diagnose; pruning is the `mcp-prune` skill.

```bash
# Configured MCPs (Claude Code reads ~/.claude.json or project .mcp.json)
ls ~/.claude.json ~/.claude/mcp.json 2>/dev/null
[ -f .mcp.json ] && echo "Project MCP config: .mcp.json"

# Process-level: which MCP servers are alive?
ps -eo pid,etime,command | grep -iE '[m]cp|[c]laude.*mcp' | head -30
```

Read the active MCP list from the harness session log if available, otherwise from config files. For each MCP, infer health from:

- whether a server process exists
- whether recent tool calls succeeded (skim `~/.claude/logs/` or session transcripts if present)
- approximate token cost contribution (large `tools` arrays, descriptions, instruction blobs)

**Surface for user:**
- "N of M MCPs failing or unused -- run the `mcp-prune` skill to prune deliberately."
- Specific MCPs that are clearly broken (process missing, last error today).

### 5. Disk space

```bash
df -h / "$HOME" 2>/dev/null
du -sh ~/Library/Developer/Xcode/DerivedData ~/Library/Caches ~/.npm ~/.cargo ~/.gradle ~/Library/Containers/com.docker.docker 2>/dev/null
```

**Surface for user:**
- Any volume above 90% full as P0.
- Caches above a sensible threshold (e.g., DerivedData > 30 GB, npm cache > 10 GB) as P2 with a one-line cleanup hint.

### 6. Skill / plugin loading errors

```bash
# Claude Code plugin cache
ls -la ~/.claude/plugins/ 2>/dev/null | head
# Recent errors in plugin logs
grep -iE 'error|failed|panic' ~/.claude/logs/*.log 2>/dev/null | tail -20
# Marketplace / plugin manifests with obvious JSON errors
find ~/.claude/plugins -name plugin.json -maxdepth 4 -exec python3 -c "import json,sys; json.load(open(sys.argv[1]))" {} \; 2>&1 | grep -i error | head
```

**Surface for user:**
- Any plugin that fails to parse / load.
- Skills referenced by name in settings but not present on disk.

## Punch List template

After running the sweep, output exactly this structure:

```markdown
# Env Health Check -- <YYYY-MM-DD HH:MM>

**Scope:** environment-level diagnostics (meta-work). Repo: <path or "none">.

## Auto-fixed
- [git] Removed stale `.git/index.lock` (no owning process)
- [git] Pruned 2 stale worktree entries

## Action required

### P0 (blocking)
- [docker] Daemon not responding -- restart Docker Desktop, then re-run.

### P1 (degraded)
- [mcp] 3 of 9 MCPs failing on startup (finance, legal, vercel). Recommend running the `mcp-prune` skill.

### P2 (suboptimal)
- [xcode] Worktree at `<path>` is using the main checkout's DerivedData, causing full rebuilds. Suggest `<worktree>/.derived-data`.

### P3 (housekeeping)
- [disk] DerivedData is 42 GB. Safe to clear when convenient.

## Skipped / not applicable
- Xcode checks: not on macOS.
```

If a section ran clean, list it under "Skipped / not applicable" with reason "no issues found" -- explicit absence beats silence.

## Rules of engagement

- **Never kill processes without confirmation.** Hung git or docker processes might be the user's foreground work.
- **Never `rm -rf` caches automatically.** Always recommend, never delete cache directories. Lockfiles and stale worktree entries are the only auto-deletes.
- **Use timeouts on every external probe.** A `docker ps` that hangs for 30s defeats the point of a health check.
- **Surface everything once.** Don't fix half and stop. The user wants the full picture so they can triage themselves.
- **Be explicit about the meta-work framing** so it's clear why this skill is operating outside the usual feature-scope discipline.
