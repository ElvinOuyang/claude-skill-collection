# Claude Skill Collection

A personal collection of [Claude Code](https://claude.ai/claude-code) skills for common workflows and tools.

## What are Skills?

Skills are reusable instruction sets that extend Claude Code's behavior for specific domains. When a matching task comes up, Claude automatically loads the relevant skill and follows its guidance — giving you consistent, accurate results without repeating yourself.

## Skills

| Skill | Description |
|---|---|
| [openclaw-config](skills/openclaw-config/) | Configure OpenClaw (self-hosted AI gateway) installed via Docker |

## Installation

To use a skill, copy the skill directory into your `~/.claude/skills/` folder:

```bash
cp -r skills/openclaw-config ~/.claude/skills/
```

Then reload plugins in Claude Code:

```
/reload-plugins
```

## Structure

```
claude-skill-collection/
└── skills/
    └── <skill-name>/
        ├── SKILL.md          # Skill instructions and frontmatter
        └── evals/
            └── evals.json    # Test cases
```

## License

MIT
