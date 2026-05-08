---
name: visual-ideation-moodboard
description: >
  Moodboard-first visual brainstorming that locks a style direction before any production
  illustration work begins. Scrapes references (Pinterest, Dribbble, web search, user-provided
  images), narrows on the user's favorites, distills the picks into a concrete style descriptor
  (palette, line weight, texture, mood, era), generates 6 candidate variations through a direct
  Playwright session (visible browser, persistent login) against ChatGPT (image-2) or Gemini
  (Nano Banana), and outputs a locked
  style-prompt artifact (`style-lock.md`) that downstream skills like `chatbot-asset-pipeline`
  and `claude-design-inbound` consume. Standalone and reusable for posters, brand directions,
  UI illustration, mascots, marketing artwork — not just iOS asset replacement. Use whenever
  the user says "visual brainstorm", "moodboard", "style direction", "illustration ideation",
  "design exploration", "rapid-fire visual ideation", "lock a style", "find a look", "before
  generating assets", or "I'll know it when I see it" — and use it proactively when the user
  is about to generate illustrations but has not yet locked a style. If `chatbot-asset-pipeline`
  is invoked without a locked style, redirect here first.
---

# Visual Ideation Moodboard

Lock a visual style **before** the user spends hours generating production assets that turn out off-tone. The cost of a wrong style direction compounds across every asset the pipeline generates — a moodboard pass up front is cheap insurance.

This skill is upstream of `chatbot-asset-pipeline`. Its only job is to produce one artifact: a `style-lock.md` file that downstream skills can paste verbatim into a generation prompt.

## When to use this skill

Use it whenever the user is in "exploration mode" for a visual direction:

- They want illustrations, posters, marketing art, mascots, UI spot art, or a brand look
- They have a vague vibe ("cozy", "Y2K", "editorial") but no concrete style descriptor
- They said something like "I'll know it when I see it" — that's a giant flag this skill is needed
- They're about to fire up the asset pipeline but have not committed to palette / line weight / texture

If a `style-lock.md` already exists in the project and the user hasn't asked to redo it, do **not** rerun this skill — go straight to the asset pipeline.

## The flow

There are four phases. Each phase ends with the user picking from options — never assume their taste.

### Phase 1: Reference scrape

Goal: 12–20 visual references collected into one viewable moodboard so the user can react.

Sources to pull from, in rough priority order:

1. **User-provided** — anything they've already pasted, dropped in a folder, or pinned. Always include these first.
2. **Pinterest / Dribbble / Behance** — search for the user's vibe phrases via a direct Playwright session (visible browser, persistent login — see `references/playwright-generation.md`) if the user has a logged-in session, otherwise via web search and image URLs.
3. **General web search** — for less-mainstream styles ("Memphis design", "ligne claire", "risograph").
4. **Existing project assets** — if the user is replacing assets in an existing app, scrape the current set so the moodboard can include "what we're moving away from" as a contrast.

Output the moodboard as a single HTML file at `design/moodboard/board.html` with a 4-column grid, each tile labeled with its source and a 1-line descriptor. Open it in the user's browser. **Do not paginate** — the user needs to see everything at once to react.

See `references/moodboard-template.html` for the grid template.

### Phase 2: User picks favorites

Ask the user to mark 3–5 favorites. Accept any of:

- Numbers/coordinates ("tiles 3, 7, 12")
- Drag-and-drop into a "favorites" folder
- Just describing what they liked ("the orange one with the thick outlines")

Do not move on with fewer than 3 picks — the distillation in phase 3 needs enough signal to triangulate.

### Phase 3: Distill into a style descriptor

Read the picks together and extract concrete attributes. The point of this phase is to convert "vibes" into something a generation model can actually reproduce.

Required dimensions to fill in (all of them, even if you have to guess and ask the user to correct):

| Dimension | Example values |
|---|---|
| Palette | "warm muted earth tones: terracotta #C66, sage #8A9, cream #F4E" |
| Line weight | "thick uniform 2pt outlines" or "no outlines, soft fills only" |
| Texture | "subtle paper grain", "flat vector", "halftone dots", "watercolor edges" |
| Mood | "playful, cozy, slightly retro" |
| Era / movement | "70s editorial", "Y2K web", "Memphis", "ligne claire" |
| Composition | "centered single subject, lots of negative space" |
| What to avoid | "no gradients, no realistic rendering, no 3D" |

Show the user the descriptor. Let them edit any row. **Do not** proceed to generation until they sign off — bad descriptors waste the whole phase 4 generation budget.

### Phase 4: Generate 6 variations

Drive a logged-in browser session (ChatGPT image-2 or Gemini Nano Banana) via direct Playwright (`launch_persistent_context`, `headless=False`) to produce 6 variations against a single anchor subject. The anchor subject should be something representative of the project (e.g., for an iOS empty-state replacement, use the project's most-frequent empty-state metaphor; for a mascot, use a 3/4 portrait pose).

Why 6 and not 4 or 12: 4 doesn't give enough variation for the user to triangulate; 12 makes the picking phase exhausting. 6 is the sweet spot from observed sessions.

Each variation should hold the descriptor constant but vary one secondary axis (camera framing, color emphasis, prop choice) so the user can see "the style applied to slightly different shots."

For Playwright mechanics, login state, "is it doing it now?" visibility, and the magenta-background convention, see `references/playwright-generation.md`. (The asset pipeline reuses the same machinery — keep them consistent.)

### Phase 5: Lock the winner

User picks 1 winner. Write `design/style-lock.md` with:

```
# Style Lock — <project-or-feature>

Locked: <date>
Locked by: <user-confirmation-quote>

## Descriptor
<the full table from phase 3, with any edits the user made during phase 4>

## Paste-ready prompt
<a single paragraph that downstream tools paste verbatim into ChatGPT/Gemini.
includes the descriptor expressed as instructions, plus the magenta-background
convention so the asset pipeline can chroma-key cleanly>

## Reference image
<filename of the winning variation, copied into design/style-lock/>

## Anti-examples
<the variations the user rejected, with one-line "why not" notes — saves
future redo passes from re-exploring dead ends>
```

This file is the **only** thing the user needs to keep. The moodboard, candidates, and rejects are exploration scratch — the lock file is the contract.

## Output guarantee

When this skill finishes, `design/style-lock.md` exists, the user has explicitly approved it, and the paste-ready prompt section is self-contained (does not reference the moodboard or the candidate images by ID — a downstream skill should be able to use just the prompt block).

## Common failure modes

- **Skipping phase 3 and going straight to generation.** Without a written descriptor, the user can't articulate what's wrong with a candidate, so feedback becomes "I dunno, it's just off." Always force the descriptor before generation.
- **Asking the user "what do you think?" without showing the moodboard inline.** They need to see all references at once. Open the HTML file — don't list URLs in chat.
- **Generating more than 6 candidates "just in case."** Decision fatigue kills the lock. Stop at 6.
- **Treating the lock as immutable forever.** It's the lock for *this* batch. If the user starts a different feature with a different vibe, run the skill again — the second run will be much faster because the structure is in place.

## Cross-skill handoff

Downstream skills look for `design/style-lock.md`. If you change the path or filename, update:

- `chatbot-asset-pipeline/SKILL.md` (consumes the lock)
- `claude-design-inbound/SKILL.md` (may emit a lock as part of the tokens PR)

When `chatbot-asset-pipeline` runs without finding a lock, it should redirect the user back to this skill rather than guessing a style.
