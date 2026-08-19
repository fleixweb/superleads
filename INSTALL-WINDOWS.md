# Superleads Windows 本地安装

本文用于安装包含 `fleix` marketplace 注册文件的 Superleads ZIP 包。安装完成后的插件标识应为：

```text
superleads@fleix
```

不要把 ZIP 文件直接作为 marketplace 路径，也不要手工复制文件到 Codex 的插件缓存目录。

## 安装结构

Windows 上涉及三个不同位置：

1. ZIP 文件：仅用于传输，可以放在桌面。
2. Marketplace 源目录：ZIP 解压后的稳定目录，供 Codex 注册和后续重装使用。
3. 插件缓存：由 Codex 自动生成和管理，不要手工修改。

建议把 marketplace 源目录放在：

```text
C:\Users\<你的用户名>\CodexMarketplaces\fleix-superleads
```

桌面不是必需的安装位置。若把解压目录留在桌面，它只是 marketplace 源目录，不是活动插件缓存。

## 1. 解压安装包

先关闭正在使用 Superleads 的 Codex 或 ChatGPT Desktop 会话。

在文件资源管理器中，将类似下面的安装包：

```text
superleads-fleix-marketplace-0.2.2-8c15e20.zip
```

解压到一个稳定目录，例如：

```text
C:\Users\<你的用户名>\CodexMarketplaces\fleix-superleads
```

解压后，找到直接包含以下文件和目录的那一层，并把该目录作为后续命令中的 `<MARKETPLACE_ROOT>`：

```text
.agents\plugins\marketplace.json
.claude-plugin\marketplace.json
.codex-plugin\plugin.json
skills\
scripts\
shared\
spec\
requirements.txt
```

例如，若这些文件位于：

```text
C:\Users\<你的用户名>\CodexMarketplaces\fleix-superleads\superleads-fleix-marketplace-0.2.2-8c15e20
```

则这个完整目录才是 `<MARKETPLACE_ROOT>`。不要使用它的上一级目录，也不要使用 ZIP 文件路径。

## 2. 确认 Marketplace 身份

在 PowerShell 中执行：

```powershell
$MarketplaceRoot = "$env:USERPROFILE\CodexMarketplaces\fleix-superleads\superleads-fleix-marketplace-0.2.2-8c15e20"
Get-Content "$MarketplaceRoot\.agents\plugins\marketplace.json"
```

确认输出中包含：

```json
"name": "fleix"
```

同时确认以下文件存在：

```powershell
Test-Path "$MarketplaceRoot\.agents\plugins\marketplace.json"
Test-Path "$MarketplaceRoot\.codex-plugin\plugin.json"
```

两条命令都应返回 `True`。

## 3. 注册并安装

在同一个 PowerShell 窗口中执行：

```powershell
codex plugin marketplace add "$MarketplaceRoot"
codex plugin add superleads@fleix
```

不要使用下面的安装选择器：

```text
superleads@personal
```

`personal` 是 Windows 默认个人 marketplace 的名称，不是 Superleads 的作者或官方 marketplace 名称。

## 4. 移除旧的 Personal 安装

确认 `superleads@fleix` 安装成功后，再执行：

```powershell
codex plugin remove superleads@personal
```

如果系统提示 `superleads@personal` 不存在，可以忽略该提示。不要手工编辑：

```text
C:\Users\<你的用户名>\.codex\config.toml
C:\Users\<你的用户名>\.agents\plugins\marketplace.json
```

## 5. 验证安装

执行：

```powershell
codex plugin marketplace list
codex plugin list
```

应能看到 marketplace `fleix` 和插件：

```text
superleads@fleix
```

再检查配置：

```powershell
Select-String -Path "$env:USERPROFILE\.codex\config.toml" -Pattern 'superleads@(fleix|personal)'
```

预期保留：

```text
superleads@fleix
```

不应继续启用：

```text
superleads@personal
```

活动缓存应由 Codex 自动创建在类似位置：

```text
C:\Users\<你的用户名>\.codex\plugins\cache\fleix\superleads\0.2.2
```

可以用下面的命令查看实际版本目录：

```powershell
Get-ChildItem "$env:USERPROFILE\.codex\plugins\cache\fleix\superleads" -Directory
```

不要直接修改这个缓存目录。更新插件时应更新 marketplace 源，然后重新执行正式安装流程。

## 6. 重新启动

安装完成后：

1. 完全退出 Codex 或 ChatGPT Desktop。
2. 重新启动应用。
3. 新建一个会话。
4. 在插件列表中确认显示为 `superleads@fleix`。
5. 使用裸 `@Superleads` 检查静态引导是否正常显示。

旧会话可能继续使用安装前加载的插件与 Skill，不适合作为安装验收依据。

## 常见问题

### 显示为 `superleads@personal`

说明插件是从默认个人 marketplace 安装的。确认当前安装包内的 `.agents\plugins\marketplace.json` 包含 `"name": "fleix"`，然后重新执行：

```powershell
codex plugin marketplace add "$MarketplaceRoot"
codex plugin add superleads@fleix
codex plugin remove superleads@personal
```

### `marketplace add` 找不到注册文件

通常是 `$MarketplaceRoot` 指向了解压目录的上一级。它必须直接包含：

```text
.agents\plugins\marketplace.json
```

### ZIP 路径可以读取，但无法安装

这是正常的。`codex plugin marketplace add` 接收解压后的 marketplace 目录，不接收 ZIP 文件。

### 安装后仍显示旧版本

先确认使用的是新会话。如果仍未更新，执行：

```powershell
codex plugin remove superleads@fleix
codex plugin add superleads@fleix
```

不要通过覆盖 `plugins\cache` 目录来更新。

### 不确定当前装的是哪一份

执行：

```powershell
codex plugin list
Select-String -Path "$env:USERPROFILE\.codex\config.toml" -Pattern 'superleads@'
```

以 `superleads@fleix` 为正确安装结果。
