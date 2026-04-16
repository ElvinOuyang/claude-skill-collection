# Harness Engineering Toolkit -- Implementation Plan

**Date:** 2026-04-15
**Spec:** [Design Spec](2026-04-15-harness-engineering-toolkit-design.md)
**Codex review:** Addressed P1 (command templates, parameterization, phase marking), P2 (graphify optional, patch scope canonical, extend checklist)

## Directory Structure

```
plugins/harness-engineering-toolkit/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    ├── harness-setup/
    │   ├── SKILL.md
    │   └── references/
    │       ├── scripts/
    │       │   ├── harness-init.sh
    │       │   ├── harness-debt.sh
    │       │   ├── harness-pr-check.sh
    │       │   ├── harness-commit-check.sh
    │       │   ├── harness-branch-check.sh
    │       │   └── harness-stop-gate.sh
    │       ├── commands/
    │       │   ├── pre-feature.md
    │       │   ├── evaluate-scope.md
    │       │   ├── test-gate.md
    │       │   ├── smoke-test.md
    │       │   ├── sync-docs.md
    │       │   ├── verify.md
    │       │   └── audit-docs.md
    │       ├── settings-hooks.json
    │       ├── harness-doc.md
    │       └── docs/
    │           ├── prd-template.md
    │           ├── system-design-template.md
    │           ├── component-registry-template.md
    │           ├── constraints-template.md
    │           ├── spec-template.md
    │           └── behavior-spec-template.md
    ├── harness-add-living-doc/
    │   └── SKILL.md
    ├── harness-extend/
    │   └── SKILL.md
    └── harness-troubleshoot/
        └── SKILL.md
```

## Build Sequence

### Phase 1: Reference templates

Create generalized reference templates from hive-mind's proven patterns. Parameterize with `{{trunk_branch}}`, `{{source_extensions}}`, `{{living_docs}}`, `{{test_command}}`, `{{smoke_test_setup}}`.

1. **Scripts (6 files):** Generalize all harness scripts. Replace `master` with `{{trunk_branch}}`, hardcoded extensions with `{{source_extensions}}`. Keep stop gate loop detection pattern exactly as-is.

2. **Command templates (7 files):** Generalize all command .md files. Replace hardcoded doc paths with `{{living_docs}}` placeholders. Replace iOS/Pumpkin-specific test/build logic with `{{test_command}}` and `{{smoke_test_setup}}`. Keep superpowers skill references.

3. **Settings hook template:** Extract hook wiring into standalone JSON template. Include optional graphify Glob|Grep hook (conditional on `graphify-out/` existence).

4. **HARNESS.md template:** Generalize architecture docs with parameter placeholders.

5. **Living doc templates (6 files):** Skeleton templates with structure and section headers. Each has placeholder content the skill fills by reading the codebase.

### Phase 2: Core skills (4 SKILL.md files)

6. **harness-setup SKILL.md** -- The main bootstrapper.
   - Interview: 3 questions (living docs, trunk branch, smoke test setup)
   - Phase 1: Scan for existing docs, draft missing from templates, get approval
   - Phase 2: Generate scripts (substitute parameters), wire hooks (merge into existing settings.json), create commands (wired to actual doc list), write HARNESS.md, update CLAUDE.md
   - Graphify: include Glob|Grep hook + graphify_queried phase if graphify-out/ exists; omit if not

7. **harness-add-living-doc SKILL.md** -- Enforcement chain updater.
   - Exhaustive touchpoint checklist (CLAUDE.md, pre-feature, sync-docs, verify, audit-docs, HARNESS.md)
   - Diff preview, apply on approval, grep-based completeness verification

8. **harness-extend SKILL.md** -- Infrastructure extender.
   - Four operations with full update checklists:
     - Add phase: init.sh, stop-gate.sh, verify.md, evaluate-scope.md, HARNESS.md, marking command
     - Add scope: stop-gate REQUIRED dict, inference logic, evaluate-scope, scope-aware commands, HARNESS.md
     - Add hook: script from pattern template, settings.json wiring, HARNESS.md
     - Add command: .md from pattern template, HARNESS.md command table
   - Stop hook loop detection pattern provided verbatim

9. **harness-troubleshoot SKILL.md** -- Diagnostic tool.
   - Decision tree: 5 problems (loop, scope mismatch, stale state, phase stuck, hook silent)
   - Each: symptom, diagnosis commands, fix
   - Loop detection pattern as copyable reference

### Phase 3: Plugin registration

10. **plugin.json** -- `{ name, version: "1.0.0", description, author, skills: "./skills/" }`

11. **README.md update** -- Add harness-engineering-toolkit table to repo root README with 4-skill listing.

### Phase 4: Review, verify, push

12. **Codex review** -- Send all 4 SKILL.md files to Codex rescue for implementation review. Fix issues.

13. **Skill-creator verify** -- Use skill-creator skill to verify trigger descriptions fire correctly and optimize.

14. **Commit and push** -- Single commit with all plugin files.

## Canonical decisions (from Codex review)

- **Patch scope:** `test_gate_passed`, `smoke_tested`, `docs_synced`, `verified` (canonical, matches stop gate)
- **Graphify:** Optional. Include when `graphify-out/` detected, silently skip otherwise. `graphify_queried` phase included in state file but only enforced when graphify is present.
- **Transient doc families** (design wireframes, etc.): Supported as optional entries in `/sync-docs` cleanup step. Not a core living doc.
- **superpowers phase marking:** Commands verify evidence (plan files, review commits) rather than trusting phase booleans. CLAUDE.md workflow instructions tell Claude to update state file after each step.
