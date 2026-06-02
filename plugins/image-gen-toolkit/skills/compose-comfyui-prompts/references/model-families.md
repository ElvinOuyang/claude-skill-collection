# Model Family Recipes

Use these as conservative starting points. Check checkpoint documentation when available because finetunes may override the parent family's conventions.

## SDXL And Unknown SDXL Finetunes

- Start with clear natural-language subject and scene description.
- Add a short visual-quality clause only when it helps: `high detail, coherent composition, controlled lighting`.
- Avoid long inherited SD 1.5 negative-prompt boilerplate by default.
- Add failure-specific negatives only when relevant: `blurry, low detail, malformed hands, extra fingers, text, watermark`.

## Pony XL And Pony-Derived Checkpoints

- Start positive prompts with a conservative score prefix: `score_9, score_8_up, score_7_up`.
- Add an appropriate source tag when useful, such as `source_anime`, `source_cartoon`, or `source_furry`.
- Add a rating tag when the user requests it, such as `rating_safe`.
- Start negatives with: `score_6, score_5, score_4`.
- Use booru-style tags for concrete visual concepts unless the checkpoint documentation recommends prose.
- Do not automatically add lower positive score tags such as `score_5_up` or `score_4_up`; add them only when the user intentionally wants more variation.

## Illustrious XL And WAI Illustrious-Derived Checkpoints

- Prefer booru-style tags for characters, attributes, pose, composition, and style concepts.
- Use concise natural-language phrases when they express relationships or scene details more clearly than tags.
- Start with a compact quality prefix only when the checkpoint documentation recommends it. For an undocumented Illustrious-derived checkpoint, try: `masterpiece, best quality, amazing quality`.
- Start negatives conservatively: `worst quality, low quality, lowres, bad anatomy, bad hands, text, watermark`.
- Treat WAI variants as checkpoint-specific: preserve creator-recommended quality and negative tags in the workflow catalog when known.

## LoRA Compatibility

- Confirm that a LoRA targets the active base family before recommending it.
- Apply trigger words only when documented in the workflow catalog or supplied by the user.
- Keep LoRA node strengths separate from trigger words. A workflow may load a LoRA correctly while still needing textual triggers.
