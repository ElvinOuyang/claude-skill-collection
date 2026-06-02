# Workflow Catalog Guide

`workflow-catalog.json` stores local knowledge that cannot be inferred reliably from a ComfyUI workflow alone.

## Record Fields

- `id`: Stable local identifier.
- `kind`: Usually `lora`; may also be `checkpoint`, `vae`, `controlnet`, `embedding`, `style`, or `custom-node`.
- `match`: Case-insensitive substrings or glob patterns matched against names found in the workflow.
- `model_families`: Compatible families such as `sdxl`, `pony-xl`, or `illustrious-xl`.
- `trigger_words`: Text required to activate the component.
- `positive_additions`: Extra positive prompt text.
- `negative_additions`: Extra negative prompt text.
- `recommended_strength_model` and `recommended_strength_clip`: Creator-recommended node values when known.
- `source_url`: Creator or model page.
- `notes`: Short operational notes.

Keep uncertain fields empty and ask the user. Do not turn guesses into catalog entries.
