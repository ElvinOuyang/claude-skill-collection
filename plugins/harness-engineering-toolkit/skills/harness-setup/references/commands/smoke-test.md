End-to-end smoke test against behavior specs. Operationalizes CLAUDE.md step 8.

## Scope detection

Read `.harness-state.json`. If `scope_override` is `patch`, use **patch mode** (steps P1-P4 below).
Otherwise, use **feature mode** (steps F1-F6 below).

---

## Patch mode (scoped to affected behaviors)

P1. Identify affected files:
    ```
    git diff --name-only $(git merge-base HEAD {{TRUNK}})..HEAD
    ```
    From the changed filenames, infer which feature area is affected.

P2. Find the matching behavior spec by feature keyword.
    If no match, list available specs and ask which to test.
    Read the spec and identify which behavior IDs are relevant to the changed files.
    Present the subset to the user: "Based on the diff, these behaviors are affected: [list]. Confirm or adjust."

P3. For each confirmed behavior ID:
    <!-- {{SMOKE_TEST_SETUP}}: replace with project-specific smoke test instructions, e.g.:
    - For web apps: launch dev server, use Playwright MCP or browser to verify
    - For iOS apps: build on simulator, use AXe CLI for accessibility-based verification
    - For CLI tools: run the command with test inputs and verify output
    - For APIs: send requests and verify responses
    -->
    Report PASS/FAIL per behavior ID

P4. If all confirmed behaviors pass, set `smoke_tested` to true in `.harness-state.json`.
    If any fail, do NOT update. Show failures and say: "Fix the issues, then run /smoke-test again."

---

## Feature mode (full spec walkthrough)

If "$ARGUMENTS" is provided, use it as the feature name to find the behavior spec.
If empty, infer from the branch name or ask.

F1. Find the behavior spec for the feature (or closest match via glob).
    If no match, list available behavior specs and ask which to test.

F2. Read the behavior spec. Identify all testable items.
    List them and note which require manual verification (skip those in automation).

F3. Set up the test environment:
    <!-- {{SMOKE_TEST_SETUP}}: same placeholder as above -->

F4. Verify each testable behavior:
    - Take evidence (screenshots, output logs) before and after each action
    - Report PASS/FAIL for each behavior spec ID

F5. Summarize results:
    - Which items passed
    - Which items failed (with evidence)
    - Which items require manual verification (skipped)

F6. If all testable items passed, set `smoke_tested` to true in `.harness-state.json`.
    If any failed, do NOT update the state file. Show failures and say: "Fix the issues, then run /smoke-test $ARGUMENTS again."
