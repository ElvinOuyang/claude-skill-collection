Preflight helper for CLAUDE.md workflow steps 1-3. After this summary, continue the mandatory workflow.

If "$ARGUMENTS" is provided:
1. Resolve it to canonical doc files using the project's spec index and behavior-spec index
2. If more than 3 candidate files match, show them and ask me to choose
3. Read the matched living docs:
   <!-- {{LIVING_DOCS_READ_LIST}}: list the project's living doc paths here, e.g.:
   - docs/prd.md (roadmap / version status)
   - docs/specs/$FEATURE.md (feature spec)
   - docs/behavior-specs/$FEATURE.md (regression requirements)
   - docs/constraints.md (platform gotchas)
   - docs/component-registry.md (reusable components)
   - docs/system-design.md (architecture)
   -->
4. Run `graphify query "$ARGUMENTS"` to map affected components

If "$ARGUMENTS" is empty:
1. Read the project's living docs (full list above) for general landscape context
2. Briefly summarize the project landscape

Summarize:
- Current documented behaviors for the feature (if scoped)
- Applicable constraints and known gotchas
- Key components and services involved
- Behavior-spec regression requirements (using the file's ID prefix if applicable)

After completing the summary, update `.harness-state.json` (create it if absent):
- Set `pre_feature_complete` to true
- Set `graphify_queried` to true (if graphify query was run in the scoped path)

Then ask me what I want to build or change.
