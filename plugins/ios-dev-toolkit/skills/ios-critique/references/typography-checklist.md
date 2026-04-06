# Typography Evaluation Checklist

## Hierarchy Check
- [ ] Can you identify 3 distinct levels? (Title, body, caption)
- [ ] Is there only ONE bold/semibold element per visual group?
- [ ] Does the hierarchy hold at arm's length? (Squint test for text)

## Text Style Usage
- [ ] All text uses `.font(.textStyle)` — no `.system(size:)`
- [ ] Custom fonts use `relativeTo:` for Dynamic Type
- [ ] `.headline` for row titles, `.body` for content, `.caption`/`.footnote` for metadata

## Dynamic Type
- [ ] Test at Default — your baseline
- [ ] Test at XXXL — common for older users
- [ ] Test at AX3 — catches layout breaks
- [ ] Critical text never truncated at large sizes
- [ ] `ViewThatFits` used where HStack breaks to VStack at large sizes

## Readability
- [ ] Body text has `.lineSpacing(3-4)` in scrollable contexts
- [ ] Line length under ~70 characters
- [ ] User-generated content has `.lineLimit()` + `.truncationMode(.tail)`
- [ ] Multiline text uses `.leading` alignment (never `.center` for paragraphs)

## Weight Distribution
- [ ] Maximum 2 font weights per screen (regular + one emphasis)
- [ ] Weight is used for hierarchy, not decoration
- [ ] `.caption2` (11pt) is rarely used — `.caption` (12pt) is the practical minimum

## Common Failures
- `.font(.body.bold())` on metadata — why is secondary info bold?
- Three different bold weights competing for attention
- `.caption2` used for important info like due dates or assignees
- Missing `.lineLimit()` on user-generated content in lists
