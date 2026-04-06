---
name: web-ui-spec-checker
description: Automatically check a running web app's UI against its design spec using Playwright MCP. Use this skill whenever the user wants to verify UI/UX implementation matches designs, catch visual regressions, check color tokens, verify component structure, or audit screens against a spec doc. Trigger on phrases like "check the UI", "verify the design", "are there any UI bugs", "does this match the spec", "playwright UI check", or when a design spec exists and the app is running locally.
compatibility:
  tools: [mcp__plugin_playwright_playwright__browser_navigate, mcp__plugin_playwright_playwright__browser_take_screenshot, mcp__plugin_playwright_playwright__browser_snapshot, mcp__plugin_playwright_playwright__browser_evaluate]
---

# UI Spec Checker

Systematically verify that a running app's UI matches its design spec. Works by reading the spec, navigating each screen with Playwright, and comparing what's rendered against what's specified.

The value is in being methodical: it's easy to spot obvious bugs but miss subtle color drifts, missing components, or wrong spacing. This skill forces a structured pass over every screen.

---

## Setup

**Before starting, confirm:**
1. The dev server is running (`npm run dev` or equivalent). Check with `browser_navigate` to the base URL.
2. You know where the spec lives — ask the user if unsure. Common locations: `docs/superpowers/specs/`, `docs/design/`, `DESIGN.md`.
3. You know which screens to check. If not specified, check all screens listed in the spec.

**Base URL:** Default to `http://localhost:3000`. Ask the user if it's different.

---

## The Check Loop (one screen at a time)

For each screen:

### 1. Read the spec section first
Before navigating, read the spec section for this screen. Note:
- Expected components and their order
- Color tokens and where they apply (background, borders, text, icons)
- Typography (size, weight)
- Interactive states (active tab, selected item)
- Any explicit "must" or "should" requirements

### 2. Navigate and screenshot
```
browser_navigate → <url>/<route>
browser_take_screenshot
```
Give the screenshot a descriptive name like `tasks-overview.png` and save to the outputs directory.

### 3. Get the accessibility snapshot
```
browser_snapshot
```
This gives you the DOM structure and visible text without relying on visual inspection alone. Use it to verify:
- Components that should exist are present
- Labels and text content match the spec
- Navigation items are all there with correct labels

### 4. Spot-check computed styles for key elements
For elements where the spec gives exact values (colors, font sizes, border widths), verify them with:
```
browser_evaluate → (function() {
  const el = document.querySelector('<selector>');
  if (!el) return 'NOT FOUND';
  const s = window.getComputedStyle(el);
  return { color: s.color, backgroundColor: s.backgroundColor, fontSize: s.fontSize, borderLeftColor: s.borderLeftColor, borderLeftWidth: s.borderLeftWidth };
})()
```

You can also use the bundled script: read `scripts/extract_styles.js` and paste into `browser_evaluate`.

**Key things to verify with computed styles:**
- Active tab color (should match spec's "interactive/active" token)
- Task card left border color + width (priority system)
- Background color (warm cream vs white vs gray)
- Heading font weight and size

### 5. Document findings per screen

For each screen, write findings in this format:

```
### <Screen Name> (<route>)
**Status:** ✅ Matches spec | ⚠️ Minor issues | ❌ Significant issues

**Verified:**
- [ list what was checked and matched ]

**Issues found:**
- [ ISSUE: description ] — Spec says X, got Y. Element: <selector>. Screenshot: <filename>.
```

---

## What to Check Per Screen

Use the spec as your source of truth. Common things to verify across most screens:

**Navigation**
- Correct number of tabs
- Correct icons and labels
- Active tab highlighted in the right color
- No extra or missing tabs

**Colors**
- Page background (warm cream `#fdf8f4` or white — spec will say which)
- Interactive elements (buttons, active states) use the correct primary color
- Priority indicators use the correct color per priority level
- Text colors match spec tokens (headings vs body vs muted)

**Typography**
- Screen title weight and size
- Body text size and color
- Labels are uppercase where spec says so

**Components**
- All specified components are present
- Components are in the specified order
- Empty states shown correctly when there's no data

**Task cards (if applicable)**
- 4px left border present
- Border color matches priority
- Meta chips row visible
- No badge/pill priority indicators (spec uses borders, not pills)

---

## Interaction Checks

For interactive elements in the spec:

```
browser_click → <element>
browser_take_screenshot   ← capture the state change
browser_snapshot          ← verify DOM updated correctly
```

Key interactions to test:
- Tab switching: click each tab, verify active state changes
- Task card tap: verify it navigates to detail
- Checkbox (My Tasks): tap, verify visual feedback

---

## Output: Bug Report

After checking all screens, write a `bug-report.md` to the outputs directory:

```markdown
# UI Spec Check — Bug Report
**Date:** <date>
**Spec:** <path to spec file>
**App URL:** <base URL>
**Screens checked:** <list>

## Summary
- Screens checked: N
- Screens passing: N
- Issues found: N (X critical, Y minor)

## Findings by Screen

### <Screen> — ✅/⚠️/❌
...

## Recommended Fixes
<prioritized list>
```

Save screenshots alongside the report in the outputs directory.

---

## Tips

- **Don't just eyeball screenshots** — computed styles catch color drifts that look fine visually but are wrong values.
- **Inline styles bypass CSS class selectors** — frameworks like Next.js/Tailwind sometimes apply dynamic values (e.g. priority colors) via `style=` attributes rather than CSS classes. `[class*="border-l"]` won't find them. Use `div[style]` and filter on `el.style.borderLeftWidth`, or walk up the DOM with `getComputedStyle` to catch both.
- **Verify the URL before checking** — client-side routing can redirect after navigation (e.g. `/tasks` → `/chat`). Always confirm `window.location.href` matches the target route before running style checks.
- **Check empty states** — the spec often defines empty states (no tasks, no members) that get skipped in testing because test data fills them in.
- **Mobile viewport matters** — if the spec is mobile-first, resize to 390×844 before checking: `browser_resize → { width: 390, height: 844 }`.
- **Auth-gated screens** — if the app requires login, navigate to login first and sign in before checking protected routes.
- **Check one screen at a time** — don't screenshot everything then compare; the spec check and screenshot should happen together so you capture the right context.
