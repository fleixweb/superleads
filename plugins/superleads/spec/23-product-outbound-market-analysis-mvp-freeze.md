# 产品出海市场分析：MVP 收口与实现前冻结（Slice 12）

本文件把 Slice 1-11 收成第一版 MVP 实现边界。它不是代码，不联网，不新增真实来源，不计算任何税率、认证、价格、趋势或物流结论。

一句话冻结：**第一轮实现先做“防错闭环”，让系统能识别、拦截和导出边界正确的产品出海市场分析样本；不要一上来接真实搜索、关税、法规、Google Trends 或国家库。**

## 1. Slice 12 边界

| 项目 | 本轮决定 |
|---|---|
| 目标 | 汇总 Slice 1-11，冻结 MVP 范围、非目标、第一批代码切片、验收命令、提交边界和开工前检查清单 |
| 当前仍不做 | 不写代码、不新增 schema/validator/fixture、不改 Skill、不接真实来源、不提交 git |
| 适用对象 | 后续 Code Slice A-C / A-E、eval、audit、export、Skill 路由和交付验收 |
| 核心策略 | 先保证“不乱说”，再追求“说得多”；先静态 fixture，后真实来源采集 |

## 2. Slice 1-11 已冻结资产总表

| Slice | 已冻结内容 | 对实现的约束 |
|---|---|---|
| Slice 1 静态样例报告 | Xing Heng / UNIQLO 两份表格化 Markdown 样例 | 用户可见输出必须人话化、表格化、保留未知项 |
| Slice 2 工作簿合同 | 12 张 XLSX/CSV 表、字段顺序、状态枚举、空值规则 | 导出不能丢未执行行、不能用空白掩盖未知 |
| Slice 3 证据边界 | 候选、网页标签、QCVN、税率、物流、趋势等禁止升级规则 | validator / audit 必须拦截高风险错误 |
| Slice 4 Skill 分工互证 | 六个 Skill 的交接、互证、三道门禁、打回规则 | 后续 Skill 接入不能把前序摘要当事实 |
| Slice 5 数据模型与 eval | ProductMarketAnalysisGraph、EvidenceCard、状态流转、fixture 和错误码草案 | 第一轮代码应先实现最小 graph / validator / fixtures |
| Slice 6 实现计划 | Code Slice A-H，A-C 为首批最小实现 | 本文件延续该顺序，不提前接真实数据 |
| Slice 7 Skill 文案入口 | 用户入口、触发词、首轮追问、非价值判断表达 | 后续路由不能混成客户开发或单客背调 |
| Slice 8 真实来源策略 | 来源优先级、Query Plan、Source/Observation、“最新”口径 | 搜索摘要和 Pack 不能直接成事实 |
| Slice 9 Source Pack 字段合同 | SourcePack / Entry / QueryTemplate / ObservationRequirement / RouteRule | Pack 只是来源入口目录，不是事实库 |
| Slice 10 Source Pack 种子样例 | 美国/中国/越南、锂电、纺织、物流、市场信号种子样例 | 样例只含入口和边界，不含真实结论 |
| Slice 11 端到端剧本 | Brief -> Pack -> Query Plan -> Observation -> EvidenceCard -> MatrixRow -> 交付 | 实现要按状态流转和三道门禁推进 |

## 3. MVP 定义

第一版 MVP 不是“自动生成完整市场报告”，而是“可验证的安全骨架”。

| 层级 | 名称 | 目标 | 是否本轮实现优先 |
|---|---|---|---|
| MVP-0 | 防错闭环 | 静态 graph + schema + validator + pass/fail fixtures，能拦住禁止升级 | 第一优先 |
| MVP-1 | 安全交付骨架 | 在 MVP-0 基础上加 audit + Markdown/CSV 最小导出 | 第二优先 |
| MVP-2 | Skill 入口接入 | 接入用户入口、首轮追问、路由到产品市场分析流程 | MVP-0/1 稳定后 |
| MVP-3 | 真实来源采集 | 接搜索、打开来源、Source Pack registry、Google Trends、关税/法规/物流来源 | 暂不进入第一轮 |

建议下一步如果开始写代码，先做 **Code Slice A-C**。如果用户希望一次看到可导出结果，可扩到 **Code Slice A-E**，但仍不接真实搜索和真实国家库。

## 4. 第一轮实现只做什么

| Code Slice | 文件/入口 | 必做 | 不做 |
|---|---|---|---|
| A Schema 骨架 | `shared/schemas/product-market-analysis.schema.json` | ProductMarketAnalysisGraph 最小结构、必填字段、状态枚举 | 不建真实国家库，不写全量法规字段 |
| B 语义 validator | `scripts/validate_product_market_analysis.py` | 禁止升级、来源边界、状态流转、内部泄露、未执行保留 | 不联网判断真实税率/认证正确性 |
| C eval fixtures | `evals/cases/product_market_analysis_cases.json` + `evals/fixtures/market_*.json` | 首批 pass/fail fixture 与预期错误码 | 不一次写完所有国家/品类场景 |
| D audit 最小门禁 | `scripts/audit_product_market_analysis.py` | 判断可交付、需修正、缺资料、来源受限 | 不代替 validator 做事实推理 |
| E CSV/Markdown 最小导出 | 独立导出入口 | 12 张表/Markdown 分组，从 MatrixRow 搬运安全字段 | 不生成新事实，不补税率，不猜港口 |

## 5. 第一轮明确不做什么

| 不做 | 原因 | 以后何时做 |
|---|---|---|
| 不接 Google Trends 实时采集 | 先确保 Trends 不会被误写成销量 | MVP-3 真实来源采集 |
| 不接关税 API / 官方税则实时查询 | 先确保候选税号不被写成最终税率 | MVP-3，且需来源日期和归类条件 |
| 不写真实 Source Pack registry | 先实现 Pack 不能当事实的边界 | MVP-3 前后分阶段接入 |
| 不做国家逐一硬编码 | 要按 Pack / Entry / QueryTemplate 扩展 | Source Pack registry 设计后 |
| 不改批量客户开发和单客背调主流程 | 避免破坏现有稳定链路 | 产品市场分析独立稳定后再考虑路由集成 |
| 不生成客户名单、目标客户类型或进入建议 | 超出本模块边界 | 需要客户名单时走批量客户开发路线 |
| 不清理 `tmp/stage5_chillys/` | 项目明确要求保留 | 除非用户明确要求整理或清理 |
| 不处理无关未跟踪目录 | 避免混入本功能变更 | 另开任务处理 |

## 6. 首批 fixture 冻结

### 6.1 必做 pass fixtures

| 文件名 | 验收重点 |
|---|---|
| `market_pass_xingheng_minimum_boundary.json` | 锂电属性、960Wh 派生、UN38.3/SDS/包装缺口、候选 HTSUS、起运港待确认 |
| `market_pass_uniqlo_minimum_boundary.json` | 网页 Product ID / Production / Body / Trim / RN，实物标签/BOM/起运港缺口，候选 HTSUS |
| `market_pass_search_summary_candidate_only.json` | 搜索摘要只作为候选线索 |
| `market_pass_not_executed_modules_retained.json` | Google Trends、价格、节日、外部因素未执行但仍保留矩阵行 |
| `market_pass_derived_wh_with_formula.json` | 派生计算必须引用输入证据卡和公式 |
| `market_pass_conflict_preserved.json` | 冲突保留，不强行合并结论 |

### 6.2 必做 fail fixtures

| 文件名 | 预期错误码 |
|---|---|
| `market_fail_search_summary_as_verified.json` | `market_search_summary_promoted` |
| `market_fail_skill_summary_as_source.json` | `market_skill_summary_as_source` |
| `market_fail_qcvn_as_un38_3.json` | `market_qcvn_promoted_to_un38_3` |
| `market_fail_candidate_htsus_as_final_rate.json` | `market_candidate_hs_promoted_to_final` |
| `market_fail_web_label_as_physical_compliance.json` | `market_web_label_promoted_to_physical_compliance` |
| `market_fail_google_trends_as_sales.json` | `market_google_trends_sales_claim` |
| `market_fail_logistics_best_or_committed.json` | `market_logistics_commitment_or_best` |
| `market_fail_departure_port_guessed.json` | `market_guess_departure_port` |
| `market_fail_not_executed_rows_missing.json` | `market_not_executed_row_missing` |
| `market_fail_source_local_path_or_hash_leak.json` | `market_delivery_internal_leak` |

## 7. 第一批错误码冻结

| 错误码 | 严重度 | 必须拦截的情况 |
|---|---|---|
| `market_search_summary_promoted` | critical | 搜索摘要被写成已核实事实 |
| `market_skill_summary_as_source` | critical | 前序 Skill 摘要或模型总结被当来源定位 |
| `market_qcvn_promoted_to_un38_3` | critical | QCVN / Vietnam Register 升级为 UN38.3 或 SDS |
| `market_candidate_hs_promoted_to_final` | critical | 候选 HS/HTS 或基础税率升级为最终归类/最终税率 |
| `market_web_label_promoted_to_physical_compliance` | critical | 网页标签升级为实物标签已合规 |
| `market_google_trends_sales_claim` | major | Google Trends 写成销量、GMV、进口量或采购需求 |
| `market_logistics_commitment_or_best` | major | 物流候选写成最佳路线、承诺交期或一定可走 |
| `market_guess_departure_port` | major | 起运港未知却默认常用港口 |
| `market_not_executed_row_missing` | major | 未执行模块没有进入矩阵 |
| `market_delivery_internal_leak` | critical | 用户可见导出泄露本地路径、hash、token、内部 ID |
| `market_matrix_row_missing_status` | major | 用户可见矩阵行缺状态 |
| `market_value_judgment` | critical | 输出建议进入、值得开发、市场潜力高、推荐客户类型等价值判断 |
| `market_geo_roles_merged` | critical | 出口申报国、原产国、起运国、目的国混写 |
| `market_brief_stale_result_delivered` | critical | Brief 改版后旧结果仍交付为当前结论 |

## 8. 数据结构实现最小集

| 对象 | MVP-0 必须有 | 可以后置 |
|---|---|---|
| `MarketAnalysisRun` | run_id、route、brief_version_id、execution_mode、delivery_status、not_executed_modules | 完整能力预检明细 |
| `MarketAnalysisBrief` | 产品、目标国、出口申报国、原产国状态、起运状态、请求模块 | 多目的国比较、贸易术语完整成本 |
| `ProductSubject` | 名称、型号/SKU、制造商/品牌、组件、未知属性 | 完整产品族去重 |
| `TradePremise` | 出口申报国、原产国、起运国、目的国拆分和状态 | 内陆段、保险、目的地费用 |
| `ProductAttributeRecord` | 属性族、属性名、值、状态、触发路径、证据卡/缺口引用 | 全品类属性库 |
| `EvidenceCard` | 来源引用、当前值、状态、supports、does_not_support、适用范围、日期 | 复杂多来源评分 |
| `MatrixRowRecord` | 表名、行标题、状态、用户可见字段、证据/缺口/冲突引用 | 富格式样式 |
| `GapRecord` | 缺什么、向谁要、影响哪个模块 | 自动提醒 |
| `ConflictRecord` | 冲突字段、冲突来源、待复核说明 | 自动冲突调解 |

## 9. 验收命令建议

具体命令可在实现时按现有 eval runner 调整，但验收顺序先冻结为：

| 顺序 | 命令/动作 | 目的 |
|---:|---|---|
| 1 | `python3 evals/run_evals.py --suite default` | 确认批量客户开发默认套件无回归 |
| 2 | `python3 evals/run_evals.py --suite deep` | 确认深度背调套件无回归 |
| 3 | `python3 evals/run_evals.py --suite all` | 确认现有全量套件无回归 |
| 4 | `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_*.json` | 确认 pass fixtures 通过 |
| 5 | `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_fail_*.json` | 确认 fail fixtures 命中预期错误码 |
| 6 | `python3 scripts/audit_product_market_analysis.py evals/fixtures/market_pass_xingheng_minimum_boundary.json` | 确认可交付但带限制 |
| 7 | 导出 smoke test | 确认 12 张表/Markdown 分组存在、无内部泄露 |

如果第一轮还没有 audit / export，4-5 先作为 MVP-0 验收；6-7 等 Code Slice D-E 完成后再启用。

## 10. 提交边界

| 提交建议 | 内容 |
|---|---|
| 文档提交 | Slice 1-12 文档、验证清单、product/spec/meta/TASKS/HANDOFF 更新 |
| 代码提交 1 | Code Slice A-C：schema、validator、fixture、case 配置 |
| 代码提交 2 | Code Slice D-E：audit、CSV/Markdown 导出、导出 smoke fixture |
| 暂不提交 | `skillhub-package/`、`social-card-superleads-cover/`、`social-card-superleads-trade-cover/` 等无关目录，除非用户另行要求 |
| 必须保留 | `tmp/stage5_chillys/` |

建议在开始写代码前，先让用户确认是否把当前 Slice 1-12 文档做一次 git 提交，避免文档设计和代码实现混在一个提交里。

## 11. 开工前冻结清单

| 检查项 | 冻结结果 |
|---|---|
| 产品名称 | 产品出海市场分析 |
| 路线边界 | 独立于批量客户开发和单客背调 |
| 默认出口申报国 | 可默认为中国，但必须可见可改 |
| 目的国范围 | MVP 以单一具体目的国为主，多目的国比较后置 |
| 输出策略 | 表格化、矩阵化、人话化，不做价值判断 |
| 数据策略 | ProductMarketAnalysisGraph 独立，不塞进 Candidate / Claim / Assessment |
| 证据策略 | EvidenceCard + Source/Observation + Gap/Conflict，搜索摘要不得成事实 |
| Source Pack 策略 | 只作来源入口目录，不是事实库 |
| 首批样本 | Xing Heng 锂电、UNIQLO 纺织 |
| 第一轮实现 | Code Slice A-C；需要导出时扩展到 A-E |
| 真实来源采集 | 后置到防错闭环稳定之后 |

## 12. 什么时候可以开始写代码

满足以下条件即可开始 Code Slice A-C：

| 条件 | 状态 |
|---|---|
| 产品 Brief、Bet、合同存在 | 已满足 |
| 输出矩阵和工作簿合同存在 | 已满足 |
| 证据边界、Skill 互证、数据模型存在 | 已满足 |
| Source Pack、端到端剧本存在 | 已满足 |
| 第一批 fixture 和错误码清楚 | 已满足 |
| 用户明确说“开始实现/写代码” | 待用户确认 |
| 是否先提交当前文档 | 建议用户确认 |

## 13. Slice 12 完成标准

| 编号 | 完成标准 |
|---|---|
| C-01 | 已汇总 Slice 1-11 的实现约束 |
| C-02 | 已冻结 MVP-0 / MVP-1 / MVP-2 / MVP-3 分层和第一轮实现边界 |
| C-03 | 已明确 Code Slice A-C / A-E 做什么和不做什么 |
| C-04 | 已冻结首批 pass/fail fixture 和错误码 |
| C-05 | 已给出验收命令顺序、提交边界和开工前检查清单 |
| C-06 | 已明确下一步只有两条路：先提交文档，或开始 Code Slice A-C |
