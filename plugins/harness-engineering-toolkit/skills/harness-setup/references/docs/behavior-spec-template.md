# {{FEATURE_NAME}} -- Behavior Spec

Regression checklist for {{FEATURE_NAME}}. Each requirement has a unique ID prefix for traceability.

**Prefix:** `{{XX}}-` (e.g., `{{XX}}-001`)
**Total requirements:** {{COUNT}}

---

## {{BEHAVIOR_GROUP_1}}

- [ ] `{{XX}}-001` {{TESTABLE_REQUIREMENT}}
- [ ] `{{XX}}-002` {{TESTABLE_REQUIREMENT}}
- [ ] `{{XX}}-003` {{TESTABLE_REQUIREMENT}}

## {{BEHAVIOR_GROUP_2}}

- [ ] `{{XX}}-010` {{TESTABLE_REQUIREMENT}}
- [ ] `{{XX}}-011` {{TESTABLE_REQUIREMENT}}

## Edge Cases

- [ ] `{{XX}}-050` {{EDGE_CASE_REQUIREMENT}}

---

## Conventions

- IDs are stable. Never renumber existing IDs when adding new ones.
- Each requirement must be independently verifiable (one assertion per line).
- Use gaps in numbering (001, 002, 010, 011) to leave room for insertions within groups.
- Group by user-facing behavior, not by implementation detail.
- When a requirement is removed, mark it `REMOVED` instead of deleting the line.
