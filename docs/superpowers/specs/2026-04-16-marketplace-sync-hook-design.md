# Marketplace Sync Hook Design

A `Stop` hook that nudges Claude once when plugin directories on disk drift from the registered list in `.claude-plugin/marketplace.json`.

## Context

This repo is a Claude Code plugin marketplace. Each plugin lives at `plugins/<name>/` with metadata at `plugins/<name>/.claude-plugin/plugin.json`, and must be registered in `.claude-plugin/marketplace.json` to appear when users update the marketplace.

The motivating bug: commit `e1fdd07` added the `harness-engineering-toolkit` plugin (4 skills) but forgot to register it in `marketplace.json`. The plugin never appeared in `/plugin` listings until a follow-up fix (`52c90f4`). A mechanical check would have caught this before the first push.

## Goals

- Detect drift between `plugins/*/` directories and `marketplace.json` registered plugins
- Nudge Claude exactly once per distinct drift state (no infinite loops)
- Stay advisory: if Claude decides not to fix, allow stop on the next attempt
- Zero new dependencies beyond what the repo already uses (`jq`, bash, standard POSIX tools)

## Non-Goals (v1)

- Detecting new skills added inside an already-registered plugin (different problem; doesn't strictly require marketplace.json updates)
- Enforcing version bumps when plugin contents change
- Validating plugin.json schema correctness
- A slash command for manual sync (can be added if useful)
- Migration to the full `harness-engineering-toolkit` enforcement system

## Architecture

### Components

**`.claude/hooks/check-marketplace-sync.sh`** — single bash script, the entire detection logic.

**`.claude/settings.json`** — wires the script as a `Stop` hook. Committed so all collaborators get the same enforcement.

**`.claude/state/marketplace-sync-warned.txt`** — single-line file holding the SHA-256 hash of the last drift state Claude was warned about. Gitignored; ephemeral per checkout.

**`.gitignore`** — adds `.claude/state/` so warning markers never leak into commits.

### Data flow

```
Claude attempts Stop
        │
        ▼
.claude/hooks/check-marketplace-sync.sh fires
        │
        ▼
Read registered: jq -r '.plugins[].name' .claude-plugin/marketplace.json
Read on-disk:    plugins/*/.claude-plugin/plugin.json → directory names
        │
        ▼
Compute set diff:
  unregistered = on-disk \ registered
  orphaned     = registered \ on-disk
        │
        ▼
drift = "unregistered:<list>|orphaned:<list>"
hash  = sha256(drift)
        │
        ▼
If drift is empty:                    → exit 0 (silent allow stop)
Else if hash matches state file:      → exit 0 (already nudged this state)
Else:                                  → write hash to state file
                                        emit reminder to stderr
                                        exit 2 (block stop, Claude sees reminder)
```

### Reminder format (emitted to stderr on first drift detection)

```
[marketplace-sync] Drift detected between plugins/ and .claude-plugin/marketplace.json.

Unregistered plugin(s) on disk (missing from marketplace.json):
  - <name>   (read plugins/<name>/.claude-plugin/plugin.json for metadata)

Orphaned entries in marketplace.json (no matching directory):
  - <name>

To fix: edit .claude-plugin/marketplace.json and add/remove entries to match.
This is a one-time nudge per drift state. If you choose not to fix, the next
Stop will succeed silently.
```

## Detection logic detail

### Listing on-disk plugins

```bash
on_disk=$(find plugins -mindepth 3 -maxdepth 3 \
  -path '*/.claude-plugin/plugin.json' -type f \
  | sed -E 's|^plugins/||; s|/\.claude-plugin/plugin\.json$||' \
  | sort -u)
```

### Listing registered plugins

```bash
registered=$(jq -r '.plugins[].name' .claude-plugin/marketplace.json | sort -u)
```

### Set diff

```bash
unregistered=$(comm -23 <(printf '%s\n' "$on_disk") <(printf '%s\n' "$registered"))
orphaned=$(comm -13 <(printf '%s\n' "$on_disk") <(printf '%s\n' "$registered"))
```

### Hash & state

```bash
state_dir=".claude/state"
state_file="$state_dir/marketplace-sync-warned.txt"
mkdir -p "$state_dir"

drift_payload="unregistered:${unregistered}|orphaned:${orphaned}"
current_hash=$(printf '%s' "$drift_payload" | shasum -a 256 | awk '{print $1}')

if [[ -f "$state_file" ]] && [[ "$(cat "$state_file")" == "$current_hash" ]]; then
  exit 0   # already nudged for this exact drift
fi
printf '%s\n' "$current_hash" > "$state_file"
```

## Settings wiring

`.claude/settings.json` (new file):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/check-marketplace-sync.sh"
          }
        ]
      }
    ]
  }
}
```

`$CLAUDE_PROJECT_DIR` is set by the harness so the path resolves regardless of cwd.

## Error handling

- `jq` missing → script prints `[marketplace-sync] error: jq not found` to stderr, exits 0 (don't block stop on tooling gaps)
- `marketplace.json` missing or unreadable → same: log error, exit 0
- `plugins/` directory missing → treat as empty on-disk set; orphaned-only check still runs
- Any unexpected failure → exit 0. The hook is advisory; it must never block stop on its own bugs

## Loop-safety contract

Exactly one nudge per distinct drift state per checkout. Drift state is fully captured by the sorted `(unregistered, orphaned)` pair. Examples:

| Scenario                                | Behavior                                  |
|-----------------------------------------|-------------------------------------------|
| No drift                                | exit 0 silently, every time               |
| New unregistered plugin appears         | exit 2 with nudge, write hash             |
| Same drift on next Stop                 | exit 0 (hash matches), no re-nudge        |
| Claude registers it → drift gone        | exit 0 silently                           |
| Different new plugin appears            | exit 2 with nudge (hash differs)          |
| Same drift but state file deleted       | exit 2 with nudge (clean slate)           |

The state file is gitignored, so a fresh clone or `rm -rf .claude/state` resets the nudge.

## Testing plan

Manual verification (no automated test framework in this repo):

1. **Baseline (no drift):** with current state, run `bash .claude/hooks/check-marketplace-sync.sh < /dev/null`; expect exit 0, no output.
2. **Unregistered drift:** temporarily remove the harness entry from `marketplace.json`, run the hook; expect exit 2, stderr names `harness-engineering-toolkit` as unregistered. Run again; expect exit 0 (already warned).
3. **Orphaned drift:** restore harness entry, then add a fake `"name": "ghost-plugin"` entry to `marketplace.json`; run hook; expect exit 2 naming `ghost-plugin` as orphaned.
4. **State change re-nudges:** with a drift active and warned, introduce a second drift; expect exit 2 again (hash differs).
5. **Tooling gap:** rename `jq` temporarily (or run with `PATH=/usr/bin`); expect exit 0 with stderr error log, not a block.
6. **End-to-end:** in a real Claude Code session, intentionally add a plugin without registering, ask Claude to stop, verify the reminder lands and Claude can act on it.

Restore `marketplace.json` after manual tests.

## File checklist

- `docs/superpowers/specs/2026-04-16-marketplace-sync-hook-design.md` — this file
- `.claude/hooks/check-marketplace-sync.sh` — new, executable
- `.claude/settings.json` — new
- `.gitignore` — append `.claude/state/`
