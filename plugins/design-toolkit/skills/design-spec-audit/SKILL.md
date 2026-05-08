---
name: design-spec-audit
description: >
  Audit a running app against its DESIGN.md / design spec by driving the actual app — not just
  reading source. Walks every screen of the running app (iOS via the AXe CLI, web via
  Playwright), captures screenshots, measures computed colors, spacing, typography, component
  variants, and motion timings, then diffs each against the spec's tokens and rules. Returns a
  P0–P3 prioritized gap list with screenshots, exact divergences ("button padding is 14pt,
  spec says 16pt"), and proposed fixes. Use whenever the user says "design audit", "spec
  audit", "audit against DESIGN.md", "design conformance check", "does the app match the
  design", "design QA", "verify design implementation", "are we on spec", "check tokens", or
  any variant where a running app needs to be checked against a design source of truth. Use
  this proactively before TestFlight / production releases when a DESIGN.md exists, since
  static review misses runtime divergences.
---

# Design Spec Audit

Verify a running app actually matches its design spec. Static code review catches obvious mistakes but misses the things that hurt most: a token referenced correctly but resolving to the wrong value at runtime, padding that's specced 16pt but rendered 14pt due to a stack default, a font weight that falls back because the family didn't load on device.

The whole point of this skill is to **drive the app**, not just grep the source.

## Required inputs

1. **The spec.** Usually `DESIGN.md`, sometimes `docs/design-system.md`, `design-tokens.json`, or a Figma export. Find it first; if none exists, stop and ask the user where the source of truth is — auditing without a spec is just opinion.
2. **A running instance.** iOS sim with the app launched, or a web app accessible at a URL. If not running, ask the user to launch it.
3. **A screen list.** Either the user provides one, or derive from the navigation graph. Don't audit "every possible screen" — pick the user-facing top 10–20 by traffic.

## Tooling — read this before doing anything

This is a recurring user preference, so be unambiguous:

- **iOS: use the AXe CLI.** Not the computer-use MCP, not coordinate taps, not screenshots-and-eyeball. AXe gives label-based interaction and structured accessibility-tree dumps that the audit can measure against. **The authoritative AXe reference for command shapes, flags, and behavior is `plugins/ios-dev-toolkit/skills/axe/SKILL.md` — defer to it.** This skill's `references/axe-ios.md` is a cheatsheet for how the audit *uses* AXe; it does not redefine AXe's contract.
- **Web: use Playwright** (the MCP if available, otherwise scripted Playwright). Playwright exposes `getComputedStyle` for any element, which is exactly what the audit needs.

Every AXe interaction command requires `--udid <UDID>`. Run `axe list-simulators` first, pick the simulator running the build under audit, and reuse that UDID for the rest of the audit. Commands without `--udid` will not work for simulator interaction.

If the user is on iOS and AXe isn't installed, stop and ask them to install it before proceeding. Don't fall back to coordinate taps — past sessions have shown this is the user's biggest pet peeve.

## The audit, step by step

### Step 1: Parse the spec into checkable rules

Convert the spec into a flat list of rules with a category and a value. Categories:

| Category | Example rule |
|---|---|
| Color tokens | `accent.primary == #2D8CFF` |
| Spacing scale | `spacing.md == 16pt`; padding inside cards must be `spacing.md` |
| Typography | `body.regular == SF Pro 17pt 400 line-height 1.4` |
| Component variant | Primary button uses `accent.primary` background, `text.onAccent` foreground |
| Motion | Modal presentation = 250ms ease-out |
| Layout | Card corner radius = 12pt |

If the spec is loose ("buttons feel snappy"), that's a P3 advisory at best — flag it for the user to tighten the spec rather than auditing against vibes.

Save the rule list to `.audit/rules.json` so the user can review and edit before the run.

### Step 2: Walk each screen

For each screen on the list:

1. **Navigate** — iOS: `axe tap --label "<text>" --udid "$UDID"` or `axe tap --id "<identifier>" --udid "$UDID"`. Web: Playwright `click`. Never coordinates.
2. **Screenshot** — iOS: `axe screenshot --udid "$UDID" --output <path>`. Web: Playwright. Capture full screen and per-component crops for the report.
3. **Capture state**:
   - **iOS**: `axe describe-ui --udid "$UDID"` returns the accessibility tree with **frames, labels, and identifiers** — that is the source of truth for *layout* and *which element is where*. It does **not** return font family/size/weight or computed colors. For color spot-checks, use the bundled `scripts/sample_pixel.py` helper to read a pixel from the screenshot at the element's center frame coordinate. For typography, fall back to source-of-truth code review or visual confirmation, and label the finding accordingly — do not claim AXe verified it. See `references/axe-ios.md` for the full set of gaps and workable paths.
   - **Web**: for each element matching the spec's selectors, capture `getComputedStyle` (color, background-color, padding, margin, font-family, font-size, font-weight, line-height, border-radius, transition).
4. **Diff** captured values against the rules. Report every divergence — even small ones; the user decides what to fix based on severity. Tag each finding with how it was verified: `runtime-axe-frame`, `runtime-pixel-sample`, `runtime-computed-style`, `static-source`, or `visual-manual`. The provenance matters because pixel-sampling and source review are weaker signals than `getComputedStyle`.

See `references/axe-ios.md` and `references/playwright-web.md` for the exact commands.

### Step 3: Categorize findings by severity

- **P0 — broken or unbrandable.** Wrong primary color, illegible contrast, missing critical font fallback. Ship-blocker.
- **P1 — clearly off-spec on a high-traffic surface.** Primary CTA padding is 14pt instead of 16pt. Visible to most users.
- **P2 — off-spec on a less-trafficked surface, or on a secondary element.** Settings screen uses spacing.sm where spec says spacing.md.
- **P3 — advisories.** Spec is ambiguous; behavior is plausible but worth tightening the spec.

Don't auto-bucket by category — a typography miss can be P0 (wrong family on every screen) or P3 (one localized line-height drift). Bucket by user impact.

### Step 4: Produce the report

Write `.audit/report.md` with:

```
# Design Spec Audit — <project> — <date>

Spec: <path>  ·  Audited screens: <N>  ·  Findings: <P0=x P1=x P2=x P3=x>

## P0
### <screen> — <component>: <one-line summary>
- Spec: `accent.primary == #2D8CFF`
- Actual: `#2A88F9` (computed from `getComputedStyle(button).backgroundColor`)
- Screenshot: `.audit/shots/<screen>-<component>.png`
- Likely cause: token resolves to a hard-coded fallback in `Theme.swift:42`
- Proposed fix: replace literal with `Theme.accent.primary`

## P1
... (same shape)
```

Also produce `.audit/report.html` rendering the markdown alongside the screenshots so the user can scan visually — markdown alone is too dry for a design report.

### Step 5: Hand off

The report is the deliverable. Don't auto-fix — the user decides which findings to ship. If they ask for fixes, work P0 → P1 → P2 in that order, one PR per category to keep review tractable.

## Common failure modes

- **Auditing source code instead of the running app.** This skill exists *because* static review misses runtime divergences. If you find yourself only `grep`-ing, restart with the running app.
- **Reaching for computer-use MCP or coordinate taps on iOS.** Use AXe. The user has flagged this preference repeatedly.
- **Treating all findings as P0.** Categorize by user impact, not by category type. A perfectly-correct screen with one minor margin miss is not P0.
- **Auditing without a spec.** If there's no source of truth, this is opinion, not audit. Ask the user where the spec lives or to write one first.

## Cross-skill handoff

- **Upstream:** `claude-design-inbound` may have produced the DESIGN.md / tokens this skill audits against.
- **Sibling:** `claude-design-outbound` can pick up the report and the screenshots and turn them into an artifact pack the designer can iterate on.
