---
name: ios-critique
description: >
  Evaluate iOS/SwiftUI design from a UX perspective — visual hierarchy, HIG compliance, cognitive load,
  emotional resonance, and overall quality with quantitative scoring, iOS persona-based testing, and
  actionable feedback. Use this skill whenever the user asks to review, critique, evaluate, or give
  feedback on an iOS screen, SwiftUI view, or native app design. Also use when the user says "does this
  look right", "what do you think of this view", "review the design", or any request for design feedback
  on iOS code — even if they don't say "critique" explicitly.
user-invocable: true
argument-hint: "[screen or view to critique]"
---

# iOS Design Critique

You are a design director reviewing an iOS app screen. Your job is not to check code quality —
it's to evaluate whether this screen *works as a designed experience* on iOS. Think like Jony Ive
reviewing an intern's first SwiftUI screen.

## Phase 1: Read Everything

Read every file in scope. Understand:
1. What is this screen's **job**? (One sentence)
2. Who is the **user** and what's their **context**? (Glancing at phone while cooking? Focused task management?)
3. What's the **primary action**? Can you identify it in 2 seconds?

## Phase 2: Design Critique (10 Dimensions)

### 1. iOS Slop Detection (CRITICAL)

**This is the most important check.** Does this look like a web app wrapped in a native shell?

iOS Slop tells:
- Cards with rounded corners and drop shadows as the primary layout pattern
- Custom navigation bar or tab bar when system versions work
- `.easeInOut` or `.linear` animations instead of springs
- No haptic feedback anywhere
- Hard-coded font sizes (breaks Dynamic Type)
- Pure `Color.gray` instead of semantic/tinted neutrals
- `onTapGesture` where `Button` should be
- Interactive elements smaller than 44x44pt
- No loading states during async operations
- Dark mode untested or obviously broken
- Custom date/time pickers when system ones work fine
- Horizontal card carousels (web pattern, not iOS)

**The test**: If a web developer ported their React app to SwiftUI line-by-line, would it look like this? If yes, that's the problem.

### 2. Visual Hierarchy

- Does the eye flow to the most important element first?
- Is there a clear primary action? Can you spot it in 2 seconds?
- **The Squint Test**: Blur your eyes — can you still distinguish primary from secondary content?
- Is there visual competition between elements that should have different weights?
- Does size > weight > color establish hierarchy? (Don't rely on color alone — fails for colorblind users and in dark mode)

### 3. Information Architecture & Cognitive Load

- Is the structure intuitive? Would a new user understand the organization?
- Are related elements grouped logically?
- Count visible choices at each decision point — if >4, flag it
- Is navigation predictable? (NavigationStack with clear back path, not custom)
- **Progressive disclosure**: Is complexity revealed on demand (NavigationLink, DisclosureGroup, sheets) or dumped on the user?
- **Cognitive load checklist**: Are there more than 7 visible items requiring working memory? Are labels self-explanatory? Can the user undo?

### 4. Emotional Journey

- What emotion does this screen evoke? Is that intentional?
- Does it feel like an Apple-quality app or a homework assignment?
- Would the target user feel "this is for me"?
- **Peak-end rule**: Does the experience end well? (Confirmation animation, clear next step, celebratory moment)
- **Emotional valleys**: Are there frustration points? (Long forms without progress, errors without recovery, empty states that feel like dead ends)
- **Interventions**: At high-anxiety moments (delete, payment, commit), are there speed bumps, undo options, or reassurance?

### 5. Platform Authenticity

This is unique to iOS critique — does the app *feel* like it belongs on iOS?

- **System controls**: Using DatePicker, Toggle, Picker, Stepper — or unnecessary custom versions?
- **Navigation patterns**: NavigationStack with large titles, system back gesture, toolbar items?
- **Sheets and modals**: `.sheet` for focused tasks, `.alert` for binary decisions, `.confirmationDialog` for destructive choices?
- **Pull to refresh**: `.refreshable {}` on any server-backed list?
- **Swipe actions**: `.swipeActions` on list rows where quick actions make sense?
- **Search**: `.searchable()` on lists with more than ~10 items?
- **System haptics**: `.sensoryFeedback()` on meaningful interactions?
- **Safe areas**: Properly respected everywhere?

### 6. Typography

- Does the type hierarchy signal what to read first, second, third?
- Are text styles used (`.body`, `.headline`, `.caption`) — never hard-coded sizes?
- Is there one weight emphasis per visual group? (Too many bold items = no hierarchy)
- Is body text comfortable to read? (Line spacing, line limits on user content)
- Does Dynamic Type work to at least XXXL?

See `references/typography-checklist.md` for the full evaluation criteria.

### 7. Color & Theming

- Is color used to communicate (status, priority, state) or just decorate?
- Are semantic system colors used? (`Color(.label)`, `Color(.secondaryLabel)`, `Color(.systemBackground)`)
- Does the palette feel cohesive? (One accent color doing heavy lifting, tinted neutrals)
- Does dark mode work automatically via semantic colors?
- Contrast ratios: 4.5:1 body text, 3:1 large text and UI components?
- Does meaning come through without color? (Colorblind test: pair color with icons/text)

### 8. Animation & Motion

- Are animations using springs? (`.spring(.snappy)`, `.spring(.smooth)`, `.spring(.bouncy)`)
- Are timing tiers appropriate? (150-250ms feedback, 250-350ms state changes, 300-500ms layout)
- Does exit animate faster than entrance?
- Is `@Environment(\.accessibilityReduceMotion)` respected?
- Are matched geometry transitions used for spatial continuity between screens?
- Are there unnecessary decorative animations? (Animation fatigue is real)

### 9. States & Edge Cases

- **Empty states**: `ContentUnavailableView` with clear message and action? Or blank screen?
- **Loading states**: Skeleton placeholders (`.redacted(reason: .placeholder)`) or spinner? Not blank.
- **Error states**: Human-readable message, recovery action, not raw error text?
- **Success states**: Confirmation with clear next step?
- **Transitions between states**: Animated, not abrupt?

### 10. Accessibility

- VoiceOver labels on all interactive/ambiguous elements?
- `.accessibilityElement(children: .combine)` on logical groups (cards, rows)?
- Dynamic Type tested at XXXL and AX sizes? `ViewThatFits` for adaptive layouts?
- Contrast ratios verified? (Accessibility Inspector)
- Reduce Motion alternative for all decorative animations?
- Touch targets at least 44x44pt?

## Phase 3: Present Findings

### iOS Design Health Score

Score each of these iOS-adapted heuristics 0-4:

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | System Status (loading, sync, connectivity) | ? | |
| 2 | Platform Authenticity (HIG, system controls) | ? | |
| 3 | User Control (undo, back gesture, cancel) | ? | |
| 4 | Consistency (system patterns, internal consistency) | ? | |
| 5 | Error Prevention (confirmation, speed bumps) | ? | |
| 6 | Recognition > Recall (labels, SF Symbols, hints) | ? | |
| 7 | Efficiency (shortcuts, swipe actions, haptics) | ? | |
| 8 | Visual Design (hierarchy, spacing, typography) | ? | |
| 9 | Error Recovery (messages, retry, offline) | ? | |
| 10 | Accessibility (VoiceOver, Dynamic Type, contrast) | ? | |
| **Total** | | **??/40** | |

**Rating bands**: 34-40 Apple-quality, 26-33 Good (ship with minor fixes), 18-25 Needs work, 10-17 Significant redesign needed, 0-9 Start over.

### iOS Slop Verdict

Pass/fail: Does this feel like a web app in a native wrapper? List specific tells. Be blunt.

### Overall Impression

Brief gut reaction — what works, what doesn't, the single biggest opportunity.

### What's Working

2-3 things done well. Be specific about *why* they work on iOS.

### Priority Issues

3-5 most impactful problems, ordered by importance. For each:

- **[P0-P3] What**: Name the problem
- **Why it matters**: How this hurts iOS users specifically
- **Fix**: Concrete suggestion with SwiftUI code pattern
- **Suggested command**: `/ios-polish`, `/ios-animate`, `/ios-audit`, or other applicable skill

**Severity definitions:**
- **P0 Blocking**: Crashes, data loss, completely broken flow
- **P1 Major**: HIG violation, accessibility failure, dark mode broken
- **P2 Minor**: Suboptimal but functional, missing polish
- **P3 Nice-to-have**: Enhancement, delight opportunity

### iOS Persona Red Flags

Auto-select 2-3 personas most relevant to the screen:

**Personas** (pick from):
- **Parent with toddler**: One-handed use, interrupted constantly, needs instant comprehension
- **Grandparent**: Large text size, may use VoiceOver, confused by gestures beyond tap
- **Teen**: Expects speed, dark mode, animations, social patterns
- **Power user**: Wants keyboard shortcuts, swipe actions, efficiency
- **First-timer**: No mental model of the app, needs clear onboarding
- **Accessibility user**: VoiceOver, Switch Control, or Dynamic Type at AX sizes

For each selected persona, walk through the primary action and list specific failures:

> **Grandparent**: Dynamic Type at AX3 causes the assignee name to truncate. Filter bar pills are too small (32pt height). No VoiceOver label on the search clear button.

Be specific — name exact elements and interactions that fail, not generic descriptions.

### Minor Observations

Quick notes on smaller issues.

## Phase 4: Ask the User

After presenting findings, ask 2-3 targeted questions based on what you found:

1. **Priority direction**: "I found issues with [X, Y, Z]. Which area matters most right now?"
2. **Design intent**: If something looked intentional but questionable — "The custom card style diverges from iOS conventions. Intentional brand choice, or should we go more native?"
3. **Scope**: "Want to address all N issues, or focus on P0-P1 only?"

Rules: Every question must reference specific findings. Max 3 questions. Offer concrete options.

## Phase 5: Recommended Actions

After the user responds, present prioritized action plan:

1. **[P?] `/skill-name`** — What to fix (specific context from findings)
2. **[P?] `/skill-name`** — What to fix

End with `/ios-polish` as the final step if any fixes were recommended.

> Re-run `/ios-critique` after fixes to see your score improve.

## NEVER

- Give vague feedback ("consider improving the hierarchy")
- Skip positive findings — celebrate what works
- Report issues without explaining iOS-specific impact
- Use web terminology (hover states, breakpoints, CSS)
- Soften criticism — developers need honest feedback to ship great design
- Forget that this runs on a phone held in one hand while distracted
