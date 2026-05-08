# AXe CLI for iOS audits

AXe is the right tool for iOS simulator audits because it interacts via accessibility labels, not screen coordinates. That makes the audit stable across device size, orientation, and minor UI tweaks — and it's the user's stated preference (do not fall back to coordinate-based tools).

If AXe is not on the user's machine, stop and ask them to install it before proceeding.

## Commands the audit uses

### Navigation

```
axe tap "Sign in"            # tap by accessibility label
axe tap-by-id "signInButton" # tap by accessibility identifier
axe swipe up                 # swipe gestures
```

### Capture

```
axe screenshot --output .audit/shots/<screen>.png
axe describe-ui --json > .audit/trees/<screen>.json
```

`describe-ui` returns the full accessibility tree with frames, labels, identifiers, and (for text elements) font name + size + weight. This is the primary data source for the audit.

### Color sampling

AXe doesn't give you computed color directly. For a color check, screenshot the screen and sample pixels at the center of the target element's frame (from `describe-ui`). The bundled audit pipeline does this — see the main SKILL.md for the diff step.

### Font verification

The accessibility tree for a `UILabel` carries font family + size. Compare these directly against the typography rule from the spec. Note: if the simulator falls back to a system font because the custom family didn't load, the AX tree will report the fallback, which is exactly the bug the audit is trying to catch.

## What NOT to do

- **No `xcrun simctl` coordinate taps.** Brittle and the user has explicitly preferred AXe.
- **No computer-use MCP.** Same reason. AXe is the supported path.
- **No "just take a screenshot and eyeball it".** Use `describe-ui` to get structured data the audit can diff.
