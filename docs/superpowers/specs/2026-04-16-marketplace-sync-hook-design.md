# Marketplace Sync Hook Design

A `Stop` hook that nudges Claude once when plugin directories on disk drift from the registered list in `.claude-plugin/marketplace.json`.

## Context

This repo is a Claude Code plugin marketplace. Each plugin lives at `plugins/<name>/` with metadata at `plugins/<name>/.claude-plugin/plugin.json`, and must be registered in `.claude-plugin/marketplace.json` to appear when users update the marketplace.

The motivating bug: commit `e1fdd07` added the `harness-engineering-toolkit` plugin (4 skills) but forgot to register it in `marketplace.json`. The plugin never appeared in `/plugin` listings until a follow-up fix (`52c90f4`). A mechanical check would have caught this before the first push.

## Goals

- Detect drift between `plugins/*/` directories and `marketplace.json` registered plugins
- Nudge Claude once per distinct drift state, then auto-release on the next Stop within a 120s cooldown (no infinite loops; matches harness convention)
- Stay advisory: if Claude decides not to fix, the next Stop succeeds
- Zero new dependencies beyond what the repo already uses (`jq`, bash, standard POSIX tools)

## Non-Goals (v1)

- Detecting new skills added inside an already-registered plugin (different problem; doesn't strictly require marketplace.json updates)
- Enforcing version bumps when plugin contents change
- Validating plugin.json schema correctness
- A slash command for manual sync (can be added if useful)
- Migration to the full `harness-engineering-toolkit` enforcement system

## Architecture

### Components

**`.claude/scripts/check-marketplace-sync.sh`** — single bash script, the entire detection logic. Located under `scripts/` to match the harness convention.

**`.claude/settings.json`** — wires the script as a `Stop` hook. Committed so all collaborators get the same enforcement.

**`/tmp/marketplace-sync-<repo-cksum>`** — loop-detection state: 3 lines (hash, count, timestamp). Per-machine, outside the repo, no gitignore needed. Matches the harness toolkit's stop-gate convention.

### Data flow

```
Claude attempts Stop
        │
        ▼
.claude/scripts/check-marketplace-sync.sh fires
(wired with `cd $(git rev-parse --show-toplevel)` so cwd = repo root)
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
RESULT = formatted reason string (empty if no drift)
hash   = cksum(RESULT)
        │
        ▼
If RESULT empty:                       → rm loop-key, exit 0 (silent allow stop)
Else apply harness loop-detection:
  - If same hash within COOLDOWN_SECS=120s and BLOCK_COUNT > MAX_BLOCKS=1
                                       → exit 0 (auto-release: already nudged)
  - Else                               → write (hash,count,ts) to /tmp loop-key
                                          echo '{"decision":"block","reason":RESULT}'
                                          exit 0  (Claude sees reason in chat)
```

### Reminder format (becomes the `reason` field in the JSON block payload)

Single-line reason (avoids JSON-newline escaping complexity, mirrors harness convention):

```
[marketplace-sync] Drift between plugins/ and .claude-plugin/marketplace.json. Unregistered on disk: <name1>, <name2>. Orphaned in manifest: <name3>. Fix: edit .claude-plugin/marketplace.json (read plugins/<name>/.claude-plugin/plugin.json for metadata). One-time nudge per drift state; next Stop on the same drift will auto-release.
```

When a section is empty, omit it (e.g. only `Unregistered on disk: ...` if nothing is orphaned). Quotes inside the reason are escaped via `sed 's/"/\\"/g'` before interpolation.

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

`comm` requires sorted input; `printf '%s\n' "$var"` on an empty var produces a blank line that `comm` treats as an entry, so guard for empty:

```bash
diff_unique() {
  # diff_unique <left> <right> <comm-flag>  → lines in left not in right
  local left="$1" right="$2" flag="$3"
  if [ -z "$left" ]; then echo ""; return; fi
  comm "$flag" <(printf '%s\n' "$left") <(printf '%s\n' "${right:- }")
}
unregistered=$(diff_unique "$on_disk" "$registered" -23)
orphaned=$(diff_unique "$registered" "$on_disk" -23)
```

### Build reason and apply harness loop-detection

Follows the canonical pattern in `plugins/harness-engineering-toolkit/skills/harness-extend/SKILL.md` (Stop — Blocking section). Loop-detection block is copied verbatim from that reference:

```bash
# Build single-line reason (empty = no drift = pass)
RESULT=""
if [ -n "$unregistered" ] || [ -n "$orphaned" ]; then
  parts="[marketplace-sync] Drift between plugins/ and .claude-plugin/marketplace.json."
  [ -n "$unregistered" ] && parts="$parts Unregistered on disk: $(echo "$unregistered" | paste -sd, -)."
  [ -n "$orphaned" ]     && parts="$parts Orphaned in manifest: $(echo "$orphaned" | paste -sd, -)."
  parts="$parts Fix: edit .claude-plugin/marketplace.json (read plugins/<name>/.claude-plugin/plugin.json for metadata). One-time nudge per drift state."
  RESULT="$parts"
fi

# --- Harness loop-detection (copied from harness-extend reference) ---
MAX_BLOCKS=1
COOLDOWN_SECS=120
REPO_PATH=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
LOOP_KEY="/tmp/marketplace-sync-$(printf '%s' "$REPO_PATH" | cksum | cut -d' ' -f1)"

if [ -z "$RESULT" ]; then
  rm -f "$LOOP_KEY"
  exit 0
fi

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
  exit 0   # auto-release: same drift repeated within cooldown
fi
# --- End loop-detection ---

ESCAPED=$(printf '%s' "$RESULT" | sed 's/"/\\"/g')
echo "{\"decision\": \"block\", \"reason\": \"${ESCAPED}\"}"
```

## Settings wiring

`.claude/settings.json` (new file). Matches the harness Stop-hook wiring convention — no `matcher` (Stop has no tool name to match on), explicit `cd` to repo root so the script's relative paths resolve:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "cd \"$(git rev-parse --show-toplevel)\" && bash .claude/scripts/check-marketplace-sync.sh"
          }
        ]
      }
    ]
  }
}
```

## Error handling

- `jq` missing → script prints `[marketplace-sync] error: jq not found` to stderr, exits 0 (don't block stop on tooling gaps)
- `marketplace.json` missing or unreadable → same: log error, exit 0
- `plugins/` directory missing → treat as empty on-disk set; orphaned-only check still runs
- Any unexpected failure → exit 0. The hook is advisory; it must never block stop on its own bugs

## Loop-safety contract

`MAX_BLOCKS=1`, `COOLDOWN_SECS=120`. Drift state is fully captured by the cksum of the formatted `RESULT` reason string. Behavior:

| Scenario                                            | Behavior                                            |
|-----------------------------------------------------|-----------------------------------------------------|
| No drift                                            | rm loop-key, exit 0 silently                        |
| New drift appears                                   | block once with reason, write `(hash,1,ts)` to /tmp |
| Same drift on next Stop within 120s                 | count → 2 → exit 0 (auto-release)                   |
| Same drift after 120s gap                           | block again (cooldown expired, count resets)        |
| Claude fixes drift                                  | rm loop-key, exit 0                                 |
| Different drift hash within cooldown                | block with new reason, count resets                 |

The /tmp loop-key is per-machine and per-repo (cksum of `git rev-parse --show-toplevel`). Survives Claude Code session boundaries. Reboot or `rm /tmp/marketplace-sync-*` resets the counter.

## Testing plan

Manual verification (no automated test framework in this repo). Run from repo root; remove `/tmp/marketplace-sync-*` between tests for clean state.

1. **Baseline (no drift):** with current state, run `bash .claude/scripts/check-marketplace-sync.sh < /dev/null`; expect exit 0, no stdout.
2. **Unregistered drift:** temporarily remove the harness entry from `marketplace.json`, run the hook; expect exit 0 with stdout `{"decision":"block","reason":"[marketplace-sync] ... Unregistered on disk: harness-engineering-toolkit ..."}`. Run again immediately; expect exit 0 with no stdout (auto-release on count > MAX_BLOCKS).
3. **Orphaned drift:** restore harness entry, then add a fake `"name": "ghost-plugin"` entry to `marketplace.json`; run hook; expect block JSON naming `ghost-plugin` as orphaned.
4. **Hash-change re-nudges:** with a drift active and counted, introduce a second drift (different plugin); expect block JSON again (new hash resets count).
5. **Cooldown expiry:** trigger a drift, wait 121s, run again; expect block JSON again (counter reset by cooldown).
6. **Tooling gap:** rename `jq` temporarily (or run with `PATH=/usr/bin`); expect exit 0 with stderr error log, no JSON to stdout, no block.
7. **End-to-end:** in a real Claude Code session, intentionally add a plugin without registering, ask Claude to stop, verify the reason text lands in the chat and Claude can act on it.

Restore `marketplace.json` and clear `/tmp/marketplace-sync-*` after manual tests.

## File checklist

- `docs/superpowers/specs/2026-04-16-marketplace-sync-hook-design.md` — this file
- `.claude/scripts/check-marketplace-sync.sh` — new, executable (chmod +x)
- `.claude/settings.json` — new

No `.gitignore` change required — loop-detection state lives in `/tmp`.
