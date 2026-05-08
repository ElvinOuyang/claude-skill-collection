---
name: live-runbook-walkthrough
description: >
  Hold the user's hand through external, multi-step, real-world processes governed by a project runbook -- IRS EIN application, LLC operating agreement signing, Wave bookkeeping setup, business banking, TestFlight/Xcode initial setup, MacBook purchase decisions against business records, and similar. Load the project's runbook from docs/, narrate field-by-field or step-by-step, log artifacts to the right folder, update living docs as steps complete, and open a PR for the resulting record updates. Use this skill whenever the user asks to be walked through a real-world workflow that has legal/financial/external-service consequences -- phrases like "walk me through", "hold my hand", "live walkthrough", "what do I do next on X", "EIN application", "operating agreement", "sign the OA", "Wave setup", "open the business bank account", "TestFlight setup", "first deploy", "should I buy this MacBook", "runbook walkthrough", or any time there's a runbook in docs/ and the user is about to execute it. Trigger even if the user doesn't reference a runbook explicitly -- the cue is "I'm about to do this irreversible/external thing, walk me through it". Be conservative: NEVER auto-fill external forms; the user fills them, the skill narrates.
---

# Live Runbook Walkthrough

Hold the user's hand through real-world, often-irreversible processes governed by a project runbook. Narrate, log, update -- but never act on external systems on the user's behalf.

## Why this skill exists

Some processes are bigger than code: filing for an EIN with the IRS, signing an LLC operating agreement, opening a business bank account, configuring TestFlight for a first release, deciding whether a MacBook purchase is a defensible business expense. They share three properties:

1. **External and irreversible.** A submitted IRS form is submitted. A signed contract is signed. A wired bank deposit is wired. There is no undo.
2. **Field-by-field tedium.** The runbook captures the exact answers (EIN responsible party, NAICS code, member contributions, beneficial-ownership disclosures, App Store Connect metadata). Getting any field wrong means restarting or, worse, filing an amendment.
3. **Generates artifacts that need filing.** A confirmation PDF, a signed agreement, a bank statement, a screenshot of the TestFlight build -- the project's living docs need to reflect these or future-you loses the audit trail.

Without this skill, the user does it alone with a runbook in one tab and the form in another, copy-pasting and hoping they didn't miss a field. With this skill, Claude reads the runbook, narrates the next field, waits for confirmation, logs the result, and at the end opens a PR that updates the project records.

The user does the typing into the external system. Claude does everything else.

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

> "Here's the plan. We're going to do <workflow>. There are <N> steps. The external systems we'll touch are <list>. The irreversible ones are <list>. You'll be entering data into <forms>; I'll narrate each field from the runbook. At the end, I'll log the artifacts to <path> and open a PR. Sound right?"

Do not start the walkthrough until the user confirms. This isn't ceremony -- it's a chance for them to say "wait, the runbook is out of date" or "actually the LLC name changed last week" before you're three fields deep into an IRS form.

## Phase 3: Walk step-by-step

For each step in the runbook:

1. **Announce the step** by name and what it accomplishes
2. **Narrate each field** the user needs to enter, with the prescribed value from the runbook. Format example:
   > Field: **Responsible party SSN/ITIN** -- enter `<value from runbook>`. (This is the one you decided would be the responsible party on <date>; the runbook locks it in at line 47.)
3. **Wait for the user to confirm completion** before moving on. Use phrasing like "let me know when you've entered that and I'll give you the next field." Do not race ahead.
4. **At decision points**, surface options from the runbook and let the user choose. Don't pick for them on legal/financial questions.
5. **For confirmation/preview screens**, prompt the user to read carefully and only proceed when they're ready.

### Hard rules during the walkthrough

- **Never auto-fill external forms.** No browser automation against IRS, state SOS, bank, Apple, etc. Even if the tooling exists, this is the user's signature/submission. Narrate; don't act.
- **Never click the final submit button on the user's behalf**, even hypothetically.
- **Stop before any irreversible action** ("submit", "sign", "wire", "publish") and explicitly ask: "This is the irreversible step. Confirm to proceed?" Wait for an unambiguous yes.
- **If the runbook is wrong or contradicts what the user sees on screen**, stop. Don't paper over it. Let the user resolve the discrepancy and update the runbook.

## Phase 4: Log artifacts

As each step generates an artifact -- a confirmation PDF, a signed document, a screenshot, a confirmation number -- ask the user to save it to the path the runbook prescribes (or, if unprescribed, suggest a path that fits the project's convention). Then record the artifact in the right place:

- **Confirmation numbers, dates, identifiers** -- add to the runbook's "Record" section or to a project-level register (e.g., `docs/business/records/<entity>.md`)
- **Files** -- ensure they live under version control if the project's convention is to commit them; otherwise note the off-repo location

Record at minimum: what was done, when, by whom, what came back, where the proof lives.

## Phase 5: Update living docs

After the workflow completes, the project's living docs almost certainly need updates. Common patterns:

- **PRD / roadmap** -- the milestone the workflow represented now moves from "planned" to "done"
- **Constraints / gotchas** -- if you hit a surprise during the walkthrough, write it down so future-you doesn't get bitten again
- **The runbook itself** -- if any step was wrong, ambiguous, or out of date, fix it now. The next time someone runs this runbook (you, in a year) will thank you.
- **Status registers** (entity register, release log, expense log) -- add the new record

Make these edits and stage them.

## Phase 6: Open a PR

Open a PR with all the doc updates and any committed artifacts. Use a concise title and a body that:

- Names the workflow that was completed
- Lists the artifacts (with paths)
- Lists the living docs updated and why
- Notes any runbook fixes
- Calls out anything the user should follow up on (e.g., "expect IRS confirmation letter in 2 weeks; file under `docs/business/records/IRS/` when it arrives")

Do not auto-merge. The user reviews and merges.

## Conservative defaults

- **Confirm before each irreversible step.** Submission, signature, wire, publish.
- **Read the runbook fully before starting.** Mid-step is too late to discover the runbook expects a precondition you don't have.
- **Surface drift, don't paper over it.** If the form has fields the runbook doesn't mention, stop and ask -- don't guess.
- **Treat tax/legal decisions as the user's.** You can pull values from the runbook; you cannot decide on a NAICS code or LLC structure on the fly.
- **No off-runbook actions.** If the user wants to deviate, fine -- update the runbook first, then proceed.

## Workflow-specific quick references

These are not exhaustive -- always defer to the project's runbook. They're starting points if the runbook is thin.

### IRS EIN (Form SS-4 via online Assistant)

- The online Assistant times out after ~15 min of inactivity; have the runbook's responsible-party SSN, entity legal name, mailing address, and NAICS code ready before starting
- Final step issues the EIN immediately as a PDF -- save it; the IRS does not email a copy
- Save to the location the runbook prescribes (commonly `docs/business/records/IRS/`)

### LLC Operating Agreement signing

- Confirm all members are present (or e-sign queue is set up) before starting
- Capture each signature page; the fully-executed version is the canonical artifact
- Update the entity register with execution date

### Wave bookkeeping setup

- Verify the EIN and bank account exist first (preconditions)
- Chart of accounts and customer/vendor seed data come from the runbook
- Note: connecting the bank is the irreversible-ish step (initiates micro-deposits)

### Business banking

- Required: EIN confirmation, operating agreement, ID, sometimes initial deposit
- Beneficial Ownership Information (BOI) reporting may be required separately -- check the runbook

### TestFlight / Xcode initial setup

- Bundle identifier, App Store Connect app record, and signing identity must all match
- The first build upload is the irreversible-ish step (locks the bundle ID to the team)
- See also: `ios-dev-toolkit:ios-testflight-deploy` skill for the pure-tech workflow

### MacBook purchase decision

- Cross-check against the project's expense policy and prior-year purchases
- This is a decision-support walkthrough, not a transaction walkthrough -- output is a written recommendation the user can act on, not a click-through

## When to escalate to the user

- Runbook is missing, stale, or contradicts the form
- Precondition artifact is missing
- The form asks something the runbook didn't anticipate
- The user expresses doubt about a value -- never push past hesitation on a legal/financial input
