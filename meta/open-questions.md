# 产品出海市场分析开放问题

以下问题尚未冻结，不能在实现中自行假定。

| 问题 | 为什么重要 | 建议在何时决定 |
|---|---|---|
| 产品版本如何唯一标识的具体 ID 规则 | Slice 5 已确认需要 `ProductSubject` 与 `version_identifiers`，但具体 ID 生成、去重和版本合并规则还未实现 | 写 JSON Schema / validator 前 |
| HS 是用户输入、候选归类还是允许多候选并列 | 决定税费与出口管制的表达方式和校验门槛 | 税费 Skill 设计前 |
| 首批真实 Source Pack registry 的国家/地区和事实域范围 | Slice 10 已用美国、中国、越南做种子样例设计，但真实 registry 是否首批内置这些国家、是否纳入具体 URL 和维护责任仍需实现前决定 | Source Pack registry 实现前 |
| Google Trends、期货、贸易统计等数据如何实际采集与许可 | Slice 8 已定义采集口径和降级规则，但具体工具、授权、频率和可复现机制未实现 | 数据接入设计前 |
| 是否以及如何支持多目的国比较 | 影响 Brief、表格、成本和证据范围；当前 MVP 以单一具体目的国为准 | MVP 后评估 |
| 是否将内陆段、贸易术语、保险和目的地费用纳入第一期 | 会显著扩大物流与成本范围 | 物流 Skill 设计前 |
| 专业确认如何提示 | 需区分报关行、认证机构、主管机关、承运人和法律顾问的确认边界 | 用户体验与状态词冻结时 |
| 两个首批样本的剩余贸易/技术缺口 | Xing Heng 已缺 UN38.3/SDS/包装/起运；UNIQLO 已缺实物标签/BOM/规格/起运；这些决定能否从候选路径进入确定税费、运输和标签结论 | 启动端到端法规/税费/物流样本研究前 |
| `ProductMarketAnalysisGraph` 第一版是完全独立 schema，还是以扩展文件引用现有 Source/Observation schema | Slice 5 已决定新增独立图谱并复用 Source/Observation 思路，但具体 schema 组织方式需实现时定 | 写 schema 前 |
| 何时从文档设计转入代码实现 | Slice 6 已冻结实现顺序；是否开始写 schema、validator 和首批 fixtures 需要用户明确确认 | 用户决定“开始实现”时 |
| 第一轮代码是否纳入现有 `all` suite | Slice 6 建议先独立 market suite，稳定后再并入现有 `all`，避免破坏当前 662/662 稳定状态 | Code Slice C/F 实现时 |
| 是否先提交 Slice 1-12 文档，还是直接开始 Code Slice A-C | Slice 12 已完成 MVP 收口；文档和代码分开提交更清楚，但是否立即提交需要用户确认 | 开始写代码前 |

## 已在 2026-07-28 Code Slice AC 初版冻结的问题

| 问题 | 当前决定 | 后续仍可细化 |
|---|---|---|
| 法规与关税记录的默认复核周期 | 已在 `spec/32-superleads-freshness-code-slice-ac.md` 冻结首版 freshness 窗口：近期外部因素 14 天；进口税费 / 出口要求 / 线上价格 30 天；Google Trends / 物流 90 天；目的国认证准入 / COO 180 天；市场报告 / 季节窗口 365 天。 | Authority registry 可以按国家、机构、来源类型和货物属性覆盖首版默认窗口。 |
