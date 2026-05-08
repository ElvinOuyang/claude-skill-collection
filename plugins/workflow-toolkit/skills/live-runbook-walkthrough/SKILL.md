---
name: live-runbook-walkthrough
description: >
  Hold the user's hand through external, multi-step, real-world processes governed by a project runbook with legal, financial, or regulatory consequences -- IRS EIN application, LLC operating agreement signing, business bank account opening, beneficial-ownership (BOI) filing, Wave/QuickBooks bookkeeping setup against tax rules, App Store Connect first-time TestFlight provisioning, and similar processes that touch external services and produce artifacts the project must keep on file. Load the project's runbook from docs/, narrate field-by-field, classify and gate sensitive artifacts before staging, update living docs as steps complete, and open a PR for the resulting record updates. Use this skill when the user is about to execute an irreversible external workflow that has a checked-in runbook (or needs one drafted) -- phrases like "walk me through the EIN application", "ready to sign the operating agreement", "let's open the business bank account", "first TestFlight setup with App Store Connect", "log the IRS confirmation", "BOI filing walkthrough", or any "I'm about to file/sign/wire X with <external service>, walk me through it". The user fills the external form; the skill narrates, logs, and gates sensitive data.
  
  Do NOT trigger for: code questions, debugging, design questions or audits, routine PR review, dependency upgrades, refactors, "how do I rebase / fix my docker / write this query", general MacBook or hardware spec comparisons, generic "what should I do next on the project" questions, code-only deploys after the first one is set up, brainstorming, or anything that doesn't touch an external regulator/bank/legal/Apple/Google service in an irreversible way. If the user is asking for help with code, ideas, or routine engineering, this is the wrong skill.
---

# Live Runbook Walkthrough

Hold the user's hand through real-world, often-irreversible processes governed by a project runbook. Narrate, log, gate sensitive data, update -- but never act on external systems on the user's behalf.

## Why this skill exists

Some processes are bigger than code: filing for an EIN with the IRS, signing an LLC operating agreement, opening a business bank account, filing a Beneficial Ownership Information report, configuring TestFlight for a first release. They share three properties:

1. **External and irreversible.** A submitted IRS form is submitted. A signed contract is signed. A wired bank deposit is wired. There is no undo.
2. **Field-by-field tedium.** The runbook captures the exact answers (responsible party, NAICS code, member contributions, beneficial-ownership disclosures, App Store Connect metadata). Getting any field wrong means restarting or, worse, filing an amendment.
3. **Generates artifacts that need filing.** A confirmation PDF, a signed agreement, a bank statement, a screenshot of the TestFlight build -- the project's living docs need to reflect these or future-you loses the audit trail. *Some of those artifacts contain SSNs, EINs, account numbers, member home addresses, or signed legal text. They cannot be casually committed to git.*

Without this skill, the user does it alone with a runbook in one tab and the form in another, copy-pasting and hoping they didn't miss a field. With this skill, Claude reads the runbook, narrates the next field, waits for confirmation, gates sensitive output, logs the result, and at the end opens a PR that updates the project records.

The user does the typing into the external system. **You fill, I narrate.** Claude does everything else around it.

## When NOT to use this skill

This skill is heavy machinery for irreversible external workflows. It is the wrong tool for ordinary engineering work. Skip it when:

- The user is asking a code question, asking for a design review, debugging a failing test, or upgrading a dependency.
- The user wants help with a routine PR, code review, refactor, or release that doesn't touch an external regulator/bank/legal service for the first time.
- The "next step" is purely internal (write code, run tests, ship a feature flag).
- The user is comparison-shopping hardware in the abstract with no expense-policy or business-records consequence -- that's a normal conversation, not a runbook walkthrough.
- The user is brainstorming or scoping; there's no checked-in runbook and no irreversible action imminent.

When in doubt, ask: "Is the user about to do something with the IRS, a bank, a state regulator, a court, Apple/Google's developer console, or sign a legal document, where getting it wrong has real-world consequences?" If no, this skill is overkill.

## Phase 1: Find and read the runbook

Ask the user which workflow this is, then locate the runbook. Conventional locations:

- `docs/runbooks/<workflow-name>.md`
- `docs/<workflow-name>.md`
- `docs/business/<workflow-name>.md`
- `runbooks/<workflow-name>.md`

If multiple match the user's phrasing, list them and ask. If none exist, stop and offer to draft one with the user before executing -- doing a real-world workflow without a checked-in runbook means there's no source of truth to follow and no place to record the result.

Once located, **read the runbook end-to-end before starting**. Note:

- The full sequence of steps
- Fields/values the runbook prescribes (and any marked "TBD" that need a decision now)
- External services involved (IRS, state SOS, bank, Apple, etc.)
- Required artifacts and where they're filed (`docs/business/records/`, `docs/releases/`, etc.)
- Any preconditions the runbook lists ("must have EIN before opening bank account", "must have provisioning profile before TestFlight upload")

If the runbook references prior artifacts the user should already have, verify they exist before starting. Missing precondition? Stop and surface it.

## Phase 2: Confirm the plan with the user

Before touching anything, restate the plan in plain language:

> "Here's the plan. We're going to do <workflow>. There are <N> steps. The external systems we'll touch are <list>. The irreversible ones are <list>. You'll be entering data into <forms>; I'll narrate each field from the runbook. You fill, I narrate -- I won't touch the external system. At the end, I'll classify any artifacts as sensitive or non-sensitive, gate the sensitive ones with you, and open a PR for the docs updates. Sound right?"

Do not start the walkthrough until the user confirms. This isn't ceremony -- it's a chance for them to say "wait, the runbook is out of date" or "actually the LLC name changed last week" before you're three fields deep into an IRS form.

## Phase 3: Walk step-by-step

For each step in the runbook:

1. **Announce the step** by name and what it accomplishes.
2. **Narrate each field** the user needs to enter, with the prescribed value from the runbook. Format example:
   > Field: **Responsible party SSN/ITIN** -- enter `<value from runbook>`. (This is the one you decided would be the responsible party on <date>; the runbook locks it in at line 47.)
3. **Wait for the user to confirm completion** before moving on. Use phrasing like "let me know when you've entered that and I'll give you the next field." Do not race ahead.
4. **At decision points**, surface options from the runbook and let the user choose. Don't pick for them on legal/financial questions.
5. **For confirmation/preview screens**, prompt the user to read carefully and only proceed when they're ready.

### Hard rules during the walkthrough

- **Never auto-fill external forms.** No browser automation against IRS, state SOS, bank, Apple, etc. Even if the tooling exists, this is the user's signature/submission. **You fill, I narrate.**
- **Never click the final submit button on the user's behalf**, even hypothetically.
- **Stop before any irreversible action** ("submit", "sign", "wire", "publish") and explicitly ask: "This is the irreversible step. Confirm to proceed?" Wait for an unambiguous yes.
- **Handle runbook drift as a hard pause, not a fix-later note.** If the runbook contradicts what the user sees on screen, or the form asks something the runbook didn't anticipate, **stop the walkthrough**. Do not improvise. See "Phase 3a: Runbook drift loop" below.

### Phase 3a: Runbook drift loop

The runbook is the source of truth. The moment reality diverges from it -- a missing field, a renamed option, an extra disclosure the form now requires, a value the runbook says is `X` but the user knows should now be `Y` -- the safe move is to fix the runbook *before* taking the next external action, not after. Reasoning: if you act first and edit the runbook later, the on-screen submission and the checked-in record will silently disagree, and the next person running this workflow (often you, in a year) will repeat the same mistake.

The loop, every time drift is detected:

1. **Pause the walkthrough.** Do not advance to the next field, do not let the user submit.
2. **Describe the drift in plain language.** "The runbook says enter `X` for field Y, but the form is now labeled differently / now requires Z / shows option `W`." Quote the runbook line.
3. **Ask the user how to resolve.** Options: update the runbook to match reality; correct the form to match the runbook; abort and investigate. Do not pick for them.
4. **Edit the runbook with the user, in this session.** Make the change, show the diff, get explicit confirmation that the new runbook text matches what they intend to do.
5. **Resume only after the runbook reflects ground truth.** Then continue from the same step with the corrected value.

This trades a few minutes of friction now for a runbook that stays trustworthy. If the user wants to defer the fix, that's their call -- but flag it loudly and capture a TODO at minimum; do not let it slip silently.

## Phase 4: Capture artifacts and classify before staging

As each step generates an artifact -- a confirmation PDF, a signed document, a screenshot, a confirmation number, a bank account number, an EIN -- ask the user to save the raw file somewhere first (typically the path the runbook prescribes, or a local out-of-repo location for sensitive originals). **Do not stage anything to git yet.**

### Why this phase is gated

Real-world workflows produce documents that are simultaneously *evidence the project needs to retain* and *information the user does not want broadcast*. An EIN confirmation letter contains the EIN itself plus the responsible party's SSN. A signed operating agreement contains member home addresses and equity allocations. A bank welcome packet contains the full account and routing numbers. A BOI filing contains beneficial owners' personal information.

Committing those originals to a repo -- especially if the repo is or might become public, or is mirrored to a hosted Git service -- is a privacy/security incident waiting to happen. Equally, *not* recording anything means the project loses its audit trail. The right move is to record what the project needs (dates, identifiers we're OK exposing, paths to where the original lives) while keeping the sensitive originals out of version control or stored only in redacted form.

### The classification gate

Before staging any artifact, walk through this list **with the user, item by item**:

1. **Enumerate every artifact** produced by the workflow. For each one, name the file, briefly describe its contents, and propose a classification:
   - **Non-sensitive** -- safe to commit as-is (e.g., the runbook itself, a public-record state filing receipt with no SSN, a screenshot that contains nothing private).
   - **Sensitive** -- contains SSN/ITIN, EIN if the project treats it as private, full bank account/routing numbers, member personal addresses, signature images, beneficial-ownership disclosures, or anything else the user wouldn't paste into a public chat.
2. **For each sensitive artifact, ask the user to choose**, and wait for an explicit answer:
   - **(a) Keep original out of git entirely**, store under a path the user names (e.g., `~/Documents/business-records/IRS/2026-EIN-confirmation.pdf`), and record only metadata in the repo (date, document type, location reference, a non-sensitive identifier if any).
   - **(b) Commit a redacted copy** (e.g., a PDF with SSN blacked out, or a markdown record where `SSN: [REDACTED]`, `EIN: 12-XXXXXXX`, `Account: ****1234`), keeping the original out of git.
   - **(c) Commit the original as-is** -- only if the user explicitly confirms this is acceptable for *this specific repo's* visibility model. Do not assume; ask each time.
3. **Confirm per item, not in bulk.** "Commit all of these?" is the wrong question. The right question is one artifact at a time: "The EIN confirmation PDF -- (a) keep out of git, (b) commit redacted, or (c) commit as-is?"
4. **For confirmation numbers, dates, and identifiers** that the user is fine surfacing, add them to the runbook's "Record" section or a project-level register (e.g., `docs/business/records/<entity>.md`). For values the user wants kept private, record only "issued YYYY-MM-DD; original at <local path>".

Only after every artifact has an explicit disposition do you move on to staging and writing records.

Record at minimum: what was done, when, by whom, what came back (in whatever redacted/abstract form was agreed), where the proof lives.

## Phase 5: Update living docs

After the workflow completes, the project's living docs almost certainly need updates. Common patterns:

- **PRD / roadmap** -- the milestone the workflow represented now moves from "planned" to "done"
- **Constraints / gotchas** -- if you hit a surprise during the walkthrough, write it down so future-you doesn't get bitten again
- **The runbook itself** -- if any drift was deferred during Phase 3a (rare; ideally fixed in-flight), capture the remaining edits now and confirm with the user before staging
- **Status registers** (entity register, release log, expense log) -- add the new record, respecting the redaction decisions from Phase 4

Make these edits and stage them.

## Phase 6: Open a PR

Open a PR with all the doc updates and any committed artifacts (only those the user explicitly approved in Phase 4). Use a concise title and a body that:

- Names the workflow that was completed
- Lists the artifacts and their disposition (committed as-is, committed redacted, kept out of git with reference path)
- Lists the living docs updated and why
- Notes any runbook fixes (and any drift the user deferred)
- Calls out anything the user should follow up on (e.g., "expect IRS confirmation letter in 2 weeks; file under `~/Documents/business-records/IRS/` when it arrives, then add a metadata record")

Do not auto-merge. The user reviews and merges.

## Conservative defaults

- **Confirm before each irreversible step.** Submission, signature, wire, publish.
- **Read the runbook fully before starting.** Mid-step is too late to discover the runbook expects a precondition you don't have.
- **Pause on drift.** Edit the runbook to match reality before continuing -- do not paper over and "fix later".
- **Classify every artifact before staging.** Per item, with explicit user disposition. Sensitive originals do not enter git by default.
- **Treat tax/legal decisions as the user's.** You can pull values from the runbook; you cannot decide on a NAICS code or LLC structure on the fly.

## Workflow-specific quick references

These are not exhaustive -- always defer to the project's runbook. They're starting points if the runbook is thin.

### IRS EIN (Form SS-4 via online Assistant)

- The online Assistant times out after ~15 min of inactivity; have the runbook's responsible-party SSN, entity legal name, mailing address, and NAICS code ready before starting
- Final step issues the EIN immediately as a PDF -- save it; the IRS does not email a copy
- The PDF contains the responsible party's SSN. **Default classification: sensitive.** Keep the original out of git; commit only a redacted record.

### LLC Operating Agreement signing

- Confirm all members are present (or e-sign queue is set up) before starting
- Capture each signature page; the fully-executed version is the canonical artifact
- Contains member personal addresses and signatures. **Default classification: sensitive.** Store original off-repo; commit only execution date + reference path.

### Business banking

- Required: EIN confirmation, operating agreement, ID, sometimes initial deposit
- Beneficial Ownership Information (BOI) reporting may be required separately -- check the runbook
- Account/routing numbers and any BOI submission receipt are sensitive. Commit redacted (`Account: ****1234`) or keep originals off-repo entirely.

### TestFlight / Xcode initial setup

- Bundle identifier, App Store Connect app record, and signing identity must all match
- The first build upload is the irreversible-ish step (locks the bundle ID to the team)
- See also: `ios-dev-toolkit:ios-testflight-deploy` skill for the pure-tech workflow

## When to escalate to the user

- Runbook is missing, stale, or contradicts the form (and Phase 3a drift loop is needed)
- Precondition artifact is missing
- The form asks something the runbook didn't anticipate
- The user expresses doubt about a value -- never push past hesitation on a legal/financial input
- An artifact's classification is ambiguous (e.g., "is the EIN itself sensitive in this project?") -- ask, don't assume
