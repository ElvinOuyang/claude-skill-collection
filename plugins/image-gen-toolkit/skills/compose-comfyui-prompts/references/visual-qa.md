# Adversarial Visual QA

Use this checklist after generation. Review the actual image at sufficient resolution. Keep observations separate from likely causes.

## Inputs

Request the generated images, intended prompt pack, workflow JSON or relevant settings, seed, dimensions, sampler, scheduler, steps, CFG, and denoise value when available. Do not block the review when only images and prompts are available; label setting-related conclusions as uncertain.

## Review Order

1. **Intent fidelity**: subject count, identity, action, pose, expression, setting, mood, medium, and requested details.
2. **Composition**: framing, crop, focal hierarchy, viewpoint, depth, background readability, and accidental clutter.
3. **Anatomy and geometry**: hands, fingers, limbs, joints, face, eyes, teeth, clothing boundaries, perspective, repeated objects, and impossible intersections.
4. **Surface quality**: blur, oversharpening, plastic texture, muddy detail, noise, color cast, banding, and inconsistent lighting.
5. **Text and marks**: unwanted text, signatures, watermarks, logos, and pseudo-text.
6. **LoRA behavior**: missing trigger effect, excessive stylization, identity leakage, costume leakage, style collisions, or overbaked details.
7. **Batch consistency**: repeated failures across seeds versus isolated failures.

## Diagnose Conservatively

Use these labels:

- `Observed`: directly visible in the image.
- `Likely cause`: evidence-based inference.
- `Confidence`: high, medium, or low.
- `Next test`: one controlled change.

Do not automatically solve every defect with more negative tags. Prefer the smallest plausible intervention:

- Remove contradictory prompt terms.
- Strengthen or simplify one concept.
- Reorder or weight a required trigger.
- Adjust one LoRA strength.
- Reduce composition complexity.
- Test a different aspect ratio.
- Adjust CFG, steps, sampler, scheduler, or denoise only when the visual pattern supports it.
- Use inpainting, ControlNet, or a detailer when prompting alone is unlikely to fix a localized issue.

## Controlled Iteration

Keep the seed fixed when testing a prompt or setting change. Change one variable at a time. Generate a small comparison batch before editing the reusable baseline. Preserve successful parts of the prior prompt.

## Report Template

```markdown
## Visual QA Verdict
- Overall:
- Keep stable:

## Findings
| Severity | Observed | Likely cause | Confidence | Next test |
| --- | --- | --- | --- | --- |

## Minimal Prompt Delta
Remove:
Add:
Reweight:

## Workflow Experiment
- Change one variable:
- Keep fixed:
- Compare:
```

Use `critical`, `major`, `minor`, and `optional` severity. Lead with failures that materially affect the user's request.
