# Playwright for web audits

Playwright is the right tool for web audits because `getComputedStyle` returns the actual rendered values — exactly what the audit needs to compare against the spec. The MCP is preferred for visibility; scripted Playwright is acceptable for CI.

## Capturing computed styles

For each spec rule that targets a web element:

```js
const el = await page.locator(selector).first();
const computed = await el.evaluate((node) => {
  const cs = getComputedStyle(node);
  return {
    color: cs.color,
    backgroundColor: cs.backgroundColor,
    padding: cs.padding,
    margin: cs.margin,
    fontFamily: cs.fontFamily,
    fontSize: cs.fontSize,
    fontWeight: cs.fontWeight,
    lineHeight: cs.lineHeight,
    borderRadius: cs.borderRadius,
    transitionDuration: cs.transitionDuration,
    transitionTimingFunction: cs.transitionTimingFunction,
  };
});
```

`getComputedStyle` returns colors as `rgb(...)` / `rgba(...)`. Convert to hex before diffing against the spec, otherwise `#2D8CFF` and `rgb(45, 140, 255)` will look like a mismatch when they're identical.

## Screenshots

Per-element screenshots make the report scannable:

```js
await page.locator(selector).screenshot({ path: `.audit/shots/${screen}-${name}.png` });
```

Full-page shots are useful for layout findings:

```js
await page.screenshot({ path: `.audit/shots/${screen}-full.png`, fullPage: true });
```

## Motion

`transitionDuration` and `transitionTimingFunction` cover most cases. For programmatic animations (Web Animations API, framer-motion), the audit can't always read the timing — flag those as P3 advisories asking the user to expose duration via a CSS variable so the audit can check it.

## Responsive

If the spec covers multiple breakpoints, run the audit at each (`page.setViewportSize({ width, height })`) and report findings per breakpoint. Don't merge breakpoints — a desktop-correct spacing miss at mobile is a separate finding.
