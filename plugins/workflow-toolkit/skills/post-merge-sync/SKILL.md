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

## Phase 2: Sync trunk safely

Detect the trunk name first -- don't assume `master`. Check `git symbolic-ref refs/remotes/origin/HEAD` or `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. The rest of this section uses `<trunk>` as a placeholder; substitute the real name (`main`, `master`, `trunk`, etc.) for every command.

The order below is deliberate. Several steps look interchangeable but aren't -- swapping them is exactly how you silently corrupt history or lose work. Read the "why" notes before reordering.

### 2.1 Capture the starting branch

Record the current branch name in a variable. You'll need it for the stash-restore decision and the punch list:

```bash
START_BRANCH=$(git branch --show-current)
```

If `START_BRANCH` is empty, the user is on detached HEAD. Stop and ask before touching anything.

### 2.2 Stash uncommitted work, but only if you'll restore it on the same branch

If `git status --porcelain` is empty, skip this step entirely.

Otherwise, stash with a descriptive, branch-tagged message so the stash is identifiable later:

```bash
git stash push -u -m "post-merge-sync: WIP on ${START_BRANCH} @ $(date -u +%Y-%m-%dT%H:%MZ)"
```

**Critical safety rule:** Never `git stash pop` onto a branch other than the one the stash came from. The original draft of this skill switched to trunk and popped there, which silently mixed unrelated WIP into trunk's working tree -- the kind of bug that gets committed as "minor cleanup" weeks later. The stash message and the `STASH_ORIGIN_BRANCH=${START_BRANCH}` variable are how you avoid this.

### 2.3 Switch to trunk and fast-forward

```bash
git checkout <trunk>
git fetch origin --prune
git merge --ff-only origin/<trunk>
```

If `--ff-only` fails, trunk and `origin/<trunk>` have diverged. Stop. Do not `git pull`, do not `git reset --hard`. Surface the divergence to the user and ask how to proceed -- this is almost always a sign of an unintended commit on local trunk that needs investigation, not automation.

### 2.4 Identify the merge commit and parent (for accurate scans later)

After fast-forwarding, find the exact commit that landed the PR. Prefer the GitHub API for accuracy:

```bash
MERGE_SHA=$(gh pr view <num> --json mergeCommit -q .mergeCommit.oid)
MERGE_PARENT="${MERGE_SHA}^"
```

If `gh` is unavailable, fall back to `git log origin/<trunk> --oneline -20` and confirm the SHA with the user. Save both values; Phase 3's scans use them as the unambiguous range `${MERGE_PARENT}..${MERGE_SHA}`.

### 2.5 Decide whether the local feature branch is safe to delete

This is the second place the original skill was unsafe. `git branch -d` only protects you when the branch's tip is reachable from the current HEAD by ordinary merge. **Squash-merge and rebase-merge produce a different commit on trunk than the branch tip**, so `-d` will refuse and the temptation is to reach for `-D`. That's how local-only commits (review fixups you never pushed, debug prints you forgot to drop) get destroyed.

Check for unmerged commits explicitly before any deletion:

```bash
UNMERGED=$(git log origin/<trunk>..${START_BRANCH} --oneline)
```

Decision tree:

- **`UNMERGED` is empty** -> the branch tip is already reachable from trunk. Run `git branch -d ${START_BRANCH}`. Safe.
- **`UNMERGED` is non-empty AND the PR was squash- or rebase-merged** (`gh pr view <num> --json mergeCommit,state` confirms merge; the listed commits are the pre-squash originals) -> show the user the unmerged commits and ask explicitly: "These commits exist only on your local branch. They were folded into the squash-merge as <MERGE_SHA>, so the *content* is on trunk but the *commit objects* will be unreachable after deletion. OK to `git branch -D`?" Wait for opt-in.
- **`UNMERGED` is non-empty AND the PR was a true merge commit** -> something is off (the branch has commits past the merge point). Stop and surface; do not delete.

Never run `git branch -D` without either confirming `UNMERGED` is empty or getting explicit user opt-in for the squash-merge case.

### 2.6 Restore the stash on the original branch, not trunk

If you created a stash in 2.2, you have two safe options. Pick based on what the user wants next:

- **They want to keep working on the feature branch's WIP** (rare after a merge -- usually the branch is being deleted). Don't delete the branch in 2.5. Switch back: `git checkout ${START_BRANCH} && git stash pop`. Only then return to trunk if needed.
- **They want a clean trunk and the WIP is for a *new* branch** (common). Create the new branch from the freshly-synced trunk first, then pop there: `git checkout -b <new-branch> && git stash pop`. Confirm the target branch name with the user.
- **Ambiguous** -> leave the stash in place, tell the user the stash ref (`stash@{0}`) and its message, and let them choose. A lingering named stash is far cheaper than silently mixed working trees.

Never `git stash pop` while HEAD is on trunk unless the stash *originated* on trunk. The stash message from 2.2 makes this auditable.

Report each step's outcome inline so the user can see what happened, including which branch the stash (if any) ended up on.

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

Use the unambiguous range you captured in 2.4 -- `${MERGE_PARENT}..${MERGE_SHA}` -- so the scan reflects exactly what landed, regardless of whether the merge was a true merge, squash, or rebase. Avoid `master..HEAD~1` and similar guesses; those silently break for squash-merges and on freshly fast-forwarded trunks.

```bash
git log --grep="TODO\|FIXME\|follow-up\|followup" "${MERGE_PARENT}..${MERGE_SHA}"
git diff "${MERGE_PARENT}..${MERGE_SHA}" -- '*.md' | grep -i "follow"
```

Also read the merged PR description and commit messages for "follow-up:" markers the user wrote during review:

```bash
gh pr view <num> --json body,commits -q '.body, .commits[].messageBody' | grep -i "follow-up\|todo\|fixme"
```

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

- **Squash or rebase merges**: the local branch's commits don't match trunk's history by SHA, even though the *content* is identical. `git branch -d` will refuse. Do **not** reflexively reach for `-D` -- first run `git log origin/<trunk>..<branch>` to enumerate the local-only commits and show them to the user. Those commits become unreachable after `-D`; if any of them contain work the squash didn't include (review fixups never pushed, debug commits, partial saves), they're gone with no easy recovery beyond reflog spelunking. Require explicit user opt-in before `-D`.
- **No GitHub remote / no `gh`**: skip the PR scan and the `mergeCommit` lookup; do the local git hygiene only and tell the user the punch list will be local-only. For the merge range, fall back to asking the user to confirm the merge SHA from `git log origin/<trunk>` rather than guessing with `HEAD~1`.
- **Worktrees**: if the merged branch is checked out in another worktree, deleting it will fail. List worktrees with `git worktree list` and offer to remove the stale one.
- **User wasn't on the merged branch**: still useful -- run the sync, report what was cleaned, skip the "you were on X" framing. The stash safety rules in 2.2/2.6 still apply: the stash, if any, came from whatever branch they were actually on, and that's where it must go back.
- **Stash conflict on restore**: `git stash pop` reports a conflict. Stop. Do not run `git stash drop`. Tell the user the stash ref is preserved (`git stash list` will show it) and let them resolve interactively.
