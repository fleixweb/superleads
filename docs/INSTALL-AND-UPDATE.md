# Superleads 技术安装与更新说明

[English](INSTALL-AND-UPDATE.en.md)

本文给协助部署的技术人员、IT 同事或 Agent 使用。普通外贸用户请直接使用 [README.md](../README.md) 中的自然语言安装请求，不必执行本页命令。

官方仓库：`https://github.com/fleixweb/superleads`  
插件标识：`superleads@fleix`

## 发布前检查

本仓库公开到 GitHub 前，不要把以下 GitHub 命令交给最终用户。发布者应先确认：

1. GitHub 仓库地址为 `fleixweb/superleads`，默认分支为 `master`。
2. Claude Code 和 Codex 的 marketplace 均能从公开仓库读取。
3. marketplace 安装后的版本与 `.codex-plugin/plugin.json` 及 `.claude-plugin/plugin.json` 一致。

## Claude Code

安装：

```bash
claude plugin marketplace add fleixweb/superleads
claude plugin install superleads@fleix
claude plugin list
```

更新：

```bash
claude plugin update superleads@fleix
```

Claude Code 要在重启后应用更新。若启用了可选的版本横幅，macOS 可直接运行；Windows 需要可用的 `bash` 与 `curl`，通常由 Git for Windows 的 Git Bash 提供。横幅不可用不会影响 Superleads；删除仓库中的 `hooks/` 也不会影响其它功能。

## Codex CLI 与 Codex app

安装：

```bash
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
codex plugin list --marketplace fleix
```

更新 marketplace 后重新安装该插件：

```bash
codex plugin marketplace upgrade fleix
codex plugin add superleads@fleix
```

Codex app 可通过 `/plugins` 添加同一 marketplace，再安装 `superleads@fleix`。该 GitHub 仓库的默认分支为 `master`；安装或更新后，请新开一个对话以加载新的 Skills。

按当前产品分发方式，ChatGPT app 使用同一已安装的 Codex 环境，不设独立的 Superleads 安装入口。

### 从 0.1.2 或更早版本迁移

`0.1.3` 起，marketplace 名称由 `superleads-dev` 更改为 `fleix`，插件标识随之变为 `superleads@fleix`。已安装旧版本的 Codex 用户执行一次：

```bash
codex plugin marketplace remove superleads-dev
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
```

Claude Code 用户请在 `/plugin` 中移除旧的 `superleads-dev` marketplace 或插件，再添加官方 marketplace 并安装 `superleads@fleix`。不要假定不同 Claude Code 版本存在相同的命令行移除语法。

如果初次安装因网络问题改用本地 ZIP 快照或本地目录注册 marketplace，该来源只能用于一次性安装，不能通过 `codex plugin marketplace upgrade` 获得 GitHub 更新。网络恢复后，应移除该本地 marketplace，再使用上面的官方 Git 来源重新添加。

### 可选版本提醒

Superleads 在 Codex 支持插件 hooks 的环境中，启动或恢复会话时会读取本地版本，并对 `master` 分支中的公开 manifest 发起一次匿名 GET。远端版本更高时才显示一行更新提示；3 秒超时、无网络或检查过程中的其他错误都会静默跳过，不会阻塞会话，也不会写入磁盘或发送用户、项目、prompt 数据。

Codex 首次发现此 hook 时会要求用户在 `/hooks` 审核并信任；未信任前不会运行。可通过环境变量 `SUPERLEADS_DISABLE_UPDATE_CHECK=1` 或 `DISABLE_TELEMETRY=1` 关闭，也可在 `/hooks` 中禁用。删除已安装插件内的 `hooks/codex-hooks.json` 也可关闭它，不影响 Skills；下次更新会恢复该可选文件。若当前 Codex host 未执行插件 hooks，GitHub 的 **Watch -> Custom -> Releases** 仍是可靠的发布通知方式。

## Hermes

Superleads 是一个多 Skill 包，不是 Hermes Python plugin。必须保留完整仓库结构，让 Hermes 发现其中的 `skills/*/SKILL.md`。

macOS、Linux 或 WSL：

```bash
git clone https://github.com/fleixweb/superleads.git ~/.hermes/skills/superleads
hermes skills list --source local
```

Windows PowerShell：

```powershell
git clone https://github.com/fleixweb/superleads.git "$HOME\.hermes\skills\superleads"
hermes skills list --source local
```

更新：

```bash
git -C ~/.hermes/skills/superleads pull --ff-only
```

Windows PowerShell 更新：

```powershell
git -C "$HOME\.hermes\skills\superleads" pull --ff-only
```

更新后新开 Hermes 对话。不要使用 `hermes plugins install`：该命令用于带 `plugin.yaml` 和 Python 入口的 Hermes 插件，不适用于 Superleads。

## 版本通知

- 最简单的更新通知：在 GitHub 仓库点 **Watch -> Custom -> Releases**。
- Claude Code 和 Codex 的可选启动横幅只对公开 manifest 做一次匿名 GET；可设置 `SUPERLEADS_DISABLE_UPDATE_CHECK=1` 或 `DISABLE_TELEMETRY=1` 关闭。
