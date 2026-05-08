# Why the Playwright MCP (and not the alternatives)

The user has hit the same confusion in three separate sessions, so this is worth being explicit about.

## Use: Playwright MCP

- Persistent browser context — the user logs in once and cookies stick across the session
- Visible browser window — the user can watch generations happen, which addresses their recurring "is it doing it now?" frustration
- Selector-based interactions (text content, ARIA roles) are stable across UI tweaks from OpenAI / Google
- The MCP's screenshot + accessibility-tree primitives are reliable for "wait until image rendered"

## Don't use: raw `playwright` Python/Node scripts

- Headless by default — invisible to the user
- A fresh browser each invocation means re-logging in every run, which is brittle (captcha, 2FA)
- Mixed reports of working vs not working depending on env; the MCP standardizes the path

## Don't use: computer-use MCP / coordinate taps

- Coordinate-based clicking breaks on every minor UI redesign
- Screen-resolution dependent
- Slower (each step takes a screenshot + reasoning loop) and more error-prone
- The user has explicitly preferred selector-based automation in past sessions

If the user only has raw `playwright` available and not the MCP, ask them to enable the MCP before proceeding rather than falling back. The visibility regression is worth a one-time install.
