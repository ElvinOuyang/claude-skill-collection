# Playwright generation mechanics

Shared between this skill and `chatbot-asset-pipeline`. Keep them in sync — the asset pipeline reuses every convention here.

## Use direct Playwright with `launch_persistent_context` and `headless=False`

Drive Chromium directly via the `playwright` Python or Node library. Two flags do all the work:

- `headless=False` — the user can watch generations happen, which addresses their recurring "is it doing it now?" frustration
- `launch_persistent_context(user_data_dir=...)` — cookies persist across runs, so the user logs in once per machine and the session stays alive indefinitely

A reasonable `user_data_dir` is `~/.cache/visual-ideation/<provider>/` — keep ChatGPT and Gemini contexts separate.

This is the user's stated preference: a Playwright instance, not the MCP wrapper. The full rationale and a minimal Python snippet live in `chatbot-asset-pipeline/references/tooling-rationale.md` — don't duplicate it here, but the gist is that direct Playwright with these flags already provides every property that motivated MCP usage, without the wrapper indirection.

If only the Playwright MCP is available, that's an acceptable fallback. Install Playwright directly (`pip install playwright && playwright install chromium`) when you can.

## Login state

Both ChatGPT and Gemini require an authenticated session. The user logs in **once** in the visible browser; the MCP's persistent context preserves cookies across the session. If the page shows a login prompt, pause and ask the user to sign in — do not try to script the login flow (captcha + 2FA make it brittle).

## Magenta background convention

For any image that will eventually become a transparent PNG, prepend the prompt with:

> "Generate against a solid magenta (#FF00FF) background with no other magenta elements in the subject."

This lets the asset pipeline chroma-key cleanly. White or transparent prompts produce checkered or near-white backgrounds that fight background removal.

## Variation generation

For 6 variations against one descriptor, send 6 separate messages rather than asking for "6 variations" in one message. One-shot multi-image responses tend to homogenize. Separate messages give genuine variance.

Wait for each generation to complete before sending the next — these UIs throttle aggressively, and parallel sends often drop.

## Visibility checkpoints

Every 2 generations, narrate progress to the user: "2 of 6 generated, looking solid; about to send #3." This addresses the recurring "is it doing it now?" frustration when the browser is silent for 30+ seconds.
