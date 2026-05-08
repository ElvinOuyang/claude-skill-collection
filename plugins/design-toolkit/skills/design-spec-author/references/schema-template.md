# DESIGN.md schema template

Copy this template, replace placeholders with values extracted from the codebase, and edit the visual theme description with the user. Keep prose descriptive — exact values inline, but in a sentence-style format another LLM (or a human) can read top-to-bottom.

---

```markdown
# DESIGN — <Project / App / Feature name>

> Source of truth for visual design. Audited by `design-spec-audit`. Refresh via
> `design-spec-author` (Flow B) when the implementation drifts.

## 1. Visual theme

<2–4 sentence paragraph capturing the overall mood and voice of the design. Example:
"A calm, utility-grade interface designed for daily check-ins. Most surfaces are
quiet — neutral grays, generous whitespace, restrained motion — so that moments
of accomplishment (streak completion, badge unlock) can use saturated accent
color and spring animations without feeling out of place. The palette leans warm
to feel hand-made rather than enterprise-default.">

## 2. Color palette

Each color is listed with its hex code and the functional role it plays. Tokens
(if the codebase uses any) are listed alongside.

- **Background — `#FFFFFF`** (token: `surface.canvas`). The default page/screen
  background. Used on every screen as the bottom layer.
- **Surface — `#F7F7F5`** (token: `surface.raised`). Cards, sheets, and any
  element that should sit slightly above the canvas.
- **Primary action — `#2563EB`** (token: `accent.primary`). All primary CTAs,
  active tab indicators, focused inputs.
- **Destructive — `#DC2626`** (token: `accent.destructive`). Delete confirmations,
  validation errors, irreversible actions.
- **Success — `#16A34A`** (token: `accent.success`). Streak hits, completion
  states, positive validation.
- **Text primary — `#0F172A`** (token: `text.primary`). Default text color on
  light surfaces.
- **Text secondary — `#64748B`** (token: `text.secondary`). Captions, helper
  text, timestamps.
- **Border — `#E5E7EB`** (token: `border.default`). Hairlines between sections,
  card borders.

> Add or remove rows to match what's actually in the codebase. If a color exists
> in code but the role is unclear, list it as `role: TBD` and resolve with the
> user during authoring.

## 3. Typography

- **Display** — SF Pro Display, 34pt, weight 700, line-height 1.1. Used for
  screen titles in large-title nav bars.
- **Headline** — SF Pro Display, 22pt, weight 600, line-height 1.2. Section
  headers within a screen.
- **Body** — SF Pro Text, 17pt, weight 400, line-height 1.4. The default text
  size; what most paragraphs render at.
- **Body emphasized** — SF Pro Text, 17pt, weight 600, line-height 1.4. Inline
  emphasis, primary list items.
- **Caption** — SF Pro Text, 13pt, weight 400, line-height 1.3. Helper text,
  timestamps, footnotes.

> Match this to the families and sizes actually used. If the codebase only uses
> 3 type roles, only list 3.

## 4. Component styling

Only document components that exist in the codebase. For each: variants, default
sizing, and notable interaction states.

### Button
- **Variants:** primary (filled, accent.primary background, text.onAccent
  foreground), secondary (outlined, accent.primary border + text), tertiary
  (text-only).
- **Default size:** height 44pt, horizontal padding 16pt, corner radius 12pt.
- **States:** pressed = 90% opacity; disabled = 40% opacity; focused (web) = 2pt
  outline using accent.primary at 50% opacity.

### Card
- **Variants:** default, elevated.
- **Default sizing:** corner radius 16pt, internal padding 16pt all sides,
  optional 1pt hairline border using border.default.
- **Elevation:** elevated variant adds a soft shadow (offset 0/4, blur 12,
  opacity 8%).

### Input
- **Default sizing:** height 44pt, horizontal padding 12pt, corner radius 8pt,
  1pt border using border.default.
- **States:** focused = border becomes accent.primary; error = border becomes
  accent.destructive and helper text in same color; disabled = surface.canvas
  background and text.secondary text.

### Navigation bar (iOS) / Top nav (web)
- <fill in only if present>

### Modal / sheet
- <fill in only if present>

> Do not invent components that don't exist in the source. If the app has only
> buttons and cards, only buttons and cards belong here.

## 5. Layout & spacing

- **Base unit:** 4pt.
- **Scale:** 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64. Anything outside this scale
  should be justified — usually it indicates a bug.
- **Default content padding:** 16pt horizontal on phone, 24pt on tablet/desktop.
- **Vertical rhythm:** 8pt between related elements, 16pt between groups, 24pt
  between sections.
- **Grid (web only):** 12-column grid, 24pt gutters, max content width 1200px.
- **Breakpoints (web only):** mobile <640, tablet 640–1024, desktop >1024.

> iOS apps usually don't need a grid section; delete it if it doesn't apply.

---

## Open divergences

> Optional. Use when the refresh flow finds intentional inconsistencies.
> Example: "Settings screen uses spacing.sm where rest of app uses spacing.md
> — A/B test scheduled to end 2026-Q3."
```

---

## How to use this template

- **Initial authoring**: replace every placeholder with values from the extractor JSON. Where a section doesn't apply (e.g., grid in an iOS app), delete the section rather than leaving "N/A".
- **Refresh**: only edit the sections that diverged. Preserve the rest of the file structure so the diff stays readable in PR review.
- **The "Open divergences" section is optional** — only include it if the refresh flow surfaced intentional inconsistencies the user wants to track.
