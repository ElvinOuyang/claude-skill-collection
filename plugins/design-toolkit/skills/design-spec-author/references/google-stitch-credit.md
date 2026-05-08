# Schema origin and credit

The 6-section descriptive schema used by this skill (project title, visual theme description, color palette, typography, component styling, layout & spacing) is adapted from Google's Stitch `design-md` skill, shipped as part of `google-labs-code/stitch-skills`.

## What was kept

- The 6-section shape, in that order.
- The principle that DESIGN.md should be **descriptive natural language with values inline**, not a token JSON dump. This is the core insight worth borrowing — DESIGN.md is consumed by LLMs and humans, both of whom prefer prose with explicit numbers over JSON parsing.
- The split between "values that come from inspecting artifacts" (palette, typography, components, spacing) and "values that need human judgment" (visual theme description). Stitch derives the artifact side from its project APIs; this skill derives them from the codebase.

## What was changed

- Stitch's skill is tightly coupled to Stitch's project APIs (`list_projects`, `get_screen`, `get_project`) and declares `allowed-tools: stitch*:*`. None of that is portable to native iOS, generic web stacks, or one-off codebases.
- This skill replaces the Stitch API integration with a codebase-scanning approach: bundled Python extractors for iOS and web, plus a worst-case generic regex scan. The output schema is the same; the input pipeline is different.
- This skill adds an explicit **refresh flow (Flow B)** with section-by-section spec-vs-impl-vs-divergence decisions. Stitch's skill is authoring-only because it pulls fresh from the Stitch project each time; spec drift is not a problem in that environment. In a regular codebase, drift is the dominant failure mode, so refresh is a first-class flow here.
- This skill is wired explicitly to `design-spec-audit` as the downstream consumer (audit → gap list → refresh decisions), which doesn't exist in the Stitch ecosystem.

## Credit

Schema design adapted from Google Stitch's `design-md` skill. The shape is theirs; the codebase-scanning pipeline, refresh flow, and audit cross-wiring are this skill's.
