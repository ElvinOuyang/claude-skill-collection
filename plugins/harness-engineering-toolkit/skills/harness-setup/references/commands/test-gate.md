Code quality gate. Dispatches a fresh-context subagent to verify tests and code rules.

1. Dispatch a fresh-context subagent (use Agent tool with a NEW agent) with this prompt:

   "You are a code quality reviewer. Check the current branch for compliance with the project's code rules.

   Run these checks and report results:

   <!-- {{TEST_COMMAND}}: replace with project-specific build and test commands, e.g.:
   a. Build:
      npm run build 2>&1 | tail -10
      Report: PASS if build succeeded, FAIL otherwise.

   b. Unit tests:
      npm run test:run 2>&1 | tail -20
      Report: PASS/FAIL for test results.

   c. Lint / type-check:
      npm run lint 2>&1 | tail -10
      npx tsc --noEmit 2>&1 | tail -10
      Report: PASS/FAIL for each.
   -->

   d. New-file spot-check:
      For each new file on this branch (git diff --diff-filter=A --name-only $(git merge-base HEAD {{TRUNK}})..HEAD):
      - Check compliance with project-specific code rules from CLAUDE.md
      - Flag any violations

   e. Test coverage:
      For each new source file (not test files), check if a corresponding test file exists.

   Report: PASS (all checks green) or FAIL (list specific violations with file:line)."

2. If the subagent reports PASS:
   - Read `.harness-state.json` to determine the current scope
   - If scope_override is `patch`: set `test_gate_passed` to true
   - If scope is `feature` (no override or scope_override is `feature`): set `per_task_reviews_done` to true
   - If no `.harness-state.json` exists: set `per_task_reviews_done` to true (default to feature behavior)
   - Report results to user.

3. If the subagent reports FAIL:
   - Do NOT update the state file
   - Show the failures
   - Say: "Fix the issues above, then run /test-gate again."
