# Superleads

**中文（GitHub 首页）** | [English](README.en.md)

> 让外贸人利用 Agent 做客户开发、客户背调和产品出海市场分析时，避免 LLM 大模型幻觉，让结果更可靠。

Superleads 是面向传统外贸和国际 B2B 贸易的业务情报 Skill Suite。它帮助外贸人用 Claude、Codex、ChatGPT app 和 Hermes 按可控流程完成三类工作：批量客户开发、单一客户背调、产品出海市场分析。所有输出都要求区分已核实信息、候选线索、待确认事项和未执行模块，避免把来源不明或未经核实的信息直接当作销售结论。

## 你会得到什么

- **批量客户开发**：按产品、目标国家、渠道和客户类型寻找进口商、经销商、批发商、零售商、品牌商、项目客户、OEM 客户等传统外贸目标客户。
- **单一客户背调**：核对一个公司、品牌、官网、实际业务、产品匹配、公开联系人与联系方式；识别同名公司、错配官网、竞争对手和风险项。
- **产品出海市场分析**：围绕一个产品进入或出口到某个国家/地区，整理 Google Trends 长期搜索兴趣、公开市场资料、线上价格参考、季节/节假日、准入合规、原产地证明、进口税费、出口国要求、运输路线和近期外部因素。
- **可交付表格**：把结果整理为 Markdown、CSV 或 Excel；Markdown 适合在 Codex / ChatGPT app 对话里直接阅读，CSV / XLSX 适合销售团队复核、筛选和交接。
- **补全已有资料**：读取你已有的客户表、官网、产品手册、目录、展会名录或公开材料，保留原始信息后再去重、补充和复核。

## 三条路线怎么选

| 你想做什么 | 可以这样说 | 交付结果 | 不会替你做什么 |
|---|---|---|---|
| 批量客户开发 | “我要开发某产品在某国家的某类客户” | 候选客户池、公开业务信号、官网/来源、公开联系入口、待核查项 | 不把候选池包装成“必买客户”或采购概率 |
| 单一客户背调 | “帮我背调这个公司/品牌/网站” | 表格化客户背调报告：这是谁、公开业务、关联方、联系入口、注意事项、来源 | 不把公开线索写成采购意愿或采购负责人已确认 |
| 产品出海市场分析 | “分析某产品出口/进入某国家的趋势、价格、准入、税费、物流和 COO 要求” | 产品市场与准入矩阵：贸易前提、趋势/价格参考、法规门槛、税费、物流、待补材料 | 不判断是否值得进入、不推荐报价、不把候选税号写成最终税率 |

## 适合谁

- 传统外贸工厂、出口贸易公司、外贸 SOHO、品牌出海团队和 B2B 销售团队。
- 正在开发进口商、经销商、批发商、零售连锁、品牌客户、项目客户或 OEM 客户的人。
- 想在报价、开发或展会前先看清客户、产品、国家、准入、税费和物流边界的人。
- 不只想要一串公司名称，而是要知道下一步联系谁、为什么联系、哪些信息仍需人工确认的人。

## 为什么不再是黑箱

Superleads 要求 Agent 区分已核实信息与待确认线索，并保留公开资料的来源、联系人归属和判断依据。资料不足时，结果会被标为候选、待核实、来源受限或未执行，而不是把猜测包装成事实。

因此，你可以复查客户开发过程、接手未完成的背调、删掉不可靠客户，并把可用资料交给销售继续跟进。做产品出海市场分析时，系统也会把默认出口申报国、原产国/制造来源、实际起运地/起运港分开写清楚；目标国是否要求原产地证明会按公开权威来源判断，用户有没有现成证书只是材料状态，不反推法规要求。

## 支持的 Agent

- **Claude Code**：作为 Claude Code 插件使用。
- **ChatGPT / Codex app、Codex CLI**：共用同一次 Codex 环境安装，无需重复安装。
- **Hermes**：作为完整的本地 Skill 包使用。

## 开始使用

你不需要懂 Git、终端或 marketplace。打开你正在使用的 Agent，新开一个对话，复制对应文字并允许它执行安装操作即可。若 Agent 没有安装权限，它应明确告诉你需要确认哪一项权限，而不是让你自己猜命令。

### Claude Code

```text
请为我完成 Superleads 的官方安装。使用官方仓库 https://github.com/fleixweb/superleads 添加 Superleads marketplace，然后安装 superleads@fleix。完成后确认 Superleads 已启用。若安装需要系统权限，请先告诉我要确认什么；不要修改我的项目文件。
```

### ChatGPT / Codex app、Codex CLI

ChatGPT / Codex app 与 Codex CLI 共用同一次 Codex 环境安装，无需重复安装。

```text
请为我在当前 Codex 环境安装 Superleads。使用官方仓库 https://github.com/fleixweb/superleads 添加 Superleads marketplace，然后安装 superleads@fleix。完成后确认已启用。若需要系统权限，请先说明需要我确认什么；不要修改我的项目文件。
```

### Hermes

```text
请把官方仓库 https://github.com/fleixweb/superleads 作为完整的 Superleads Skill 包安装到当前 Hermes profile 的 Skills 目录。不要把它当作 Hermes Python plugin 安装，也不要只复制其中一个 SKILL.md。安装后确认 using-superleads 等 Superleads Skills 可以被识别；若需要权限，请先说明。
```

## 第一次提需求

安装后，可以直接这样说：

### 1. 批量客户开发

```text
我要开发 [产品] 在 [国家/地区] 的 [客户类型]。优先寻找 [渠道或特征]，不纳入 [排除条件]。请用 Superleads 输出可跟进的候选客户表，保留官网、来源、公开联系方式、开发切入点和待核实项；不要把未核实线索当成事实。
```

### 2. 单一客户背调

```text
帮我背调这个客户：[公司名/官网/品牌/邮箱/地址]。请用表格告诉我这是谁、公开在做什么、和哪些品牌或公司有关、哪里可以联系、跟进前要注意什么、信息从哪里来；不要把搜索摘要当成事实。
```

### 3. 产品出海市场分析

```text
请做 [产品/型号] 出口到 [目标国家/地区] 的产品出海市场分析。默认出口申报国是 [中国/其他国家]，原产国是 [已知则填写]，起运地是 [已知则填写]。请表格化整理 Google Trends、公开市场和价格参考、准入合规、COO/原产地证明、进口税费、出口国要求、物流路线/预申报和近期外部因素；只给客观参考，不判断是否值得进入。
```

## 输出与导出

普通用户可以直接让 Agent 在对话里输出 Markdown 表格。开发者或本地流程可以使用统一 Markdown 交付命令：

```bash
python3 scripts/export_superleads_markdown.py input.json --route auto --output report.md --format json
```

也可以显式指定路线：

```bash
python3 scripts/export_superleads_markdown.py input.json --route bulk_customer_development --output bulk-report.md --format json
python3 scripts/export_superleads_markdown.py input.json --route customer_background_research --output background-report.md --format json
python3 scripts/export_superleads_markdown.py input.json --route product_outbound_market_analysis --output market-report.md --format json
```

Markdown 交付器会先做用户可见输出检查，通过后才写文件。CSV / XLSX 适合表格交付和团队复核；常用命令见 [Superleads 常用命令](docs/superleads-common-commands.md)。

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

扫描下方微信二维码添加 Fleix，反馈 Superleads 的安装、使用、客户开发、客户背调或产品出海市场分析问题。

**添加好友时请备注：`Superleads反馈`。未备注该来意的好友申请不予通过。**

<img src="assets/wechat-feedback-qr.png" alt="Fleix 微信反馈二维码" width="260">

## 技术资料

- [技术安装与更新说明（中文）](docs/INSTALL-AND-UPDATE.md)
- [Technical installation and update guide (English)](docs/INSTALL-AND-UPDATE.en.md)
- [Superleads 常用命令](docs/superleads-common-commands.md)
