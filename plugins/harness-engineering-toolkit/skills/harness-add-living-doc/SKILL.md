---
name: harness-add-living-doc
description: >
  Add a new living document to every enforcement touchpoint in an existing Claude Code harness. Use when adding a doc to the harness, when the harness doesn't check a specific document, when integrating a new doc into enforcement, or when the user says "harness is missing [doc]", "add [doc] to harness", "harness doesn't check [X]", "track a new document", or "new doc to enforcement chain". Also use after creating a new living doc (PRD, spec, constraints, etc.) that needs to be wired into the existing harness. Ensures no enforcement touchpoint is missed.
---

# Harness Add Living Doc

Add a new living document to every enforcement touchpoint in an existing harness system. This skill ensures the new doc is checked at every stage: preflight reading, post-implementation sync, adversarial verification, and doc auditing.

## Prerequisites

A harness system must already exist in the project. Verify by checking for:
- `.claude/scripts/harness-*.sh`
- `.claude/commands/` with harness commands (pre-feature, sync-docs, verify, audit-docs)
- `.claude/HARNESS.md`

If no harness exists, use `harness-setup` instead.

## Step 1: Understand the doc

Ask the user (or infer from context):
1. **Path:** Where does the doc live? (e.g., `docs/prd.md`)
2. **Purpose:** What does it document? (one sentence)
3. **Update trigger:** When should this doc be updated? (e.g., "when a version ships", "when new components are added", "when architecture changes")

## Step 2: Scan enforcement touchpoints

Read ALL of these files and identify where doc families are enumerated:

| File | What to look for |
|------|-----------------|
| `CLAUDE.md` | Living docs table, step 1 read list (all workflows), step 9 sync list |
| `.claude/commands/pre-feature.md` | Read list (the docs read during preflight) |
| `.claude/commands/sync-docs.md` | Numbered check items (each doc family is a check) |
| `.claude/commands/verify.md` | Adversarial subagent prompt -- both `pre_feature_complete` check (was it read?) and `docs_synced` check (was it updated?) |
| `.claude/commands/audit-docs.md` | Scope examples list AND the "Also check if in scope" section |
| `.claude/HARNESS.md` | Command description table (what each command reads/checks) |

For each file, note exactly where the other doc families appear so the new doc can be added in the same pattern.

## Step 3: Show diff preview

Present the user with a preview of EVERY edit:

```
=== CLAUDE.md ===
Living docs table: add row for [doc]
Step 1 (both workflows): add [doc] to read list
Step 9: add [doc] to sync list with update trigger

=== .claude/commands/pre-feature.md ===
Add [doc] to read list at step N

=== .claude/commands/sync-docs.md ===
Add check N: "[purpose]. If yes, flag [doc path]."

=== .claude/commands/verify.md ===
pre_feature_complete check: add [doc] to "were these docs read?" list
docs_synced check: add [doc]-specific verification

=== .claude/commands/audit-docs.md ===
Scope examples: add "[doc name]" to the example list
Also check section: add [doc]-specific audit criteria

=== .claude/HARNESS.md ===
/pre-feature description: add [doc] to what it reads
/sync-docs description: add [doc] to what it checks
```

Wait for user approval before applying.

## Step 4: Apply changes

Edit all files. Use the exact patterns observed in step 2 -- match indentation, formatting, and style of existing doc family entries.

## Step 5: Verify completeness

Run a completeness check:

```bash
# Find all references to an existing doc family (e.g., "specs" or "behavior-specs")
grep -rn "specs" .claude/commands/ .claude/HARNESS.md CLAUDE.md --include="*.md" | grep -v node_modules

# Now check the new doc appears in the same files
grep -rn "[new-doc-name]" .claude/commands/ .claude/HARNESS.md CLAUDE.md --include="*.md"
```

Compare the two lists. If the new doc is missing from any file where other doc families appear, flag it and fix.

## Common mistakes

| Mistake | How to avoid |
|---------|-------------|
| Missing `/verify` pre_feature_complete check | The adversarial subagent has TWO places to check docs: "was it read?" (pre_feature_complete) and "was it updated?" (docs_synced). Update both. |
| Missing `/audit-docs` scope example | The scope example list in the first line is how users discover what's auditable. Add the new doc name there. |
| Inconsistent naming | Use the same short name everywhere (e.g., "PRD" not sometimes "prd" and sometimes "product roadmap") |
| Forgetting HARNESS.md | The command description table is documentation, not enforcement, but it goes stale and confuses future sessions. |
