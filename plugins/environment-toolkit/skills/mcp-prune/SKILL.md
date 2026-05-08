---
name: mcp-prune
description: >
  Audit installed MCP servers by token cost, failure rate, and recent usage, then disable the offenders on user confirmation. Use when the user says "help me uninstall some of the failing mcps please", "prune MCPs", "disable failing MCPs", "audit MCPs", "MCP cleanup", "MCPs are slow", "MCPs are failing", "MCPs are token-heavy", "uninstall MCPs", "my context window is full of MCP tools", "trim MCP servers", "which MCPs can I turn off", or otherwise wants to reduce the cost or noise of installed Model Context Protocol servers. Use this skill proactively whenever an env health check flags failing MCPs, when the session's available_tools list is dominated by MCPs the user hasn't touched in days, or when token usage is suspicious and MCP tool descriptions are the obvious bloat. Always preserve a reversible record of what was disabled so the user can undo it later.
---

# MCP Prune

A deliberate, evidence-based pass over installed MCP servers: classify them by usefulness vs cost, warn about capabilities lost, disable the dead weight on confirmation, and write a reversible record.

## Why this skill exists

The triggering session was: *"help me uninstall some of the failing mcps please?"* -- the user had ~20 MCPs configured, several were failing on startup or timing out, and the tool descriptions alone were eating significant context budget. The fix at the time was to disable finance, legal, context7, playwright, supabase, and vercel MCPs, with a clear warning about the capabilities lost (e.g., "disabling playwright MCP means you lose browser automation, but you can still run Playwright via npx").

That kind of pruning is high-leverage but easy to get wrong: turn off the wrong MCP and a long-running workflow silently degrades. So this skill enforces the steps:

1. List every MCP with **evidence** (status, token cost, last successful use).
2. Group into Safe to disable / Consider disabling / Keep.
3. For every candidate disable, explicitly state the **capability lost** and any non-MCP fallback.
4. Disable only on explicit user confirmation.
5. Write a reversible record so undo is one command.

## Workflow

### Step 1: Discover the MCP inventory

MCPs are configured in one of three places:
- `~/.claude.json` (Claude Code, user scope)
- `~/.claude/mcp.json` (older / alternate path)
- `<project>/.mcp.json` (project scope)
- Plugin-bundled MCPs declared by installed plugins

Read all of them and produce a single deduped list. For each MCP capture:

- **Name / key** (as it appears in config)
- **Scope** (user / project / plugin)
- **Transport** (stdio command, http url, etc.)
- **Status** (process running? last connect succeeded? error on stderr?)
- **Tool count** (how many tools it exposes -- a strong proxy for token cost)
- **Last successful tool call** (skim recent session transcripts under `~/.claude/projects/` if present; if not, mark "unknown")
- **Approx token cost** (sum of name + description lengths across the MCP's tools, in tokens; a rough char-count / 4 estimate is fine)

```bash
# Example discovery sketch -- adjust to whatever config exists
ls ~/.claude.json ~/.claude/mcp.json ./.mcp.json 2>/dev/null
python3 - <<'PY'
import json, os, glob
paths = [os.path.expanduser("~/.claude.json"), os.path.expanduser("~/.claude/mcp.json"), ".mcp.json"]
for p in paths:
    if os.path.exists(p):
        try:
            data = json.load(open(p))
            mcps = data.get("mcpServers") or data.get("mcp_servers") or {}
            print(p, "->", list(mcps.keys()))
        except Exception as e:
            print(p, "FAILED TO PARSE:", e)
PY
```

If the active session exposes an MCP via an `mcp__<server>__<tool>` tool naming convention, those names are also evidence the MCP is loaded right now.

### Step 2: Score each MCP

For every MCP, compute a simple triage label:

- **Safe to disable** -- meets at least one:
  - status = failing / never connected
  - tool count is large AND no successful call in the last 30 days
  - duplicates capability already covered by another MCP or by built-in tools
- **Consider disabling** -- meets at least one:
  - high token cost (e.g., >2k tokens of tool descriptions) AND infrequent use
  - flaky (intermittent failures in recent sessions)
  - capability the user can trivially get via CLI/SDK without the MCP wrapper
- **Keep** -- recently used, working, low-cost, or no good non-MCP fallback.

Be conservative. When in doubt, downgrade the recommendation (Safe -> Consider, Consider -> Keep). The cost of a false positive (turning off something the user relies on) is much higher than leaving a borderline MCP enabled.

### Step 3: Present the audit and confirm

Output exactly this structure, then **stop and wait for confirmation** before disabling anything:

```markdown
# MCP Audit -- <YYYY-MM-DD>

Total configured: <N>. Working: <W>. Failing: <F>. Estimated token cost (descriptions only): ~<T> tokens.

## Safe to disable
| MCP | Status | Cost | Last used | Capability lost | Fallback |
|---|---|---|---|---|---|
| finance | failing-on-startup | ~800 tok | never | quote/financial data tools | curl an API directly |
| legal   | failing-on-startup | ~600 tok | never | legal-doc retrieval | none needed -- not used |

## Consider disabling
| MCP | Status | Cost | Last used | Capability lost | Fallback |
|---|---|---|---|---|---|
| playwright | working | ~1.5k tok | 12 days ago | browser automation tools | `npx playwright` directly |
| context7   | flaky   | ~1.2k tok | 4 days ago  | doc-search shortcuts | WebFetch / WebSearch |

## Keep
- supabase (working, used today)
- gmail (working, used today)
- google-calendar (working, used yesterday)

## Proposed action
Disable: finance, legal, playwright, context7.
Net token reduction: ~4.1k tokens of tool descriptions per request.
Reversible via: `<path-to-disabled-record>`.

Reply "confirm" to apply, or list the subset you want to disable.
```

Always show the **fallback** column. The user's most common pushback is "wait, but how do I do X without the MCP?" -- pre-empt it.

### Step 4: Disable on confirmation -- safe-write protocol

`~/.claude.json` is the user's primary Claude Code config. A naive in-place `json.dump(data, open(path, "w"))` will corrupt it on any interruption (Ctrl-C, OOM, disk full, crash). The window between `open(..., "w")` and the final flush is when the file is empty/truncated. **Never write the live config that way.**

You MUST follow this order, every time:

1. **Verify host semantics first.** The `disabledMcpServers` key is the convention this skill uses, but not every Claude Code version reads it back. Confirm the host actually honors it (check release notes, or test on a throwaway config) before relying on it for restore. If you can't confirm, fall back to "remove from `mcpServers` and keep the full original entry in the reversible record" -- restore is then a manual paste, but nothing silently re-enables.
2. **Create the reversible record FIRST (Step 5), before mutating `~/.claude.json`.** If a crash happens mid-write, the user must still have a recovery path on disk. Record-after-mutation is unsafe.
3. **Snapshot a timestamped backup before touching the file:** copy `~/.claude.json` -> `~/.claude.json.bak.YYYYMMDDHHMMSS`. This is the rollback target.
4. **Write atomically:** write the new JSON to a temp file *in the same directory* (so rename is atomic on the same filesystem), `fsync` it, then `os.replace` over the original. Never write directly to the destination path.
5. **Parse-validate after write:** re-open the destination, `json.load` it, and assert the expected shape (e.g. `mcpServers` is a dict, all targeted names are now under `disabledMcpServers`, untouched servers are still present byte-for-byte at the key level). If parsing or shape checks fail, immediately restore from the timestamped backup and stop. Do not retry blindly.

```bash
# Safe-write sketch: backup-first, atomic rename, parse-validate, rollback on failure.
python3 - "$@" <<'PY'
import json, sys, os, shutil, tempfile, datetime, traceback

to_disable = sys.argv[1:]
path = os.path.expanduser("~/.claude.json")
ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
backup = f"{path}.bak.{ts}"

# 0. Sanity: original must parse before we touch anything.
with open(path) as f:
    original_text = f.read()
try:
    data = json.loads(original_text)
except Exception as e:
    sys.exit(f"refusing to mutate: original {path} does not parse: {e}")

# 1. Reversible record FIRST (see Step 5). Do this before any mutation
#    so a crash here leaves the live config untouched.
write_reversible_record(data, to_disable)  # see Step 5

# 2. Timestamped backup BEFORE mutation.
shutil.copy2(path, backup)

# 3. Compute the new state in memory.
active = data.setdefault("mcpServers", {})
disabled = data.setdefault("disabledMcpServers", {})
moved = {}
for name in to_disable:
    if name in active:
        moved[name] = active.pop(name)
disabled.update(moved)

# 4. Atomic write: temp file in same dir -> fsync -> os.replace.
dir_ = os.path.dirname(path) or "."
fd, tmp = tempfile.mkstemp(prefix=".claude.json.", dir=dir_)
try:
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)  # atomic on same filesystem
except Exception:
    # write failed before replace; remove temp and bail. Original is intact.
    try: os.unlink(tmp)
    except FileNotFoundError: pass
    raise

# 5. Parse-validate after write. Roll back on any failure.
try:
    with open(path) as f:
        verify = json.load(f)
    assert isinstance(verify.get("mcpServers", {}), dict)
    for name in moved:
        assert name in verify.get("disabledMcpServers", {}), f"{name} missing post-write"
        assert name not in verify.get("mcpServers", {}), f"{name} still active post-write"
except Exception:
    traceback.print_exc()
    shutil.copy2(backup, path)  # rollback from timestamped backup
    sys.exit(f"post-write validation failed; rolled back from {backup}")

print("disabled:", list(moved.keys()))
print("backup:", backup)
PY
```

The four invariants -- **record-before-mutate**, **backup-before-mutate**, **temp+rename never in-place**, **parse-validate then rollback on failure** -- are non-negotiable. If you find yourself "just this once" calling `json.dump(data, open(path, "w"))` directly, stop and use the protocol above.

### Step 5: Write the reversible record (BEFORE mutating config)

This step runs *before* Step 4's mutation. The reversible record is the user's recovery path; it must exist on disk before the live config is touched.

Write a project-level note (or user-level if there's no project) so the user can undo:

```
.claude/mcp-prune-log.md
```

Append, don't overwrite. Each entry:

```markdown
## 2026-05-07 14:22 -- pruned 4 MCPs

Disabled: finance, legal, playwright, context7

Reason: failing on startup (finance, legal); high token cost and infrequent use (playwright, context7).

Saved config snippet (paste back into `mcpServers` to restore):
```json
{
  "finance": { ... },
  "legal":   { ... },
  "playwright": { ... },
  "context7":   { ... }
}
```

Capabilities lost & fallbacks:
- playwright -> use `npx playwright` from a shell
- context7   -> use WebFetch / WebSearch
- finance, legal -> none needed; not in use
```

Mention this file path in the final summary so the user knows where to look.

### Step 6: Tell the user what to do next

End the run with a short paragraph:

- How many MCPs were disabled and the rough token saving.
- Where the reversible record lives.
- A reminder: "Restart Claude Code (or your host) for tool-list changes to take effect."

## Rules of engagement

- **Never disable an MCP without explicit confirmation.** Even an obviously broken one might be the user's project-of-the-week.
- **Always show the capability lost and a fallback.** This is the difference between pruning and breaking workflows.
- **Be reversible by default.** Move-to-disabled, with a saved config snippet, beats delete every time.
- **Don't editorialize about MCPs you can't measure.** If you don't have evidence on usage or cost, say "unknown" -- guessing is how you turn off the user's daily driver.
- **One audit per session.** This is a deliberate, batched action, not something to redo every time the conversation drifts near MCPs.
- **Never write `~/.claude.json` in place.** Always: write reversible record first, then timestamped backup, then atomic temp-file + `os.replace`, then parse-validate, then rollback on any failure. A corrupted `~/.claude.json` breaks the user's entire Claude Code install.
