---
name: ios-audit
description: >
  Run technical quality checks on iOS/SwiftUI code across accessibility, performance, HIG compliance,
  theming, and anti-patterns. Generates a scored report with P0-P3 severity ratings and an actionable
  fix plan. Use this skill whenever the user wants an accessibility check, performance audit, HIG
  compliance review, Dark Mode verification, Dynamic Type audit, or technical quality review of iOS
  code. Also use when preparing an iOS app for App Store submission, TestFlight, or user testing — any
  request to verify iOS code quality should trigger this skill.
user-invocable: true
argument-hint: "[area (screen, feature, or entire app)]"
---

# iOS Technical Audit

You are running a systematic technical quality audit on SwiftUI code. Don't fix issues — document
them with precise locations, severity, and fix recommendations. This is a code-level audit, not a
design critique.

## Diagnostic Scan

Read every file in scope. Run comprehensive checks across 5 dimensions. Score each 0-4.

### 1. Accessibility

**Check for:**

**VoiceOver:**
- Interactive elements without `.accessibilityLabel()` (especially icon-only buttons)
- Logical groups not combined with `.accessibilityElement(children: .combine)`
- Decorative images not hidden with `.accessibilityHidden(true)`
- Missing `.accessibilityHint()` on non-obvious interactions
- Missing `.accessibilityValue()` on stateful controls
- Custom controls missing `.accessibilityAddTraits()` (`.isButton`, `.isSelected`, etc.)

**Dynamic Type:**
- Hard-coded font sizes (`.system(size: N)` instead of `.font(.body)` etc.)
- Custom fonts without `relativeTo:` parameter
- Layouts that break at XXXL or AX sizes (missing `ViewThatFits`)
- Truncated critical text at large sizes (needs `.minimumScaleFactor()` or layout adaptation)

**Contrast:**
- Text on colored backgrounds below 4.5:1 ratio (body) or 3:1 (large text, UI components)
- Custom colors without dark mode variants
- Meaning conveyed by color alone without icon/text pairing

**Motor:**
- Touch targets below 44x44pt (check `.frame()` on buttons, use `.contentShape()` to expand)
- `onTapGesture` instead of `Button` (loses accessibility, highlight state, keyboard support)
- Complex gestures without `.accessibilityAction()` alternative
- Missing keyboard support on iPad

**Reduce Motion:**
- Decorative animations not gated by `@Environment(\.accessibilityReduceMotion)`
- Rapid flashing or auto-playing motion

**Score 0-4**: 0=Inaccessible, 1=Major gaps (no VoiceOver labels, hard-coded fonts), 2=Partial effort, 3=Good (most covered, minor gaps), 4=Excellent (VoiceOver navigable, Dynamic Type to AX, contrast verified)

### 2. Performance

**Check for:**

**View body complexity:**
- Large `body` properties with complex conditional logic (should extract subviews)
- Expensive computed properties called from `body`
- Missing `@State` / `@Observable` granularity causing unnecessary re-renders

**Lists & scroll performance:**
- `ForEach` without stable `id` (causes identity churn)
- Non-lazy containers for large data sets (`VStack` instead of `LazyVStack`)
- Missing `.scrollTargetLayout()` for paging
- Images without `.resizable()` + `.aspectRatio()` sizing

**Animation performance:**
- Animating layout properties instead of transform/opacity
- `.animation(_, value:)` on parent views (broad invalidation)
- Complex views inside animated containers without `drawingGroup()`

**Data & networking:**
- Missing `.task` cancellation handling
- Unbounded data fetches (no pagination)
- Redundant network calls (missing caching or dedup)

**Memory:**
- Large images not downsampled
- Closures capturing `self` strongly in long-lived contexts
- SwiftData queries without proper predicates (fetching entire tables)

**Score 0-4**: 0=Severe (ANR risk, memory leaks), 1=Major (janky scroll, expensive body), 2=Partial, 3=Good (mostly optimized), 4=Excellent (lean, stable identity, lazy everywhere)

### 3. HIG Compliance

**Check for:**

**Navigation:**
- Custom navigation bars instead of `NavigationStack` + `.navigationTitle` + `.toolbar`
- Custom back buttons that break swipe-back gesture
- `NavigationView` instead of `NavigationStack` (deprecated)
- Missing large title on primary screens

**Controls:**
- Custom toggles/pickers/date pickers when system versions work
- `onTapGesture` on elements that should be `Button`, `NavigationLink`, or `Toggle`
- Missing `.confirmationDialog` or `.alert` for destructive actions
- Delete actions without `.destructive` role

**Lists:**
- Missing `.refreshable {}` on server-backed lists
- Missing `.searchable()` on lists with 10+ items
- Custom separators instead of `.listRowSeparator()`
- Missing `.swipeActions` where quick actions make sense
- Manual `VStack` + `ForEach` + `Divider` instead of `List`

**Feedback:**
- No haptic feedback (`.sensoryFeedback()`) on any interactions
- Missing loading indicators during async operations
- No empty state handling (`ContentUnavailableView`)
- Silent error handling (catch blocks that swallow errors)

**Layout:**
- Hard-coded safe area padding instead of system handling
- `UIScreen.main.bounds` usage (deprecated, non-adaptive)
- `GeometryReader` where `containerRelativeFrame()` works
- Missing keyboard avoidance

**Score 0-4**: 0=Ignores HIG, 1=Major violations (custom nav, no refreshable), 2=Partial, 3=Good (mostly compliant), 4=Excellent (feels like a first-party app)

### 4. Theming & Dark Mode

**Check for:**

**Colors:**
- Hard-coded color literals (`Color.white`, `Color.gray`, `Color(red:green:blue:)`)
- Custom named colors without dark mode variants in asset catalog
- `Color("name")` colors — verify each has Both Appearances in asset catalog
- Missing semantic system colors where appropriate (`Color(.label)`, `Color(.systemBackground)`)

**Backgrounds:**
- `.background(.white)` or `.background(Color.white)` (breaks in dark mode)
- Hard-coded shadows (invisible in dark mode — need border/elevation alternative)

**Images:**
- Template images without `.foregroundStyle()` (won't adapt)
- Custom icons with baked-in colors (won't adapt)

**Testing:**
- Toggle between Light and Dark in Xcode previews or Environment Overrides
- Check for invisible text, missing borders, wrong backgrounds

**Score 0-4**: 0=Light mode only, 1=Many hard-coded colors, 2=Partial (some semantic), 3=Good (dark mode works, minor issues), 4=Excellent (all semantic, both modes polished)

### 5. iOS Anti-Patterns (iOS Slop Detection)

**Check for each and flag:**
- [ ] Cards with rounded corners + shadows as primary layout
- [ ] Custom tab bar or navigation bar
- [ ] `.easeInOut` or `.linear` animations (should be springs)
- [ ] No haptic feedback anywhere
- [ ] Hard-coded font sizes
- [ ] Pure `Color.gray` usage
- [ ] Touch targets < 44x44pt
- [ ] No loading states during async
- [ ] Dark mode broken
- [ ] `onTapGesture` where `Button` should be
- [ ] `ObservableObject` / `@Published` / `@StateObject` (prefer `@Observable`)
- [ ] `NavigationView` (deprecated, use `NavigationStack`)
- [ ] `foregroundColor()` (deprecated, use `foregroundStyle()`)
- [ ] `cornerRadius()` (deprecated, use `clipShape(.rect(cornerRadius:))`)
- [ ] Force unwraps or force `try` in non-critical paths

**Score 0-4**: 0=Web-app-in-native-wrapper (5+ tells), 1=Heavy web feel (3-4 tells), 2=Some tells (1-2), 3=Mostly clean, 4=Feels like a first-party Apple app

## Generate Report

### iOS Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | ?/4 | |
| 2 | Performance | ?/4 | |
| 3 | HIG Compliance | ?/4 | |
| 4 | Theming & Dark Mode | ?/4 | |
| 5 | Anti-Patterns | ?/4 | |
| **Total** | | **??/20** | |

**Rating bands**: 18-20 Ship it, 14-17 Good (address weak areas), 10-13 Needs work, 6-9 Major overhaul, 0-5 Start over

### iOS Slop Verdict

Pass/fail on each anti-pattern check. Be blunt.

### Executive Summary

- Audit score: **??/20** ([rating band])
- Issues by severity: P0: ?, P1: ?, P2: ?, P3: ?
- Top 3 critical issues
- Recommended priority

### Detailed Findings

Tag every issue **P0-P3**:
- **P0 Blocking**: Crash, data loss, accessibility barrier
- **P1 Major**: HIG violation, Dark Mode broken, VoiceOver unusable
- **P2 Minor**: Suboptimal, workaround exists
- **P3 Polish**: Enhancement, no real user impact

For each:
- **[P?] Issue name**
- **Location**: File, line number
- **Category**: Accessibility / Performance / HIG / Theming / Anti-Pattern
- **Impact**: How it affects users
- **Standard**: HIG guideline or WCAG criterion violated
- **Fix**: Specific code change
- **Suggested skill**: `/ios-polish`, `/ios-animate`, `/ios-critique`

### Systemic Issues

Recurring problems that indicate patterns, not one-offs:
- "Hard-coded colors in 12 files — need semantic color migration"
- "No `.accessibilityElement(children: .combine)` on any card views"
- "Zero haptic feedback across entire app"

### Positive Findings

What's working well. Good practices to maintain.

### Recommended Actions

Prioritized fix plan:

1. **[P?] `/skill-name`** — What to fix (context from findings)
2. **[P?] `/skill-name`** — What to fix

End with `/ios-polish` as the final step.

> Re-run `/ios-audit` after fixes to see your score improve.

## NEVER

- Fix issues yourself — this is an audit, not a fix pass
- Report issues without file and line locations
- Skip positive findings
- Mark everything P0 — prioritize ruthlessly
- Use web terminology (ARIA, semantic HTML, breakpoints)
- Forget that this is iOS — check against HIG, not WCAG-only
- Report deprecated API usage without naming the modern replacement
