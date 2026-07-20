# Superleads

**中文（GitHub 首页）** | [English](README.en.md)

> 让 Agent 按证据做客户开发，而不是交付一份无法复查的黑箱名单。

Superleads 是面向传统外贸和 B2B 出口业务的客户开发与客户背调 Skill Suite。它帮助 Claude、Codex、ChatGPT app 和 Hermes 按可控流程完成找客户、查客户、整理客户资料，避免把来源不明或未经核实的信息直接当作销售结论。

## 你会得到什么

- **开发海外客户**：按产品、目标国家、渠道和客户类型寻找进口商、经销商、批发商、零售商、品牌商、项目客户或 OEM 客户。
- **客户背调**：核对公司、品牌、官网、实际业务、产品匹配、公开联系人与联系方式；识别同名公司、错配官网、竞争对手和风险项。
- **可跟进的客户表**：整理为 Excel 或 CSV，包含客户资料、官网和来源链接、公开联系方式、开发建议、优先级、待核实事项和风险说明。
- **补全已有名单**：读取你已有的客户表、官网、目录或展会名录，保留原始信息后再去重、补充和复核。

## 适合谁

- 传统外贸工厂、出口贸易公司、外贸 SOHO、品牌出海团队和 B2B 销售团队。
- 正在开发进口商、经销商、批发商、零售连锁、品牌客户、项目客户或 OEM 客户的人。
- 不只想要一串公司名称，而是要知道下一步联系谁、为什么联系、哪些信息仍需人工确认的人。

## 为什么不再是黑箱

Superleads 要求 Agent 区分已核实信息与待确认线索，并保留公开资料的来源、联系人归属和客户优先级的判断依据。资料不足时，结果会被标为候选或待核实，而不是把猜测包装成事实。

因此，你可以复查客户开发过程、接手未完成的背调、删掉不可靠客户，并把可用资料交给销售继续跟进。

## 支持的 Agent

- **Claude Code**：作为 Claude Code 插件使用。
- **Codex CLI 和 Codex app**：作为 Codex 插件使用。
- **ChatGPT app**：使用已安装的 Codex 环境，无需重复安装一份 Superleads。
- **Hermes**：作为完整的本地 Skill 包使用。

## 开始使用

你不需要懂 Git、终端或 marketplace。打开你正在使用的 Agent，新开一个对话，复制对应文字并允许它执行安装操作即可。若 Agent 没有安装权限，它应明确告诉你需要确认哪一项权限，而不是让你自己猜命令。

### Claude Code

```text
请为我完成 Superleads 的官方安装。使用官方仓库 https://github.com/fleixweb/superleads 添加 Superleads marketplace，然后安装 superleads@superleads-dev。完成后确认 Superleads 已启用。若安装需要系统权限，请先告诉我要确认什么；不要修改我的项目文件。
```

### Codex CLI 或 Codex app

```text
请为我在当前 Codex 环境安装 Superleads。使用官方仓库 https://github.com/fleixweb/superleads 添加 Superleads marketplace，然后安装 superleads@superleads-dev。完成后确认已启用。若需要系统权限，请先说明需要我确认什么；不要修改我的项目文件。
```

### ChatGPT app

先按上面的 Codex 方式完成一次安装，无需再单独安装。之后在 ChatGPT app 新开对话，直接说：

```text
请使用 Superleads 帮我做海外客户开发或客户背调，并保留来源、待核实项和判断依据。
```

### Hermes

```text
请把官方仓库 https://github.com/fleixweb/superleads 作为完整的 Superleads Skill 包安装到当前 Hermes profile 的 Skills 目录。不要把它当作 Hermes Python plugin 安装，也不要只复制其中一个 SKILL.md。安装后确认 using-superleads 等 Superleads Skills 可以被识别；若需要权限，请先说明。
```

## 第一次提需求

安装后，可以直接这样说：

```text
我要开发 [产品] 在 [国家/地区] 的 [客户类型]。优先寻找 [渠道或特征]，不纳入 [排除条件]。请用 Superleads 输出可跟进的客户表，保留官网、来源、公开联系方式、开发建议和待核实项；不要把未核实线索当成事实。
```

## 更新

不需要自己执行 Git 更新。在原来的 Agent 中复制下面这段即可：

```text
请检查 Superleads 官方仓库 https://github.com/fleixweb/superleads 是否有新版本；如有，请按当前安装方式更新，并告诉我更新后的版本，以及是否需要重启或新开对话才能生效。不要修改我的项目文件。
```

想收到发布通知，请在本仓库点 **Watch -> Custom -> Releases**。

## 许可与发布

Superleads 使用 [PolyForm Noncommercial 1.0.0](LICENSE) 许可证。使用、复制、修改和分发都应遵守许可证；涉及商业用途、再销售、托管服务或纳入收费交付前，请先按许可证核对边界并联系 Fleix。

正式版本以 Git tag 发布。普通用户只需按当前 Agent 的安装和更新方式使用即可。

## 问题反馈

扫描下方微信二维码添加 Fleix，反馈 Superleads 的安装、使用、客户开发或客户背调问题。

**添加好友时请备注：`Superleads反馈`。未备注该来意的好友申请不予通过。**

<img src="assets/wechat-feedback-qr.png" alt="Fleix 微信反馈二维码" width="260">

## 技术资料

- [技术安装与更新说明（中文）](docs/INSTALL-AND-UPDATE.md)
- [Technical installation and update guide (English)](docs/INSTALL-AND-UPDATE.en.md)
