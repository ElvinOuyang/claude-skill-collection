---
name: openclaw-config
description: >
  Guide for configuring OpenClaw — a self-hosted personal AI gateway — installed via Docker.
  Use this skill whenever the user asks about: setting up OpenClaw with Docker, configuring
  openclaw.json, adding messaging channels (Telegram, Discord, WhatsApp, etc.), setting AI
  provider API keys, adjusting gateway settings (port, bind, auth), troubleshooting an
  OpenClaw Docker container, updating OpenClaw, or enabling sandbox/extensions. Trigger even
  if the user just says "openclaw" without an explicit config request — they almost certainly
  need guidance on configuration.
---

# OpenClaw Docker Configuration Guide

OpenClaw is a self-hosted personal AI gateway that runs as a Docker container. It connects messaging platforms (Telegram, Discord, WhatsApp, Signal, iMessage, Slack, MS Teams) to AI providers (Anthropic, OpenAI, OpenRouter, Ollama, DeepSeek, vLLM, etc.).

- **Official repo:** https://github.com/openclaw/openclaw
- **Docs:** https://docs.openclaw.ai
- **Docker image:** `ghcr.io/openclaw/openclaw` (tags: `main`, `latest`, `<version>`)

---

## Installation

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh
```

To use a pre-built image instead of building locally (faster):
```bash
export OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw:main
./docker-setup.sh
```

The setup script builds the image, runs the interactive onboarding wizard, and starts the gateway daemon.

### docker-compose services

| Service | Purpose |
|---|---|
| `openclaw-gateway` | Main daemon — port 18789 |
| `openclaw-cli` | Management CLI — run one-off commands |

All management commands use:
```bash
docker compose run --rm openclaw-cli <command>
```

---

## Configuration File: `~/.openclaw/openclaw.json`

The primary config file is `~/.openclaw/openclaw.json`, written in **JSON5** format (allows comments and trailing commas). It is mounted into the container at `/home/node/.openclaw/openclaw.json`.

### Top-level structure

```json5
{
  "meta": { /* version/timestamps, managed by openclaw */ },
  "gateway": { /* port, bind, auth */ },
  "agents": { /* model defaults, concurrency, workspace */ },
  "models": { /* provider API keys and model specs */ },
  "channels": { /* messaging platform integrations */ },
  "skills": { /* skill/plugin system */ },
  "cron": { /* scheduled tasks */ },
  "tools": { /* tool config */ },
  "session": { /* conversation history/context */ },
  "env": { /* inline env var definitions */ }
}
```

### Gateway settings

Controls how the daemon listens and authenticates.

```json5
"gateway": {
  "port": 18789,
  "mode": "local",
  "bind": "loopback",        // "loopback" = 127.0.0.1 only (safe default)
                              // "lan" = all interfaces (needed for LAN access)
  "auth": {
    "mode": "token",          // token-based auth
    "allowTailscale": true    // allow Tailscale device auth
  }
}
```

> **Security:** Keep `bind` set to `"loopback"` unless you specifically need LAN or remote access. Never expose port 18789 directly to the public internet. The gateway token (stored in `~/.openclaw/.env`) should be treated like a password.

To change bind mode via CLI:
```bash
docker compose run --rm openclaw-cli config set gateway.bind lan
docker compose run --rm openclaw-cli config get gateway.bind
```

### AI provider API keys

API keys go in the `models.providers` section. Use environment variable interpolation (`${VAR_NAME}`) to keep secrets out of the config file.

```json5
"models": {
  "providers": {
    "anthropic": { "apiKey": "${ANTHROPIC_API_KEY}" },
    "openai":    { "apiKey": "${OPENAI_API_KEY}" },
    "openrouter": { "apiKey": "${OPENROUTER_API_KEY}" }
  }
}
```

Environment variables are resolved in this order:
1. Process environment
2. `./.env` (current working directory)
3. `~/.openclaw/.env` ← **recommended place for secrets**
4. `env` block inside `openclaw.json`

Recommended: put API keys in `~/.openclaw/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### Agent defaults

Controls which model runs tasks and how many can run at once.

```json5
"agents": {
  "defaults": {
    "model": {
      "primary": "anthropic/claude-sonnet-4-5",
      "fallbacks": ["openai/gpt-4o", "anthropic/claude-haiku-3-5"]
    },
    "workspace": "~/.openclaw/workspace",
    "maxConcurrent": 4,
    "subagents": { "maxConcurrent": 8 },
    "contextTokens": 128000
  }
}
```

---

## Adding Messaging Channels

### Via CLI (recommended)

```bash
# Telegram
docker compose run --rm openclaw-cli channels add --channel telegram --token "<BOT_TOKEN>"

# For other channels, omit --token to enter interactive setup:
docker compose run --rm openclaw-cli channels add --channel discord
```

### Via openclaw.json directly

```json5
"channels": {
  "telegram": {
    "token": "${TELEGRAM_BOT_TOKEN}"
    // additional policies configurable here
  },
  "discord": {
    // guild-specific settings
  }
}
```

---

## Common Management Commands

```bash
# Check gateway status
docker compose run --rm openclaw-cli status

# Open the web dashboard (get URL + token)
docker compose run --rm openclaw-cli dashboard --no-open

# View logs
docker compose logs openclaw-gateway
docker compose logs openclaw-gateway --tail 100

# Restart the gateway
docker compose restart openclaw-gateway

# Health check
curl -fsS http://127.0.0.1:18789/healthz

# Diagnose configuration problems
docker compose run --rm openclaw-cli doctor
docker compose run --rm openclaw-cli doctor --fix

# Device/pairing management
docker compose run --rm openclaw-cli devices list
docker compose run --rm openclaw-cli devices approve <requestId>

# Stop everything
docker compose down

# Stop and remove volumes (full reset)
docker compose down -v
```

---

## Environment Variables (Docker build/runtime)

These are set in your shell before running `./docker-setup.sh` or `docker compose`:

| Variable | Purpose |
|---|---|
| `OPENCLAW_IMAGE` | Use a pre-built remote image (skip local build) |
| `OPENCLAW_SANDBOX` | Enable Docker-in-Docker agent sandbox (`1` or `true`) |
| `OPENCLAW_EXTRA_MOUNTS` | Extra bind mounts, comma-separated (e.g. `$HOME/.ssh:/home/node/.ssh:ro`) |
| `OPENCLAW_HOME_VOLUME` | Persist `/home/node` in a named Docker volume |
| `OPENCLAW_DOCKER_SOCKET` | Override Docker socket path |
| `OPENCLAW_EXTENSIONS` | Space-separated list of extensions to pre-install |
| `OPENCLAW_DOCKER_APT_PACKAGES` | Additional apt packages to install at build time |

Example with sandbox and extra mounts:
```bash
export OPENCLAW_IMAGE=ghcr.io/openclaw/openclaw:main
export OPENCLAW_SANDBOX=1
export OPENCLAW_EXTRA_MOUNTS="$HOME/.ssh:/home/node/.ssh:ro,$HOME/projects:/home/node/projects:rw"
./docker-setup.sh
```

---

## Updating OpenClaw

```bash
cd openclaw
git pull
./docker-setup.sh
```

This rebuilds the image and restarts the gateway with the latest code.

---

## Troubleshooting

| Symptom | What to try |
|---|---|
| Gateway won't start | `docker compose logs openclaw-gateway` — check for port conflicts or missing env vars |
| Can't reach dashboard | Check `gateway.bind` — must be `"lan"` for non-localhost access |
| API calls failing | Verify API keys in `~/.openclaw/.env`; check provider name matches exactly |
| Channel not responding | Re-run `channels add`; verify bot token is valid |
| General config issues | `docker compose run --rm openclaw-cli doctor --fix` |
| Permission errors on `~/.openclaw` | Ensure the directory is owned by your user: `chown -R $USER ~/.openclaw` |
