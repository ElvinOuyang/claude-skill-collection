---
name: chatbot-asset-pipeline
description: >
  Browser-driven illustration asset pipeline. Drives a logged-in ChatGPT (image-2) or Gemini
  (Nano Banana) session via the Playwright MCP to generate N production illustrations against
  a locked style prompt, captures each on a magenta (#FF00FF) chroma-key background, runs
  background removal to produce transparent PNGs, drops the results into the iOS asset catalog
  with @1x/@2x/@3x and Contents.json, and supports regeneration of broken or off-style assets.
  Requires a locked style — if `design/style-lock.md` is missing, redirect the user to the
  `visual-ideation-moodboard` skill first instead of guessing a style. Use whenever the user
  says "generate illustrations", "replace placeholder assets", "asset regeneration",
  "illustrator handoff", "ChatGPT image gen", "Gemini Nano Banana", "magenta background",
  "transparent PNG", "iOS asset catalog regen", "regen those broken assets", or otherwise asks
  for a batch of styled illustrations to ship into a project. Also use proactively when the
  user has just locked a style and the next obvious step is to produce the actual asset set.
---

# Chatbot Asset Pipeline

Generate a batch of on-style production illustrations by driving a real chatbot UI in a visible browser, then process the outputs into shippable assets (transparent PNGs in an iOS asset catalog, or wherever the user needs them).

## Hard prerequisite: a locked style

This skill does **not** invent a style. If `design/style-lock.md` is missing or the user hasn't approved one, stop and tell the user:

> I don't see a `design/style-lock.md`. Generating now means we'll burn 30+ minutes on assets that probably won't match. Run the `visual-ideation-moodboard` skill first to lock a direction — that takes ~15 minutes and saves the regen pass. Want me to start that?

Why this matters: the recurring failure mode in real sessions is generating 20 assets, realizing the style drifted, and regenerating from scratch. The lock file prevents that.

## Inputs

Before starting, collect:

1. **Style lock** — `design/style-lock.md` (must exist and be user-approved)
2. **Asset list** — names + 1-line subject descriptions for each illustration. For iOS, this is usually a list of empty-state / onboarding / paywall scenes.
3. **Target catalog** — where to place output. For iOS that's `Assets.xcassets/<AssetName>.imageset/`. For web it's typically `public/illustrations/`.
4. **Resolution** — for iOS, `@3x` is the source of truth; @2x and @1x are downscaled. The three scales must represent the same point size, so the source dimensions must be divisible by 6 (LCM of 2 and 3) — otherwise `scale_ios_assets.py` pads with transparency up to the next multiple of 6 and rewrites @3x at the padded size. Default source is 1026×1026 (closest multiple of 6 to the chat UI's 1024×1024); ask the chatbot for that exact dimension or accept the auto-pad.
5. **Provider** — ChatGPT (image-2) or Gemini (Nano Banana). Default to whichever the user has logged in.

If any are missing, ask before starting — silent guessing wastes the generation budget.

## The flow

### Phase 1: Browser session setup

Use the Playwright MCP — **not** raw `playwright` and **not** the computer-use MCP. See `references/tooling-rationale.md` for why; the short version is that the MCP gives the user a visible browser they can watch, which the user explicitly wants.

Open the chosen provider's chat UI. If a login prompt appears, pause and ask the user to sign in. Do not script the login (captcha + 2FA make it brittle, and the user has stable cookies once signed in).

### Phase 2: Generation loop

For each asset in the list:

1. Open a **new chat** in the UI. Stale chat context contaminates style drift across assets.
2. Paste the style-lock's "paste-ready prompt" block, then append the per-asset subject line.
3. Always include the magenta-background instruction:
   > "Generate against a solid magenta (#FF00FF) background. The subject must contain no magenta elements."
4. Send the message; wait for the image to render fully (don't capture during the generation animation).
5. Save the raw output to `.asset-pipeline/raw/<asset-name>.png`.
6. Narrate progress to the user every 2 assets ("3 of 12 generated, on track"). The user has flagged "is it doing it now?" silence as frustrating — keep the running tally visible.

If the UI throttles or returns a refusal, retry once with a softer phrasing; if it still fails, mark the asset for the regen pass and continue.

### Phase 3: Background removal

For each raw PNG, chroma-key out the magenta and produce a transparent PNG.

Use the bundled `scripts/strip_magenta.py`. It does two passes: (1) a chroma-key keyer that converts pure magenta to fully transparent and feathers a soft alpha ramp across anti-aliased edges, and (2) a **despill pass** that removes the magenta tint from any pixel that isn't fully transparent. The despill matters — feathering alone leaves edge pixels with magenta RGB under partial alpha, and when those get composited on a non-magenta background the magenta bleeds through as a pink fringe. White-background or generic "remove background" approaches produce the checkered-edge problem the user keeps hitting; magenta chroma-key + despill is robust.

Output: `.asset-pipeline/transparent/<asset-name>.png`.

### Phase 4: iOS asset catalog (or other target)

For iOS:

1. For each asset, ensure `Assets.xcassets/<asset-name>.imageset/` exists.
2. Place the transparent PNG as `<asset-name>@3x.png`.
3. Generate `<asset-name>@2x.png` and `<asset-name>@1x.png` using bundled `scripts/scale_ios_assets.py`. The script enforces that all three scales are exact integer point-equivalents (size_2x = 2 × size_1x, size_3x = 3 × size_1x); if the source dims aren't divisible by 6 it pads with transparency up to the next multiple of 6 and rewrites the @3x file at the padded size. This is required for crisp Asset Catalog rendering — non-aligned scales force the iOS renderer to interpolate at runtime.
4. Write/update `Contents.json` with the standard 3-scale block. See `references/ios-contents-json.md` for the exact shape.

For web targets, drop the transparent PNG straight into the path the user gave; skip Contents.json.

### Phase 5: Review and regen pass

Open a quick review HTML at `.asset-pipeline/review.html` showing each finished asset on the project's actual background color (not white — context matters for judging). Ask the user to mark any that look off.

For each marked asset, regenerate with the user's correction note appended to the prompt ("less saturated", "different pose", "smaller subject"). Regen happens in-place — overwrite the raw + transparent + scaled set.

If regen pressure gets high (>30% of the batch), stop and ask whether the style-lock needs revisiting. That's a signal the lock isn't tight enough, not that more regens will help.

### Phase 6: Cleanup

Delete `.asset-pipeline/raw/` and `.asset-pipeline/transparent/` once the user confirms the catalog is good. Keep `.asset-pipeline/review.html` and a `manifest.json` mapping asset name → final prompt used → timestamp, so future runs can audit what was generated and how.

If the user has cleanup-agent subagents available, dispatch them for the cleanup step in parallel — it's pure mechanical file work.

## Outputs

- Asset catalog updated in place with @1x/@2x/@3x and Contents.json
- `.asset-pipeline/manifest.json` recording the run for audit
- `.asset-pipeline/review.html` the user can re-open to spot-check later

## Common failure modes

- **Checkered backgrounds.** Caused by white-background generation + naive bg-removal. Always use magenta chroma-key.
- **Login state lost mid-run.** The provider logged the user out. Pause, ask them to re-auth, resume — don't restart the whole batch.
- **Style drift across assets.** Each asset must start a **new chat** with the full style-lock prompt. Reusing the same chat lets the model "evolve" the style, which is exactly what we don't want.
- **"Is it doing it now?" silence.** Narrate every 2 assets. The browser is visible but easy to lose attention on during a long batch.
- **Trying to use computer-use MCP for this.** It's coordinate-based and brittle. The Playwright MCP is the right tool — see `references/tooling-rationale.md`.

## Cross-skill handoff

- **Upstream:** `visual-ideation-moodboard` — produces the `style-lock.md` this skill consumes.
- **Downstream / parallel:** `claude-design-inbound` may emit an asset list this skill processes as PR #3 of a stacked-PR import.
