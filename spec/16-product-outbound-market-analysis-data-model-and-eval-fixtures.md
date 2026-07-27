# 产品出海市场分析：数据模型与 eval 夹具设计（Slice 5）

本文件冻结第一版 `产品出海市场分析` 的未来实现数据模型与 eval 夹具设计。它不是代码，不新增 JSON Schema、不新增 eval 文件、不接入真实来源；目标是让后续实现时知道“数据应该长什么样、哪些错误必须被测试拦住”。

一句话设计：**用独立的产品市场分析图谱承载产品、贸易前提、证据卡、Skill 交接、状态流转和交付矩阵；复用 Superleads 现有来源/观察与导出审计思路，但不把产品市场分析塞进客户 Candidate / Claim / Assessment。**

## 1. Slice 5 边界

| 项目 | 本轮决定 |
|---|---|
| 目标 | 把证据卡、状态流转、禁止升级断言、Skill 交接整理成未来可实现的数据对象和 eval 夹具设计 |
| 适用对象 | 后续 schema、validator、audit、export、Markdown 报告、XLSX/CSV 工作簿、Skill 实现 |
| 首批样本 | Xing Heng `48V20Ah` LiFePO4 电池包；UNIQLO Men's Corduroy Overshirt `470177` |
| 本轮不做 | 不写 Python、不写 JSON Schema、不新增 eval fixtures、不改导出器、不跑真实联网研究 |
| 输出 | 对象模型、状态枚举、状态流转门禁、证据覆盖规则、Skill 交接结构、eval 夹具清单、错误码草案 |

## 2. 总体数据架构

### 2.1 第一版实现形态

| 设计项 | 决定 |
|---|---|
| 主图谱 | 新增独立 `ProductMarketAnalysisGraph`，不要直接复用客户开发的 `ResearchGraph` 主对象 |
| 可复用模块 | 复用现有 `Source` / `Observation` 思路、安全公开 URL 校验、审计/导出模式和中文工作簿输出习惯 |
| 不复用为主数据的对象 | 不把产品分析对象强行写成 `Candidate`、`Entity`、`Claim`、`Assessment`、`ContactClaim` |
| 原因 | 产品市场分析不是客户名单，不评价客户，不做业务相关性 disposition；用客户图谱对象会诱导错误导出和错误审计 |
| 兼容方式 | 后续可通过 `shared/schemas/source-observation.schema.json` 复用来源与观察对象，避免重复造来源系统 |

### 2.2 顶层对象

| 对象 | 人话作用 | 是否用户可见 | 关键关系 |
|---|---|---|---|
| `MarketAnalysisRun` | 一次产品出海市场分析任务 | 否 | 绑定 Brief、Skill 任务、交付物 |
| `MarketAnalysisBrief` | 本轮研究范围和贸易前提 | 部分可见 | 绑定产品、目标市场、出口/原产/起运条件 |
| `ProductSubject` | 被分析的产品版本 | 可见 | 绑定属性、组件、包装、技术资料缺口 |
| `TradePremise` | 卖方/出口申报国/原产国/起运地/目的国拆分 | 可见 | 影响税费、出口、物流和准入 |
| `ProductAttributeRecord` | 产品属性与触发项 | 可见 | 触发合规、出口、物流、价格可比规则 |
| `Source` / `Observation` | 打开的网页、PDF、官方税则、用户文件和抽取片段 | 部分可见 | 被证据卡引用；搜索结果只能做线索 |
| `EvidenceCard` | 一个字段的证据最小单位 | 部分可见 | 支持矩阵行、状态流转、互证和缺口 |
| `StateTransitionRecord` | 字段状态为什么升级/降级 | 否 | 防止搜索摘要直接变已核实 |
| `SkillHandoffRecord` | Skill 输入输出和交接 | 否 | 记录上游 Brief 版本、产出证据卡、打回状态 |
| `BoundaryAssertionResult` | 禁止升级规则的检查结果 | 否/摘要可见 | 对应 Slice 3/4 规则和 eval 错误码 |
| `MatrixRowRecord` | 未来 Markdown / XLSX / CSV 的一行 | 可见 | 只从证据卡、缺口或未执行状态生成 |
| `GapRecord` | 待用户/供应商/报关行/承运人补的材料 | 可见 | 进入待确认事项和对应业务表 |
| `ConflictRecord` | 来源或 Skill 之间的冲突 | 可见 | 不能强行合并成单一结论 |
| `MarketDeliveryManifest` | 一次交付的清单和自检摘要 | 部分可见 | 绑定工作簿、Markdown、审计结果 |

## 3. 核心对象字段设计

### 3.1 `MarketAnalysisRun`

| 字段 | 必填 | 说明 |
|---|---|---|
| `run_id` | 是 | 本次分析运行 ID |
| `route` | 是 | 固定为 `product_outbound_market_analysis` |
| `created_at` / `updated_at` | 是 | 运行创建和更新时间 |
| `brief_id` | 是 | 当前使用的 Brief |
| `brief_version_id` | 是 | 下游 Skill 必须绑定这个版本 |
| `default_export_declaration_country` | 是 | 默认出口申报国，可见且可被用户修改 |
| `execution_mode` | 是 | `planning_only`、`sample_static`、`source_opened`、`full_research` 等 |
| `delivery_status` | 是 | `planning_only`、`draft_matrix`、`ready_with_limitations`、`blocked_needs_input`、`needs_correction` |
| `not_executed_modules` | 是 | 本轮没有执行的模块，如 Google Trends、价格、法规、物流 |

### 3.2 `MarketAnalysisBrief`

| 字段 | 必填 | 说明 |
|---|---|---|
| `brief_id` / `brief_version_id` | 是 | 任何修改都会产生新版本，触发下游复核 |
| `product_subject_id` | 是 | 绑定一个明确产品版本 |
| `target_country_or_region` | 是 | 单一具体目的国；地区研究需落到具体国家 |
| `seller_country_or_region` | 否 | 卖方所在国，不能等同出口申报国 |
| `export_declaration_country` | 是 | 出口申报国；默认中国但必须可改 |
| `origin_country_status` | 是 | 原产国状态和证据等级 |
| `departure_country_or_region` | 否 | 实际起运国/地区 |
| `departure_node` | 否 | 起运港、机场、口岸、仓库；未知写待确认 |
| `destination_node` | 否 | 目的港、机场、口岸、交付地；未知写待确认 |
| `trade_term` | 否 | Incoterms；第一期可为空，但不能被默认猜测 |
| `analysis_modules_requested` | 是 | 趋势、价格、准入、税费、出口、物流、外部因素等 |
| `business_decision_policy` | 是 | 固定为“只给客观参考，不做进入建议” |

### 3.3 `ProductSubject`

| 字段 | 必填 | 说明 |
|---|---|---|
| `product_subject_id` | 是 | 产品对象 ID |
| `display_name` | 是 | 用户能看懂的名称 |
| `version_identifiers` | 是 | 型号、Design No.、Product ID、SKU 等 |
| `manufacturer_or_brand` | 否 | 制造商、品牌或公开页面显示主体 |
| `product_family` | 否 | 仅作描述，不可替代产品属性判断 |
| `components` | 是 | 产品本体、电池、附件、内包装、外包装可分开 |
| `profile_status` | 是 | `sufficient_for_planning`、`needs_user_clarification`、`needs_technical_docs` |
| `unknown_key_attributes` | 是 | 必须保留的未知项 |

### 3.4 `TradePremise`

| 字段 | 必填 | 说明 |
|---|---|---|
| `trade_premise_id` | 是 | 贸易前提 ID |
| `seller_country_or_region` | 否 | 卖方所在国 |
| `export_declaration_country` | 是 | 出口申报国 |
| `origin_country_or_region` | 否 | 原产国或公开制造来源 |
| `origin_evidence_level` | 是 | L0-L4，沿用原产地证据等级 |
| `departure_country_or_region` | 否 | 实际起运国 |
| `departure_node` | 否 | 港口/机场/口岸/仓库 |
| `destination_country_or_region` | 是 | 目的国 |
| `destination_node` | 否 | 目的港/机场/交付地 |
| `status` | 是 | 已核实、待业务确认、未提供、有冲突待复核等 |
| `separation_check` | 是 | 是否明确拆分出口申报国、原产国、起运国、目的国 |

### 3.5 `ProductAttributeRecord`

| 字段 | 必填 | 说明 |
|---|---|---|
| `attribute_id` | 是 | 属性记录 ID |
| `product_subject_id` | 是 | 所属产品 |
| `component_scope` | 是 | 产品本体、电池、包装、辅料、附件等 |
| `attribute_family` | 是 | 商业技术、物理运输、电气安全、化学危险品、人体消费安全、农业生物、战略与知识产权、贸易分类 |
| `attribute_name` | 是 | 如电池容量、纤维成分、液体、磁性、食品接触 |
| `value` | 是 | 当前值；未知也写状态值，不留空 |
| `unit` | 否 | Wh、kg、mm、%、USD 等 |
| `status` | 是 | 使用统一状态枚举 |
| `trigger_paths` | 是 | 触发的核验路径，如锂电运输、纺织标签、出口管制 |
| `evidence_card_ids` | 是 | 支持该属性的证据卡；未执行/未提供可为空但要有缺口记录 |
| `gap_ids` | 否 | 关联缺口 |

### 3.6 `EvidenceCard`

证据卡是 Slice 5 最重要的对象。未来任何用户可见事实行，都应能追到证据卡或明确的缺口/未执行记录。

| 字段 | 必填 | 说明 |
|---|---|---|
| `evidence_card_id` | 是 | 证据卡 ID |
| `run_id` / `brief_version_id` | 是 | 防止旧 Brief 的证据误用到新 Brief |
| `producer_skill` | 是 | A-F 六个 Skill 之一 |
| `reviewer_skill` | 否 | 通常为 Skill F 或交叉校验 Skill |
| `field_domain` | 是 | 产品属性、市场趋势、价格、目的国准入、进口税费、出口要求、物流、外部因素等 |
| `field_name` | 是 | 要支持的字段 |
| `current_value` | 是 | 原文值、派生值、候选值或状态值 |
| `status` | 是 | 统一状态枚举 |
| `source_refs` | 是 | 引用 `Source` / `Observation`；搜索线索也要标明不能支持已核实 |
| `source_type` | 是 | 官方、产品页、PDF、Google Trends、平台价格、搜索结果、用户文件等 |
| `source_locator` | 是 | URL、文件名、页码、章节、表格、官方查询入口；不能只有搜索摘要 |
| `source_date` | 是 | 生效/发布/报告日期；没有写 `日期未见` |
| `observed_at` | 是 | 本轮观察日期 |
| `applicability_scope` | 是 | 型号、国家、时间、标准、运输情形、订单/批次、规格 |
| `supports` | 是 | 该证据能支持什么 |
| `does_not_support` | 是 | 明确不能升级成什么 |
| `derived_from_card_ids` | 否 | 派生计算时引用原始数字证据 |
| `formula_text` | 否 | 派生计算公式，如 `960 Wh = 48 V × 20 Ah` |
| `gap_ids` | 否 | 缺口 |
| `boundary_rule_ids` | 是 | 关联 Slice 3/4 禁止升级规则 |
| `review_status` | 是 | `not_reviewed`、`passed`、`returned`、`blocked`、`downgraded` |

### 3.7 `StateTransitionRecord`

| 字段 | 必填 | 说明 |
|---|---|---|
| `transition_id` | 是 | 状态流转记录 ID |
| `evidence_card_id` | 是 | 关联证据卡 |
| `from_status` / `to_status` | 是 | 状态变化 |
| `transition_reason` | 是 | 为什么升级、降级或阻断 |
| `gate` | 是 | Brief 冻结门、证据来源门、交付边界门、人工打回等 |
| `allowed` | 是 | 是否允许该流转 |
| `blocking_rule_id` | 否 | 不允许时对应规则 |
| `reviewed_by_skill` | 是 | 哪个 Skill 复核 |
| `reviewed_at` | 是 | 复核时间 |

### 3.8 `SkillHandoffRecord`

| 字段 | 必填 | 说明 |
|---|---|---|
| `handoff_id` | 是 | Skill 交接 ID |
| `from_skill` / `to_skill` | 是 | 交接双方 |
| `input_brief_version_id` | 是 | 消费哪一版 Brief |
| `input_card_ids` | 是 | 消费哪些证据卡 |
| `output_card_ids` | 是 | 产出哪些证据卡 |
| `returned_to_skill` | 否 | 被打回给谁 |
| `return_reason` | 否 | 打回原因 |
| `staleness_status` | 是 | `current`、`stale_due_to_brief_change`、`requires_rerun` |
| `handoff_status` | 是 | `passed`、`returned`、`blocked`、`downgraded`、`not_executed` |

### 3.9 `MatrixRowRecord`

| 字段 | 必填 | 说明 |
|---|---|---|
| `matrix_row_id` | 是 | 工作簿/Markdown 行 ID |
| `sheet_name` | 是 | 12 张中文工作表之一 |
| `row_topic` | 是 | 本行主题 |
| `row_type` | 条件必填 | 特殊行类型，如 `origin_proof_requirement`、`certification_requirement`、`destination_requirement`；普通行可省略 |
| `user_visible_cells` | 是 | 用户可见列和值 |
| `status` | 是 | 统一状态枚举 |
| `evidence_card_ids` | 条件必填 | 已核实、候选、初步参考、派生计算必须引用证据卡 |
| `gap_ids` | 条件必填 | 待确认、未提供、未执行时必须有缺口或说明 |
| `boundary_rule_ids` | 是 | 关联禁止升级规则 |
| `internal_refs_hidden` | 是 | 必须为 true，确保不暴露本地路径、哈希、内部 ID |

## 4. 统一状态枚举

| 内部值 | 用户可见 | 支持确定结论 | 最低证据要求 |
|---|---|---|---|
| `verified` | 已核实 | 仅支持该字段本身 | 非搜索来源可定位、字段直接可见、范围匹配 |
| `derived_calculation` | 派生计算 | 仅支持该计算值 | 引用已核实数字和公式 |
| `candidate` | 候选 | 否 | 可作为下一步核验方向，搜索线索也只能到这里 |
| `preliminary_reference` | 初步参考 | 否 | 公开信号存在但口径有限 |
| `business_confirmation_required` | 待业务确认 | 否 | 需要订单、供应链、报关或订舱资料 |
| `technical_docs_required` | 待技术资料确认 | 否 | 需要 SDS、UN38.3、BOM、标签、规格书、包装资料 |
| `physical_verification_required` | 待实物核验 | 否 | 需要实物照片、标签、样品或检测 |
| `professional_confirmation_required` | 待专业确认 | 否 | 需要报关、认证、承运人、主管机关或律师确认 |
| `source_restricted` | 来源受限 | 否 | 只能看到摘要、付费墙或受限页面 |
| `not_executed` | 未执行 | 否 | 本轮未采集，不得有事实结论 |
| `not_applicable` | 不适用 | 条件性支持排除 | 必须有排除依据 |
| `not_provided` | 未提供 | 否 | 用户或公开来源未提供 |
| `conflict_pending_review` | 有冲突待复核 | 否 | 至少两个来源/证据卡冲突 |

## 5. 状态流转门禁

| 流转 | 是否允许 | 条件 |
|---|---|---|
| 搜索线索 → 候选 | 允许 | 记录待打开 URL 或待核验字段，不写已核实 |
| 搜索线索 → 已核实 | 禁止 | 搜索摘要不能支持事实字段 |
| 候选 → 已核实 | 条件允许 | 打开原始来源，字段直接可见，范围和日期匹配 |
| 已核实 → 派生计算 | 禁止 | 派生计算是新卡，必须引用原始卡和公式 |
| 已核实数字 → 派生计算 | 条件允许 | 公式、单位和输入值完整 |
| 候选 HS/HTS → 最终税率 | 禁止 | 产品归类、原产地、税基、有效税表和专业确认不足 |
| 网页标签信息 → 实物标签合规 | 禁止 | 需要实物标签和专业核验 |
| 运输候选 → 最佳运输方式/承诺交期 | 禁止 | 运输方式只能条件化参考 |
| 用户未提供证书 → 目标国不需要认证 | 禁止 | 用户材料状态不能反推目标国准入要求 |
| 用户提供证书 → 目标国认可/产品已合规 | 禁止 | 证书必须核对目标国、型号、标准、日期、签发机构和范围，且仍需目标规则支持 |
| 证书入口 → 已具备认证 | 禁止 | 必须打开文件并核对范围，入口本身只能作待核验线索 |
| 未执行 → 任意事实结论 | 禁止 | 未执行只能保留未执行行 |
| 来源受限 → 已核实数字 | 禁止 | 只能写可见内容和限制 |
| 任意状态 → 有冲突待复核 | 允许 | 出现同字段来源冲突时必须保留冲突 |

## 6. 证据覆盖规则

| 规则 | 未来 validator 应检查 |
|---|---|
| `verified` 不能只引用 `search_result` | 否则报 `market_search_summary_promoted` |
| `derived_calculation` 必须有 `derived_from_card_ids` 和 `formula_text` | 否则报 `market_derived_calculation_missing_basis` |
| `candidate` 不能出现在“最终税率/最终归类/已合规/可出运”字段 | 否则报对应升级错误 |
| `not_executed` 的用户可见单元不能包含趋势、价格、税率、旺季等结论 | 否则报 `market_not_executed_has_conclusion` |
| `conflict_pending_review` 必须关联冲突来源 | 否则报 `market_conflict_without_sources` |
| `not_applicable` 必须有排除依据 | 否则报 `market_not_applicable_without_basis` |
| 每个 `MatrixRowRecord` 必须有状态 | 否则报 `market_matrix_row_missing_status` |
| 用户可见来源不得出现本地路径、哈希、内部 ID、带 token URL | 否则报 `market_delivery_internal_leak` |

## 7. Skill 交接数据规则

| 检查点 | 未来 eval 应验证 |
|---|---|
| Skill 输出必须绑定 Brief 版本 | Brief 改版后旧证据不能无提示进入交付 |
| Skill F 不能凭空新增事实 | 除 `未执行`、`未提供`、`待确认` 行外，交付行必须引用证据卡 |
| 下游发现上游属性冲突必须打回 | 不能只在最终报告里静默改写 |
| 打回后受影响 Skill 必须重跑或降级 | 不能用旧结果继续输出确定字段 |
| 每个事实域至少有一个复核结果 | 可为通过、降级、打回、未执行，但不能缺失 |
| 前序 Skill 摘要不能作为 `source_locator` | 否则报 `market_skill_summary_as_source` |

## 8. 工作簿映射规则

| 工作表 | 主要来源对象 | 必须保留的边界 |
|---|---|---|
| `市场事实总览` | Brief、TradePremise、关键 EvidenceCard、GapRecord | 总体状态不能写市场进入建议 |
| `产品档案与触发项` | ProductSubject、ProductAttributeRecord | 未知属性不能留空 |
| `长期需求与搜索趋势` | EvidenceCard / MatrixRowRecord | Google Trends 只写相对搜索兴趣 |
| `公开市场资料与行业信息` | EvidenceCard | 付费摘要不补数字 |
| `线上市场与价格参考` | EvidenceCard | 挂牌价不等于成交价或推荐价 |
| `季节、节日与销售窗口` | EvidenceCard | 节日不自动等于旺季 |
| `产品准入与合规要求` | Attribute + EvidenceCard + GapRecord | 证书/网页不升级完整合规 |
| `进口税费` | EvidenceCard + BoundaryAssertionResult | 候选税号和基础税率不升级最终税率 |
| `出口国要求` | TradePremise + EvidenceCard + GapRecord | 出口申报国不能与原产国混写 |
| `运输方式、路线、港口与申报节点` | TradePremise + EvidenceCard | 候选方式不写最佳或承诺交期 |
| `近期外部因素` | EvidenceCard | 无日期不称最新 |
| `信息来源与待确认事项` | Source、Observation、GapRecord、ConflictRecord | 不暴露本地路径、哈希、内部 ID |

## 9. eval 夹具文件布局建议

本 Slice 不创建这些文件，只冻结未来布局建议。

| 类型 | 建议路径 | 说明 |
|---|---|---|
| 数据 schema | `shared/schemas/product-market-analysis.schema.json` | 独立图谱 schema，复用 Source/Observation 定义 |
| 语义规则 | `shared/references/product-market-analysis-boundary-rules.md` | 从 Slice 3/4/5 提炼机器可读规则前的人类版 |
| eval case 配置 | `evals/cases/product_market_analysis_cases.json` | 记录 pass/fail fixture、预期错误码、测试层级 |
| fixture 文件 | `evals/fixtures/market_*.json` | 统一 `market_` 前缀，避免混入客户开发 fixture |
| 静态输出样例 | `evals/fixtures/market_output_*.md` 或 `docs/validation/...` | 用于扫描禁止短语和表格结构 |
| 未来 validator | `scripts/validate_product_market_analysis.py` 或集成现有 validator | 具体实现时再决定 |
| 未来 audit/export | `scripts/audit_product_market_analysis.py`、`scripts/export_product_market_workbook.py` 或复用现有导出框架 | 具体实现时再决定 |

## 10. eval 分层

| 层级 | 验什么 | 示例 |
|---|---|---|
| Schema 层 | 对象是否齐全、字段是否有状态、引用是否存在 | EvidenceCard 缺 source_locator 应失败 |
| Evidence 层 | 来源能不能支持字段 | 搜索摘要被写已核实应失败 |
| Boundary 层 | 禁止升级规则 | QCVN 升级 UN38.3 应失败 |
| Handoff 层 | Skill 交接和 Brief 版本 | Brief 改版后旧物流结论未重跑应失败 |
| Export 层 | 12 张工作表、状态、空值、内部信息隐藏 | 缺 `未执行` 行或泄露本地路径应失败 |
| Static text 层 | 用户可见报告是否有禁止短语 | 出现“建议进入”“最佳运输方式”应失败 |

## 11. 首批 pass fixture 设计

| fixture 名称 | 目的 | 预期 |
|---|---|---|
| `market_pass_xingheng_minimum_boundary.json` | Xing Heng 样本只保留已核实参数、派生 Wh、UN38.3/SDS/起运港缺口 | validate/audit/export 均通过 |
| `market_pass_uniqlo_minimum_boundary.json` | UNIQLO 样本保留 Product ID、Production、Body/Trim、网页标签与实物标签边界 | validate/audit/export 均通过 |
| `market_pass_search_summary_candidate_only.json` | 搜索结果只作为候选线索，不支持已核实字段 | 通过 |
| `market_pass_not_executed_modules_retained.json` | Google Trends、价格、节日、外部因素未执行但仍有矩阵行 | 通过 |
| `market_pass_conflict_preserved.json` | 两个来源对同一字段冲突，最终标有冲突待复核 | 通过 |
| `market_pass_brief_changed_downstream_downgraded.json` | Brief 改版后下游结果降级或要求重跑 | 通过 |
| `market_pass_derived_wh_with_formula.json` | 48V × 20Ah 派生 960Wh，有输入卡和公式 | 通过 |
| `market_pass_export_no_internal_leak.json` | 导出中不出现本地路径、哈希、内部对象名 | 通过 |

## 12. 首批 fail fixture 设计

| fixture 名称 | 失败原因 | 预期错误码 |
|---|---|---|
| `market_fail_search_summary_as_verified.json` | 搜索摘要直接写成已核实事实 | `market_search_summary_promoted` |
| `market_fail_skill_summary_as_source.json` | 前序 Skill 摘要被当成来源定位 | `market_skill_summary_as_source` |
| `market_fail_qcvn_as_un38_3.json` | Vietnam Register / QCVN 91 被升级为 UN38.3 | `market_qcvn_promoted_to_un38_3` |
| `market_fail_missing_sds_marked_ready.json` | 未见 SDS 却写锂电运输资料齐全 | `market_missing_sds_promoted` |
| `market_fail_candidate_htsus_as_final_rate.json` | 候选 HTSUS 或基础税率写成最终税率 | `market_candidate_hs_promoted_to_final` |
| `market_fail_chapter99_without_conditions.json` | Chapter 99 未绑定报关日、原产地、最终 10 位税号就判定适用/不适用 | `market_tax_rate_unconditional` |
| `market_fail_web_label_as_physical_compliance.json` | UNIQLO 网页标签信息写成实物标签已合规 | `market_web_label_promoted_to_physical_compliance` |
| `market_fail_google_trends_as_sales.json` | Google Trends 写成销量、采购需求或市场份额 | `market_google_trends_sales_claim` |
| `market_fail_platform_price_as_transaction_price.json` | 平台挂牌价写成成交价或推荐报价 | `market_platform_price_promoted` |
| `market_fail_logistics_best_or_committed.json` | 候选运输方式写成最佳方式或承诺交期 | `market_logistics_commitment_or_best` |
| `market_fail_departure_port_guessed.json` | 起运港未知却默认某港口 | `market_guess_departure_port` |
| `market_fail_geo_roles_merged.json` | 出口申报国、原产国、起运国、目的国混为一个出口国 | `market_geo_roles_merged` |
| `market_fail_not_executed_rows_missing.json` | 未执行模块在最终矩阵中消失 | `market_not_executed_row_missing` |
| `market_fail_conflict_hidden.json` | 来源冲突被强行合并为单一结论 | `market_conflict_not_preserved` |
| `market_fail_illegal_status_transition.json` | 搜索线索直接流转为已核实 | `market_forbidden_status_transition` |
| `market_fail_brief_changed_without_rerun.json` | Brief 改版后旧 Skill 结果仍作为当前结论交付 | `market_brief_stale_result_delivered` |
| `market_fail_value_judgment_in_delivery.json` | 用户可见报告出现市场进入或推荐开发判断 | `market_value_judgment` |
| `market_fail_source_local_path_or_hash_leak.json` | 导出泄露本地路径、哈希或内部 ID | `market_delivery_internal_leak` |

## 13. 错误码分级草案

| 严重度 | 错误码类型 | 处理 |
|---|---|---|
| critical | 搜索摘要升级、税费最终化、合规最终化、危险品运输错误、价值判断 | 阻断交付 |
| major | 来源定位缺失、状态缺失、Brief 过期、冲突未保留、未执行行缺失 | 退回修正或降级 |
| minor | 日期未见但未称最新、限制说明不够清楚、来源名称不够友好 | 可交付但需提示修正 |

## 14. 两个样本的最小 fixture 断言

### 14.1 Xing Heng `48V20Ah`

| 断言 | 最低数据要求 |
|---|---|
| 产品版本明确 | ProductSubject 有 `48V20Ah` 和 `BAT001.02` |
| Wh 为派生计算 | EvidenceCard 状态为 `derived_calculation`，引用 48V 和 20Ah 两张卡 |
| UN38.3 未证实 | 对应 MatrixRow 为 `technical_docs_required`，不得 `verified` |
| SDS 未见 | 对应 GapRecord 必须存在 |
| QCVN 证书边界 | EvidenceCard 的 `does_not_support` 必须写不能替代 UN38.3/SDS |
| 候选 HTSUS | `8507.60.00` 只能是 `candidate` 或 `professional_confirmation_required` |
| 起运港 | `business_confirmation_required`，不得默认港口 |
| 运输方式 | FCL/LCL/空运/快递均为候选或待确认，不得最佳/承诺 |

### 14.2 UNIQLO `470177`

| 断言 | 最低数据要求 |
|---|---|
| 产品版本明确 | ProductSubject 有 Product ID `470177` |
| Production: China | 可 `verified` 为网页 Production，但 TradePremise 中出口申报国/起运港仍可待确认 |
| Body/Trim | 只支持主体和饰边 100% Cotton，不能推导辅料 |
| 网页标签 | RN/洗护/成分为网页信息，实物标签为 `physical_verification_required` |
| 候选 HTSUS | `6205.20.20` 只能是候选或待专业确认 |
| 克重/单重 | 未公开时必须 `technical_docs_required`，不得估算 |
| 运输方式 | 候选组织方式，不推荐最佳方式 |

## 15. 与现有 Superleads 机制的关系

| 现有机制 | 产品出海市场分析怎么用 |
|---|---|
| Source / Observation | 继续复用，保证公开来源、用户文件、观察片段可追溯 |
| SearchLog 思路 | 搜索只记录线索，不支持已核实事实 |
| audit_delivery 思路 | 复用“阻断交付 / 降级交付 / 风险说明”的思路，但规则不同 |
| export_workbook 思路 | 复用中文业务表和不暴露内部 ID 的导出习惯 |
| Candidate / Entity / Contact | 不作为本模块主对象，避免产品市场分析变成客户名单 |
| Claim / ClaimEvidence | 不作为本模块主事实载体；用 EvidenceCard + MatrixRow 防止搜索摘要写成 Claim |

## 16. Slice 5 完成标准

| 编号 | 完成标准 |
|---|---|
| C-01 | 已明确第一版独立 `ProductMarketAnalysisGraph`，并说明与现有 ResearchGraph 的关系 |
| C-02 | 已定义 Brief、产品、贸易前提、产品属性、证据卡、状态流转、Skill 交接、矩阵行等核心对象 |
| C-03 | 已定义统一状态枚举和非法状态流转 |
| C-04 | 已定义证据覆盖规则，能防止搜索摘要、Skill 摘要、候选税号、网页标签、运输候选等错误升级 |
| C-05 | 已列出首批 pass/fail eval 夹具设计和错误码草案 |
| C-06 | Xing Heng / UNIQLO 两个样本都有最小 fixture 断言 |
| C-07 | 当前仍不写代码；后续实现可按本文件拆成 schema、validator、audit、export 和 eval fixtures |
