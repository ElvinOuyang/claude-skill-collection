---
name: ios-animate
description: >
  Review an iOS/SwiftUI feature and enhance it with purposeful animations, micro-interactions, haptics,
  and motion that improve usability and delight. Uses SwiftUI springs, matched geometry, symbol effects,
  and gesture-driven animation. Use this skill whenever the user mentions adding animation, transitions,
  micro-interactions, motion design, making a view feel alive, or wants an iOS screen to feel more fluid
  and responsive. Also use when things feel "static", "abrupt", "janky", or "lifeless" in an iOS app.
user-invocable: true
argument-hint: "[view or feature to animate]"
---

# iOS Animation & Motion

You are adding purposeful motion to a SwiftUI interface. Motion on iOS should feel like physics —
objects have mass, momentum, and settle naturally. The goal is not "add animations" but "make the
interface feel alive and responsive."

## Assess Animation Opportunities

Read every file in scope, then identify:

1. **Missing feedback**: Actions without visual or haptic acknowledgment (button taps, toggles, sends)
2. **Jarring transitions**: Instant state changes that feel abrupt (show/hide, filter changes, navigation)
3. **Unclear relationships**: Elements that appear/disappear without spatial context (where did it go?)
4. **Lack of delight**: Functional but joyless interactions (task completion, empty→content, achievements)
5. **Missed guidance**: Opportunities to direct attention (new content, errors, calls to action)

State findings briefly, then plan.

## Plan Animation Strategy

Before writing code, decide:

- **Hero moment**: The ONE signature animation on this screen. (What defines the experience?)
- **Feedback layer**: Which interactions need acknowledgment? (Every tap should respond)
- **Transition layer**: Which state changes need smoothing? (Show/hide, expand/collapse, navigation)
- **Delight layer**: Where can we surprise and reward? (Completion, achievement, discovery)

**The cardinal rule**: One well-orchestrated experience beats scattered animations everywhere.

## Implement Motion

Work through these categories systematically. Skip what's not relevant.

### Springs (The Foundation)

**Always use springs. Never use `.easeInOut` or `.linear`.**

Springs feel physical because they model real-world physics — objects don't move in
cubic bezier curves. iOS users are trained on spring animations from every system interaction.

| Spring | Feel | Use For |
|--------|------|---------|
| `.spring(.snappy)` | Quick, precise, professional | Button taps, toggles, selection changes, filter state |
| `.spring(.smooth)` | Fluid, natural, unhurried | Layout changes, expanding sections, sheet presentations |
| `.spring(.bouncy)` | Playful, energetic, celebratory | Task completion, achievements, onboarding, empty→content |
| `.spring(.snappy, extraBounce: 0.1)` | Snappy with subtle life | Cards, chips, interactive drag elements |

```swift
// Quick feedback
withAnimation(.spring(.snappy)) { isSelected.toggle() }

// Layout change
withAnimation(.spring(.smooth)) { isExpanded.toggle() }

// Celebration
withAnimation(.spring(.bouncy)) { showConfetti = true }
```

### Timing Tiers

| Category | Duration | Examples |
|----------|----------|---------|
| Micro-feedback | 100-200ms | Toggle, checkbox, button press, haptic |
| State changes | 200-350ms | Filter change, tab switch, content reveal |
| Layout transitions | 300-500ms | Section expand, sheet present, keyboard |
| Hero transitions | 400-600ms | Navigation push, zoom transition |
| Celebratory | 500-800ms | Task complete, achievement, confetti |

**Nothing over 500ms for standard UI.** Longer durations are only for moments of delight.

### Exit Faster Than Enter

Users adding content are building anticipation. Users dismissing content want it gone.

```swift
.transition(.asymmetric(
    insertion: .opacity.combined(with: .scale(0.9)).animation(.spring(.smooth)),
    removal: .opacity.animation(.spring(.snappy))
))
```

### Micro-Interactions

**Button feedback:**
```swift
// Scale feedback on press (use ButtonStyle, not manual animation)
struct ScaleButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.96 : 1)
            .animation(.spring(.snappy), value: configuration.isPressed)
    }
}
```

**Toggle/selection haptics:**
```swift
Toggle("Notifications", isOn: $enabled)
    .sensoryFeedback(.selection, trigger: enabled)
```

**Action confirmation haptics:**
```swift
Button("Complete Task") { completeTask() }
    .sensoryFeedback(.success, trigger: taskCompleted)
```

**Error haptics:**
```swift
Button("Delete") { attemptDelete() }
    .sensoryFeedback(.error, trigger: deleteFailed)
```

### State Transitions

**Show/hide content:**
```swift
if showDetail {
    DetailView()
        .transition(.opacity.combined(with: .move(edge: .bottom)))
}
// Trigger with: withAnimation(.spring(.snappy)) { showDetail.toggle() }
```

**Expand/collapse:**
```swift
VStack {
    Button { withAnimation(.spring(.smooth)) { isExpanded.toggle() } } label: {
        HStack {
            Text("Details")
            Image(systemName: "chevron.right")
                .rotationEffect(.degrees(isExpanded ? 90 : 0))
        }
    }
    if isExpanded {
        ExpandedContent()
            .transition(.opacity.combined(with: .scale(0.95, anchor: .top)))
    }
}
```

**Loading → content:**
```swift
if isLoading {
    PlaceholderView()
        .redacted(reason: .placeholder)
        .transition(.opacity)
} else {
    ContentView()
        .transition(.opacity.combined(with: .scale(0.98)))
}
// Animate the state change:
// withAnimation(.spring(.smooth)) { isLoading = false }
```

### Navigation & Spatial Transitions

**Zoom transition (iOS 18+):**
```swift
// Source
NavigationLink(value: item) {
    ItemRow(item)
        .matchedTransitionSource(id: item.id, in: namespace)
}

// Destination (in .navigationDestination)
ItemDetail(item)
    .navigationTransition(.zoom(sourceID: item.id, in: namespace))
```

**Matched geometry within a view:**
```swift
// For elements that move between states (e.g., selected indicator)
RoundedRectangle(cornerRadius: 8)
    .fill(Color.accentColor)
    .matchedGeometryEffect(id: "selection", in: namespace)
```

### Content Transitions

**Numeric text (counters, scores, badges):**
```swift
Text(count, format: .number)
    .contentTransition(.numericText())
    .animation(.spring(.snappy), value: count)
```

**Symbol replacement:**
```swift
Image(systemName: isPlaying ? "pause.fill" : "play.fill")
    .contentTransition(.symbolEffect(.replace))
```

### SF Symbol Effects

```swift
// Bounce on event (tap confirmation, "added")
Image(systemName: "checkmark.circle.fill")
    .symbolEffect(.bounce, value: trigger)

// Pulse for ongoing activity (syncing, recording)
Image(systemName: "antenna.radiowaves.left.and.right")
    .symbolEffect(.pulse)

// Variable color for progress (wifi strength, upload)
Image(systemName: "wifi")
    .symbolEffect(.variableColor.iterative)

// Wiggle for attention (notification, error)
Image(systemName: "bell.fill")
    .symbolEffect(.wiggle, value: hasNotification)
```

### Staggered List Animations

```swift
ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
    ItemRow(item)
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 20)
        .animation(
            .spring(.snappy).delay(Double(index) * 0.05),
            value: appeared
        )
}
.onAppear { appeared = true }
```

**Rules**: 50-100ms stagger per item. Cap total stagger at ~500ms (first 5-8 items stagger, rest appear together).

### Gesture-Driven Animation

```swift
.gesture(
    DragGesture()
        .onChanged { value in
            // Follow finger — no animation needed, direct tracking
            offset = value.translation.height
        }
        .onEnded { value in
            // Snap to target with spring — this is the satisfying part
            withAnimation(.spring(.snappy)) {
                offset = value.translation.height > threshold ? targetOffset : 0
            }
        }
)
```

### Haptics Guide

Haptics are the invisible animation — they make interactions feel physical.

| Haptic | Use For |
|--------|---------|
| `.sensoryFeedback(.selection, trigger:)` | Picks, toggles, filter changes, tab switches |
| `.sensoryFeedback(.impact(.light), trigger:)` | Subtle taps, drag snaps, scroll stops |
| `.sensoryFeedback(.impact(.medium), trigger:)` | Confirmations, sends, drops |
| `.sensoryFeedback(.success, trigger:)` | Task complete, save, achievement |
| `.sensoryFeedback(.error, trigger:)` | Failed action, invalid input |
| `.sensoryFeedback(.warning, trigger:)` | Destructive action confirmation |

**Rules**: Key moments only. Haptics on every scroll event = bad. Haptics on task completion = good.

### Reduce Motion

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

// Decorative animations: remove
withAnimation(reduceMotion ? .none : .spring(.snappy)) {
    showContent = true
}

// Functional transitions: simplify (cross-fade instead of spatial movement)
.transition(reduceMotion ? .opacity : .opacity.combined(with: .move(edge: .bottom)))
```

**Rule of thumb**: Reduce means reduce, not remove. Opacity changes are usually fine.
Spatial movement and bouncing are what causes discomfort.

## Verification

After implementing, check:

- [ ] All animations use springs (no `.easeInOut`, `.linear`, or `.default`)
- [ ] Timing is appropriate (feedback <250ms, state changes <350ms, layout <500ms)
- [ ] Exit animates faster than entrance
- [ ] Haptics added on meaningful interactions (not every scroll/drag)
- [ ] `accessibilityReduceMotion` checked for all decorative motion
- [ ] No animation blocks user interaction
- [ ] Matched geometry used for spatial continuity between views
- [ ] Symbol effects used where SF Symbols indicate state changes
- [ ] Content transitions on changing text/numbers
- [ ] Staggered entrance on lists (50-100ms per item, capped at ~500ms total)
- [ ] Feels physical, not computational — springs, momentum, settling

## NEVER

- Use `.easeInOut` or `.linear` — always springs
- Use `.animation(_, value:)` on a parent that animates everything — be surgical
- Add bounce/elastic easing — feels dated on iOS
- Exceed 500ms for standard UI feedback
- Add animation without purpose — every animation needs a reason
- Animate everything — animation fatigue makes apps feel exhausting
- Forget `prefers-reduced-motion` — this is an accessibility violation
- Add haptics to passive/read-only interactions — key moments only
- Use `Task.sleep(nanoseconds:)` for animation delays — use `.delay()` or `Task.sleep(for:)`
