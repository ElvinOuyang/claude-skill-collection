Pre-completion adversarial verification. This is the only gate that sets verified=true.

1. Read `.harness-state.json` and note which phases are marked true vs false.

2. Dispatch a fresh-context subagent (use Agent tool with a NEW agent, not the current session) with this prompt:

   "You are an adversarial reviewer verifying that an implementation followed the project's mandatory workflow. You have NO context from the implementation session -- verify everything independently.

   Read these files:
   - CLAUDE.md (the mandatory workflow -- this is the source of truth)
   - .harness-state.json (what the implementer claims is done)
   <!-- {{LIVING_DOCS_READ_LIST}}: also read any project-specific code rule files, e.g.:
   - platform-specific CLAUDE.md files (ios-native/CLAUDE.md, etc.)
   -->

   Run these commands:
   - git diff --name-only $(git merge-base HEAD {{TRUNK}})..HEAD (what files changed)
   - git diff --diff-filter=A --name-only $(git merge-base HEAD {{TRUNK}})..HEAD (new files only)
   - git log --oneline $(git merge-base HEAD {{TRUNK}})..HEAD (commit history)

   For each phase marked true in .harness-state.json, verify the claim:
   - pre_feature_complete: were living docs read? (check commit evidence or spec references in commit messages)
   - graphify_queried: best-effort -- check if graphify-out/ exists
   - plan_created: does a plan file exist for this feature?
   - plan_reviewed: is there evidence of review iterations (fix commits after plan)?
   - execution_skill_active: were implementation commits made following a plan?
   - per_task_reviews_done: is there evidence of review between task commits (fix commits, review-driven changes)?
   - smoke_tested: were smoke tests run (screenshots, test output, verification logs)?
   - spec_written: does a spec file exist for this feature?
   - docs_synced: do changed source files have corresponding updates in living docs?

   For each phase marked false, flag it as incomplete.

   Also check mechanically (these cannot be faked):
   - New source files have corresponding test files
   - Living docs mention new files from the diff
   - No violations of project-specific code rules in new files

   Report: PASS (all required phases verified for the inferred scope) or FAIL (list specific failures with file:line evidence).
   Do NOT be lenient. If you cannot verify a claim, mark it FAIL.
   Infer scope the same way the stop hook does: new source files = feature, modified only = patch, docs only = design."

3. If the subagent reports PASS:
   - Set `verified` to true in `.harness-state.json`
   - Report: "Verification passed. Ready for PR."

4. If the subagent reports FAIL:
   - Do NOT set `verified` to true
   - Show the failures
   - Say: "Consult CLAUDE.md Mandatory Workflow to address these gaps. Run /verify again after fixing."

5. After PR is created (gh pr create), remove `.harness-state.json` to clean up the session.
