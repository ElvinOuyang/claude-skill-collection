# iOS Motion & Animation Reference

## SwiftUI Spring Presets

These are the springs you should use 95% of the time:

| Spring              | Feel                      | Use For                                    |
|--------------------|---------------------------|--------------------------------------------|
| `.spring(.snappy)` | Quick, precise            | Button taps, toggles, selection changes    |
| `.spring(.smooth)`  | Fluid, natural            | Layout changes, expanding/collapsing       |
| `.spring(.bouncy)`  | Playful, energetic        | Celebrations, achievements, onboarding     |
| `.spring(.snappy, extraBounce: 0.1)` | Snappy with subtle life | Cards, chips, interactive elements |

**Custom springs** (rarely needed):
```swift
.spring(duration: 0.3, bounce: 0.15)  // Fine-tuned control
```

## Timing Tiers

| Category          | Duration    | Spring        | Examples                           |
|-------------------|------------|---------------|------------------------------------|
| Micro-feedback    | 100-200ms  | `.snappy`     | Toggle, checkbox, button press     |
| State changes     | 200-350ms  | `.snappy`     | Filter change, tab switch, reveal  |
| Layout transitions| 300-500ms  | `.smooth`     | Section expand, sheet present      |
| Hero transitions  | 400-600ms  | `.smooth`     | Navigation push, zoom transition   |
| Celebratory       | 500-800ms  | `.bouncy`     | Task complete, achievement unlock  |

**The cardinal rule:** Nothing over 500ms for standard UI. Longer animations are only for
moments of delight, and even those should stay under 800ms.

## Exit Faster Than Enter

Users showing content are building anticipation — a brief entrance animation feels purposeful.
Users dismissing content want it gone — a slow exit feels like the app is fighting them.

```swift
.transition(.asymmetric(
    insertion: .opacity.combined(with: .scale(0.9)).animation(.spring(.smooth)),
    removal: .opacity.animation(.spring(.snappy))
))
```

## Matched Geometry & Navigation Transitions

**For navigation pushes (iOS 18+):**
```swift
// Source view
NavigationLink(value: item) {
    ItemCard(item)
        .matchedTransitionSource(id: item.id, in: namespace)
}

// Destination
.navigationTransition(.zoom(sourceID: item.id, in: namespace))
```

**For custom transitions within a view:**
```swift
// Use matchedGeometryEffect for elements that move between states
.matchedGeometryEffect(id: "selectedItem", in: namespace)
```

**Warning:** Don't use `matchedGeometryEffect` for NavigationStack transitions — use
`navigationTransition(.zoom)` instead. They solve different problems.

## Content Transitions

For text/number changes without moving the view:

```swift
Text(count, format: .number)
    .contentTransition(.numericText())  // Rolling number animation

Image(systemName: icon)
    .contentTransition(.symbolEffect(.replace))  // Smooth symbol swap
```

## Gesture-Driven Animations

For interactive animations that follow the user's finger:

```swift
.gesture(
    DragGesture()
        .onChanged { value in
            offset = value.translation.height
        }
        .onEnded { value in
            withAnimation(.spring(.snappy)) {
                offset = value.translation.height > threshold ? targetOffset : 0
            }
        }
)
```

Use `.spring(.snappy)` for the snap-back — it should feel physically responsive.

## Reduce Motion

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

// For decorative animations:
withAnimation(reduceMotion ? .none : .spring(.snappy)) {
    // state change
}

// For functional transitions (show/hide), simplify rather than remove:
.transition(reduceMotion ? .opacity : .opacity.combined(with: .scale(0.95)))
```

**Rule of thumb:** Reduce Motion means reduce, not remove. Cross-fades and opacity
changes are usually fine. Spatial movement and bouncing are what causes discomfort.

## Staggered Animations

For lists or grids where items appear sequentially:

```swift
ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
    ItemView(item)
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 20)
        .animation(
            .spring(.snappy).delay(Double(index) * 0.05),
            value: appeared
        )
}
```

Stagger delay: 50-100ms per item. More than 100ms feels slow. Cap total stagger at ~500ms
(show first 5-8 items staggered, rest appear together).

## Symbol Effects

```swift
// Bounce on event (great for "added to cart", "saved")
Image(systemName: "checkmark.circle.fill")
    .symbolEffect(.bounce, value: trigger)

// Pulse for ongoing activity
Image(systemName: "antenna.radiowaves.left.and.right")
    .symbolEffect(.pulse)

// Variable color for progress
Image(systemName: "wifi")
    .symbolEffect(.variableColor.iterative)
```
