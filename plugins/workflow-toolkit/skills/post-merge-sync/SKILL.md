---
name: post-merge-sync
description: >
  Mechanical post-merge sync ritual: detect the just-merged branch, fast-forward master, delete the merged branch, restore stashed work, and produce a punch list of follow-ups implied by the merge (living docs, rebasable PRs, lingering TODOs). Use this skill whenever the user signals a PR was just merged and they need to clean up and figure out what's next -- phrases like "I just merged the PR", "I just merged the OA signed PR into master", "we are now back in game", "anything else left on this branch", "this repo doesn't seem to have the proper git branch", "sync to master", "fast-forward master", "post-merge cleanup", "clean up after merge", "branch hygiene", or any time the user is on a feature branch whose PR has landed and they need to get back to a clean trunk and a clear next-step list. Trigger even when the user doesn't explicitly say "sync" -- the cue is "I merged X, now what?". Do not trigger for pre-merge work (use review/PR skills) or for merging itself (use git tooling).
---

# Post-Merge Sync

Run the mechanical ritual that follows a PR landing on master, so the user gets back to a clean trunk and a clear "what's left" punch list without doing it by hand for the fourth time this month.

## Why this skill exists

The user merges roughly 4+ PRs per month and every time repeats the same chore: figure out what branch they're on, fetch, fast-forward, delete the local branch, recover stashed work, then re-orient -- "anything else left on this branch?" The ritual is simple but easy to miss steps (forgotten stashes, undeleted branches, open PRs that are now rebasable, living docs that haven't been updated to reflect the merge). The cost of skipping a step is silent drift: stale branches, stash entries that pile up, follow-up TODOs forgotten until they bite weeks later.

The job here is mechanical hygiene plus a short act of synthesis: read what just landed and tell the user what it implies for the rest of the repo.

## Phase 1: Diagnose where the user is

Before changing anything, figure out the current state. Run in parallel:

```bash
git status
git branch --show-current
git log --oneline -10
git stash list
gh pr list --state open --limit 20
gh pr list --state merged --limit 5 --json number,title,headRefName,mergedAt
```

From this, identify:

- **Current branch** -- are they on the merged branch, on master, or somewhere else?
- **Which PR was just merged** -- match against the user's wording ("the OA signed PR", "the harness PR"); confirm with the user if ambiguous
- **Local working state** -- uncommitted changes, untracked files, stashes
- **Other open PRs** -- candidates for rebase against the new master

If the user said "this repo doesn't seem to have the proper git branch" or similar, they're probably on a detached HEAD or on master with uncommitted leftovers. Don't assume; check.

## Phase 2: Sync master

Standard sequence -- adapt to the repo's trunk name (`main` vs `master`):

1. **Stash uncommitted work** if any, with a descriptive message: `git stash push -m "post-merge-sync: pre-fetch state on <branch>"`
2. **Switch to trunk**: `git checkout master` (or `main`)
3. **Fetch and fast-forward**: `git fetch origin && git merge --ff-only origin/master`
   - If fast-forward fails, stop and surface the divergence to the user. Do not force-update.
4. **Delete the merged branch**: `git branch -d <merged-branch>`
   - Use `-d` (safe) not `-D`. If git refuses because the branch isn't merged into the current head, verify the PR really did merge (squash/rebase merges leave the local branch "unmerged" by content; check the PR state with `gh pr view`). Only use `-D` after confirming the PR is merged on the remote.
5. **Prune remote-tracking refs**: `git fetch --prune`
6. **Restore the stash** if you created one: `git stash pop` (warn about conflicts if any).

Report each step's outcome inline so the user can see what happened.

## Phase 3: Scan for follow-ups (the punch list)

This is the synthesis step that distinguishes the skill from a plain shell alias. After the merge is clean, look for things the merge implies need doing.

Read the merged PR's diff and title (`gh pr view <number> --json title,body,files`). Then check these sources for follow-ups:

### Living docs

Scan the project's living documentation for stale references. Common locations:

- `CLAUDE.md` -- agent instructions; check for outdated workflow references
- `README.md` -- setup/usage; check if the merged change altered commands or paths
- `docs/` -- product/spec/PRD docs; check for "Planned" items that just shipped
- `.harness-state.json` or similar harness state -- if the project uses a harness, check if phases need to advance

For each living doc, ask: does the merged change make any sentence in this doc wrong, and does any "next" item in this doc now move to "done"?

### Rebasable open PRs

For each open PR returned by `gh pr list`:

- If its base is master and it was branched before the merge, it may now have conflicts or simply be stale -- flag it as a rebase candidate
- If its description references the just-merged work as a dependency, flag it as unblocked

### TODOs and follow-up commits

```bash
git log --grep="TODO\|FIXME\|follow-up\|followup" master..HEAD~1
git diff <merge-base>..master -- '*.md' | grep -i "follow"
```

Look in the merged PR description and commit messages for "follow-up:" markers the user wrote during review.

### Tests and CI signals

If the merged PR added or changed tests, note whether the user should run them locally to confirm a green baseline before branching for the next feature.

## Phase 4: Output the punch list

Produce a short markdown summary the user can scan in 10 seconds. Use this template:

```markdown
## Post-merge sync complete

**Merged:** #<num> <title>
**Master:** fast-forwarded to <sha> (<n> commits)
**Branch deleted:** <name>
**Stash:** <restored / none / conflicted>

## What's left

### Living docs to update
- [ ] <file>:<line> -- <why>

### Rebasable PRs
- [ ] #<num> <title> -- branched before merge, likely needs rebase

### Follow-ups mentioned in the PR
- [ ] <text from PR body / commit message>

### Suggested next action
<one sentence: "Start the X branch", "Rebase #Y first", "Update CLAUDE.md before anything else", etc.>
```

If a section is empty, omit it -- don't pad.

## Conservative defaults

- **Never force-push, force-delete, or rewrite history** as part of this ritual. If the safe path fails, surface the problem and stop.
- **Confirm before deleting** if `git branch -d` requires `-D`. Show the user the PR state and ask.
- **Do not auto-rebase open PRs.** Flag them; let the user choose order.
- **Do not auto-edit living docs** unless the user explicitly asks. The punch list is the deliverable; edits are a separate request.

## When to escalate to the user

Stop and ask if any of these happen:

- Fast-forward fails (master and origin/master diverged)
- Stash pop produces conflicts
- The "merged" branch can't be confirmed merged on the remote
- The repo uses an unusual trunk name or workflow (release branches, GitFlow) -- ask before applying the standard recipe

## Edge cases worth handling

- **Squash or rebase merges**: the local branch's commits don't match master's history. Use `gh pr view <num> --json state,mergedAt` to confirm merge, then `git branch -D` is safe.
- **No GitHub remote / no `gh`**: skip the PR scan; do the local git hygiene only and tell the user the punch list will be local-only.
- **Worktrees**: if the merged branch is checked out in another worktree, deleting it will fail. List worktrees with `git worktree list` and offer to remove the stale one.
- **User wasn't on the merged branch**: still useful -- run the sync, report what was cleaned, skip the "you were on X" framing.
