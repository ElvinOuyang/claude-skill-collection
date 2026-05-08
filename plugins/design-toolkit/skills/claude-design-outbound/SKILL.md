---
name: claude-design-outbound
description: >
  Export the current implementation back to Claude Design as an artifact pack a designer can
  iterate on — annotated screenshots of every screen, a token dump (color/spacing/typography
  values actually in use), a component inventory with variant matrices, and a current spec
  snapshot in DESIGN.md form. This is the reverse of `claude-design-inbound`: instead of
  importing a designer's artifacts, this skill packages the implementation's reality so the
  designer can react to "what shipped" rather than "what was specced." Use whenever the user
  says "export to Claude Design", "send to Claude Design", "hand off current implementation",
  "design feedback round", "snapshot for designer", "what does the app actually look like
  right now", "package up the current state for design review", or any variant where the
  current implementation needs to leave the codebase as a designer-consumable bundle.
---

# Claude Design Outbound

Send the current implementation back to Claude Design as a pack the designer can react to. The asymmetry this skill addresses: designers iterate on what they think shipped, but implementations drift — sometimes intentionally (engineering tradeoffs), sometimes not (token resolved to a fallback). An accurate snapshot of what's actually rendering is the unblock for the next design round.

## When to use

- The user wants a "feedback round" — designer reviews, designer iterates, then `claude-design-inbound` brings the next version back in.
- A component shipped with engineering tradeoffs and the designer needs to see them in context.
- An audit (`design-spec-audit`) found drift and the user wants to capture the current state before deciding what to fix vs respec.
- The team wants a periodic "current state" snapshot for design archives.

## What's in the pack

The output is a single directory `design/outbound/<date>/` containing:

```
design/outbound/2026-05-07/
├── README.md            ← cover sheet: what's in the pack, how to read it
├── screens/             ← annotated screenshots, one per screen
│   ├── tasks-list.png
│   ├── tasks-list.annotated.png   ← same shot with callouts
│   ├── tasks-detail.png
│   └── ...
├── components/          ← per-component variant matrices
│   ├── button.png
│   ├── button.matrix.md
│   ├── card.png
│   └── ...
├── tokens/
│   ├── colors.json       ← actual computed colors keyed by token name
│   ├── spacing.json
│   ├── typography.json
│   └── motion.json
├── inventory.md         ← every component / screen / asset, organized
└── DESIGN.snapshot.md   ← spec-shaped snapshot of current reality
```

The designer's input is a single folder they can drag into Claude Design.

## The flow

### Step 1: Capture screens

Drive the running app the same way `design-spec-audit` does:

- **iOS** — AXe CLI (`axe screenshot`, `axe describe-ui`). Not coordinate taps, not computer-use MCP.
- **Web** — Playwright. Capture full-page shots and per-component crops.

Walk the user-facing top 10–20 screens (don't try to capture everything). For each:

1. Full screenshot to `screens/<screen>.png`.
2. Annotated copy to `screens/<screen>.annotated.png` with callouts naming components and key tokens (e.g., "Primary CTA · `accent.primary`/`16/24` padding"). Use the bundled `references/annotation-style.md` for visual conventions so multiple runs look consistent.

Annotations are the highest-signal part of the pack — they translate "pixels" into "tokens", which is what the designer is iterating on.

### Step 2: Component inventory + variants

Identify reusable components from the codebase and capture all variants of each in one shot. For a button: default / hover / pressed / disabled / loading, primary / secondary / destructive — laid out in a grid.

Write a 1-page `<component>.matrix.md` per component listing:

- Variants present
- Variants in spec but missing in code
- Variants in code but not in spec ("ad hoc" — flag for the designer)

### Step 3: Token dump

Read tokens from the codebase **and** from the running app. Both because:

- The codebase value is the intent.
- The runtime value is what shipped (and may differ if a fallback resolved unexpectedly).

For each token write `tokens/<category>.json`:

```json
{
  "accent.primary": {
    "intent": "#2D8CFF",
    "runtime": "#2D8CFF",
    "match": true,
    "used_in": ["primary button", "selection ring", "link text"]
  },
  "accent.warning": {
    "intent": "#FFA800",
    "runtime": "#FFA500",
    "match": false,
    "note": "runtime resolves to fallback; investigate before shipping"
  }
}
```

The `used_in` list is the designer's most-asked-for piece of context — they want to know which surfaces a token change will ripple through.

### Step 4: Current-state spec snapshot

Generate `DESIGN.snapshot.md` in the same shape as the project's existing `DESIGN.md` (or a sensible default if none exists). This is **not** the canonical spec — it's a snapshot of what shipped, labeled as such at the top:

```
> NOTE: This is a runtime snapshot generated <date> by claude-design-outbound.
> It describes what the app is doing today, not what it should do.
> Use this as input to the next design iteration in Claude Design,
> then bring the resulting changes back via claude-design-inbound.
```

The designer compares this against their working spec to spot drift, then iterates.

### Step 5: Cover sheet

Write `README.md` as a 1-page cover:

- Date + project + branch / commit SHA the snapshot was taken on
- Which screens are included, which aren't, why
- Any known caveats (e.g., "tasks-detail captured pre-redesign, list shows post-redesign")
- A short list of suggested follow-ups (mismatched tokens, ad-hoc variants, missing variants) — keep this terse; the designer will form their own list

### Step 6: Hand off

The pack is the deliverable. If the user has a Claude Design link to drop the pack into, share the directory path; if they want it zipped, zip `design/outbound/<date>/` and report the path.

Don't auto-upload anywhere — the user controls where it goes.

## Outputs

- `design/outbound/<date>/` directory with the full pack
- A short summary printed to the user listing what was captured and any anomalies worth flagging immediately (e.g., "3 tokens have runtime mismatches, see `tokens/colors.json`")

## Common failure modes

- **Skipping annotations.** Without callouts, a screenshot is just a screenshot — the designer has to reverse-engineer which token controls which surface. Annotations are the value-add.
- **Capturing only the codebase token values, not runtime.** Drift is the whole reason this skill exists. Always capture both.
- **Capturing every screen.** Pick the top 10–20 by user impact. The pack is for iteration, not archive.
- **Reusing yesterday's pack.** Each round needs a fresh capture — designs change, and stale packs cause designers to iterate on outdated state.

## Cross-skill handoff

- **Reverse:** `claude-design-inbound` — once the designer iterates on the pack, the result comes back in via the inbound skill as a stacked PR.
- **Upstream feeder:** `design-spec-audit` — if an audit was just run, its `.audit/report.md` and screenshots can be reused/extended into the outbound pack instead of recapturing from scratch.
