---
name: ios-testflight-deploy
description: >
  REQUIRED when doing ANY iOS TestFlight deployment or App Store Connect upload. This skill contains
  critical workflow steps, API key auth configuration, sandbox workarounds, and failure recovery that
  you CANNOT know from general knowledge alone -- including gotchas like export path cleanup, build
  number conflicts, sandbox-blocked SPM hooks, and the decision tree for when to deploy from a feature
  branch vs merging server changes first. Trigger on: "deploy to testflight", "upload build", "ship to
  device", "push to testflight", "send build", "testflight upload", "build and upload", "ship it",
  "deploy the app", "test on device", "cut a testflight build", "xcodebuild archive", "exportArchive",
  "agvtool", "app store connect upload", "ipa upload", "beta testers", "testflight release",
  "manual deploy", "device testing loop". Even simple-sounding deploy requests need this skill because
  the auth setup, sandbox configuration, and error handling are non-obvious.
---

# iOS TestFlight Deploy

Deploy iOS builds to TestFlight for device testing during development. Designed for rapid debug loops where you need to get code onto a physical device quickly and repeatedly.

## When to Deploy from Which Branch

Not every deploy needs a merge to master. The deciding factor is whether the iOS app depends on server-side changes that aren't live yet.

```
Does this deploy include server-side changes
the iOS app depends on?
        |
    yes / no
       |        \
       v         v
  Are those      Deploy from
  changes        current branch
  already        (any branch works)
  deployed?
    |
 yes / no
   |      \
   v       v
 Deploy    Merge server
 from      changes first,
 current   wait for deploy,
 branch    THEN deploy iOS
```

**Deploy from any branch** when:
- Changes are iOS-only (UI, animations, bug fixes, new views)
- Server changes the app depends on are already deployed
- You're iterating on a feature branch and want rapid device feedback

**Merge server changes first** when:
- iOS app calls a NEW endpoint that doesn't exist in production yet
- iOS app depends on a CHANGED endpoint signature or response format
- Database migrations are required before the app can function

TestFlight doesn't care about your git branch -- it only cares about bundle ID, version, and build number.

## Prerequisites

### App Store Connect API Key (one-time setup)

Xcode GUI sessions expire unpredictably -- API key auth is persistent and works without Xcode open. Set this up once.

1. Go to [App Store Connect > Users and Access > Integrations > App Store Connect API](https://appstoreconnect.apple.com/access/integrations)
2. Click "+" to generate a new key with "Developer" or "Admin" role
3. Note the **Key ID** (shown in the table) and **Issuer ID** (shown at the top of the page)
4. Download the `.p8` file (you can only download it once)
5. Store it safely:

```bash
mkdir -p ~/.appstoreconnect
mv ~/Downloads/AuthKey_<KEY_ID>.p8 ~/.appstoreconnect/
```

The Key ID in the filename must match the Key ID from the website. If they differ, use the one from the filename -- it's the actual key identifier.

### ExportOptions.plist

Your Xcode project needs an `ExportOptions.plist` for automated uploads. If one doesn't exist, create it in your iOS project directory:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store-connect</string>
    <key>destination</key>
    <string>upload</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
    <key>uploadSymbols</key>
    <true/>
</dict>
</plist>
```

The `destination: upload` key makes `xcodebuild -exportArchive` upload directly to App Store Connect in one step.

## Deploy Workflow

### Step 1: Determine the next build number

The build number must exceed the highest build currently on App Store Connect. Check locally:

```bash
cd <ios-project-dir>
agvtool what-version
```

If you know the latest TestFlight build number, increment from that. When in doubt, ask the user what the latest build number is, or increment generously.

```bash
agvtool new-version -all <NEXT_NUMBER>
```

### Step 2: Archive

```bash
xcodebuild \
  -scheme <SCHEME_NAME> \
  -destination 'generic/platform=iOS' \
  -archivePath /tmp/claude/<AppName>.xcarchive \
  archive
```

This must run with sandbox disabled (`dangerouslyDisableSandbox: true`) because Swift Package Manager needs to copy git hook templates during dependency resolution, which the sandbox blocks.

### Step 3: Export and upload

```bash
rm -rf /tmp/claude/<AppName>Export

xcodebuild -exportArchive \
  -archivePath /tmp/claude/<AppName>.xcarchive \
  -exportOptionsPlist <path-to>/ExportOptions.plist \
  -exportPath /tmp/claude/<AppName>Export \
  -allowProvisioningUpdates \
  -authenticationKeyPath ~/.appstoreconnect/AuthKey_<KEY_ID>.p8 \
  -authenticationKeyID <KEY_ID> \
  -authenticationKeyIssuerID <ISSUER_ID>
```

The export path directory must not exist beforehand -- `xcodebuild` fails if it does. Always `rm -rf` it first.

### Step 4: Confirm

Look for these lines in the output:
```
Upload succeeded.
** EXPORT SUCCEEDED **
```

The build will appear in TestFlight after Apple finishes processing (usually 2-5 minutes). The user can then update the app on their device.

## Rapid Debug Loop Pattern

When iterating on iOS fixes with device testing:

```
Fix code --> Build & upload --> User tests on device --> Reports bug
    ^                                                        |
    |________________________________________________________|
```

Each iteration:
1. Make the fix
2. Run the 3-step deploy (bump, archive, export)
3. Tell the user the build number and that it's processing
4. User updates TestFlight on device and tests
5. Repeat as needed

Don't create a PR for each iteration. Accumulate fixes on the feature branch and create a single PR when the debug loop is done.

## Common Failures

| Error | Cause | Fix |
|---|---|---|
| `Failed to Use Accounts` / `No Accounts` | Xcode GUI session expired | Use API key auth flags (see Step 3) |
| `missing Xcode-Username` | Same as above -- keychain entry missing | Use API key auth flags |
| `Apple Account or password was entered incorrectly` | Wrong Key ID | Key ID must match the `.p8` filename (e.g., `AuthKey_ABC123.p8` means Key ID is `ABC123`) |
| `The directory ... does not contain an Xcode project` | Wrong working directory | Run from the directory containing `.xcodeproj` |
| `fatal: cannot copy ... hooks/commit-msg.sample` | Sandbox blocking SPM git hooks | Run with `dangerouslyDisableSandbox: true` |
| `exportArchive ... already exists` | Export path from previous run | `rm -rf /tmp/claude/<AppName>Export` before export |
| Build number rejected by ASC | Build number already used | Increment build number past the latest on TestFlight |
| `No signing certificate "iOS Distribution" found` | No distribution cert in CLI context | The `-allowProvisioningUpdates` flag with API key auth handles cloud signing automatically |

## Project-Specific Configuration

Store your project's deploy configuration in a memory file or CLAUDE.md so future sessions don't need to rediscover it:

```markdown
## TestFlight Deploy Config
- Scheme: <scheme name>
- ExportOptions: <path to ExportOptions.plist>
- API Key: ~/.appstoreconnect/AuthKey_<KEY_ID>.p8
- Key ID: <KEY_ID>
- Issuer ID: <ISSUER_ID>
- Team ID: <TEAM_ID>
- Current build range: ~<latest build number>
```
