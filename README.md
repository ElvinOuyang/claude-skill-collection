# Claude Skill Collection

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces.md) with curated skills for iOS development, web development, and AI agent workflows.

## Installation

Add this marketplace to Claude Code:

```
/plugin marketplace add ElvinOuyang/claude-skill-collection
```

Then install the plugins you need:

```
/plugin install ios-dev-toolkit@claude-skill-collection
/plugin install web-dev-toolkit@claude-skill-collection
/plugin install ai-dev-toolkit@claude-skill-collection
/plugin install openclaw-config@claude-skill-collection
```

To enable auto-updates: `/plugin` > Marketplaces tab > select this marketplace > Enable auto-update.

## Plugins

### ios-dev-toolkit

iOS/SwiftUI development skills for building, polishing, and deploying iOS apps.

| Skill | Description |
|---|---|
| axe | iOS Simulator automation via AXe CLI |
| ios-animate | Enhance SwiftUI views with purposeful animations, haptics, and motion |
| ios-audit | Technical quality checks: accessibility, performance, HIG compliance |
| ios-critique | UX evaluation with quantitative scoring and persona-based testing |
| ios-polish | Final quality pass for spacing, typography, color, and animation |
| ios-simulator-nav | Navigate iOS Simulator with AXe label-based taps |
| ios-testflight-deploy | TestFlight deployment workflow with failure recovery |

### web-dev-toolkit

Web development skills for mobile workflows, testing, and UI verification.

| Skill | Description |
|---|---|
| web-mobile-playwright-tests | Convert mobile workflow docs into Playwright test projects |
| web-mobile-workflow | Generate mobile browser workflow documentation via Playwright |
| web-ui-spec-checker | Check running web app UI against design specs |

### ai-dev-toolkit

Skills for iterating on AI agent prompts, generating tests, and optimizing projects.

| Skill | Description |
|---|---|
| prompt-eval | Test AI system prompts with mock tools and eval assertions |
| spec-driven-tests | Generate tests from specs, PRDs, and implementation plans |
| token-efficient-setup | Set up CLAUDE.md with token efficiency rules |

### openclaw-config

| Skill | Description |
|---|---|
| openclaw-config | Configure OpenClaw self-hosted AI gateway via Docker |

## Structure

```
claude-skill-collection/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    ├── ios-dev-toolkit/
    │   ├── .claude-plugin/plugin.json
    │   └── skills/
    ├── web-dev-toolkit/
    │   ├── .claude-plugin/plugin.json
    │   └── skills/
    ├── ai-dev-toolkit/
    │   ├── .claude-plugin/plugin.json
    │   └── skills/
    └── openclaw-config/
        ├── .claude-plugin/plugin.json
        └── skills/
```

## Updating

After pushing changes to this repo, bump the `version` in the relevant `plugin.json`. Users with auto-update enabled will get the new version at Claude Code startup. Manual update:

```
/plugin marketplace update claude-skill-collection
```

## License

All rights reserved. No license is granted at this time.
