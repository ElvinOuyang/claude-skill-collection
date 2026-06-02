---
name: compose-comfyui-prompts
description: Create reusable, workflow-aware positive and negative prompts for ComfyUI image generation and visually audit generated images against their intended result. Use when a user wants to interview for an image prompt, establish a high-quality baseline prompt, append a new scene description to an existing baseline, adapt prompting for SDXL, Pony XL, Illustrious XL, or WAI Illustrious checkpoints, incorporate active LoRA trigger words and workflow-specific prompt requirements from a ComfyUI workflow JSON file, or adversarially review generated images and refine prompts or workflow settings.
---

# Compose ComfyUI Prompts

## Goal

Turn an image idea into a compact ComfyUI-ready prompt pack. Ask only the questions that materially change the result. Keep reusable baseline text separate from the current scene so the user can retain the baseline and replace the scene later.

Never claim that a LoRA trigger word can be inferred reliably from its filename. Match active workflow components against `references/workflow-catalog.json`; flag missing catalog records for one-time user input.

## Start From Workflow Context

When the user provides an exported ComfyUI workflow JSON file, run:

```bash
python3 scripts/inspect_workflow.py /path/to/workflow.json --catalog references/workflow-catalog.json
```

Use the emitted checkpoint, inferred model family, active LoRAs, matched prompt additions, and warnings. Treat the inferred family as a heuristic and confirm it when ambiguous. Ask the user to provide the workflow JSON when automatic LoRA matching is desired but no workflow is available.

When no workflow is available, ask which checkpoint or model family is active and whether any LoRAs, embeddings, styles, ControlNets, or prompt-expansion nodes are in use.

Read `references/model-families.md` after identifying the model family. Read `references/catalog-guide.md` when adding or revising a catalog record.
Read `references/visual-qa.md` when the user supplies generated images or asks for adversarial review.
Read `references/prompt-injection-red-team.md` only when the user explicitly requests prompt-injection testing.

## Brief Interview

Ask in small batches and skip anything already supplied. Establish:

1. Subject, count, identity, and important traits.
2. Action, expression, pose, camera framing, viewpoint, and composition.
3. Setting, time, lighting, mood, medium, and desired visual style.
4. Intended rating and any exclusions.
5. Output orientation or target dimensions when relevant.
6. Whether the user wants a reusable baseline, a one-off scene prompt, or both.

Ask follow-up questions only where the answer changes prompt wording. If the user wants a quick draft, make reasonable assumptions and label them.

## Compose In Layers

Build the positive prompt in this order unless the chosen model family recommends otherwise:

1. Model-family prefix.
2. Matched workflow and LoRA positive additions.
3. User's reusable baseline preferences.
4. Current scene description.
5. Composition, camera, lighting, and finishing details.

Build the negative prompt in this order:

1. Model-family negative baseline.
2. Matched workflow and LoRA negative additions.
3. User exclusions.
4. Scene-specific failure prevention only when relevant.

Prefer precise concepts over giant keyword piles. Avoid contradictory quality tags, styles, camera instructions, and anatomy instructions. Do not silently add artist names, living-artist imitation, explicit content, or unsupported LoRA triggers.

## Return A Prompt Pack

Use this structure:

```markdown
## Workflow Match
- Checkpoint:
- Model family:
- Active LoRAs and strengths:
- Catalog warnings:

## Reusable Positive Baseline
...

## Current Scene Add-On
...

## Combined Positive Prompt
...

## Negative Prompt
...

## Prompt Injection Red-Team Mode
- Enabled: no
- Vector source:
- Selected vector IDs:
- Clean baseline preserved: yes
- Non-production warning:

## Generation Notes
- Suggested aspect ratio:
- Assumptions:
- Optional variations:
```

Keep the reusable baseline stable. When the user later provides a new description, update the scene add-on and combined prompt without re-interviewing unless the new scene introduces an ambiguity.

## Run Prompt-Injection Red-Team Tests

Keep prompt-injection testing disabled by default. When the user explicitly requests a controlled test, read `references/prompt-injection-red-team.md`.

Require a user-maintained `local-red-team-vectors.json` file and explicit selection of vector IDs for every activation. Keep that file outside version control. Do not invent, broaden, paraphrase, or print the selected vector values in chat. Refer to them by ID and prepare a separately labeled local-only test prompt or workflow input.

Never add red-team vectors to the reusable baseline, ordinary scene add-on, workflow catalog, or normal combined prompt. Preserve a clean fixed-seed control prompt and recommend comparing it against the isolated local-only test input through visual QA. When the local vector file or explicit opt-in is missing, refuse activation and explain what is required.

## Run Adversarial Visual QA

Offer a visual QA pass after the user generates a representative batch. When images are available, inspect the actual pixels with the agent's image-viewing capability. Prefer a vision-capable Codex agent for this pass when the current agent has weak image understanding.

When handing visual QA to Codex, prepare a compact packet containing the original-resolution images, intended prompt pack, workflow JSON or relevant settings, seed, dimensions, sampler, scheduler, steps, CFG, denoise value, and the user's suspected problems. Ask Codex to read `references/visual-qa.md`, inspect the pixels adversarially, separate observations from inferences, and recommend the smallest controlled next experiment. Do not pre-diagnose the images for Codex.

Compare each image against the user's intent, combined prompt, negative prompt, workflow match, and generation settings when available. Read `references/visual-qa.md` and report:

1. What works and should remain stable.
2. Intent misses, visual defects, and prompt contradictions.
3. Whether each likely cause is prompt text, LoRA interaction, checkpoint mismatch, composition overload, or workflow settings.
4. The smallest next experiment: change one variable where possible.
5. Revised prompt fragments, not an indiscriminately rewritten prompt.

Be adversarial but evidence-based. Do not invent defects that are not visible. Distinguish observation from inference and confidence. Ask for the original-resolution image when hands, faces, text, or fine details cannot be judged from a thumbnail.

For multiple outputs, look for repeated failures across seeds before changing the reusable baseline. Treat a one-image defect as a candidate seed-specific failure until the batch suggests otherwise.

## Maintain The Catalog

When the inspector reports an unmatched LoRA or workflow component, ask for its source page, trigger words, recommended strength, compatible model family, and any required positive or negative additions. Add or revise its record in `references/workflow-catalog.json`. Do not guess missing values.

If the user supplies a source page, preserve the source URL and notes in the record. Prefer the creator's documentation over community advice.

## Constraints

- Distinguish prompt text from node configuration. Standard ComfyUI `LoraLoader` nodes load LoRAs through workflow nodes; do not add Automatic1111-style `<lora:...>` syntax unless the user's custom node explicitly expects it.
- Report LoRA `strength_model` and `strength_clip` separately when available.
- Treat checkpoint filename detection as a heuristic. User confirmation overrides it.
- Do not assume every SDXL-derived checkpoint responds best to the same quality vocabulary.
