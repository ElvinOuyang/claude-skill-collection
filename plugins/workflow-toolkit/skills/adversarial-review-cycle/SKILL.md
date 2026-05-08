---
name: adversarial-review-cycle
description: >
  Run a structured adversarial review loop before merging or shipping. Dispatch an opus-powered review subagent with explicit "try to break this" framing, classify findings P0/P1/P2/P3, fix the P0/P1s, then run a second pass from a different angle (security, correctness, UX, perf) and only mark complete when both passes return clean. Use this skill whenever the user signals they want a hardening pass before shipping -- phrases like "adversarial review", "second opinion", "try to break this", "review before merge", "double-check before PR", "before I ship", "hardening pass", "can you poke holes", "stress test this", "what would you attack", "is this actually done", "do an adversarial pass", or any time the user has just finished implementation and wants verification beyond their own gut. Trigger even when the user doesn't say "adversarial" explicitly -- the cue is "I think it's done, prove me wrong". This pattern correlates strongly with shipping clean (the v1.9.1 hotfix, video-use audit, and harness scaffold all used 2 rounds and shipped clean). Do not trigger for early-stage design review (use brainstorming) or for lightweight code review (use the standard code-review skill).
---

# Adversarial Review Cycle

Run two rounds of adversarial review on completed work to catch the things the implementer can't see. Built around a simple finding: when the user runs this loop, outcomes correlate with `fully_achieved` -- v1.9.1 hotfix, video-use audit, and harness scaffold each used two rounds and shipped clean.

## Why this skill exists

Implementers are bad at finding their own bugs. Not because they're careless -- because the assumptions that let them write the code in the first place also blind them to what's wrong with it. A reviewer with no investment in the implementation, prompted to actively hunt for failure, sees a different surface.

The pattern this skill encodes:

1. **Round 1 -- broad attack.** A fresh reviewer with explicit "break this" framing surfaces the obvious-in-retrospect problems.
2. **Triage and fix.** Classify findings; fix the high-severity ones now.
3. **Round 2 -- different angle.** A second reviewer attacks from a different axis (if Round 1 was correctness, Round 2 is security or UX or perf). The angle change is what catches the second-order issues.
4. **Ship only when both passes return clean** (or all remaining findings are accepted P2/P3 with rationale).

The user already does this informally; this skill makes it mechanical so it actually happens every time, not just when the user remembers.

## When to invoke

Invoke after the implementer believes the work is done -- tests passing, feature working, ready for PR. **Not** during active implementation; the loop's value depends on a stable target.

If the work is small (one-line fix, doc edit), one round is enough; ask the user. For anything non-trivial -- a new feature, a hotfix that touches multiple files, a refactor, a new harness or skill -- run both rounds.

## Phase 1: Set up the review

Before dispatching, gather:

1. **What changed.** `git diff <base>..HEAD`, list of files, summary of intent.
2. **What "done" means here.** The spec, PRD section, ticket, or the user's stated goal. Without this, the reviewer has no yardstick.
3. **Known risks.** Anything the implementer was nervous about during the build. Surface these to the reviewer explicitly -- they're high-yield attack surfaces.
4. **Out-of-scope.** Things the reviewer should not flag (e.g., "we know logging is sparse; that's a follow-up").

Pick the **Round 1 angle**. Default is correctness + completeness against the spec. If the work has a clear primary risk (security-sensitive, perf-sensitive, UX-sensitive), lead with that.

## Phase 2: Round 1 -- broad attack

Dispatch a subagent with `model: "opus"` (this is review work; opus is the right tool, and the parent CLAUDE.md hook expects the keyword "review" or "adversarial" in the prompt). Use a prompt structured like this:

```
You are doing an adversarial review of completed work. Your job is to try to break it -- not to validate it, not to be agreeable, not to soften findings. Be specific, be technical, be ruthless.

Context:
- Goal: <what done means>
- Changes: <diff summary or paths>
- Known risks the implementer flagged: <list>
- Out of scope: <list>
- Review angle for this pass: <correctness / security / UX / perf>

For each finding:
- Classify P0 (blocks shipping; data loss, crash, security hole, breaks core path), P1 (must fix before merge; wrong behavior in common case, missing essential test), P2 (should fix soon; awkward UX, latent edge case, missing nice-to-have test), P3 (nit; style, minor doc).
- Cite file:line for code findings.
- Explain the failure mode -- what input/state triggers it, what goes wrong, what the user sees.
- Propose a fix only if it's obvious; otherwise just describe the problem.

If you find nothing, say so explicitly and explain what you tried -- a clean review with a list of attack vectors attempted is far more credible than a clean review with no narrative.
```

Wait for the report. Resist the urge to argue with findings before triage -- read the whole thing first.

## Phase 3: Triage

Walk through findings with the user (or by yourself if you're operating autonomously and the user has delegated this):

| Severity | Action |
|----------|--------|
| P0 | Fix now. Do not proceed to Round 2 with a P0 open. |
| P1 | Fix before merge. Usually fix now. |
| P2 | Fix now if cheap, otherwise file as a follow-up TODO with rationale. |
| P3 | Fix only if trivial, else accept and move on. |

For each accepted-without-fix finding, write one line of rationale ("accepted: edge case requires X which we don't support and won't") -- this is what makes "ship clean" a real claim and not a hand-wave.

## Phase 4: Implement fixes

Apply fixes. Re-run tests. Confirm the original spec/PRD goal still holds.

If any fix is non-trivial, treat it as a mini-implementation and follow whatever quality bar the project uses (TDD, type checks, etc.). Don't degrade quality to clear the review faster.

## Phase 5: Round 2 -- different angle

Dispatch a **second** subagent (also `model: "opus"`), with an explicitly different review angle from Round 1. The angle change is the whole point -- repeating the Round 1 angle is mostly wasted because the obvious issues there have been fixed.

Angle rotation guide:

- Round 1 was **correctness** → Round 2 is **security** (input validation, auth, secrets, injection, race) or **UX** (error messaging, edge-case behavior, accessibility) or **perf** (hot path, allocations, N+1, scaling)
- Round 1 was **security** → Round 2 is **correctness** or **resilience** (failure modes, partial failure, retry/idempotency)
- Round 1 was **UX** → Round 2 is **correctness** or **accessibility** (keyboard nav, screen reader, contrast, focus)
- Round 1 was **perf** → Round 2 is **correctness** under load or **observability**

The Round 2 prompt is the same shape as Round 1 but with the new angle named, plus this addition:

```
A prior adversarial pass already covered <Round 1 angle> and the findings were <list / fixed / accepted>. Do not re-litigate those; assume they're handled. Your angle is <Round 2 angle>. Find what the prior pass would not have noticed.
```

Triage Round 2 findings the same way. Fix P0/P1.

## Phase 6: Ship-or-spin decision

After Round 2:

- **Both rounds clean (or only accepted P2/P3 left):** ship. Open the PR; reference the review log if you kept one.
- **Round 2 surfaced new P0/P1:** fix and run a third round on the affected angle. The second-order issues that show up after a fix are a known failure mode -- don't skip the third pass if it's warranted.
- **Reviewer keeps coming back with the same flavor of finding:** the implementation may have a structural problem the reviewer is circling. Step back and consider whether the design needs revisiting rather than another patch.

## Optional: review log artifact

If the project tracks review history, write a short log entry:

```markdown
## Adversarial review -- <feature/PR>
**Date:** <date>
**Rounds:** 2 (correctness, then security)

### Round 1 (correctness)
- P0: <finding> -- fixed in <commit>
- P1: <finding> -- fixed in <commit>
- P2: <finding> -- accepted, follow-up filed as <link>

### Round 2 (security)
- P1: <finding> -- fixed in <commit>
- (no P0)

**Outcome:** clean, shipped.
```

File location is project-dependent -- common spots are `docs/reviews/`, the PR description itself, or a section in `CHANGELOG.md`. Skip if the project has no convention.

## Conservative defaults

- **Two rounds is the floor for non-trivial work**, not the ceiling. Three rounds is fine. One round is fine for tiny changes.
- **Use `model: "opus"`** for review subagents. Reviewing is reasoning-heavy and the hook in the user's CLAUDE.md expects opus + a review keyword in the dispatch.
- **Different angle every round.** Repeating the same angle wastes a round.
- **Do not let the implementer be the reviewer.** Even if "the implementer" is Claude in the same session, dispatch a fresh subagent so the review has a real cold-start perspective.
- **Do not soften findings to make the implementer feel better.** A pleasing review is a useless review.
- **Do not ship with open P0/P1.** Either fix them or downgrade them with explicit rationale (rare; defaults to fix).

## When to escalate to the user

- Reviewer disagrees with the spec ("the goal as stated is wrong"). The user owns the goal; surface the disagreement.
- Round 2 keeps finding P0s. Something is structurally off; the user needs to weigh "patch and ship" vs "redesign".
- Reviewer flags something outside the agreed scope as P0. Scope creep mid-review needs the user's call.

## Related skills

- `superpowers:requesting-code-review` -- lighter-weight verification before merge; use that for routine work
- `superpowers:verification-before-completion` -- evidence-before-claims discipline; complementary to this skill
- `superpowers:receiving-code-review` -- once findings come back, this skill governs how to triage them
- `code-review:code-review` -- standard PR-level review; not adversarial, useful as a final pass after this loop
