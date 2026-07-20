# Superleads Technical Installation And Update Guide

[中文](INSTALL-AND-UPDATE.md)

This document is for technical staff, IT support, or an Agent performing deployment. Ordinary foreign-trade users should use the natural-language installation request in [README.md](../README.md) and do not need to run these commands.

Official repository: `https://github.com/fleixweb/superleads`  
Plugin identifier: `superleads@fleix`

## Pre-Publication Check

Do not give the GitHub commands below to end users before this repository is public. The publisher should first confirm that:

1. The GitHub repository is `fleixweb/superleads` and its default branch is `master`.
2. Claude Code and Codex can both read the marketplace from the public repository.
3. The marketplace-installed version matches `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`.

## Claude Code

Install:

```bash
claude plugin marketplace add fleixweb/superleads
claude plugin install superleads@fleix
claude plugin list
```

Update:

```bash
claude plugin update superleads@fleix
```

Claude Code applies an update after restart. The optional version banner runs directly on macOS. On Windows it needs working `bash` and `curl`, normally supplied by Git Bash from Git for Windows. An unavailable banner does not affect Superleads; deleting the repository `hooks/` directory does not affect other functionality.

## Codex CLI And Codex App

Install:

```bash
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
codex plugin list --marketplace fleix
```

Refresh the marketplace, then reinstall the plugin to update:

```bash
codex plugin marketplace upgrade fleix
codex plugin add superleads@fleix
```

In the Codex app, use `/plugins` to add the same marketplace and install `superleads@fleix`. The GitHub repository's default branch is `master`. Start a new chat after installing or updating so the new Skills are loaded.

Under the current distribution design, the ChatGPT app uses the same installed Codex environment and has no separate Superleads installation entry.

### Migrate From 0.1.2 Or Earlier

Starting with `0.1.3`, the marketplace name changes from `superleads-dev` to `fleix`; the plugin identifier is now `superleads@fleix`. Existing Codex users need this one-time migration:

```bash
codex plugin marketplace remove superleads-dev
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
```

Claude Code users should remove the former `superleads-dev` marketplace or plugin through `/plugin`, then add the official marketplace and install `superleads@fleix`. Do not assume that every Claude Code version has the same command-line removal syntax.

If an initial installation uses a local ZIP snapshot or local directory because GitHub is unreachable, that source is one-time only and cannot receive GitHub updates through `codex plugin marketplace upgrade`. Once the network works again, remove the local marketplace and add the official Git source above.

### Optional Version Notice

Where Codex supports plugin hooks, Superleads reads the local version when a session starts or resumes and makes one anonymous GET of the public manifest on the `master` branch. It prints one update line only when a newer remote version is available. A 3-second timeout, no network, or any check failure is silent; it does not block the session, write to disk, or send user, project, or prompt data.

When Codex first discovers this hook, the user must review and trust it through `/hooks`; it does not run before that approval. Set `SUPERLEADS_DISABLE_UPDATE_CHECK=1` or `DISABLE_TELEMETRY=1` to disable it, or disable it in `/hooks`. Deleting `hooks/codex-hooks.json` from the installed plugin also disables the notice without affecting Skills; a later update restores that optional file. If the current Codex host does not execute plugin hooks, GitHub **Watch -> Custom -> Releases** remains the reliable release-notification path.

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
- Claude Code's and Codex's optional session-start banners make one anonymous GET to the public manifest. Set `SUPERLEADS_DISABLE_UPDATE_CHECK=1` or `DISABLE_TELEMETRY=1` to disable them.
