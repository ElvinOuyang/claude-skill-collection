# AXe CLI for iOS audits

AXe is the right tool for iOS simulator audits because it interacts via accessibility labels and identifiers, not screen coordinates. That makes the audit stable across device size, orientation, and minor UI tweaks — and it's the user's stated preference (do not fall back to coordinate-based tools).

**This file is a usage cheatsheet for the audit. The authoritative AXe reference lives at `plugins/ios-dev-toolkit/skills/axe/SKILL.md` — defer to it for command shapes, flags, and behavior. Do not re-document AXe here; only document how the audit uses it.**

If AXe is not on the user's machine, stop and ask them to install it before proceeding.

## Step 0 — pick a simulator UDID

Every interaction command requires `--udid <UDID>`. Run once at the start of the audit:

```bash
axe list-simulators
```

Pick the booted simulator running the app and use that UDID for every subsequent command. If multiple sims are booted, ask the user which one is running the build under audit.

## Commands the audit uses

All examples below assume `UDID=<the-target-simulator-udid>` is in scope.

### Navigation

```bash
axe tap --label "Sign in" --udid "$UDID"           # tap by accessibility label
axe tap --id "signInButton" --udid "$UDID"         # tap by accessibility identifier
axe swipe --direction up --udid "$UDID"            # swipe gestures (see `axe swipe --help`)
```

Prefer selector taps over coordinates. Use `axe describe-ui --udid "$UDID"` first to discover available labels and identifiers.

For multi-step flows prefer `axe batch` (one process invocation, reuses the HID session, supports `--wait-timeout` for selector polling). See the AXe skill, Step 5, for the full batch contract.

### Capture

```bash
axe screenshot --udid "$UDID" --output .audit/shots/<screen>.png
axe describe-ui --udid "$UDID" > .audit/trees/<screen>.json
```

`describe-ui` returns the accessibility tree: labels, identifiers, frames (x/y/width/height), and element types. **It does not return font family, font size, font weight, or rendered colors.** Treat it as the source of truth for *layout* and *which element is where*, not for typography or color.

### Color sampling — gap, with a workable path

AXe does not expose computed colors. The audit handles this by:

1. `axe screenshot` to capture the rendered screen as PNG.
2. `axe describe-ui` to find the target element's frame `(x, y, w, h)`.
3. Use the bundled helper `scripts/sample_pixel.py <screenshot.png> <x> <y>` (this skill ships it) to read the pixel at the element's center. Compare the sampled hex against the spec token.

The helper is intentionally simple — it is *not* doing OCR or layer extraction; it just reads one pixel. That is enough to catch "primary CTA shipped with the wrong hex" but is **not** sufficient for gradients, translucent overlays, or anti-aliased edges. For those, flag as P3 ("manual visual verification needed") rather than over-claiming a result.

### Font / typography verification — gap, be explicit

Neither `axe describe-ui` nor `axe screenshot` carries typography metadata (font family, point size, weight, line-height). This is a real limitation of the AXe path.

Workable options, in order of preference:

1. **Source-of-truth check**: read the SwiftUI / UIKit code for the element (`Text(...).font(.body)`, `UIFont.preferredFont(forTextStyle: .body)`) and compare against the spec. This is not "auditing the running app", but it is honest.
2. **Bundle-level check**: confirm the custom font file is in the app bundle (`Info.plist` `UIAppFonts`, file present in target). Catches the "font didn't ship" failure mode.
3. **Visual snapshot check**: include the screenshot crop in the report and ask a human to confirm the typography looks right. Mark as P3 advisory.

Do **not** claim AXe verified the font — it didn't. The audit report should label typography findings as "static analysis" or "visual" rather than "runtime-verified".

### Frame / spacing verification — supported

`describe-ui` frames are real runtime values. Spacing rules ("card padding == 16pt") can be checked by computing `child.x - parent.x` and `child.y - parent.y` from the tree and diffing against the spec.

## What NOT to do

- **No `xcrun simctl` coordinate taps.** Brittle and the user has explicitly preferred AXe.
- **No computer-use MCP.** Same reason. AXe is the supported path.
- **No "just take a screenshot and eyeball it" for color/spacing.** Use `describe-ui` frames + the pixel-sampling helper for objective values where AXe supports it. For typography, be explicit that this is a gap.
- **No commands without `--udid`.** Every interaction command requires it; only `list-simulators` and `init` do not.
