# Playwright generation mechanics

Shared between this skill and `chatbot-asset-pipeline`. Keep them in sync — the asset pipeline reuses every convention here.

## Use the Playwright MCP, not raw `playwright`

The MCP gives us a persistent browser context the user can see. Raw `playwright` scripts spawn a headless browser the user can't watch, which kills the "is it doing it now?" visibility the user keeps asking for.

If the user has only raw `playwright` installed, ask them to enable the Playwright MCP before continuing. Don't fall back to headless — the loss of visibility is more painful than the install step.

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
