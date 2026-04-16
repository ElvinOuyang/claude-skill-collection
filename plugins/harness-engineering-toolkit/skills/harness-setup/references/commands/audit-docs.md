Audit living docs against source code. Do NOT edit anything.

Scope: If "$ARGUMENTS" is provided, audit only that feature area or doc family. If "$ARGUMENTS" is empty and the audit would touch more than 5 doc files, ask me to narrow scope first.

Skip README.md index files unless I explicitly ask for doc-index auditing.

<!-- {{LIVING_DOCS_SYNC_LIST}}: for each living doc family in the project, define the audit checks.
Example audit checks per doc type:

For each spec file in scope:
- Read the spec
- Resolve primary source files using the spec index, component registry, and graphify query results
- List behaviors documented in the spec that do not exist in code (stale docs)
- List behaviors in code that are not documented in any spec (missing docs)

For each behavior-spec file in scope:
- Read the behavior spec
- Resolve source files from the behavior-spec index
- List regression requirements that reference views, actions, or flows that no longer exist
- List implemented behaviors that lack a regression requirement

Also check if in scope:
- PRD/Roadmap: versions/phases marked "Shipped" that don't match code state, shipped work not reflected, known bugs that have been fixed but not updated
- Component registry: components/hooks/services in code but missing from registry, and registry entries referencing deleted code
- System design: architecture descriptions that contradict the current codebase
- Constraints: stale or missing platform gotchas
-->

Report format per file:
  [file path]
  - Stale (documented but missing): ...
  - Undocumented (in code but not in docs): ...
  - Notes: ...
