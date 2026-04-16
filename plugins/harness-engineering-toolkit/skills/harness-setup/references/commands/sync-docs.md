Post-implementation doc sync. Operationalizes CLAUDE.md step 9 -- use only after implementation and verification are complete.

Run `git diff --name-only $(git merge-base HEAD {{TRUNK}})..HEAD` to find all files changed on this branch.

Ignore tests, lockfiles, generated files, and doc files. Focus on changed production code.

For each changed file that can affect behavior:

<!-- {{LIVING_DOCS_SYNC_LIST}}: list the project's living docs and what to check for each, e.g.:
1. **Specs**: Does the change affect behavior documented in docs/specs/? If yes, list the spec file and what needs updating.
2. **Behavior specs**: Does the change affect regression requirements? If yes, list the file and affected items.
3. **Component registry**: Were new components, hooks, services, or utilities added? If yes, they need entries in the registry.
4. **Constraints**: Did you encounter a platform gotcha or non-obvious limitation? If yes, add to constraints doc.
5. **System design**: Did the architecture change (new services, changed data flow, new API routes)? If yes, flag the architecture doc.
6. **Design wireframes**: If wireframe docs exist for the shipped feature, flag them for removal.
7. **PRD/Roadmap**: Does this change ship a version, phase, or fix a known bug? If yes, flag which section needs updating.
-->

Show me the full list of proposed doc updates with diffs before making any changes. Wait for my approval, then apply them.
