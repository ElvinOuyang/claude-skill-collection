---
name: token-efficient-setup
description: Use when setting up a new project's CLAUDE.md, when the user asks to reduce token usage, add token efficiency rules, or optimize Claude Code output verbosity. Also use when creating CLAUDE.md from scratch for any project.
---

# Token-Efficient Setup

Add token-efficiency rules to a project's CLAUDE.md based on the project type. Rules eliminate sycophantic openers, filler text, restating questions, and over-engineering — reducing output tokens by ~60% with zero signal loss.

Based on [drona23/claude-token-efficient](https://github.com/drona23/claude-token-efficient).

## Process

1. **Detect project type** by scanning the codebase
2. **Present detection + selected profile** to the user for confirmation
3. **Merge rules** into existing CLAUDE.md (or create one)

## Detection Logic

Scan the project root and first two directory levels for signals:

| Signal | Profile |
|--------|---------|
| `.ipynb` files, `pandas`/`numpy`/`scipy` imports, `*.R` files, `data/` dirs | **analysis** |
| Agent configs, `agents/` dir, bot frameworks, heavy CI/CD automation, MCP servers | **agents** |
| Source code (`*.ts`, `*.py`, `*.swift`, `*.go`, `*.rs`, etc.), `package.json`, `Cargo.toml`, `*.xcodeproj` | **coding** |
| User explicitly says "benchmark" | **benchmark** |

Most projects are **coding**. When signals overlap (e.g., a coding project with some notebooks), pick the dominant type and mention the overlap to the user.

## Merging Rules

**If CLAUDE.md exists:** Append a clearly marked section at the end:

```markdown

## Token Efficiency

<!-- From https://github.com/drona23/claude-token-efficient -->
<!-- Profile: {profile_name} -->

{profile rules here}
```

**If no CLAUDE.md exists:** Create one with the universal rules at the top, then the profile-specific rules below.

**Never overwrite** existing project-specific instructions. The token efficiency section goes at the bottom because the repo itself says "User instructions always override this file."

## Profiles

Read `references/profiles.md` for the full text of each profile. The four profiles are:

- **coding** — Code first, explanation only if non-obvious. No over-engineering, no speculative features, no blind edits. Review = state bug, show fix, stop.
- **analysis** — Lead with findings. Numbers need units/sources. Distinguish data from inference. Summary-first reports.
- **agents** — Structured output only (JSON/bullets/tables). No narration. No confirmation-seeking. Parseable without post-processing.
- **benchmark** — Ultra-minimal. Deliver exactly what was requested, no extras.

## After Setup

Tell the user:
- What profile was selected and why
- Where the rules were added
- That they can switch profiles by editing the section header comment
