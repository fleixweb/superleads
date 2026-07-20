# Superleads Technical Installation And Update Guide

[中文](INSTALL-AND-UPDATE.md)

This document is for technical staff, IT support, or an Agent performing deployment. Ordinary foreign-trade users should use the natural-language installation request in [README.md](../README.md) and do not need to run these commands.

Official repository: `https://github.com/fleixweb/superleads`  
Plugin identifier: `superleads@superleads-dev`

## Pre-Publication Check

Do not give the GitHub commands below to end users before this repository is public. The publisher should first confirm that:

1. The GitHub repository is `fleixweb/superleads` and its default branch is `main`.
2. Claude Code and Codex can both read the marketplace from the public repository.
3. The marketplace-installed version matches `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`.

## Claude Code

Install:

```bash
claude plugin marketplace add fleixweb/superleads
claude plugin install superleads@superleads-dev
claude plugin list
```

Update:

```bash
claude plugin update superleads@superleads-dev
```

Claude Code applies an update after restart. The optional version banner runs directly on macOS. On Windows it needs working `bash` and `curl`, normally supplied by Git Bash from Git for Windows. An unavailable banner does not affect Superleads; deleting the repository `hooks/` directory does not affect other functionality.

## Codex CLI And Codex App

Install:

```bash
codex plugin marketplace add fleixweb/superleads
codex plugin add superleads@superleads-dev
codex plugin list --marketplace superleads-dev
```

Refresh the marketplace, then reinstall the plugin to update:

```bash
codex plugin marketplace upgrade superleads-dev
codex plugin add superleads@superleads-dev
```

In the Codex app, use `/plugins` to add the same marketplace and install `superleads@superleads-dev`. Start a new chat after installing or updating so the new Skills are loaded.

Under the current distribution design, the ChatGPT app uses the same installed Codex environment and has no separate Superleads installation entry.

## Hermes

Superleads is a multi-Skill package, not a Hermes Python plugin. Preserve the complete repository structure so Hermes can discover `skills/*/SKILL.md`.

macOS, Linux, or WSL:

```bash
git clone https://github.com/fleixweb/superleads.git ~/.hermes/skills/superleads
hermes skills list --source local
```

Windows PowerShell:

```powershell
git clone https://github.com/fleixweb/superleads.git "$HOME\.hermes\skills\superleads"
hermes skills list --source local
```

Update:

```bash
git -C ~/.hermes/skills/superleads pull --ff-only
```

Windows PowerShell update:

```powershell
git -C "$HOME\.hermes\skills\superleads" pull --ff-only
```

Start a new Hermes chat after updating. Do not use `hermes plugins install`: that command is for Hermes plugins with a `plugin.yaml` and Python entry point, not Superleads.

## Version Notifications

- The simplest release notification is **Watch -> Custom -> Releases** in the GitHub repository.
- Claude Code's optional session-start banner makes one anonymous GET to the public manifest. Set `SUPERLEADS_DISABLE_UPDATE_CHECK=1` or `DISABLE_TELEMETRY=1` to disable it.
