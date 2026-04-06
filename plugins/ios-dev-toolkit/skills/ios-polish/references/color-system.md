# iOS Color System Reference

## Semantic Colors (Always Use These First)

### Text Colors
| SwiftUI                          | Purpose                    | Light        | Dark         |
|----------------------------------|----------------------------|-------------|-------------|
| `Color(.label)`                  | Primary text               | Near-black  | Near-white  |
| `Color(.secondaryLabel)`         | Secondary text, metadata   | 60% gray    | 60% gray    |
| `Color(.tertiaryLabel)`          | Disabled text, placeholders| 30% gray    | 30% gray    |
| `Color(.quaternaryLabel)`        | Barely visible text        | 18% gray    | 16% gray    |

### Background Colors
| SwiftUI                                  | Purpose                    |
|------------------------------------------|----------------------------|
| `Color(.systemBackground)`               | Primary background         |
| `Color(.secondarySystemBackground)`      | Cards, grouped sections    |
| `Color(.tertiarySystemBackground)`       | Nested cards, input fields |
| `Color(.systemGroupedBackground)`        | Grouped table background   |
| `Color(.secondarySystemGroupedBackground)`| Grouped table cells       |

### Separator & Fill Colors
| SwiftUI                          | Purpose                    |
|----------------------------------|----------------------------|
| `Color(.separator)`              | Thin lines between items   |
| `Color(.opaqueSeparator)`        | Non-translucent separators |
| `Color(.systemFill)`             | Filled UI elements         |
| `Color(.secondarySystemFill)`    | Secondary fills            |
| `Color(.tertiarySystemFill)`     | Input field backgrounds    |

## Tinted Neutrals (The Taste Differentiator)

Pure gray feels clinical. Tinted neutrals feel intentional:

**Warm palette** (family apps, food, lifestyle):
- Background: cream/warm white (like Pumpkin's `warmCream`)
- Borders: warm tan/sand
- Secondary text: warm gray with slight brown tint

**Cool palette** (productivity, finance, health):
- Background: cool blue-white
- Borders: cool slate
- Secondary text: blue-gray

**How to implement:**
```swift
// In your asset catalog or Color extension:
// Don't: Color.gray
// Do: A custom color with slight warm/cool tint that adapts to dark mode
extension Color {
    static let warmNeutral = Color("warmNeutral")  // Light: warm gray, Dark: warm dark gray
}
```

Always define both light and dark mode variants in your asset catalog.

## Accent Color Strategy

**One accent color handles 80% of color needs:**
- Tint color (buttons, links, navigation tints)
- Selected states (tab bar, segmented controls)
- Key data points (charts, badges)

**Supporting colors are functional, not decorative:**
- `Color(.systemRed)` — destructive, urgent, errors
- `Color(.systemGreen)` — success, complete
- `Color(.systemYellow)` / `.systemOrange` — warnings, pending

**Semantic system colors** (`.systemRed`, `.systemBlue`, etc.) automatically adjust for
dark mode and accessibility — prefer them over custom hex colors for functional states.

## Dark Mode Design

Dark mode is not "invert the colors." Key differences:

1. **Elevated surfaces** — In dark mode, higher surfaces are *lighter*, not darker.
   `secondarySystemBackground` is lighter than `systemBackground` in dark mode.
2. **Reduce saturation** — Bright colors that look great on white can vibrate on dark backgrounds.
   Use `.opacity(0.85)` or lighter tints for accent colors in dark mode.
3. **Borders matter more** — Shadows are invisible in dark mode. Use subtle borders
   (`Color(.separator)`) or elevated backgrounds to create depth.
4. **Test with pure black** — Some users enable "Smart Invert" or have OLED screens.
   `Color(.systemBackground)` is pure black in dark mode — make sure your UI works on it.

## Accessibility Color Considerations

- **4.5:1 contrast ratio** for body text (WCAG AA)
- **3:1 contrast ratio** for large text (>= 18pt or 14pt bold) and UI components
- **Never use color alone** to convey information. Pair red with an icon or label.
- **Increase Contrast** accessibility setting: check that your UI responds.
  Semantic colors handle this automatically — custom colors may not.
