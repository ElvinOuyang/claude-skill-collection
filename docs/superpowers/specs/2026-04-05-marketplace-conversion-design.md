# Marketplace Conversion Design

Convert `claude-skill-collection` from a manual-install skill repo into a Claude Code plugin marketplace.

## Context

The repo currently has one skill (`openclaw-config`) installed by copying to `~/.claude/skills/`. The owner has 13 additional personal skills at `~/.claude/skills/` (non-symlinked, self-authored) that should be published through this marketplace.

## Design

### Plugin Grouping (4 plugins)

**`ios-dev-toolkit`** (7 skills)
- `axe` -- iOS Simulator automation via AXe CLI
- `ios-animate` -- SwiftUI animation enhancement
- `ios-audit` -- iOS code quality checks (a11y, perf, HIG)
- `ios-critique` -- iOS UX evaluation with scoring
- `ios-polish` -- Final quality pass for SwiftUI views
- `ios-simulator-nav` -- Simulator navigation with AXe
- `ios-testflight-deploy` -- TestFlight deployment workflow

**`web-dev-toolkit`** (3 skills)
- `web-mobile-playwright-tests` -- Convert mobile workflows to Playwright tests
- `web-mobile-workflow` -- Generate mobile browser workflow docs
- `web-ui-spec-checker` -- Check UI against design specs

**`ai-dev-toolkit`** (3 skills)
- `prompt-eval` -- Test AI system prompts with evals
- `spec-driven-tests` -- Generate tests from specs/PRDs
- `token-efficient-setup` -- Optimize CLAUDE.md for token efficiency

**`openclaw-config`** (1 skill)
- `openclaw-config` -- Configure OpenClaw Docker gateway

### Repo Structure

```
claude-skill-collection/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── ios-dev-toolkit/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   │       ├── axe/
│   │       ├── ios-animate/
│   │       ├── ios-audit/
│   │       ├── ios-critique/
│   │       ├── ios-polish/
│   │       ├── ios-simulator-nav/
│   │       └── ios-testflight-deploy/
│   ├── web-dev-toolkit/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   │       ├── web-mobile-playwright-tests/
│   │       ├── web-mobile-workflow/
│   │       └── web-ui-spec-checker/
│   ├── ai-dev-toolkit/
│   │   ├── .claude-plugin/plugin.json
│   │   └── skills/
│   │       ├── prompt-eval/
│   │       ├── spec-driven-tests/
│   │       └── token-efficient-setup/
│   └── openclaw-config/
│       ├── .claude-plugin/plugin.json
│       └── skills/
│           └── openclaw-config/
├── README.md
├── CONTRIBUTING.md
└── LICENSE
```

### marketplace.json Schema

```json
{
  "name": "claude-skill-collection",
  "owner": {
    "name": "Elvin Ouyang",
    "email": ""
  },
  "metadata": {
    "description": "Curated skills for iOS dev, web dev, and AI agent workflows",
    "version": "2.0.0"
  },
  "plugins": [
    {
      "name": "ios-dev-toolkit",
      "source": "./plugins/ios-dev-toolkit",
      "description": "iOS/SwiftUI development skills: animation, audit, critique, polish, simulator nav, TestFlight deploy, and AXe automation",
      "version": "1.0.0",
      "keywords": ["ios", "swiftui", "xcode", "testflight", "simulator"]
    },
    {
      "name": "web-dev-toolkit",
      "source": "./plugins/web-dev-toolkit",
      "description": "Web development skills: mobile workflows, Playwright test generation, and UI spec checking",
      "version": "1.0.0",
      "keywords": ["web", "playwright", "mobile", "testing", "ui"]
    },
    {
      "name": "ai-dev-toolkit",
      "source": "./plugins/ai-dev-toolkit",
      "description": "AI development skills: prompt evaluation, spec-driven tests, and token-efficient project setup",
      "version": "1.0.0",
      "keywords": ["ai", "prompts", "testing", "evals", "token-efficiency"]
    },
    {
      "name": "openclaw-config",
      "source": "./plugins/openclaw-config",
      "description": "Configure OpenClaw self-hosted AI gateway via Docker",
      "version": "1.0.0",
      "keywords": ["openclaw", "docker", "ai-gateway"]
    }
  ]
}
```

### plugin.json Schema (per plugin)

Each plugin gets a minimal manifest:

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "<plugin description>",
  "author": {
    "name": "Elvin Ouyang"
  },
  "license": "MIT",
  "skills": "./skills/"
}
```

### Install UX

```bash
/plugin marketplace add ElvinOuyang/claude-skill-collection
/plugin install ios-dev-toolkit@claude-skill-collection
/plugin install web-dev-toolkit@claude-skill-collection
/plugin install ai-dev-toolkit@claude-skill-collection
/plugin install openclaw-config@claude-skill-collection
```

### Update Flow

Bump `version` in the relevant `plugin.json` when skills change. Users with auto-update enabled get updates at Claude Code startup. Manual update: `/plugin marketplace update claude-skill-collection`.

### Exclusions

- `ios-testflight-deploy-workspace/` -- eval iteration artifacts, not a skill
- `ui-spec-checker-workspace/` -- eval iteration artifacts, not a skill
- `__pycache__/` directories
- Symlinked skills in `~/.claude/skills/` (third-party, not owned)

## Implementation Steps

1. Remove old `skills/` directory from repo root
2. Create `.claude-plugin/marketplace.json`
3. Create 4 plugin directories with `.claude-plugin/plugin.json` each
4. Copy skill files from `~/.claude/skills/` into the correct plugin `skills/` subdirectories
5. Update README.md with marketplace install instructions
6. Update .gitignore for `__pycache__/`
7. Commit and push
