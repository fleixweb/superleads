# Tasks

## 已完成

- `python3 evals/run_evals.py --suite default` 通过
- `python3 evals/run_evals.py --suite deep` 通过
- `python3 evals/run_evals.py --suite all` 通过
- `source.open` 公开 GET 烟测已恢复（`https://example.com`，`200`）
- `tmp/stage5_chillys/` 的 Chilly's 真实背调样本已验证可导出
- `docs/validation/default-discovery-us-generator-aftermarket-run.md` 已记录当前默认发现受限状态

## 当前下一步

1. 继续争取 `search.web`，否则只能依赖用户给定 URL 列表或目录材料。
2. 按 `docs/validation/default-discovery-us-generator-aftermarket-run.md` 再跑至少 2 轮查询。
3. 完成至少 20 个去重 Candidate 的真实执行验证。
4. 记录 SearchLog / Source / Observation / Contact / 导出结果。

## 当前阻塞

- 本次会话的能力预检为 `search.web=unknown`、`source.open=available`。
- `max_output_without_manual_sources=standard_development_list`，但缺少搜索仍不足以自然扩成默认发现候选池。
## 产品出海市场分析

- 已完成一次公开来源补齐试跑：`docs/validation/product-market-analysis-public-source-fill-20260726.md`。
- 本次试跑选择 Tianneng `TMLiN-4810S1` 与 XM Textiles `Canvas-270` 作为可抽取技术字段的示范 SKU。
- 结论：公开目录/TDS 能补齐部分技术字段；SKU 级原产地、HS、UN38.3/SDS、起运港/出口申报国仍不能由公开来源自动猜测。

## 产品出海市场分析：真实样本复核

- 已按公开来源复核两个更真实样本：Xing Heng `48V20Ah` LiFePO4 电池包、UNIQLO Men's Corduroy Overshirt `470177`。
- 新增验证记录：`docs/validation/product-market-analysis-public-source-fill-xingheng-uniqlo-20260726.md`。
- 已同步更新：`spec/11-first-market-analysis-sample-briefs.md`、`spec/10-product-outbound-market-analysis-contract.md`、`meta/decision-log.md`、`meta/open-questions.md`。
- 下一步：基于这两个样本设计端到端输出矩阵的验收夹具/测试，重点覆盖“候选税号不等于最终税率”“QCVN 测试不等于 UN38.3/SDS”“网页标签不等于实物标签已合规”。

## 产品出海市场分析：输出矩阵验收设计

- 已新增 `spec/12-product-outbound-market-analysis-output-matrix-and-acceptance.md`。
- 已冻结对话展示顺序、12 张 XLSX/CSV 工作表、状态词、人话解释、Xing Heng / UNIQLO 两个样本的正向与负向验收断言。
- 推荐下一步 Slice 1：不联网、不接新来源，先用已验证字段生成两份静态 Markdown 样例，确保表格结构、状态词和“不得输出”断言可测。

## 产品出海市场分析：静态样例报告 Slice 1

- 已新增 `docs/validation/product-market-analysis-static-sample-reports-slice1-20260726.md`。
- 该文档用已复核字段生成 Xing Heng / UNIQLO 两份 Markdown 样例报告，不联网、不新增来源。
- 自检覆盖：表格化结构、状态词、候选税号边界、QCVN/UN38.3/SDS 边界、UNIQLO 网页标签/实物标签边界、未执行模块不得编造成结论。
- 下一步建议：进入 Slice 2，定义 XLSX/CSV 样本矩阵的表头、状态枚举和空值保留规则；仍可先不接真实搜索。

## 产品出海市场分析：工作簿合同 Slice 2

- 已新增 `spec/13-product-outbound-market-analysis-workbook-contract.md`。
- 已新增 `docs/validation/product-market-analysis-workbook-slice2-sample-matrix-20260726.md`。
- 已冻结 12 张 XLSX/CSV 工作表、字段顺序、状态枚举、空值保留规则、两个样本的最小行矩阵和自检断言。
- 下一步建议：进入 Slice 3 证据边界校验规则，优先把“候选税号不能升级”“QCVN 不能升级 UN38.3/SDS”“网页标签不能升级实物标签合规”做成可检查清单或轻量测试夹具。

## 产品出海市场分析：证据边界校验规则 Slice 3

- 已新增 `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md`。
- 已新增 `docs/validation/product-market-analysis-evidence-boundary-slice3-checklist-20260726.md`。
- 已冻结证据类型、允许表述、禁止升级规则、降级/阻断规则、禁止短语、Xing Heng / UNIQLO 样本特定断言。
- 文档清单验收通过：候选税号未升级最终税率，QCVN/Vietnam Register 未升级 UN38.3/SDS，UNIQLO 网页标签未升级实物标签合规，未执行模块未编造成结论。
- 下一步二选一：继续产品设计做 Slice 4 Skill 分工互证流程；或进入轻量实现，做 Markdown/CSV 禁止升级扫描脚本和 eval fixture。

## 产品出海市场分析：Skill 分工互证流程 Slice 4

- 已新增 `spec/15-product-outbound-market-analysis-skill-orchestration.md`。
- 已新增 `docs/validation/product-market-analysis-skill-orchestration-slice4-checklist-20260726.md`。
- 已冻结六个 Skill 的输入、输出、证据卡、互证矩阵、三道门禁、打回/降级规则、状态流转和 Brief 改版重跑触发。
- 文档清单验收通过：前序摘要不能直接变事实，搜索摘要只能做线索，冲突/缺口/未执行必须保留到最终矩阵，Xing Heng / UNIQLO 两个样本均可套入流程。
- 后续已进入 Slice 5 数据模型与 eval 夹具设计。

## 产品出海市场分析：数据模型与 eval 夹具设计 Slice 5

- 已新增 `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md`。
- 已新增 `docs/validation/product-market-analysis-data-model-eval-fixtures-slice5-checklist-20260726.md`。
- 已冻结未来独立 `ProductMarketAnalysisGraph`、EvidenceCard、StateTransitionRecord、SkillHandoffRecord、MatrixRowRecord、Gap/Conflict、状态枚举、非法状态流转和证据覆盖规则。
- 已设计首批 pass/fail eval fixture 清单与错误码草案，覆盖搜索摘要升级、Skill 摘要当来源、QCVN 升级 UN38.3、候选税号变最终税率、网页标签变实物标签合规、Google Trends 写成销量、物流承诺、起运港猜测、未执行行丢失等。
- 后续已进入 Slice 6 实现前执行计划。

## 产品出海市场分析：实现前执行计划 Slice 6

- 已新增 `spec/17-product-outbound-market-analysis-implementation-plan.md`。
- 已新增 `docs/validation/product-market-analysis-implementation-plan-slice6-checklist-20260726.md`。
- 已冻结后续实现顺序：Schema 骨架、语义 validator、eval fixtures/cases、audit 最小门禁、CSV/Markdown 最小导出、eval 集成、Skill 文档/路由接入、真实来源采集接入。
- 已冻结第一批建议 pass/fail fixture 和错误码，第一轮代码目标是防错闭环，不接 Google Trends、关税 API、法规库或真实搜索。
- 后续已进入 Slice 7 Skill 文案/用户入口设计。

## 产品出海市场分析：Skill 文案与用户入口设计 Slice 7

- 已新增 `spec/18-product-outbound-market-analysis-skill-copy-and-user-entry.md`。
- 已新增 `docs/validation/product-market-analysis-skill-copy-entry-slice7-checklist-20260726.md`。
- 已冻结用户入口、触发词、非触发词、容易误判表达、首轮回应模板、缺信息追问模板、最多 3 个追问规则、用户材料说明、输出承诺和未来 Skill description 草案。
- 文档验收通过：产品市场分析与批量客户开发/单客背调入口区分清楚；用户问“值不值得做”时只转客观分析；同时要求市场和找客户时拆成两个阶段；Xing Heng / UNIQLO 样本文案未越界。
- 后续已完成 Slice 8 真实来源采集策略。

## 产品出海市场分析：真实来源采集策略 Slice 8

- 已新增 `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md`。
- 已新增 `docs/validation/product-market-analysis-real-source-collection-slice8-checklist-20260726.md`。
- 已冻结真实来源采集流程：Brief、能力预检、采集计划、搜索线索、打开来源、证据卡、交叉复核、矩阵交付。
- 已冻结各事实域来源优先级和降级策略，覆盖产品资料、Google Trends、市场/价格、目的国准入、进口税费、出口国要求、物流/预申报、近期外部因素。
- 已提出 Source Pack 机制，避免国家逐一硬编码；Source Pack 只是来源入口目录，不是事实库。
- 后续已完成 Slice 9 Source Pack 字段合同。

## 产品出海市场分析：Code Slice D-E

- 已新增 `scripts/audit_product_market_analysis.py`，用于最小 audit 门禁。
- 已新增 `scripts/export_product_market_workbook.py`，用于 12 张 CSV + 可选 Markdown / manifest 的安全导出。
- 已新增 `evals/run_product_market_analysis_evals.py`，用于独立 market suite 验收。
- 已新增 `evals/fixtures/market_fail_blocked_needs_input_minimal.json`，用于验证 `blocked_needs_input` 分流。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-d-e-20260726.md`。
- 已验证：Xing Heng / UNIQLO pass 样本可通过 audit 并导出；候选税号升级 fail 样本被 audit 阻断；独立 market suite `21/21` 通过；现有 `default/deep` 主 eval 未回归。

## 产品出海市场分析：Source Pack 字段合同 Slice 9

- 已新增 `spec/20-product-outbound-market-analysis-source-pack-contract.md`。
- 已新增 `docs/validation/product-market-analysis-source-pack-contract-slice9-checklist-20260726.md`。
- 已冻结 Source Pack 的对象边界、Pack 类型、SourcePack / SourceEntry / QueryTemplate / ObservationRequirement / PackRouteRule 字段、状态枚举、产品触发标签、路由规则和禁止字段。
- 文档验收通过：Source Pack 只是来源入口目录，不是事实库；Pack / Entry / QueryTemplate 不能直接变 EvidenceCard 或 MatrixRow 事实；Pack 日期不能当法规/税率/价格日期。
- 后续已完成 Slice 10 Source Pack 种子样例设计。

## 产品出海市场分析：Source Pack 种子样例 Slice 10

- 已新增 `spec/21-product-outbound-market-analysis-source-pack-seed-samples.md`。
- 已新增 `docs/validation/product-market-analysis-source-pack-seed-samples-slice10-checklist-20260726.md`。
- 已用美国 / 中国 / 越南 + 跨太平洋物流 / 美国市场信号 / 锂电通用规则 / 纺织服装通用规则 / 产品原始来源设计首批种子 Pack 样例。
- 已设计 SourceEntry 类型、QueryTemplate、PackRouteRule、ObservationRequirement 的种子样例，并演示 Xing Heng / UNIQLO 两个样本如何路由。
- 文档验收通过：种子样例没有填具体税率、认证结论、固定物流时效、趋势结论、价格区间或市场进入建议。
- 后续已完成 Slice 11 端到端运行剧本。

## 产品出海市场分析：端到端运行剧本 Slice 11

- 已新增 `spec/22-product-outbound-market-analysis-end-to-end-runbook.md`。
- 已新增 `docs/validation/product-market-analysis-end-to-end-runbook-slice11-checklist-20260726.md`。
- 已冻结 Brief -> Source Pack -> Query Plan -> SearchLog / Source -> Observation -> EvidenceCard -> MatrixRow -> Markdown / XLSX 的端到端人工运行顺序。
- 已明确三道门禁、状态流转、Skill 交接、打回/降级点、两个样本人工剧本、Mermaid 图和用户可见报告骨架。
- 文档验收通过：Xing Heng 不升级 UN38.3/SDS/普通货/起运港/最终税率；UNIQLO 不升级实物标签合规/全成分/出口申报国/起运港/最终归类；趋势、价格、物流和价值判断均未越界。
- 后续已完成 Slice 12 MVP 收口与实现前冻结。

## 产品出海市场分析：MVP 收口与实现前冻结 Slice 12

- 已新增 `spec/23-product-outbound-market-analysis-mvp-freeze.md`。
- 已新增 `docs/validation/product-market-analysis-mvp-freeze-slice12-checklist-20260726.md`。
- 已把 Slice 1-11 收口为 MVP-0 防错闭环、MVP-1 安全交付骨架、MVP-2 Skill 入口接入、MVP-3 真实来源采集四层。
- 已冻结第一轮优先 Code Slice A-C：schema、validator、首批 fixtures；若需要可扩到 A-E：audit 与 CSV/Markdown 最小导出。
- 已明确第一轮不接 Google Trends、关税 API、真实法规库、真实 Source Pack registry，不改批量客户开发和单客背调主流程。
- 下一步二选一：先提交 Slice 1-12 文档；或用户明确后开始 Code Slice A-C。

## 产品出海市场分析：Code Slice A-C schema / validator / fixtures

- 已新增 `shared/schemas/product-market-analysis.schema.json`。
- 已新增 `scripts/validate_product_market_analysis.py`。
- 已新增 `evals/cases/product_market_analysis_cases.json`。
- 已新增首批 market fixtures：
  - pass：`market_pass_xingheng_minimum_boundary.json`、`market_pass_uniqlo_minimum_boundary.json`、`market_pass_search_summary_candidate_only.json`、`market_pass_not_executed_modules_retained.json`、`market_pass_derived_wh_with_formula.json`、`market_pass_conflict_preserved.json`。
  - fail：`market_fail_search_summary_as_verified.json`、`market_fail_skill_summary_as_source.json`、`market_fail_qcvn_as_un38_3.json`、`market_fail_candidate_htsus_as_final_rate.json`、`market_fail_web_label_as_physical_compliance.json`、`market_fail_google_trends_as_sales.json`、`market_fail_logistics_best_or_committed.json`、`market_fail_departure_port_guessed.json`、`market_fail_not_executed_rows_missing.json`、`market_fail_source_local_path_or_hash_leak.json`、`market_fail_matrix_row_missing_status.json`、`market_fail_value_judgment_in_delivery.json`、`market_fail_geo_roles_merged.json`、`market_fail_brief_changed_without_rerun.json`。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-a-c-20260726.md`。
- 已验证：
  - `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_*.json` 通过。
  - `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_fail_*.json` 按预期失败并覆盖预期错误码。
  - `python3 evals/run_evals.py --suite default`：`77/77`。
  - `python3 evals/run_evals.py --suite deep`：`623/623`。
  - `python3 evals/run_evals.py --suite all`：`663/663`。
- 当前下一步：继续 Code Slice D-E（audit 最小门禁 + CSV/Markdown 最小导出）。

## 产品出海市场分析：真实业务感 fixture 补充

- 已新增 3 个更贴近真实业务的 pass fixture：Tianneng 锂电、XM Canvas-270 面料、平台/零售价格仅参考。
- 已新增 3 个更贴近真实业务的 fail fixture：工厂新闻升级原产地/默认港口、纺织证书/HTS 过度断言、平台价升级成交价/推荐价。
- 已新增 validator 错误码 `market_platform_price_promoted`。
- 已新增验证记录：`docs/validation/product-market-analysis-realistic-fixtures-20260726.md`。
- 已验证独立 market suite：`python3 evals/run_product_market_analysis_evals.py --suite all` = `27/27`。
- 已回归通过：`python3 evals/run_product_market_analysis_evals.py --suite all` = `27/27`；`python3 evals/run_evals.py --suite default` = `77/77`；`deep` = `623/623`；`all` = `663/663`。当前下一步可提交本轮 fixture 增补。

## 产品出海市场分析：Slice 13 COO / 原产地证明需求判断

- 已新增 Slice 13 设计文档：`spec/24-product-outbound-market-analysis-origin-proof-requirements.md`。
- 已新增验收清单：`docs/validation/product-market-analysis-origin-proof-requirements-slice13-checklist-20260727.md`。
- 已同步更新既有规格：产品合同、工作簿合同、证据边界、Skill 分工、真实来源采集策略、Source Pack 字段合同、端到端 runbook。
- 已冻结规则：目标国是否需要 COO / proof of origin 必须主动按官方/权威来源判断；用户当前是否有 COO 只是材料准备状态，不能反推法规要求。
- 下一步代码增量建议：schema / validator / fixtures 增加 `origin_proof_requirement` 行类型、目标国要求状态、用户材料状态和对应 fail 规则。

## 产品出海市场分析：Code Slice F COO / 原产地证明防错规则

- 已更新 schema：新增 `OriginProofRequirementStatus`、`OriginProofUserMaterialStatus`、`MatrixRowType`、`OriginProofRequirementRecord`，并允许矩阵行挂载 `origin_proof_requirement`。
- 已更新 validator，新增错误码：
  - `market_origin_proof_user_material_conflated`
  - `market_origin_marking_conflated_with_coo`
  - `market_origin_preferential_overgeneralized`
  - `market_user_coo_promoted_to_official_ruling`
  - `market_origin_requirement_without_authority`
- 已新增 4 个 pass fixture：
  - `market_pass_origin_proof_conditionally_required_user_missing.json`
  - `market_pass_origin_proof_normally_not_required_marking_required.json`
  - `market_pass_origin_proof_user_coo_scope_limited.json`
  - `market_pass_origin_proof_unable_to_verify_source_limited.json`
- 已新增 5 个 fail fixture：
  - `market_fail_user_missing_coo_as_not_required.json`
  - `market_fail_marking_as_coo_required.json`
  - `market_fail_preferential_origin_as_all_imports.json`
  - `market_fail_coo_as_final_origin_ruling.json`
  - `market_fail_origin_requirement_without_official_source.json`
- 已更新 `evals/cases/product_market_analysis_cases.json`，market case 总数为 36。
- 已增强 `evals/run_product_market_analysis_evals.py`：fail case 会检查 `expected_error_codes`。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-f-origin-proof-20260727.md`。
- 已验证：
  - `python3 evals/run_product_market_analysis_evals.py --suite all` = `36/36`
  - `python3 evals/run_evals.py --suite default` = `77/77`
  - `python3 evals/run_evals.py --suite deep` = `623/623`
  - `python3 evals/run_evals.py --suite all` = `663/663`
- 当前下一步：提交 Code Slice F；之后可选 Code Slice G（导出列/Markdown 展示优化）或 Skill 入口接入前的最小路由设计。

## 产品出海市场分析：Code Slice G Skill 入口与路由

- 已新增 `skills/analyzing-product-outbound-market/` 独立 Skill 入口。
- 已新增 `shared/references/product-outbound-market-intake.md`，包含触发/非触发、首轮回应、追问和产品触发项提示。
- 已更新 `using-superleads`、`route-map`、`user-intake`，明确产品出海市场分析、批量客户开发、客户背调三条路线并列。
- 已新增 `scripts/route_superleads_intake.py` 作为轻量路由 guardrail。
- 已新增 `evals/cases/superleads_route_cases.json` 和 `evals/behavioral/product-market-route-prompts.json`。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-g-skill-entry-routing-20260727.md`。
- 已验证：market suite `36/36`；主 default `84/84`；deep `630/630`；all `670/670`。
- 当前下一步：提交 Code Slice G；然后进入 Code Slice H（导出列/Markdown 展示优化）。

## 产品出海市场分析：Code Slice H 导出列 / Markdown 展示优化

- 已优化 `export_product_market_workbook.py`：CSV/Markdown 字段名更人话，新增贸易前提拆分行、COO Markdown 专区和未执行模块顶部摘要。
- 已把 COO / proof of origin 的用户可见展示改为“目标国是否要求原产地证明”“用户现在有没有可用材料”“什么情况下需要”“不能写成什么”。
- 已把默认出口申报国、原产国/制造来源、实际起运地/起运港拆开展示；未知港口仍保留待业务确认，不猜港。
- 已更新导出回归断言并新增验证记录：`docs/validation/product-market-analysis-code-slice-h-export-display-20260727.md`。
- 已验证：market suite `36/36`；主 default `84/84`；deep `630/630`；all `670/670`。
- 下一步建议：Code Slice I，做真实 Source Pack registry / Query Plan 读取骨架，仍只生成来源计划，不自动生成事实。

## 产品出海市场分析：Code Slice I Source Pack / Query Plan

- 已新增 seed Source Pack registry：`shared/source_packs/product_market_seed_packs.json`。
- 已新增 Query Plan generator：`scripts/plan_product_market_sources.py`。
- 已新增 source-plan fixtures / cases / runner：
  - `evals/fixtures/source_plan_*_brief.json`
  - `evals/cases/product_market_source_plan_cases.json`
  - `evals/run_product_market_source_plan_evals.py`
- 已验证：source-plan `6/6`、market `36/36`、default `84/84`、deep `630/630`、all `670/670`。
- 当前下一步：Code Slice J，设计 Query Plan 执行记录与真实来源采集衔接的最小 SearchLog / Source / Observation 夹具；继续保持“搜索摘要不成事实、未打开来源不成证据”。
