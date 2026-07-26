# 当前 Bet：产品出海市场分析产品合同

## 目标

将已确认的产品边界冻结为一份可实施、可评测的产品合同，先验证通用品类世界模型和证据边界，再讨论代码与 Skill 实现。

## 本轮范围

- 明确输入、输出、信息状态、证据层级、六个 Skill 的职责与互证规则。
- 覆盖常规货物、拼箱、国际快递、空运、铁路、公路、散货、散杂、滚装、冷链、危化等贸易现实。
- 用两条已确认的高差异贸易路径作为首批参数化验收样本：越南原产锂电产品出口美国、中国原产纺织品出口美国。
- 基于 Xing Heng / UNIQLO 两个真实样本，冻结第一版表格化输出矩阵与端到端验收断言。
- 冻结 XLSX/CSV 工作簿表名、字段顺序、状态枚举、空值保留规则和两个样本的最小样例矩阵。
- 冻结证据边界校验规则，明确候选、测试报告、网页信息、税率列示、运输方式等不得升级为最终结论。
- 冻结 Skill 分工互证流程，明确六个 Skill 的输入、输出、证据卡、互证矩阵、打回规则和交付门禁。
- 冻结数据模型与 eval 夹具设计，明确未来独立图谱、证据卡、状态流转、Skill 交接、工作簿映射和首批 pass/fail fixture。
- 冻结实现前执行计划，明确后续代码实现应按 schema、validator、fixtures、audit、export、eval 集成、Skill 接入、真实来源接入分步推进。
- 冻结 Skill 文案与用户入口设计，明确用户怎么触发、系统怎么首轮回应、怎么追问、怎么避免误路由到客户开发或单客背调。
- 冻结真实来源采集策略，明确各事实域来源优先级、能力门槛、Query Plan、Source/Observation 记录、“最新”口径、Source Pack 和降级规则。
- 冻结 Source Pack 字段合同，明确 Pack 只是来源入口目录，不是事实库，并定义 SourcePack、SourceEntry、QueryTemplate、ObservationRequirement、PackRouteRule 的字段、状态、路由和禁止升级规则。
- 冻结 Source Pack 种子样例设计，用美国 / 中国 / 越南 + Xing Heng / UNIQLO 两个样本说明首批 Pack、Entry、QueryTemplate、RouteRule 和 ObservationRequirement 如何组织，但不填事实结论。
- 冻结端到端运行剧本，明确 Brief -> Source Pack -> Query Plan -> Source/Observation -> EvidenceCard -> MatrixRow -> 交付的状态流转、门禁、打回、降级和两个样本剧本。
- 冻结 MVP 收口与实现前边界，明确第一轮只做防错闭环，优先 Code Slice A-C，必要时扩到 A-E，不接真实来源和国家库。

## 不在本轮范围

- 编写或修改 Skill、脚本、JSON Schema、导出器、测试或插件版本。
- 接入付费数据、承运人 API、海关 API、自动监测、提醒或报价计算器。
- 创建真实国家/地区 Source Pack 数据库或内置具体 URL 清单。
- 冻结任何具体国家、产品或法规的事实结论。
- 执行 git 提交；是否先提交 Slice 1-12 文档需用户另行确认。

## 不可接受的结果

- 将出口申报国、原产国、实际起运国和目的国混为一个“出口国”。
- 用搜索摘要、模型记忆、付费报告摘要或前序 Skill 的摘要充当事实来源。
- 用固定行业分类假定产品属性、合规、税率或运输方式。
- 将平台卖家、零售、电商、礼品或项目渠道自动变成批量客户开发范围。
- 输出“建议进入”“值得开发”“市场潜力高”“最佳运输方式”等价值判断。

## 完成标准

- `spec/10-product-outbound-market-analysis-contract.md` 明确所有已确认的外部契约与边界。
- 有明确的开放问题和决策记录，未确认事项不伪装为已冻结范围。
- 两条参数化验收样本都能用合同检查其输入缺口、触发路径和交付矩阵；未提供的产品参数不得被模型补猜。
- `spec/12-product-outbound-market-analysis-output-matrix-and-acceptance.md` 明确对话展示、XLSX/CSV 工作表、状态词、两个样本的正向/负向验收断言。
- `spec/13-product-outbound-market-analysis-workbook-contract.md` 明确工作簿表结构、状态枚举、空值规则和最小行数要求。
- `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md` 明确证据类型、禁止升级规则、降级/阻断规则和两个样本的特定断言。
- `spec/15-product-outbound-market-analysis-skill-orchestration.md` 明确六个 Skill 如何分工、互证、打回、降级和表格化交付。
- `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md` 明确未来实现的数据对象、状态流转、证据覆盖规则、eval 分层、fixture 清单和错误码草案。
- `spec/17-product-outbound-market-analysis-implementation-plan.md` 明确实现顺序、首批最小代码切片、第一批 pass/fail fixture、错误码和开工前检查清单。
- `spec/18-product-outbound-market-analysis-skill-copy-and-user-entry.md` 明确产品出海市场分析的用户入口、触发词、非触发词、首轮回应、追问规则、未来 Skill 文案和路由草案。
- `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md` 明确真实来源采集流程、事实域来源优先级、能力降级、Source Pack 和两个样本的来源路径。
- `spec/20-product-outbound-market-analysis-source-pack-contract.md` 明确 Source Pack 字段合同、Pack 类型、来源入口、路由规则、产品触发标签、复核状态和禁止把 Pack 当事实的 eval / audit 规则。
- `spec/21-product-outbound-market-analysis-source-pack-seed-samples.md` 明确首批 Source Pack 种子样例、种子 Entry / QueryTemplate / RouteRule / ObservationRequirement、两个样本路由演示和负向事实清单。
- `spec/22-product-outbound-market-analysis-end-to-end-runbook.md` 明确端到端人工运行剧本、三道门禁、状态流转、Skill 交接、两个样本剧本、Mermaid 图、报告骨架和 E2E 验收断言。
- `spec/23-product-outbound-market-analysis-mvp-freeze.md` 明确 MVP 分层、第一轮代码切片、非目标、fixture / 错误码、验收命令、提交边界和开工前检查清单。
