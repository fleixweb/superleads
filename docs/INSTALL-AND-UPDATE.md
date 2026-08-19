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

Claude Code 要在重启后应用更新。Superleads 不会在会话启动时自动联网检查版本；更新不会影响其它功能。

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
共享安装环境不等于相同的运行时宿主；Run 的宿主身份应按当前会话实际暴露的工具判定。

### 本地开发的精简运行时包

### WSL Python 依赖

校验和正式 Markdown 导出应在 WSL 的隔离环境中运行，不依赖桌面 Python：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` 固定支持的 JSON Schema 运行时；不要用桌面环境临时安装的旧版
`jsonschema` 代替它。

### Windows / Codex Desktop 运行时依赖

精简运行时包会携带根目录 `requirements.txt`。在 Windows 上维护或测试已安装的
Codex Desktop 运行时包时，从包含该文件的包根目录读取依赖清单，并在**专用于
Superleads 的隔离维护环境**中准备它；不要把环境写入可能被刷新掉的插件缓存：

```powershell
$runtimeRoot = Resolve-Path .\superleads
py -3 -m venv .\superleads-runtime-venv
& .\superleads-runtime-venv\Scripts\python.exe -m pip install -r "$runtimeRoot\requirements.txt"
```

将 `$runtimeRoot` 替换为实际运行时包根目录。不要搜索、借用或调用其他 Agent、IDE
或桌面应用自带的 Python / venv；也不要做全局安装。缺少 `jsonschema` 或
`referencing` 时，正式确定性校验与 Markdown 正式导出走无脚本路径，并标注
“本环境未运行确定性校验”。在校验可运行但缺少 `openpyxl` 时，
`export_workbook.py --format auto` 会输出 UTF-8-SIG CSV；只有明确必须生成 XLSX
时才使用 `--format xlsx`，该显式请求不会静默降级。

本地 marketplace 若指向源码目录，Codex 会把开发资料和历史 UAT 一并复制到缓存。发布
前或本地联调时，先在源码根目录构建精简运行时包，再让本地 marketplace 的 Superleads
source 指向该工件，最后重新安装：

```bash
python3 scripts/build_superleads_plugin_package.py --format json
python3 scripts/check_superleads_plugin_distribution.py --plugin-root dist/superleads --source-root . --runtime-package --format json
ln -sfnT "$PWD/dist/superleads" "$HOME/plugins/superleads"
codex plugin add superleads@fleix
```

工件只包含运行时所需的 manifest、Skills、scripts、shared 规则和 spec；不包含
`tmp/`、`evals/`、`tests/`、历史验证文档或 Git 元数据。保留源码 `tmp/stage5_chillys/`，
它不会被移动或删除。上面的软链接命令适用于本机 marketplace 已注册为
`$HOME/plugins/superleads` 的 Linux/macOS 布局；其它本地路径应改为对应的 marketplace source。

### 从 0.1.2 或更早版本迁移

`0.1.3` 起，marketplace 名称由 `superleads-dev` 更改为 `fleix`，插件标识随之变为 `superleads@fleix`。已安装旧版本的 Codex 用户执行一次：

```bash
codex plugin marketplace remove superleads-dev
codex plugin marketplace add fleixweb/superleads --ref master
codex plugin add superleads@fleix
```

Claude Code 用户请在 `/plugin` 中移除旧的 `superleads-dev` marketplace 或插件，再添加官方 marketplace 并安装 `superleads@fleix`。不要假定不同 Claude Code 版本存在相同的命令行移除语法。

如果初次安装因网络问题改用本地 ZIP 快照或本地目录注册 marketplace，该来源只能用于一次性安装，不能通过 `codex plugin marketplace upgrade` 获得 GitHub 更新。网络恢复后，应移除该本地 marketplace，再使用上面的官方 Git 来源重新添加。

### 按需检查更新

Superleads 不会在会话启动、恢复、帮助、当前版本或已安装状态查询时联网。只有用户明确要求“检查更新”、`@superleads update` 或查询 Superleads 的 GitHub 版本时，宿主才可以读取项目官方公开版本来源。检查只读取宿主明确提供的激活插件目录中的本地 manifest；若宿主提供会话缓存，可在同一会话复用远端检查结果，用户明确要求刷新时才重新请求。不会扫描旧缓存、备份或临时目录。远端不可达、超时或返回异常时，只会显示“本次未能确认远端版本”，不会误报已经是最新版本，也不会发送用户、项目、prompt 数据。

优先来源是 GitHub Releases 的稳定发布。固定 tag 的 manifest 只标为标签版本，`master` 分支 manifest 只标为仓库版本，不会称为“最新稳定版”。

当前源码和运行时包均不包含 SessionStart、resume 或自动远端更新 hook。GitHub 的 **Watch -> Custom -> Releases** 仍可用于接收发布通知。

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
- Superleads 不会在 Claude Code 或 Codex 的会话启动时执行远端版本检查。
