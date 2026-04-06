# iOS Typography Reference

## San Francisco Text Style Hierarchy

| Text Style     | Default Size | Weight   | Use For                        |
|---------------|-------------|----------|--------------------------------|
| `.largeTitle`  | 34pt        | Regular  | Screen titles (large nav only) |
| `.title`       | 28pt        | Regular  | Section headers, hero text     |
| `.title2`      | 22pt        | Regular  | Subsection headers             |
| `.title3`      | 20pt        | Regular  | Card titles, group headers     |
| `.headline`    | 17pt        | Semibold | Row titles, emphasized body    |
| `.body`        | 17pt        | Regular  | Primary content text           |
| `.callout`     | 16pt        | Regular  | Secondary content, descriptions|
| `.subheadline` | 15pt        | Regular  | Supporting text, metadata      |
| `.footnote`    | 13pt        | Regular  | Timestamps, tertiary info      |
| `.caption`     | 12pt        | Regular  | Labels, badges, fine print     |
| `.caption2`    | 11pt        | Regular  | Rarely used — very small       |

## Dynamic Type Scaling

All text styles scale automatically with the user's preferred text size. At the largest
accessibility sizes (AX1-AX5), layouts need to adapt:

```swift
// Use ViewThatFits for layouts that break at large sizes
ViewThatFits {
    HStack { label; value }  // Preferred: side-by-side
    VStack(alignment: .leading) { label; value }  // Fallback: stacked
}
```

### Testing Dynamic Type

Test at these sizes minimum:
- **Default** — your baseline
- **XXXL** (largest non-accessibility) — common for older users
- **AX3** (mid accessibility) — catches most layout breaks

In Xcode: Environment Overrides > Dynamic Type, or `@Environment(\.dynamicTypeSize)`

## Weight as Hierarchy

The golden rule: **one bold/semibold per visual group, everything else regular.**

```swift
// Good: clear hierarchy
Text("Buy groceries")
    .font(.headline)  // Semibold by default
Text("Assigned to Mom")
    .font(.subheadline)
    .foregroundStyle(.secondary)

// Bad: competing weights
Text("Buy groceries")
    .font(.body.bold())
Text("Assigned to Mom")
    .font(.caption.bold())  // Why is this bold?
```

## Line Spacing & Readability

- Body text in scrollable views: add `.lineSpacing(4)` for readability
- Keep line length under ~70 characters for comfortable reading
- Use `.lineLimit(2)` + `.truncationMode(.tail)` for user-generated content in lists
- Multiline text: `.multilineTextAlignment(.leading)` (never `.center` for body text)

## Custom Fonts

If using a custom font, always provide Dynamic Type scaling:

```swift
.font(.custom("YourFont", size: 17, relativeTo: .body))
```

The `relativeTo:` parameter makes the custom font scale with Dynamic Type.
