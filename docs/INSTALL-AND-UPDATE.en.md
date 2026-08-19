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

Claude Code applies an update after restart. Superleads does not make an automatic network version check when a session starts; updating does not affect other functionality.

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
The shared installation environment does not determine the runtime host; determine the Run host from the tools actually exposed in the current session.

### Lean Runtime Package For Local Development

### Python Dependencies (Cross-Platform)

Basic plugin use does not require the user to install Python dependencies. When
maintaining the source, running deterministic validation, or invoking formal
export scripts, use an isolated Superleads environment for the current platform.
Do not install globally or write the environment into a managed plugin cache.
`requirements.txt` pins the supported JSON Schema and export runtime.

macOS, Linux, or WSL:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

Do not substitute older dependencies provided temporarily by another application.

### Windows / Codex Desktop Runtime Dependencies

The lean runtime package includes its root `requirements.txt`. When maintaining
or testing an installed Codex Desktop runtime package on Windows, read that
file from the package root and prepare it in an **isolated Superleads
maintenance environment**; do not write the environment into a plugin cache
that can be refreshed:

```powershell
$runtimeRoot = Resolve-Path .\superleads
py -3 -m venv .\superleads-runtime-venv
& .\superleads-runtime-venv\Scripts\python.exe -m pip install -r "$runtimeRoot\requirements.txt"
```

Replace `$runtimeRoot` with the actual runtime package root. Do not search for,
borrow, or invoke Python / venv installations from another Agent, IDE, or
desktop application, and do not install packages globally. If `jsonschema` or
`referencing` is unavailable, formal deterministic validation and formal
Markdown delivery use the no-script path and carry the marker
`本环境未运行确定性校验`. When validation can run but `openpyxl` is unavailable,
`export_workbook.py --format auto` writes UTF-8-SIG CSV. Use `--format xlsx`
only when an XLSX file is explicitly required; that explicit request must not
silently downgrade.

When a local marketplace points at the source repository, Codex copies development
assets and historical UAT files into its cache. Before a local release or runtime
test, build the lean package, point the local Superleads marketplace source at the
artifact, then reinstall:

```bash
python3 scripts/build_superleads_plugin_package.py --format json
python3 scripts/check_superleads_plugin_distribution.py --plugin-root dist/superleads --source-root . --runtime-package --format json
ln -sfnT "$PWD/dist/superleads" "$HOME/plugins/superleads"
codex plugin add superleads@fleix
```

The artifact contains only the runtime manifest, Skills, scripts, shared
rules, and spec. It excludes `tmp/`, `evals/`, `tests/`, historical validation
documents, and Git metadata. Source `tmp/stage5_chillys/` remains in place. The
symlink command assumes a Linux/macOS local marketplace source at
`$HOME/plugins/superleads`; adapt it to the registered local source path otherwise.

### Migrate From 0.1.2 Or Earlier

Starting with `0.1.3`, the marketplace name changes from `superleads-dev` to `fleix`; the plugin identifier is now `superleads@fleix`. Existing Codex users need this one-time migration:

```bash
codex plugin marketplace remove superleads-dev
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
```

Claude Code users should remove the former `superleads-dev` marketplace or plugin through `/plugin`, then add the official marketplace and install `superleads@fleix`. Do not assume that every Claude Code version has the same command-line removal syntax.

If an initial installation uses a local ZIP snapshot or local directory because GitHub is unreachable, that source is one-time only and cannot receive GitHub updates through `codex plugin marketplace upgrade`. Once the network works again, remove the local marketplace and add the official Git source above.

### Check For Updates On Demand

Superleads does not use the network when a session starts or resumes, or for help, current-version, or installed-status requests. Only an explicit update request, `@superleads update`, or a request for the Superleads GitHub version may read the project's official public version source. The check reads only the host-supplied active plugin manifest; when the host supplies a session cache, it can reuse a remote result in that session, and only an explicit refresh may fetch again. It never scans old caches, backups, or temporary directories. If the remote source is unavailable, times out, or returns an invalid response, the result is only "Unable to confirm the remote version this time"; it never reports that the installed version is current by mistake or sends user, project, or prompt data.

GitHub Releases is the preferred stable source. A fixed tag manifest is labeled only as a tag version, while a `master` manifest is labeled only as a repository version and never as the latest stable release.

The source tree and runtime package contain no SessionStart, resume, or automatic remote-update hook. GitHub **Watch -> Custom -> Releases** remains an available release-notification option.

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
- Superleads does not make a remote version check when a Claude Code or Codex session starts.
