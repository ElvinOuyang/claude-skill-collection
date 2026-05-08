# Why direct Playwright (and not the alternatives)

The user has hit the same confusion in three separate sessions, so this is worth being explicit about.

## Use: direct Playwright with a persistent context and a visible browser

Drive Chromium directly via `playwright` (Python or Node), launched with:

- `launch_persistent_context(user_data_dir=..., headless=False)` — gives a real browser window the user can watch AND persists cookies/login across runs (one login lasts indefinitely)
- Selector-based interactions (`page.get_by_role`, `page.get_by_text`) — stable across minor UI tweaks from OpenAI / Google
- `page.wait_for_selector(...)` and `page.screenshot(...)` — reliable for "wait until image rendered" gates

A reasonable user_data_dir is `~/.cache/chatbot-asset-pipeline/<provider>/` — keep ChatGPT and Gemini contexts separate so a logout in one doesn't affect the other.

This is the user's stated preference: they explicitly want a Playwright instance they can see and interact with directly, not an MCP wrapper around it.

## Don't use: the Playwright MCP

The MCP wraps the same Playwright primitives but adds an indirection layer that the user has flagged as friction in past sessions. Direct Playwright with `headless=False` + `launch_persistent_context` already provides every property that motivated MCP usage (visibility, persistent cookies, selector-based interaction) without the wrapper.

If the only Playwright you have is the MCP, that's fine to use as a fallback — but install Playwright directly when you can (`pip install playwright && playwright install chromium`) and prefer that.

## Don't use: computer-use MCP / coordinate taps

- Coordinate-based clicking breaks on every minor UI redesign
- Screen-resolution dependent
- Slower (each step takes a screenshot + reasoning loop) and more error-prone
- The user has explicitly preferred selector-based automation in past sessions

## Minimal Python pattern

```python
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.expanduser("~/.cache/chatbot-asset-pipeline/chatgpt")

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,            # user-visible
        viewport={"width": 1280, "height": 900},
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://chatgpt.com/")
    # If page shows login: pause, ask user to sign in, wait for them to confirm.
    # Cookies persist via user_data_dir, so login is one-time per machine.
```

If the user has cookies already persisted from a normal Chrome session, point `user_data_dir` at the appropriate Chrome profile directory instead — but only with explicit user opt-in, since that profile holds other personal state.
