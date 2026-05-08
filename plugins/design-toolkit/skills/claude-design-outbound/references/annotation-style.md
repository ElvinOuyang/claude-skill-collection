# Annotation style for outbound screenshots

Annotations turn screenshots into something a designer can iterate on. Keep them consistent across the pack so the designer doesn't have to re-learn the legend per screen.

## Visual conventions

- **Callout color:** magenta `#FF00FF`. Stands out on every UI without competing with brand colors. (Same chroma-key convention used by the asset pipeline — keep the toolkit consistent.)
- **Callout font:** SF Mono / JetBrains Mono / monospace at 12pt. Readable, signals "this is metadata, not part of the design."
- **Leader lines:** 1pt solid magenta from the callout text to the element it labels. Avoid arrows — they imply direction; we want neutral pointers.
- **Numbered index:** prefix each callout with `[1]`, `[2]`, etc. Useful for cross-referencing in the cover sheet.

## What to label

For each screen, label:

1. **Container components** — "Primary card · `radius.md` · `spacing.md` padding"
2. **Primary CTA** — "Primary button · `accent.primary` bg · `text.onAccent` fg · `body.semibold` type"
3. **Anomalies** — anything that doesn't match a token: "Hard-coded `#2A88F9` (should be `accent.primary`)"
4. **Ad-hoc variants** — components used here that don't appear in the design system: "Ad-hoc list row variant — flag for designer"

Aim for 4–8 callouts per screen. More than that and the screenshot becomes unreadable; fewer and it's just a screenshot with decoration.

## What NOT to label

- Pixel measurements ("padding: 16px"). The token name carries the value; doubling up creates clutter.
- Subjective notes ("this feels off"). Save those for the cover sheet's "follow-ups" section.
- Every single element. Pick what's load-bearing for the iteration round.

## Implementation hint

Generate annotations as a separate layer (PNG with transparent background) and composite over the screenshot. That way the original screenshot stays clean and the annotated version can be regenerated without re-capturing the app.
