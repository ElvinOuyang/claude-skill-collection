---
name: ios-local-staging-run
description: >
  Run the local staging environment for an iOS + Supabase project. Starts Docker, boots local
  Supabase, snapshots production data, starts the dev server, builds and launches the iOS app on the
  simulator with real data. Use this skill for the daily development workflow after the one-time setup
  is done. Trigger on: "run staging", "start local dev", "launch simulator with data", "test on
  simulator", "run local supabase", "start the staging stack", "test with real data", "boot simulator",
  "run the app locally", "offline testing", "simulator testing", "dev:staging", "snapshot prod data",
  "refresh staging data". This skill handles Docker socket issues, bundle ID lookup, env switching,
  and the full startup sequence that you cannot know from general knowledge. For first-time setup, see
  the `ios-local-staging-setup` skill instead.
---

# iOS Local Staging Run

Daily workflow for running an iOS app on the simulator against a local Supabase instance with real
production data. Assumes the one-time setup from `ios-local-staging-setup` is already done.

## Quick Start (if everything is already set up)

```bash
supabase start                        # Start local Supabase
./scripts/snapshot-prod-to-local.sh   # Copy production data into local DB
npm run dev:staging                    # Start Next.js pointed at local Supabase
# Build & run in Xcode simulator with --skip-auth
```

## Full Startup Sequence

Follow this decision tree. Each step depends on the previous one.

```
1. Is Docker running?
   ├─ No  → open -a "Docker Desktop", wait for socket
   └─ Yes → continue

2. Is local Supabase running?
   ├─ No  → supabase start
   ├─ Stuck ("already running" error) → supabase stop --no-backup && supabase start
   └─ Yes → continue

3. Does local DB have data?
   ├─ No / stale → ./scripts/snapshot-prod-to-local.sh
   └─ Yes → continue (skip if data is fresh enough)

4. Is the dev server running? (only needed if app calls a web API)
   ├─ No  → npm run dev:staging (background)
   └─ Yes → continue

5. Build and launch on simulator
   → xcodebuild, xcrun simctl install, xcrun simctl launch
```

### Step 1: Start Docker

```bash
# Check if Docker daemon is responsive
docker info >/dev/null 2>&1 || open -a "Docker Desktop"

# Wait for the socket to be ready (takes a few seconds after launch)
for i in $(seq 1 30); do
  docker ps >/dev/null 2>&1 && echo "Docker ready" && break
  sleep 2
done
```

**Common issue**: `docker info` may succeed but `docker ps` fails because the Docker Desktop socket
(`~/.docker/run/docker.sock`) isn't ready yet. The `supabase` CLI uses this socket, not
`/var/run/docker.sock`. Just wait -- it typically takes 5-10 seconds after launching Docker Desktop.

### Step 2: Start local Supabase

```bash
supabase start
```

This applies all migrations in `supabase/migrations/` and starts the local Postgres, Auth, REST API,
and Realtime services. First run pulls ~1GB of Docker images.

**If it says "already running" but containers aren't healthy:**

```bash
supabase stop --no-backup && supabase start
```

The `--no-backup` flag is important here -- it discards the Docker volume completely so you get a
clean slate. Plain `supabase stop` (without `--no-backup`) preserves the volume, which can leave
corrupted state behind. Since you'll re-snapshot data in the next step anyway, always use
`--no-backup` when recovering from a stuck state.

**Verify it's up:**

```bash
supabase status
# Should show API URL: http://127.0.0.1:54321
```

### Step 3: Snapshot production data

```bash
./scripts/snapshot-prod-to-local.sh
```

This copies the owner's data from production into local Supabase and creates auth users. You only
need to re-run this when:
- Production data has changed and you want fresh data
- You ran `supabase stop --no-backup` (which wipes the volume)
- The local DB is empty (first time)

The script verifies itself at the end by signing in and checking row counts.

### Step 4: Start the dev server

Only needed if the iOS app calls a server-side API (e.g., an AI chat endpoint).

```bash
npm run dev:staging
```

This script:
1. Checks Docker and Supabase are running
2. Swaps `.env.local` to point at local Supabase
3. Starts Next.js bound to `0.0.0.0` (so simulator can reach it at `127.0.0.1:3000`)
4. Restores `.env.local` to production when you Ctrl+C

If you don't have this npm script, start your dev server manually and make sure your env points at
local Supabase.

### Step 5: Build, install, and launch

```bash
# Find the simulator UDID
UDID=$(xcrun simctl list devices available | grep "iPhone 16 Pro" | grep -oE '[A-F0-9-]{36}' | head -1)

# Build (quiet mode suppresses xcodebuild noise)
xcodebuild -scheme YourApp -destination "id=$UDID" -quiet build

# Find the built .app
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "YourApp.app" \
  -path "*/Debug-iphonesimulator/*" -maxdepth 5 2>/dev/null | head -1)

# Get the actual bundle ID (don't guess!)
BUNDLE_ID=$(plutil -extract CFBundleIdentifier raw "$APP_PATH/Info.plist")

# Install and launch with --skip-auth
xcrun simctl install $UDID "$APP_PATH"
xcrun simctl launch $UDID $BUNDLE_ID -- --skip-auth
```

**Important**: Always look up the bundle ID from the built app's `Info.plist`. Bundle IDs are often
not what you'd guess (e.g., `com.ppklabs.pumpkintheputler` instead of `com.pumpkin.family`).

### Step 6: Visual verification

This step is critical -- without it you won't know if data actually loaded. Use the
`ios-simulator-nav` skill's AXe CLI to inspect what's on screen.

```bash
# Screenshot the current state
axe screenshot --udid $UDID --output /tmp/staging_verify.png

# Inspect the accessibility tree for real content
axe describe-ui --udid $UDID
```

**How to tell if staging data loaded correctly:**

| Signal | Real data (good) | Preview/empty (bad) |
|--------|------------------|---------------------|
| Task list | Real task names, dates, assignees | "All caught up!" or skeleton placeholders |
| User name | Real name from production | "Test User" |
| Task count | Matches snapshot output (e.g., "67 tasks") | 0 tasks or a handful of fake ones |
| Chat history | Real message history with timestamps | Hardcoded preview messages or empty |
| Profile card | Real family member stats (Overdue/Active/Done > 0) | All zeros |

**Quick AXe checks:**

```bash
# Look for the empty state indicator -- if this appears, data didn't load
axe describe-ui --udid $UDID | grep -i "all caught up\|no tasks\|test user"

# Look for real content -- task names, member names from your production data
axe describe-ui --udid $UDID | grep -i "AXLabel"
```

If the app shows empty/preview state after launching, see the Troubleshooting section below. The
most common fix is re-running the snapshot script.

**Navigate through tabs** to verify data across the app (tabs are often not in the accessibility
tree -- use coordinates from SIMULATOR_MAP.md or discover them per the `ios-simulator-nav` skill):

```bash
# Screenshot each major tab to confirm data throughout
axe tap -x 40 -y 810 --udid $UDID    # Tasks tab
sleep 1 && axe screenshot --udid $UDID --output /tmp/staging_tasks.png

axe tap -x 120 -y 810 --udid $UDID   # Calendar tab
sleep 1 && axe screenshot --udid $UDID --output /tmp/staging_calendar.png

axe tap -x 200 -y 810 --udid $UDID   # Chat tab
sleep 1 && axe screenshot --udid $UDID --output /tmp/staging_chat.png
```

The tab coordinates above are approximate -- adjust for your app's layout or use the
`ios-simulator-nav` skill to discover the correct tap targets.

## Restarting vs Refreshing

| Scenario | What to do |
|----------|-----------|
| Made code changes (Swift) | Rebuild + relaunch (step 5) |
| Made code changes (web API) | Dev server auto-reloads, just retry in app |
| Want fresh production data | Re-run snapshot script (step 3) |
| Supabase is unhealthy | `supabase stop --no-backup && supabase start`, then snapshot |
| Docker crashed | Restart Docker Desktop, then `supabase start` |
| Switching branches | Rebuild, potentially re-run snapshot if schema changed |

## Shutting Down

```bash
# Stop the dev server: Ctrl+C (env auto-restores to production)

# Stop Supabase (data persists in Docker volume for next time)
supabase stop

# Or stop and wipe all data (you'll need to re-snapshot next time)
supabase stop --no-backup
```

## Troubleshooting

### "Cannot connect to Docker daemon"
Docker Desktop is not fully started. Run `open -a "Docker Desktop"` and wait for `docker ps` to
succeed. The Supabase CLI specifically needs `~/.docker/run/docker.sock` which appears a few seconds
after the Docker app launches.

### "supabase start is already running"
A previous `supabase start` is stuck or zombie containers are lingering. The fix is always the same:

```bash
supabase stop --no-backup && supabase start
./scripts/snapshot-prod-to-local.sh
```

Use `--no-backup` (not plain `supabase stop`) to ensure corrupted Docker volumes are fully cleared.
Then re-snapshot because `--no-backup` wipes all data.

### App shows "All caught up!" / empty state
The app fell back to PreviewData, which means either:
- Local Supabase isn't running (check `supabase status`)
- The snapshot script wasn't run (check `./scripts/snapshot-prod-to-local.sh`)
- The app wasn't launched with `--skip-auth`

To recover, run the full fix sequence and **verify each step**:

```bash
# 1. Ensure Supabase is healthy
supabase status  # Should show all services with correct ports

# 2. Check if DB has data
curl -s "http://127.0.0.1:54321/rest/v1/tasks?select=id&limit=1" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
# Should return rows, not []

# 3. If empty, re-snapshot
./scripts/snapshot-prod-to-local.sh

# 4. Relaunch app and verify real data appears
xcrun simctl terminate $UDID $BUNDLE_ID
xcrun simctl launch $UDID $BUNDLE_ID -- --skip-auth
# Take a screenshot to confirm real data, not empty state
```

### App shows skeleton loading forever
The simulator is connecting to local Supabase but auth failed. Check:
- Was the snapshot script run after the last `supabase stop --no-backup`?
- Does `curl http://127.0.0.1:54321/rest/v1/` respond?

### "simulator not found" or install fails
Boot the simulator first: `xcrun simctl boot $UDID`. The `xcodebuild build` command may boot it
automatically, but `simctl install` requires it to be running.

### Dev server not reachable from simulator
Make sure the server binds to `0.0.0.0`, not just `localhost`. The iOS simulator resolves
`127.0.0.1` correctly but may have issues with `localhost` (IPv6 on some macOS versions).

## Related Skills

- **`ios-local-staging-setup`** -- One-time setup: create scripts, configure auto-detection, add env files.
- **`ios-simulator-nav`** -- Navigate the running simulator via AXe CLI.
- **`ios-testflight-deploy`** -- Deploy to physical devices via TestFlight.
