# Contributing

## Adding a New Skill

1. Create a directory under `skills/<skill-name>/`
2. Write `SKILL.md` with the required frontmatter:

```markdown
---
name: skill-name
description: >
  When to trigger this skill and what it does.
  Be specific — this is what Claude reads to decide whether to use the skill.
---

# Skill Title

...instructions...
```

3. Add test cases to `skills/<skill-name>/evals/evals.json`
4. Update the skills table in `README.md`

## Skill Guidelines

- Keep `SKILL.md` under 500 lines
- Include concrete commands and config examples, not just concepts
- Add a troubleshooting section for common failure modes
- Test against at least 3 realistic user prompts before committing
