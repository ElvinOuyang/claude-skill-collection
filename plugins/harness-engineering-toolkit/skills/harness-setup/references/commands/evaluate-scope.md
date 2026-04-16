Evaluate whether the stop gate's inferred scope matches this session's intent.

1. Read `.harness-state.json` -- note the current scope (or lack of scope_override) and which phases are incomplete.

2. Check the git state:
   - `git diff --name-only $(git merge-base HEAD {{TRUNK}})..HEAD` -- what changed on the branch
   - `git diff --name-only HEAD` -- any uncommitted changes in this session

3. Review the conversation context. Determine which category fits:
   - **Bug fix / refactor / small change**: Set `scope_override` to `patch` (requires only `docs_synced` + `verified`)
   - **Design discussion**: Set `scope_override` to `design` (requires `pre_feature_complete`, `graphify_queried`, `spec_written`, `docs_synced`, `verified`)
   - **New feature implementation**: Scope is correct at `feature`. Begin CLAUDE.md Mandatory Workflow from step 1 (`/pre-feature`)
   - **Exploration / chat with no implementation intent**: Set `scope_override` to `patch` and mark `docs_synced` and `verified` as true (no enforcement needed)

4. Apply the decision:
   ```python
   import json
   s = json.load(open(".harness-state.json"))
   s["scope_override"] = "patch"  # or "design", or leave as-is for feature
   # For exploration: also set phases
   # s["phases"]["docs_synced"] = True
   # s["phases"]["verified"] = True
   json.dump(s, open(".harness-state.json", "w"), indent=2)
   ```

5. Report what you set and why in one sentence.
