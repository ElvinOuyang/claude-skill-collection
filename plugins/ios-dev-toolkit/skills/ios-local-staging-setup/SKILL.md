---
name: ios-local-staging-setup
description: >
  Set up a local staging environment for an iOS + Supabase project from scratch. Creates all the
  infrastructure needed to run an iOS simulator against a local Supabase instance with real production
  data -- compile-time auto-detection, staging auth, env switching scripts, and a prod-to-local data
  snapshot pipeline. Use this skill when setting up local development for a new iOS project, adding
  offline testing capability, creating a staging environment, or when someone says "set up local dev",
  "I want to test on simulator with real data", "add local Supabase support", "make this work offline",
  or "set up staging". This is the SETUP skill (run once per project). For the daily RUN workflow, see
  the `ios-local-staging-run` skill.
---

# iOS Local Staging Setup

One-time setup that adds local staging infrastructure to an iOS + Supabase project. After this, the
simulator automatically talks to a local Supabase instance with real data, while device/TestFlight
builds continue hitting production -- zero manual config switching.

## Prerequisites

Before starting, verify these are installed:

| Tool | Install | Verify |
|------|---------|--------|
| Docker Desktop | [docker.com/desktop](https://docker.com/products/docker-desktop) | `docker info` |
| Supabase CLI | `brew install supabase/tap/supabase` | `supabase --version` |
| Node.js + npm | Already in project | `node --version` |
| Xcode + Simulator | Already in project | `xcrun simctl list devices` |

## What You're Building

The local staging system has four components:

```
┌─────────────────────────────────────────────────────┐
│  iOS Simulator (auto-detects local Supabase)        │
│  - #if DEBUG && targetEnvironment(simulator)        │
│  - --skip-auth launch arg → auto sign-in            │
│  - Falls back to PreviewData if Supabase is down    │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
       Supabase API            Next.js API (optional)
       127.0.0.1:54321         127.0.0.1:3000
               │                      │
┌──────────────┴──────────────────────┴───────────────┐
│  Local Supabase (Docker)                            │
│  - Same schema as production (via migrations)       │
│  - Snapshot of production data for one family       │
│  - Local auth users with known passwords            │
└─────────────────────────────────────────────────────┘
```

## Setup Steps

Work through these in order. Each step produces a specific file or code change.

### Step 1: Initialize Supabase locally

If the project doesn't already have a `supabase/` directory:

```bash
supabase init
```

This creates `supabase/config.toml`. Set the `project_id` to your project name. Migrations go in
`supabase/migrations/` -- if the project already has migrations, they'll apply automatically on
`supabase start`.

If the project already has Supabase set up remotely but no local config, you may need to pull
migrations:

```bash
supabase db pull          # Pull schema from remote into a migration file
```

### Step 2: Create the staging env file

Create `.env.local.staging` at the project root. This points your Next.js (or other web server) at
the local Supabase instance. The anon and service_role keys below are Supabase's well-known local
dev keys -- they're the same for every `supabase start` and safe to commit.

```env
# Local Supabase staging environment
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# Copy over any external API keys from .env.local (AI services, etc.)
# Push notifications typically won't work locally -- keep keys to avoid startup errors
```

Also create a `.env.local.production` backup of the current `.env.local` so scripts can swap between them:

```bash
cp .env.local .env.local.production
```

Add both staging files to `.gitignore` (production backup has real keys):

```gitignore
.env.local.staging
.env.local.production
```

### Step 3: Add iOS compile-time auto-detection

This is the key pattern. The iOS app detects `#if DEBUG && targetEnvironment(simulator)` at compile
time and switches all URLs to localhost. No runtime config, no build schemes, no xcconfig switching.

**SupabaseService (or your Supabase client singleton):**

```swift
@MainActor
final class SupabaseService: Sendable {
    static let shared = SupabaseService()
    let client: SupabaseClient

    /// True when running on the simulator in a Debug build.
    nonisolated static let isLocalStaging: Bool = {
        #if DEBUG && targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }()

    private init() {
        let urlString: String
        let key: String

        #if DEBUG && targetEnvironment(simulator)
        // Local Supabase -- well-known dev keys, same for every `supabase start`.
        urlString = "http://127.0.0.1:54321"
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
        #else
        // Production -- read from Info.plist / xcconfig / environment
        urlString = Bundle.main.infoDictionary?["SUPABASE_URL"] as? String ?? ""
        key = Bundle.main.infoDictionary?["SUPABASE_ANON_KEY"] as? String ?? ""
        #endif

        client = SupabaseClient(
            supabaseURL: URL(string: urlString)!,
            supabaseKey: key
        )
    }
}
```

**Any service that calls your web API** (e.g., a butler/chat endpoint on Vercel):

```swift
init(baseURL: URL? = nil) {
    if let baseURL {
        self.baseURL = baseURL
    } else if SupabaseService.isLocalStaging {
        self.baseURL = URL(string: "http://127.0.0.1:3000")!
    } else {
        self.baseURL = URL(string: "https://your-app.vercel.app")!
    }
}
```

### Step 4: Add --skip-auth launch argument support

The `--skip-auth` launch argument lets the simulator bypass OAuth entirely. When local Supabase is
running, it signs in with email/password. When it's not, it falls back to hardcoded preview data.

**In your App struct:**

```swift
@main
struct YourApp: App {
    var body: some Scene {
        WindowGroup {
            Group {
                #if DEBUG
                if CommandLine.arguments.contains("--skip-auth") {
                    MainTabView()  // Skip the login screen entirely
                } else {
                    authGatedContent
                }
                #else
                authGatedContent
                #endif
            }
            .task { await startApp() }
        }
    }

    private func startApp() async {
        #if DEBUG
        if CommandLine.arguments.contains("--skip-auth") {
            if SupabaseService.isLocalStaging {
                do {
                    try await authService.signInForLocalStaging()
                } catch {
                    loadPreviewData()  // Supabase not running -- use mock data
                    return
                }
            } else {
                loadPreviewData()
                return
            }
        }
        #endif
        // Normal auth flow...
    }
}
```

**In your AuthService:**

```swift
#if DEBUG
/// Sign in with email/password for local staging (simulator only).
/// The snapshot script creates users as `{name}@staging.local` with password `staging123`.
func signInForLocalStaging(email: String = "owner@staging.local") async throws {
    try await supabase.auth.signIn(email: email, password: "staging123")
}
#endif
```

**In Xcode scheme** (optional but recommended): Edit scheme > Run > Arguments > add `--skip-auth`
to "Arguments Passed on Launch". This way Xcode always passes it when running on the simulator.

### Step 5: Create the data snapshot script

This script copies production data into local Supabase, scoped to a single family/org/user. It:
1. Finds the owner's data in production via the Supabase REST API
2. Clears local tables
3. Creates local auth users with a known password (`staging123`)
4. Imports the production data

Create `scripts/snapshot-prod-to-local.sh`. The script should:

```bash
#!/bin/bash
# Snapshot production data into local Supabase.
# Prerequisites: supabase start, .env.local.production exists
set -euo pipefail

# --- Configuration (customize per project) ---
OWNER_EMAIL="owner@example.com"
STAGING_PASSWORD="staging123"
TABLES=(table1 table2 table3)  # Your tables in FK-safe order

# --- Load production credentials ---
PROD_URL=$(grep '^NEXT_PUBLIC_SUPABASE_URL=' .env.local.production | cut -d= -f2-)
PROD_KEY=$(grep '^SUPABASE_SERVICE_ROLE_KEY=' .env.local.production | cut -d= -f2-)

# --- Local Supabase (well-known keys) ---
LOCAL_URL="http://127.0.0.1:54321"
LOCAL_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

# Step 1: Find owner in production
# Step 2: Export tables filtered by owner's scope (family_id, org_id, etc.)
# Step 3: Clear local DB (reverse FK order)
# Step 4: Create auth users via Supabase Admin API
# Step 5: Import data via REST API with Prefer: resolution=merge-duplicates
# Step 6: Verify by signing in and checking RLS
```

Key implementation details:
- Use `curl` + Supabase REST API for both export and import (no pg_dump needed)
- Filter production data by the owner's scope (family, org, team) -- never copy everything
- Create auth users via `POST /auth/v1/admin/users` with `email_confirm: true`
- Use email format `{name}@staging.local` so local users are obviously not production
- Clear tables in reverse FK order to avoid constraint violations
- Verify at the end by signing in as the owner and checking row counts

### Step 6: Create the dev-staging script

Create `scripts/dev-staging.sh` that starts the full stack in one command:

```bash
#!/bin/bash
# Start the full local staging environment.
# Usage: npm run dev:staging
set -euo pipefail
cd "$(dirname "$0")/.."

# Check Docker
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker is not running. Please start Docker Desktop."
  exit 1
fi

# Ensure Supabase is running
if supabase status >/dev/null 2>&1; then
  echo "[staging] Local Supabase is already running."
else
  echo "[staging] Starting local Supabase..."
  supabase start
fi

# Switch env to staging
cp .env.local.staging .env.local
echo "[staging] Switched .env.local to local Supabase"

# Restore production env on exit
cleanup() {
  if [ -f .env.local.production ]; then
    cp .env.local.production .env.local
    echo "[staging] Restored .env.local to production"
  fi
}
trap cleanup EXIT

# Start Next.js bound to 0.0.0.0 so simulator can reach it
echo "[staging] Starting dev server..."
npx next dev -H 0.0.0.0
```

Add an npm script:

```json
"dev:staging": "bash scripts/dev-staging.sh"
```

### Step 7: Configure App Transport Security

The simulator needs to make HTTP (not HTTPS) requests to `127.0.0.1`. Add an ATS exception in your
`Info.plist` (or via Xcode target > Info > Custom iOS Target Properties):

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsLocalNetworking</key>
    <true/>
</dict>
```

`NSAllowsLocalNetworking` permits HTTP connections to localhost/loopback addresses only. It's safe
for App Store review -- Apple explicitly allows it and it has no effect on production network
requests.

Without this, Supabase and API calls to `http://127.0.0.1` will silently fail on the simulator.

### Step 8: Add PreviewData fallback

Create a `PreviewData.swift` file (under a `Debug/` folder) that provides hardcoded mock data for
when local Supabase isn't running. This lets the simulator still show a populated UI even without
Docker.

```swift
#if DEBUG
enum PreviewData {
    static let currentMember = Member(id: ..., name: "Test User", ...)
    static let members: [Member] = [...]
    static let messages: [Message] = [...]
    // Add whatever your app needs to render a populated state
}
#endif
```

### Step 9: Configure Xcode scheme

In the Xcode scheme for the simulator target:
1. Edit Scheme > Run > Arguments
2. Add `--skip-auth` to "Arguments Passed on Launch"
3. This is optional -- you can also pass it via `xcrun simctl launch ... -- --skip-auth`

## Verification

After setup, run through this sequence to confirm everything works end-to-end.

### Functional checks

- [ ] `supabase start` -- local Supabase starts, migrations apply
- [ ] `./scripts/snapshot-prod-to-local.sh` -- data imports, verification passes
- [ ] `npm run dev:staging` -- Next.js starts pointed at local Supabase, env restores on Ctrl+C
- [ ] Build and run on simulator -- app auto-connects to `127.0.0.1:54321`
- [ ] `--skip-auth` -- app signs in as staging user
- [ ] Kill Supabase, relaunch app -- falls back to PreviewData gracefully
- [ ] Build for device -- still connects to production (compile-time switch)

### Visual verification (required)

The functional checks above confirm the plumbing works, but you need to visually confirm real
production data is showing -- not empty states, skeleton loading, or hardcoded preview data. Use
the `ios-simulator-nav` skill's AXe CLI:

```bash
# Screenshot the app after launching with --skip-auth
axe screenshot --udid $UDID --output /tmp/staging_setup_verify.png

# Inspect the accessibility tree for real content
axe describe-ui --udid $UDID
```

**What to look for:**

| Signal | Real data (setup worked) | Preview/empty (something broke) |
|--------|--------------------------|----------------------------------|
| User name | Real name from production | "Test User" |
| Task list | Real tasks with dates and assignees | "All caught up!" or skeletons |
| Item count | Matches snapshot output (e.g., "67 tasks") | 0 or a handful of hardcoded items |
| Chat history | Real messages with timestamps | Canned preview messages or empty |

If you see preview/empty state, check: Is Supabase running? Was snapshot run? Was `--skip-auth`
passed? See the `ios-local-staging-run` skill's troubleshooting section for the full decision tree.

## Gotchas

- **Docker socket**: If `supabase start` fails with "Cannot connect to Docker daemon" but `docker info`
  works, Docker Desktop may not be fully started. The socket at `~/.docker/run/docker.sock` takes a
  few seconds to appear after launch. Run `open -a "Docker Desktop"` and wait.

- **Bundle ID**: When launching via `xcrun simctl launch`, always look up the actual bundle ID from
  the built app -- never hardcode or guess it. Bundle IDs are often surprising (e.g.,
  `com.ppklabs.pumpkintheputler` instead of `com.pumpkin.family`). Use:
  ```bash
  BUNDLE_ID=$(plutil -extract CFBundleIdentifier raw path/to/YourApp.app/Info.plist)
  ```

- **IPv4 binding**: The simulator resolves `localhost` to IPv6 on some macOS versions. Bind your
  dev server to `0.0.0.0` explicitly (e.g., `next dev -H 0.0.0.0`) and use `127.0.0.1` in the
  iOS code, not `localhost`.

- **RLS policies**: Your production RLS policies apply in local Supabase too. The snapshot script
  must create auth users with the same UUIDs as production so that row-level security works
  correctly with the imported data.

## Related Skills

- **`ios-local-staging-run`** -- Daily workflow: start the stack, snapshot data, launch the simulator.
  Use that skill after this setup is complete.
- **`ios-simulator-nav`** -- Navigate the running simulator via AXe CLI.
- **`ios-testflight-deploy`** -- Deploy to physical devices via TestFlight.
