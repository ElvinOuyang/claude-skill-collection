---
name: ios-polish
description: >
  Final quality pass for iOS/SwiftUI views — fixes spacing, typography, color, animation, accessibility,
  and HIG compliance to make interfaces feel crafted, not coded. Use this skill whenever the user mentions
  polish, finishing touches, pre-launch review, "something looks off", visual QA, design pass, or wants
  to elevate an iOS view from functional to beautiful. Also use when reviewing SwiftUI code for design
  quality, even if the user doesn't say "polish" explicitly — any request to make an iOS screen look
  better, feel more native, or match Apple-quality apps should trigger this skill.
---

# iOS Polish

You are performing a final design quality pass on SwiftUI views. Your job is not just to check for
correctness — it's to make the interface feel *crafted*. Every Apple-quality app shares certain traits:
generous spacing, purposeful typography, restrained color, fluid motion, and invisible accessibility.
This skill teaches you to see what's missing and fix it.

## Pre-Polish Assessment

Before changing anything, read every file in scope and answer:

1. **What is this screen's job?** (One sentence. If you can't say it simply, the screen may be doing too much.)
2. **What's the primary action?** It should be visually obvious within 2 seconds.
3. **The Squint Test** — blur your eyes. Can you still tell primary content from secondary? If everything blends together, hierarchy is broken.
4. **The Native Test** — does this feel like an iOS app or a web page in a native wrapper? Cards-everywhere, custom tab bars, missing haptics, and linear animations are web tells.

State your findings briefly, then proceed to the systematic pass.

---

## Systematic Polish (10 Dimensions)

Work through each dimension in order. For each one, note what you'd change and why, then make the change. Skip dimensions that are already solid — don't touch what works.

### 1. Spacing & Layout

Great spacing is the single biggest difference between "designed" and "default."

**Principles:**
- **Tight for related, generous for groups.** Elements that belong together get 4-8pt spacing. Sections get 24-32pt. Screens breathe with 16pt horizontal margins minimum.
- **Consistent scale.** Pick from the iOS standard: 4, 8, 12, 16, 20, 24, 32, 48. Don't use arbitrary values like 10 or 14 for padding.
- **Rhythm over symmetry.** Unequal spacing (more above a section header than below) creates visual flow. Perfectly equal spacing feels static.
- **Safe areas.** Always respect them. Use `.safeAreaInset(edge:)` for floating elements, never manual padding that guesses notch/indicator heights.
- **Lists.** Prefer `List` with `.listRowInsets()` over manual `VStack` + `ForEach` + `Divider` — the system handles separators, swipe actions, and dynamic type scaling.

**Red flags:** Hard-coded padding like `.padding(10)`, missing spacing between sections, elements touching safe area edges, `ScrollView` content hidden behind navigation bars.

### 2. Typography

iOS typography should feel effortless. San Francisco does the heavy lifting — you direct it.

**Principles:**
- **Use text styles, not sizes.** `.font(.body)`, `.font(.headline)`, `.font(.caption)` — never `.font(.system(size: 14))`. Text styles scale with Dynamic Type automatically.
- **Weight carries hierarchy.** One `.semibold` or `.bold` headline per section. Everything else stays `.regular`. Too many weights creates noise.
- **Three levels max.** Title, body, caption. If you need four, simplify the content first.
- **Let text breathe.** `.lineSpacing(4)` on body text. Multiline labels need room.
- **Secondary text earns its place.** Every `.caption` or `.footnote` should answer: "Would the user miss this if it were gone?" If no, remove it.

**Red flags:** Hard-coded font sizes, more than 2 font weights on screen, `.font(.caption2)` used for important info, missing `lineLimit()` on user-generated content.

See `references/typography.md` for the full text style hierarchy and Dynamic Type testing guide.

### 3. Color System

Color communicates. Every color choice should answer "what does this tell the user?"

**Principles:**
- **Semantic colors first.** Use `Color(.label)`, `Color(.secondaryLabel)`, `Color(.tertiaryLabel)`, `Color(.systemBackground)`, `Color(.secondarySystemBackground)`. These adapt to dark mode and accessibility settings automatically.
- **One accent, used sparingly.** Your brand color (tint color) should appear on primary actions and key UI elements. Everything else is neutral.
- **Tinted neutrals > pure gray.** Warm apps use cream/sand neutrals. Cool apps use slate/blue-gray. Pure `#808080` gray feels lifeless. This is a taste call that separates good from great.
- **Color for meaning.** Red = destructive/urgent. Green = success/complete. Yellow/amber = warning/pending. Don't use these colors decoratively.
- **Dark mode is a first-class design.** Not inverted light mode. Backgrounds get slightly elevated (`Color(.secondarySystemBackground)`), text uses `Color(.label)`. Test both appearances.

**Red flags:** Hard-coded color literals (`Color.gray`), custom colors that don't adapt to dark mode, more than 3 non-neutral colors on one screen, decorative color that doesn't communicate meaning.

See `references/color-system.md` for the semantic color palette and dark mode design guide.

### 4. Visual Hierarchy

The user's eye should flow naturally from what matters most to what matters least.

**Principles:**
- **Size > Weight > Color.** Establish hierarchy through font size first, then weight, then color. Don't rely on color alone — it fails for colorblind users and in dark mode.
- **One hero per screen.** The primary content or action should be unmistakable. If two things compete for attention, one needs to be demoted.
- **Progressive disclosure.** Don't show everything at once. Use `DisclosureGroup`, `NavigationLink`, or `.sheet` to reveal detail on demand.
- **Whitespace is hierarchy.** More space above a heading than below it visually groups the heading with its content, not the section above.
- **De-emphasize chrome.** Navigation bars, tab bars, and toolbars should recede. Content is king. Use `.toolbarBackground(.hidden)` when the screen benefits from it.

**Red flags:** Multiple elements competing for attention, uniform text size across different content types, section headers that feel disconnected from their content.

### 5. Animation & Motion

Motion should feel like physics, not CSS transitions.

**Principles:**
- **Springs, always.** Use `.spring(.snappy)` for quick UI feedback (toggles, taps). `.spring(.smooth)` for layout changes (expanding sections, sheet presentations). `.spring(.bouncy)` only for playful, celebratory moments (task completion).
- **Timing tiers.** Quick feedback: 150-250ms. State changes: 250-350ms. Layout transitions: 300-500ms. Never exceed 500ms for UI — it feels sluggish.
- **Exit faster than enter.** Show animations can build anticipation. Dismiss should be instant or very fast. Users removing something want it gone.
- **Matched geometry for continuity.** When an element moves between views (e.g., a task card opening to detail), use `matchedGeometryEffect` or `navigationTransition(.zoom)` to maintain spatial context.
- **Respect Reduce Motion.** Wrap decorative animations in `withAnimation(accessibilityReduceMotion ? .none : .spring(.snappy))` or use `@Environment(\.accessibilityReduceMotion)`. Functional transitions (showing/hiding content) can stay, but simplify them.

**Red flags:** `.linear` or `.easeInOut` animations (feel mechanical), animations longer than 500ms, missing Reduce Motion support, decorative animations with no purpose, `.animation(_, value:)` on a parent that animates everything.

See `references/motion.md` for the spring configurations, transition patterns, and gesture-driven animation guide.

### 6. SF Symbols & Iconography

SF Symbols are free design polish — use them well.

**Principles:**
- **Match symbol weight to text weight.** In a `.headline` context, use `.font(.headline)` on the symbol too. Mismatched weights look sloppy.
- **Hierarchical rendering for depth.** `.symbolRenderingMode(.hierarchical)` adds subtle depth to symbols. Use it as default over `.monochrome` for decorative icons.
- **Filled vs. outlined.** Filled (`.fill`) for selected/active states (tab bar, toggles). Outlined for inactive/unselected. This is a core iOS pattern.
- **Symbol effects for feedback.** `.symbolEffect(.bounce)` on tap, `.symbolEffect(.pulse)` for ongoing activity, `.symbolEffect(.variableColor)` for progress. These feel native and delightful with zero effort.
- **Size with font, not frame.** Use `.font(.title2)` or `.imageScale(.large)` — not `.frame(width: 24, height: 24)`. This scales with Dynamic Type.

**Red flags:** Symbols that don't match surrounding text weight, `.monochrome` used everywhere, custom icons where an SF Symbol exists, symbols sized with `.frame()`.

### 7. Interaction & Feedback

Every touch should have a response. Silence feels broken.

**Principles:**
- **44x44pt touch targets.** Apple's HIG minimum. Anything smaller is a tap-frustration source. Use `.contentShape(Rectangle())` to expand hit areas beyond visible bounds.
- **Buttons, not tap gestures.** Use `Button` for tappable elements — it provides built-in accessibility, highlight states, and keyboard support. `onTapGesture` loses all of this.
- **Haptics.** `.sensoryFeedback(.selection, trigger: value)` for picks/toggles. `.sensoryFeedback(.impact(.medium), trigger: action)` for confirmations. `.sensoryFeedback(.success, trigger: completion)` for achievements. Haptics are the difference between "app" and "native app."
- **Loading states everywhere.** Every async operation needs visual feedback. `.redacted(reason: .placeholder)` for skeleton screens. `ProgressView()` for indeterminate waits. Never leave the user staring at unchanged UI while something loads.
- **Destructive actions need speed bumps.** `.swipeActions` with `.destructive` role. Confirmation `.alert` or `.confirmationDialog` for irreversible actions.

**Red flags:** Small touch targets, `onTapGesture` on interactive elements, no loading indicators during network calls, delete without confirmation, silent errors.

### 8. Empty, Loading & Error States

These are the states users see most during first use and poor connectivity. They set the emotional tone.

**Principles:**
- **Empty states are invitations.** Use `ContentUnavailableView` (iOS 17+) with a clear message and action button. "No tasks yet" is functional. "All caught up! Time to relax." is human.
- **Loading states build trust.** Show skeleton placeholders (`.redacted(reason: .placeholder)`) that match the final layout shape. This feels faster than a spinner.
- **Error states are recoverable.** Show what happened, what the user can do (retry, check connection), and a button to do it. Never show raw error messages.
- **Transitions between states.** Animate from loading to content with `.transition(.opacity.combined(with: .scale(0.95)))`. Abrupt state switches feel jarring.

**Red flags:** Blank screens during loading, generic "Something went wrong", no retry mechanism, abrupt state transitions, empty lists with no explanation.

### 9. Accessibility

Accessibility is design quality you can't see, but millions of users feel.

**Principles:**
- **VoiceOver labels on everything interactive.** Every `Button`, toggle, and tappable element needs `.accessibilityLabel()` if the visual label isn't sufficient (e.g., icon-only buttons).
- **Dynamic Type to XXXL.** Test your views at the largest accessibility text size. Use `ViewThatFits` or `.minimumScaleFactor()` when space is tight. Never truncate critical info.
- **Contrast ratios.** 4.5:1 for body text, 3:1 for large text and UI components (borders, icons). Use Accessibility Inspector to verify.
- **Group related elements.** `.accessibilityElement(children: .combine)` on card views so VoiceOver reads "Task: Buy groceries, assigned to Mom, due tomorrow" as one unit, not four separate elements.
- **Reduce Motion.** Already covered in Animation, but double-check: every `withAnimation` and `.transition` should have a reduced-motion alternative.

**Red flags:** Icon-only buttons without labels, views that break at large text sizes, low contrast on secondary text, VoiceOver reading individual elements of a logical group.

### 10. Platform Conventions (HIG Compliance)

The best polish is invisible — the app just *feels* like it belongs on iOS.

**Principles:**
- **System navigation.** `NavigationStack` with `navigationTitle` and `toolbar`, not custom headers. The system handles large title collapsing, safe areas, and back gestures.
- **System controls.** Use `DatePicker`, `Toggle`, `Picker`, `Stepper` — not custom versions unless you have a genuine UX reason. Users know how system controls work.
- **Pull to refresh.** `.refreshable { }` on any list that shows server data. It's expected.
- **Swipe actions.** `.swipeActions` for quick actions on list rows. Leading for positive (complete), trailing for destructive (delete).
- **Sheets for focused tasks.** Use `.sheet` or `.fullScreenCover` for creation flows. Alerts for binary decisions. Confirmation dialogs for destructive choices.
- **Search.** `.searchable()` on any list with more than ~10 items. Users expect it.

**Red flags:** Custom navigation bars, custom toggles/pickers without reason, missing pull-to-refresh on server data, alerts used for complex input, no search on long lists.

---

## The iOS Slop Test

Before finishing, run this quick check. "iOS Slop" is the native equivalent of "AI Slop" — it's the
telltale signs of a web developer's first iOS app, or an AI that hasn't learned platform taste.

**Fail if any of these are true:**
- [ ] Cards with rounded corners and shadows used as the primary layout pattern (web pattern — iOS uses grouped lists, rows, and whitespace)
- [ ] Custom tab bar or navigation bar when system versions work fine
- [ ] `.easeInOut` or `.linear` animations instead of springs
- [ ] No haptic feedback anywhere in the app
- [ ] Hard-coded font sizes (breaks Dynamic Type)
- [ ] Pure gray (`Color.gray`) instead of semantic/tinted neutrals
- [ ] Interactive elements smaller than 44x44pt
- [ ] No loading states during async operations
- [ ] Dark mode untested or obviously broken
- [ ] `onTapGesture` used where `Button` should be

---

## Verification Checklist

After making all changes, verify:

- [ ] Squint test: primary content/action is clearly dominant
- [ ] Native test: feels like iOS, not a web app in a wrapper
- [ ] Spacing: consistent scale (4/8/12/16/24/32), generous between sections
- [ ] Typography: text styles only, 2-3 hierarchy levels, weights are intentional
- [ ] Color: semantic colors, one accent, tinted neutrals, dark mode works
- [ ] Animation: springs, appropriate timing, Reduce Motion respected
- [ ] SF Symbols: weight-matched, hierarchical rendering, filled/outlined state
- [ ] Touch targets: 44x44pt minimum, Buttons not tap gestures
- [ ] Haptics: selection, impact, success/error feedback present
- [ ] Empty/loading/error: all three states handled with human copy
- [ ] Accessibility: VoiceOver labels, Dynamic Type to XXXL, contrast ratios
- [ ] HIG: system navigation, system controls, pull-to-refresh, swipe actions
- [ ] iOS Slop test: all items pass

---

## NEVER

- Add decorative animations that serve no UX purpose
- Use `.easeInOut` or `.linear` — always use springs
- Hard-code font sizes — always use text styles
- Use `Color.gray` — use `Color(.secondaryLabel)` or tinted neutrals
- Use `onTapGesture` for buttons — use `Button`
- Skip loading states — every async operation needs feedback
- Ignore dark mode — test both appearances
- Add haptics to every single interaction — that's as bad as none. Key moments only.
- Over-polish at the expense of shipping — know when good enough is great
