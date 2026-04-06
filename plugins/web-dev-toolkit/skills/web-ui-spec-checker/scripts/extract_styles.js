/**
 * extract_styles.js
 * Paste into browser_evaluate to extract computed styles for spec comparison.
 * Returns an object with the key visual properties of a selector.
 *
 * Usage: pass selector as a string argument, or hardcode it below.
 */
(function extractStyles(selector) {
  const el = document.querySelector(selector);
  if (!el) return { error: `Element not found: ${selector}` };

  const s = window.getComputedStyle(el);
  return {
    selector,
    color: s.color,
    backgroundColor: s.backgroundColor,
    fontSize: s.fontSize,
    fontWeight: s.fontWeight,
    borderLeft: s.borderLeft,
    borderLeftColor: s.borderLeftColor,
    borderLeftWidth: s.borderLeftWidth,
    padding: s.padding,
    display: s.display,
    textContent: el.textContent?.trim().slice(0, 80),
  };
})
