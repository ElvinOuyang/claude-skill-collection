---
name: design-spec-author
description: >
  Author or refresh a project's DESIGN.md — the design source-of-truth that pairs with
  `design-spec-audit`. Scans the actual codebase to extract observed values (colors,
  typography, spacing, components, layout) instead of inventing them, asks the user only
  for the few fields that need human judgment (visual theme description, canonical pick
  when the codebase is inconsistent), and writes a 6-section descriptive DESIGN.md
  modeled on Google Stitch's well-shaped schema. Two flows: (A) initial authoring when
  no DESIGN.md exists, (B) refresh with per-section diffs ("spec wins / impl wins / mark
  divergence") when DESIGN.md has drifted from the code. Generic across iOS (Color/Font
  extensions, Theme.swift, Asset Catalog), web (tailwind.config, CSS custom properties,
  design-token files), and unfamiliar stacks (worst-case: hex/font/spacing scan across
  source). Use whenever the user says "set up DESIGN.md", "create a design spec", "we
  need a DESIGN.md", "draft a DESIGN.md from the current codebase", "extract a design
  system from the existing app", "refresh DESIGN.md", "DESIGN.md is out of date", "our
  design spec is stale", or routes audit gaps back into spec decisions. Use proactively
  when the user invokes `design-spec-audit` but no DESIGN.md exists — redirect here
  first; auditing without a spec is opinion. Do NOT trigger for visual brainstorming or
  style exploration (use `visual-ideation-moodboard`), asset generation (use
  `chatbot-asset-pipeline`), or one-off color/font lookups.
---

# Design Spec Author

Produce or refresh `DESIGN.md` so the project has a single, readable source of truth that downstream skills (especially `design-spec-audit`) can check against. The spec is descriptive natural language, not a token JSON dump — the point is that another LLM (or a human) can read DESIGN.md and apply it consistently to a new screen.

This skill exists because the user has authored DESIGN.md across several projects and the recurring failure mode is "I asked Claude to write the spec and it just made values up." The fix is simple: read the codebase first, then talk to the user.

## When to use this skill

Reach for it when:

- The user wants to bootstrap a design spec for an app/site that already has visual choices baked into the code but no written contract
- The user has a stale DESIGN.md and wants to reconcile it with the current implementation
- The user invoked `design-spec-audit` but there's no spec — auditing against nothing is opinion, redirect to authoring first
- An audit produced a P0–P2 gap list and the user wants to route those gaps into spec-vs-impl decisions instead of just "fix the code"

Do **not** reach for it when:

- The user is exploring a *new* visual direction (no codebase signal yet) — that's `visual-ideation-moodboard`
- The user wants to generate assets/illustrations — that's `chatbot-asset-pipeline`
- The user is asking a one-off "what's our primary color" — just answer, don't re-derive a whole spec

## Required inputs

1. **A codebase to read.** This is the non-negotiable input. Without source to scan, the skill devolves into asking the user for values, which is exactly the failure mode we're avoiding.
2. **The user's attention for ~3 short prompts.** They have to (a) confirm the canonical value when the codebase is inconsistent, (b) supply or edit the visual theme description, (c) approve the final DESIGN.md before writing it.
3. **(Optional) An existing DESIGN.md.** If present, this is a refresh. If absent, it's an initial author.

## The two flows

### Flow A — Initial authoring (no DESIGN.md yet)

1. **Detect platform.** Look for `*.xcodeproj` / `Package.swift` / `*.swift` (iOS), `tailwind.config.*` / `package.json` / CSS files (web), or fall back to "scan source for hex codes, font names, and spacing values" (worst-case generic).
2. **Run the extractor for that platform.** Use `scripts/extract_ios_tokens.py` for iOS, `scripts/extract_web_tokens.py` for web, or implement the worst-case scan inline. The extractor outputs a JSON dump grouped by category (colors, typography, spacing, components, layout). Don't paraphrase the dump — keep raw evidence so the user can see *where* each value came from.
3. **Group findings by the 6-section schema** — see `references/schema-template.md`. The schema is fixed; only the values change.
4. **Resolve inconsistencies with the user.** Where the codebase shows multiple values for the same role (e.g., `#2563EB` in 12 places, `#1E40AF` in 8 places), present both with file:line evidence and ask which is canonical. Don't pick for them — the wrong choice locks in for every future audit.
5. **Draft the visual theme description.** This is the only field that doesn't come from code. Take 3–4 representative screens (screenshots if a runtime is available, or the most visually-loaded views), propose a 2–4 sentence description capturing mood/voice (e.g., *"calm utility-grade interface with warm touches at moments of accomplishment"*), and let the user edit. Don't ship Lorem-ipsum vibes here — a vague theme description makes the rest of the spec unanchorable.
6. **Assemble DESIGN.md** using the schema template. Pick the path: project root if no `docs/` exists, `docs/DESIGN.md` if a `docs/` folder is already in use.
7. **Show the user the full DESIGN.md before writing.** They have one chance to spot wrong-canonical-pick mistakes here. After they approve, write the file and open a PR (`feat(design): author DESIGN.md from current codebase`).

### Flow B — Refresh (DESIGN.md exists but has drifted)

1. **Re-scan the codebase exactly as in Flow A** — same extractor, same JSON dump.
2. **Diff observed-now against DESIGN.md, section by section.** Don't compute a giant unified diff and dump it on the user — split it by the 6 schema sections so each decision is small.
3. **For each divergence, present three options:**
   - **Spec wins** — DESIGN.md stays, the code is the bug; flag for a follow-up code change (do not apply that change here, just note it for `design-spec-audit` or a fix PR).
   - **Impl wins** — the code reflects an intentional evolution; update DESIGN.md to match.
   - **Mark as divergence** — both are intentional but in tension (e.g., A/B test, deprecated path); annotate DESIGN.md with `> divergence: <reason>` and leave the code alone.
4. **Apply the user's choices section by section** to a working copy of DESIGN.md. Re-show the assembled file before writing — the user should see the consolidated changes, not just per-section diffs.
5. **Write and open a PR** (`refresh(design): reconcile DESIGN.md with implementation drift`). If "spec wins" was chosen for any section, list those as follow-up code changes in the PR description so `design-spec-audit` can pick them up.

This flow pairs naturally with `design-spec-audit`. The audit produces a P0–P3 gap list; the user can route any of those gaps back into a refresh decision (do we want the spec or the impl to win?). When you're invoked specifically to action audit findings, work the gap list section by section the same way.

## The 6-section schema (descriptive, not a token dump)

DESIGN.md must follow this shape. Keep it natural-language so a downstream LLM can apply it without parsing JSON. Full template with placeholders is in `references/schema-template.md`.

1. **Project title** — name of the project, app, or feature.
2. **Visual theme description** — one paragraph capturing overall mood/voice (e.g., *"calm utility-grade interface with warm touches at moments of accomplishment"*).
3. **Color palette** — hex codes paired with functional roles (background, surface, primary action, destructive, success, etc.). Both raw hex and human-readable role.
4. **Typography rules** — font families, sizes, weights, line-heights, with semantic role (display, body, caption).
5. **Component styling** — only components actually present in the codebase (buttons, cards, inputs, navigation bars, modals, etc.). Each with: variants present, default sizes/paddings, interaction states.
6. **Layout principles & spacing strategy** — base spacing unit, scale (e.g., 4 / 8 / 16 / 24 / 32), grid usage if any, breakpoint logic if web.

Why descriptive over a token JSON: the audited consumers of DESIGN.md are Claude (for `design-spec-audit`), human reviewers, and future-you. JSON is exact but unreadable; descriptive prose with explicit hex/values inline is exact *and* readable.

## Platform extractors (bundled scripts)

- `scripts/extract_ios_tokens.py` — scans Swift sources for `Color(`, `.font(`, `.padding(`, `Theme.*`, `Asset Catalog` xcassets, and `Color.swift` / `Theme.swift` extensions. Outputs `{ colors: [{hex, role_hint, sites: [...]}], typography: [...], spacing: [...], components: [...] }`.
- `scripts/extract_web_tokens.py` — reads `tailwind.config.*` (theme.extend.colors / fontFamily / spacing), CSS custom properties (`--color-*`, `--space-*`), and any `design-tokens.json` / `tokens.css`. Same output shape.
- **Worst-case generic scan** — if neither extractor fits the stack, grep the source for `#[0-9A-Fa-f]{6}` (colors), font-family declarations, and px/rem/pt values. The output will be noisier; lean harder on the "resolve inconsistencies with the user" step.

When in doubt about whether the right script exists, run it once and inspect the JSON before showing anything to the user. The extractor is fast; rerunning it costs nothing.

## Common failure modes

- **Inventing values instead of reading code.** This is the original failure that motivated the skill. If you find yourself guessing at "what color is the primary button probably," stop and run the extractor.
- **Picking the canonical value yourself when the code is inconsistent.** The user has context you don't (which screen is the canonical one, which value is deprecated). Always surface inconsistencies with evidence and let them decide.
- **Skipping the visual theme description.** It's the only field that requires human judgment, and it's also the field that anchors every other decision. A spec without a theme description reads as a list of values without a reason.
- **Treating refresh as a one-shot diff dump.** Section-by-section, three-option choices. A unified diff with no decision framework forces the user to make all the calls at once and they'll just rubber-stamp it.
- **Writing DESIGN.md to a random path.** Project root by default, `docs/DESIGN.md` only if a `docs/` folder already exists. Don't invent new locations — `design-spec-audit` and other consumers expect the standard path.

## Cross-skill wiring

- **Pairs with `design-spec-audit`** — author DESIGN.md here, audit against it there, refresh here when audit gaps prompt spec-vs-impl decisions.
- **Pairs with `claude-design-inbound`** — that skill may produce a DESIGN.md as part of its tokens PR; if so, this skill validates and harmonizes, treating it as a Flow B refresh.
- **Upstream:** none required (works against any codebase).
- **Output:** `DESIGN.md` (project root, or `docs/DESIGN.md` if a `docs/` folder exists).

## References

- `references/schema-template.md` — the exact 6-section schema with placeholders.
- `references/google-stitch-credit.md` — schema origin and credit.

The 6-section schema is adapted from Google Stitch's `design-md` skill (`google-labs-code/stitch-skills/design-md`). Stitch's skill is tightly coupled to Stitch's project APIs and isn't reusable across iOS/web/generic codebases, but its output schema is well-shaped for LLM consumption — that part is what's mirrored here.
