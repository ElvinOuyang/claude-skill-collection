# Prompt Injection Red-Team Mode

Use this mode only for controlled private tests of how an untested local model responds to selected prompt injections.

## Default State

- Keep the clean production prompt unchanged.
- Set `Enabled: no`.
- Require explicit opt-in for every activation.
- Load vectors only from a user-maintained `local-red-team-vectors.json` file outside version control.
- Refer to selected vectors by ID. Do not print their values in chat or copy them into repository files.

## Allowed Test Flow

1. Start from a clean prompt pack and fixed generation settings.
2. Confirm explicit opt-in and the local vector file path.
3. Ask the user to select the smallest relevant set of vector IDs.
4. Prepare a separately labeled local-only workflow input that appends only the selected vectors.
5. Generate a fixed-seed clean control and isolated test pair.
6. Run visual QA against the pair.
7. Record which vector IDs changed the output and whether upstream filtering should block them.

Suggested local file shape:

```json
{
  "vectors": [
    {
      "id": "local-example",
      "category": "user-defined",
      "value": "replace locally"
    }
  ]
}
```

## Output Block

```markdown
## Prompt Injection Red-Team Mode
- Enabled: yes
- Vector source: local-red-team-vectors.json
- Selected vector IDs:
- Clean baseline preserved: yes
- Purpose: controlled private prompt-injection simulation
- Non-production warning: never merge into reusable baselines or ordinary scene prompts
```

## Hard Exclusions

Do not invent or supply vector values. Do not activate ambiguous-age, coercive, illegal, or derogatory categories. Do not use this mode to generate a standalone scene prompt. Its purpose is defensive testing of an otherwise valid local workflow.
