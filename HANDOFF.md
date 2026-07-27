# Handoff

- 分支：`master`
- 最新提交：以 `git log --oneline -1` 为准；本文件记录到 Code Slice A-C
- 当前工作树：Code Slice A-C 已完成并纳入本次提交边界；无关未跟踪目录保留不处理。

## 已验证

- 默认套件：`77/77`
- 深度套件：`623/623`
- 全量套件：`663/663`
- `source.open` 公开 GET 烟测已恢复（`https://example.com`，`200`）
- `tmp/stage5_chillys/chillys_stage5_real_graph.json`、`audit_delivery`、`export_workbook` 链路可用

## 当前结论

仓库核心图谱/导出/审计链路稳定。当前已恢复 `source.open`，但 `search.web` 仍未知，因此下一步是争取搜索能力，或接受用户给定 URL/目录材料继续做公开来源读取。

## 下一步

1. 争取 `search.web` 或用户给定 URL 列表。
2. 再按默认发现文档完成 20+ Candidate 验证。
3. 处理 `tmp/stage5_chillys/` 的长期归档方式。
## 产品出海市场分析补充状态

- 2026-07-26 已按公开来源试填两个样本，见 `docs/validation/product-market-analysis-public-source-fill-20260726.md`。
- 可用示范 SKU：Tianneng `TMLiN-4810S1`（锂电动力电池）、XM Textiles `Canvas-270`（涤棉工作服面料）。
- 已验证：公开 PDF/TDS 可抽取产品技术字段；原产地只能停在证据状态，不能由“某国工厂/办公室/出货地”推断为 SKU 原产。
- 下一步：如果用户确认继续，应基于该文档把“原产地证据等级”和“技术资料缺口矩阵”纳入产品合同或未来 Skill 验收。

## 产品出海市场分析真实样本状态

- 2026-07-26 已按公开来源复核 Xing Heng / UNIQLO 两个真实样本，见 `docs/validation/product-market-analysis-public-source-fill-xingheng-uniqlo-20260726.md`。
- 样本 A：Xing Heng `48V20Ah` LiFePO4 电池包，Design No. `BAT001.02`；公开来源支持越南制造/装配线索、48V/20Ah、960Wh 派生值、候选 HTSUS `8507.60.00`；UN38.3、SDS、包装、起运港和最终归类仍待确认。
- 样本 B：UNIQLO Men's Corduroy Overshirt，Product ID `470177`；公开来源支持 `Production: China`、Body/Trim 100% Cotton、8-wale corduroy、RN 139864、洗护说明、候选 HTSUS `6205.20.20`；实物标签、辅料/BOM、起运港和最终归类仍待确认。
- 产品合同已加入外部模型结果处理、原产地证据等级、认证/测试/SDS 边界、HS/HTS 候选边界。下一步可进入端到端输出矩阵验收设计，暂不需要继续更换样本。

## 产品出海市场分析输出矩阵状态

- 2026-07-26 已新增 `spec/12-product-outbound-market-analysis-output-matrix-and-acceptance.md`，冻结第一版用户可见报告顺序、XLSX/CSV 表结构、状态词和验收断言。
- 关键验收：候选税号不得变最终税率；QCVN/Vietnam Register 文件不得变 UN38.3/SDS；UNIQLO 网页文案不得变实物标签已合规；未执行的 Google Trends/价格/节假日/外部因素必须显式写未执行。
- 下一步建议：做 Slice 1 静态样本报告模板，不联网、不接新数据源，只验证输出矩阵和负向断言。

## 产品出海市场分析静态样例报告 Slice 1

- 2026-07-26 已新增 `docs/validation/product-market-analysis-static-sample-reports-slice1-20260726.md`。
- 该样例模拟用户在 ChatGPT app / Codex 中看到的两份表格化报告：Xing Heng 锂电与 UNIQLO 纺织品。
- 已通过文档内自检：不出现市场进入建议、不把候选税号当最终税率、不把 QCVN/Vietnam Register 当 UN38.3/SDS、不把网页标签当实物标签已合规、不编造未执行的趋势/价格/节日/外部因素。
- 下一步建议：做 Slice 2 XLSX/CSV 表头与状态枚举，不需要先接入联网研究。

## 产品出海市场分析工作簿合同 Slice 2

- 2026-07-26 已新增 `spec/13-product-outbound-market-analysis-workbook-contract.md`，冻结 12 张 XLSX/CSV 工作表、字段顺序、状态枚举、空值保留规则和最小行数要求。
- 已新增 `docs/validation/product-market-analysis-workbook-slice2-sample-matrix-20260726.md`，给出 Xing Heng / UNIQLO 两个样本的最小行矩阵。
- 关键规则：未知不留空、不填 0；未执行模块也保留行；每行有状态；候选 HTSUS、UN 编号、运输方式不得升级为最终结论；来源表不得暴露本地路径/哈希/内部 ID。
- 下一步建议：Slice 3 证据边界校验规则，可先做文档清单，再决定是否进入轻量脚本/evals。

## 产品出海市场分析证据边界校验规则 Slice 3

- 2026-07-26 已新增 `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md`，冻结证据类型、允许表述、禁止升级、降级/阻断和样本特定断言。
- 已新增 `docs/validation/product-market-analysis-evidence-boundary-slice3-checklist-20260726.md`，对 Slice 1 Markdown 样例和 Slice 2 工作簿矩阵做人工边界验收。
- 关键规则：搜索/外部模型只能做候选线索；QCVN/Vietnam Register 不能升级 UN38.3/SDS；网页标签不能升级实物标签合规；官方税则税率不能升级最终税率；运输方式不能升级最佳方式或承运承诺；未执行市场模块必须写未执行。
- 后续已进入 Slice 4 Skill 分工互证流程。

## 产品出海市场分析 Skill 分工互证流程 Slice 4

- 2026-07-26 已新增 `spec/15-product-outbound-market-analysis-skill-orchestration.md`，冻结六个 Skill 的分工、共享证据卡、互证矩阵、三道门禁、打回/降级规则、状态流转和 Brief 改版重跑触发。
- 已新增 `docs/validation/product-market-analysis-skill-orchestration-slice4-checklist-20260726.md`，完成人工验收：前序 Skill 摘要不能直接变事实，搜索摘要只能做线索，冲突/缺口/未执行必须保留到最终矩阵。
- 两个样本验收边界已纳入流程：Xing Heng 不得把 QCVN/Vietnam Register 升级为 UN38.3/SDS，不得默认起运港或最终税率；UNIQLO 不得把网页标签升级为实物标签合规，不得把候选 `6205.20.20` 写成最终归类。
- 后续已进入 Slice 5 数据模型与 eval 夹具设计。

## 产品出海市场分析数据模型与 eval 夹具设计 Slice 5

- 2026-07-26 已新增 `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md`，冻结未来独立 `ProductMarketAnalysisGraph`、EvidenceCard、StateTransitionRecord、SkillHandoffRecord、MatrixRowRecord、Gap/Conflict、状态枚举、非法状态流转和证据覆盖规则。
- 已新增 `docs/validation/product-market-analysis-data-model-eval-fixtures-slice5-checklist-20260726.md`，完成人工验收：数据模型不把产品市场分析塞进 Candidate / Claim / Assessment，搜索摘要和 Skill 摘要不能升级事实，工作簿行必须追到证据卡/缺口/未执行记录。
- 首批 eval 夹具设计已覆盖：Xing Heng / UNIQLO 最小通过样本、搜索候选、未执行保留、冲突保留、Brief 改版降级，以及 QCVN->UN38.3、候选 HTSUS->最终税率、网页标签->实物标签合规、Google Trends->销量、物流承诺、起运港猜测、内部路径泄露等失败样本。
- 后续已进入 Slice 6 实现前执行计划。

## 产品出海市场分析实现前执行计划 Slice 6

- 2026-07-26 已新增 `spec/17-product-outbound-market-analysis-implementation-plan.md`，冻结后续代码实现顺序：Schema 骨架、语义 validator、eval fixtures/cases、audit 最小门禁、CSV/Markdown 最小导出、eval 集成、Skill 文档/路由接入、真实来源采集接入。
- 已新增 `docs/validation/product-market-analysis-implementation-plan-slice6-checklist-20260726.md`，完成人工验收：第一轮代码只做防错闭环，不接 Google Trends、关税 API、法规库或真实搜索，不影响现有 default/deep/all 套件。
- 第一批建议实现：Code Slice A-C，即 `shared/schemas/product-market-analysis.schema.json`、`scripts/validate_product_market_analysis.py`、`evals/cases/product_market_analysis_cases.json` 和首批 `market_pass_*.json` / `market_fail_*.json` fixture。
- 后续已进入 Slice 7 Skill 文案/用户入口设计。

## 产品出海市场分析 Skill 文案与用户入口设计 Slice 7

- 2026-07-26 已新增 `spec/18-product-outbound-market-analysis-skill-copy-and-user-entry.md`，冻结用户入口、触发词、非触发词、容易误判表达、首轮回应模板、缺信息追问模板、最多 3 个追问规则、用户材料说明、输出承诺和未来 Skill description 草案。
- 已新增 `docs/validation/product-market-analysis-skill-copy-entry-slice7-checklist-20260726.md`，完成人工验收：产品市场分析与批量客户开发/单客背调入口区分清楚；用户问“值不值得做”时只转客观分析；同时要求市场和找客户时拆成两个阶段。
- 样本文案验收通过：Xing Heng 锂电样本保留 UN38.3/SDS/包装/起运港/最终税率边界；UNIQLO 纺织样本保留实物标签/BOM/克重/起运港/最终归类边界。
- 后续已完成 Slice 8 真实来源采集策略。

## 产品出海市场分析真实来源采集策略 Slice 8

- 2026-07-26 已新增 `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md`，冻结真实来源采集流程、能力门槛、来源优先级、Query Plan、Source/Observation 记录规则、“最新”口径、Source Pack 概念和两个样本来源路径。
- 已新增 `docs/validation/product-market-analysis-real-source-collection-slice8-checklist-20260726.md`，完成人工验收：搜索摘要不能变事实，打开来源才形成 Observation；官方/原始来源优先，平台/摘要仅参考；能力不足时降级为候选、来源受限、未执行或待确认。
- 样本来源路径已冻结但不新增事实：Xing Heng 需覆盖产品页/证书/危险品法规/税则/出口国/物流/市场，且不得升级 UN38.3/SDS/起运港/最终税率；UNIQLO 需覆盖产品页/实物标签/BOM/美国标签规则/税则/出口国/物流/市场，且不得升级实物标签合规/最终归类。
- 后续已完成 Slice 9 Source Pack 字段合同。

## 产品出海市场分析 Source Pack 字段合同 Slice 9

- 2026-07-26 已新增 `spec/20-product-outbound-market-analysis-source-pack-contract.md`，冻结 Source Pack 的对象边界、Pack 类型、SourcePack / SourceEntry / QueryTemplate / ObservationRequirement / PackRouteRule 字段、状态枚举、产品触发标签、路由规则和禁止字段。
- 已新增 `docs/validation/product-market-analysis-source-pack-contract-slice9-checklist-20260726.md`，完成人工验收：Source Pack 只是来源入口目录，不是事实库；Pack / Entry / QueryTemplate 不能直接变 EvidenceCard 或 MatrixRow 事实；Pack 日期不能当法规/税率/价格日期。
- 样本路由边界已纳入字段合同：Xing Heng 锂电样本不得由美国/锂电/物流 Pack 升级 UN38.3、SDS、起运港或最终税率；UNIQLO 纺织样本不得由美国/中国/纺织 Pack 升级实物标签合规、起运港或最终归类。
- 后续已完成 Slice 10 Source Pack 种子样例设计。

## 产品出海市场分析 Source Pack 种子样例 Slice 10

- 2026-07-26 已新增 `spec/21-product-outbound-market-analysis-source-pack-seed-samples.md`，用美国 / 中国 / 越南 + 跨太平洋物流 / 美国市场信号 / 锂电通用规则 / 纺织服装通用规则 / 产品原始来源设计首批种子 Pack 样例。
- 已新增 `docs/validation/product-market-analysis-source-pack-seed-samples-slice10-checklist-20260726.md`，完成人工验收：种子样例没有填具体税率、认证结论、固定物流时效、趋势结论、价格区间或市场进入建议。
- 已设计 SourceEntry 类型、QueryTemplate、PackRouteRule、ObservationRequirement 的种子样例，并演示 Xing Heng / UNIQLO 两个样本如何路由；Xing Heng 不升级 UN38.3/SDS/起运港/最终税率，UNIQLO 不升级实物标签合规/起运港/最终归类。
- 后续已完成 Slice 11 端到端运行剧本。

## 产品出海市场分析端到端运行剧本 Slice 11

- 2026-07-26 已新增 `spec/22-product-outbound-market-analysis-end-to-end-runbook.md`，冻结 Brief -> Source Pack -> Query Plan -> SearchLog / Source -> Observation -> EvidenceCard -> MatrixRow -> Markdown / XLSX 的端到端人工运行顺序。
- 已新增 `docs/validation/product-market-analysis-end-to-end-runbook-slice11-checklist-20260726.md`，完成人工验收：三道门禁、状态流转、Skill 交接、打回/降级点、两个样本人工剧本、Mermaid 图和用户可见报告骨架均已覆盖。
- 样本边界：Xing Heng 不升级 UN38.3/SDS/普通货/起运港/最终税率；UNIQLO 不升级实物标签合规/全成分/出口申报国/起运港/最终归类；趋势、价格、物流和价值判断均未越界。
- 后续已完成 Slice 12 MVP 收口与实现前冻结。

## 产品出海市场分析 MVP 收口与实现前冻结 Slice 12

- 2026-07-26 已新增 `spec/23-product-outbound-market-analysis-mvp-freeze.md`，把 Slice 1-11 收口为 MVP-0 防错闭环、MVP-1 安全交付骨架、MVP-2 Skill 入口接入、MVP-3 真实来源采集四层。
- 已新增 `docs/validation/product-market-analysis-mvp-freeze-slice12-checklist-20260726.md`，完成人工验收：第一轮优先 Code Slice A-C；需要导出时扩到 A-E；不接 Google Trends、关税 API、真实法规库或真实 Source Pack registry。
- 已冻结首批 pass/fail fixture、错误码、验收命令顺序和提交边界；实现前建议先确认是否提交 Slice 1-12 文档。
- 下一步：二选一——先提交 Slice 1-12 文档，或在用户明确后开始 Code Slice A-C。

## 产品出海市场分析 Code Slice A-C 实现状态

- 2026-07-26 已开始并完成第一轮 Code Slice A-C：schema、validator、首批 fixtures。
- 新增 schema：`shared/schemas/product-market-analysis.schema.json`，定义最小 `ProductMarketAnalysisGraph`，包含 runs / briefs / products / trade_premises / attributes / sources / observations / evidence_cards / matrix_rows / gaps / conflicts / handoffs / state_transitions。
- 新增 validator：`scripts/validate_product_market_analysis.py`，输出 JSON `{ ok, issue_count, issues }`，支持单文件和多文件输入，支持 fixture `extends` / `patches`。
- 新增 case 合同：`evals/cases/product_market_analysis_cases.json`。注意：现有 `evals/run_evals.py` 暂不会执行 `market_validate` 字段；market suite 当前用独立 validator 命令验收。
- 新增 fixtures：6 个 `market_pass_*.json`，14 个 `market_fail_*.json`。覆盖 Xing Heng / UNIQLO 最小边界、搜索摘要候选、未执行模块保留、派生 Wh、冲突保留，以及搜索摘要升级、Skill 摘要当来源、QCVN->UN38.3、候选 HTSUS->最终税率、网页标签->实物标签合规、Google Trends->销量、物流承诺、默认起运港、未执行行丢失、内部路径泄露、缺状态、价值判断、地理角色混写、Brief 过期交付。
- 验证记录：`docs/validation/product-market-analysis-code-slice-a-c-20260726.md`。
- 已验证：`python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_*.json` 通过；`market_fail_*.json` 按预期 exit 1 并覆盖预期错误码；`python3 evals/run_evals.py --suite default` 为 `77/77`，`deep` 为 `623/623`，`all` 为 `663/663`。数量比上一轮各多 1 是新增 schema self-check 被纳入。
- Code Slice A-C 已纳入提交边界；无关未跟踪目录 `skillhub-package/`、`social-card-superleads-cover/`、`social-card-superleads-trade-cover/` 仍未处理。
- 下一步建议：Code Slice D-E，即最小 audit 门禁和 CSV/Markdown 导出。

## 产品出海市场分析 Code Slice D-E 实现状态

- 2026-07-26 已新增 `scripts/audit_product_market_analysis.py` 与 `scripts/export_product_market_workbook.py`，补齐 market 模块的最小审计与安全导出链路。
- 已新增 `evals/run_product_market_analysis_evals.py`，用于独立跑 market pass / fail / blocked 样本；不会改动现有 `evals/run_evals.py` 主链路。
- 已新增 `evals/fixtures/market_fail_blocked_needs_input_minimal.json`，用于验证 `blocked_needs_input` 分流。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-d-e-20260726.md`。
- 已验证：
  - `python3 scripts/audit_product_market_analysis.py evals/fixtures/market_pass_xingheng_minimum_boundary.json --format json` 通过，`delivery_status=ready_with_limitations`。
  - `python3 scripts/audit_product_market_analysis.py evals/fixtures/market_fail_blocked_needs_input_minimal.json --format json` 分流为 `blocked_needs_input`。
  - `python3 scripts/export_product_market_workbook.py evals/fixtures/market_pass_uniqlo_minimum_boundary.json --output-dir ... --format csv --markdown ... --manifest ...` 通过，12 张 CSV + Markdown + manifest 可生成。
  - `python3 scripts/export_product_market_workbook.py evals/fixtures/market_fail_candidate_htsus_as_final_rate.json --output-dir ... --format csv` 被 audit 阶段阻断。
  - `python3 evals/run_product_market_analysis_evals.py --suite all` 通过，`21/21`。
- 现有 `default/deep` 主 eval 未回归：`77/77`、`623/623` 保持通过。

## 产品出海市场分析：真实业务感 fixture 补充

- 2026-07-26 已按用户要求补充更贴近真实业务的 market pass/fail fixture。
- 新增 pass：
  - `evals/fixtures/market_pass_tianneng_lithium_realistic_boundary.json`：Tianneng `TMLiN-4810S1` 锂电目录字段、480Wh 派生、越南工厂线索边界、UN38.3/SDS/包装/起运节点缺口。
  - `evals/fixtures/market_pass_xm_canvas_realistic_boundary.json`：XM Textiles `Canvas-270` TDS 字段、纺织归类/标签缺口、Oeko-Tex 与 `0 Certificates` 冲突保留、中国出货线索边界。
  - `evals/fixtures/market_pass_platform_price_reference_only.json`：零售/平台标价仅作为线上市场参考，不升级成交价、批发价、目标价或推荐报价。
- 新增 fail：
  - `evals/fixtures/market_fail_factory_news_as_sku_origin_and_port.json`：工厂新闻升级 SKU 原产地并默认海防港，触发 `market_guess_departure_port`。
  - `evals/fixtures/market_fail_textile_cert_and_hts_overstated.json`：证书文字与纺织候选归类被升级为最终结论，触发 `market_candidate_hs_promoted_to_final`。
  - `evals/fixtures/market_fail_platform_price_as_recommended_transaction_price.json`：零售标价升级成交价/推荐价，触发新增 `market_platform_price_promoted`，并由 `market_value_judgment` 兜底。
- Validator 新增 `market_platform_price_promoted` 规则，用于拦截线上/平台/零售挂牌价升级为成交价、批发价、外贸目标价或推荐报价。
- Case 文件已扩展到 27 个 market case；独立 market suite 已验证 `27/27`。
- 新增验证记录：`docs/validation/product-market-analysis-realistic-fixtures-20260726.md`。
- 已回归：`python3 evals/run_product_market_analysis_evals.py --suite all` = `27/27`；`python3 evals/run_evals.py --suite default` = `77/77`；`deep` = `623/623`；`all` = `663/663`。下一步可提交本轮 fixture 增补；不要处理 `tmp/stage5_chillys/`。

## 产品出海市场分析 Slice 13：目标国原产地证明 / COO 要求判断

- 2026-07-27 已新增 `spec/24-product-outbound-market-analysis-origin-proof-requirements.md` 和 `docs/validation/product-market-analysis-origin-proof-requirements-slice13-checklist-20260727.md`。
- 已将 Slice 13 语义同步回：`spec/10-product-outbound-market-analysis-contract.md`、`spec/13-product-outbound-market-analysis-workbook-contract.md`、`spec/14-product-outbound-market-analysis-evidence-boundary-rules.md`、`spec/15-product-outbound-market-analysis-skill-orchestration.md`、`spec/19-product-outbound-market-analysis-real-source-collection-strategy.md`、`spec/20-product-outbound-market-analysis-source-pack-contract.md`、`spec/22-product-outbound-market-analysis-end-to-end-runbook.md`。
- 核心纠偏：COO / proof of origin 必须拆成“目标国规则是否需要”和“用户材料是否已准备”两条线；用户未提供 COO 不等于目标国不需要，Made in / origin marking 不等于 COO 文件，优惠税率 proof of origin 不得泛化为所有普通进口必需，用户 COO 不等于海关最终原产地裁定。
- 工作簿新增 `origin_proof_requirement` 专门行语义，Source Pack 新增 `destination_origin_proof_pack` / `origin_proof_requirement` 查询组语义。
- 本轮仍为产品设计文档，不写代码、不联网验证具体国家规则。下一步若进入代码：扩展 schema / validator / fixtures，新增 `market_origin_proof_user_material_conflated`、`market_origin_marking_conflated_with_coo`、`market_origin_preferential_overgeneralized`、`market_user_coo_promoted_to_official_ruling`、`market_origin_requirement_without_authority` 等规则。

## 产品出海市场分析 Code Slice F：COO / 原产地证明防错闭环

- 2026-07-27 已把 Slice 13 落到代码层：`shared/schemas/product-market-analysis.schema.json` 新增 `OriginProofRequirementStatus`、`OriginProofUserMaterialStatus`、`MatrixRowType` 和 `OriginProofRequirementRecord`，`MatrixRowRecord` 允许 `row_type=origin_proof_requirement` 与 `origin_proof_requirement` 专门结构。
- `scripts/validate_product_market_analysis.py` 新增 5 个 COO / proof of origin 边界错误码：
  - `market_origin_proof_user_material_conflated`
  - `market_origin_marking_conflated_with_coo`
  - `market_origin_preferential_overgeneralized`
  - `market_user_coo_promoted_to_official_ruling`
  - `market_origin_requirement_without_authority`
- 新增 4 个 pass fixture：条件性需要但用户未提供、普通进口通常不要求但 marking 另列、用户 COO 仅限订单/批次范围、无权威来源时 `unable_to_verify`。
- 新增 5 个 fail fixture：用户没给 COO 被写成不需要、marking 当 COO、优惠 proof 泛化所有普通进口、用户 COO 当海关最终裁定、确定性 COO 状态无官方/权威来源。
- `evals/run_product_market_analysis_evals.py` 已增强：market fail case 现在会校验 `expected_error_codes`，避免“失败但不是预期原因”。
- 新增验证记录：`docs/validation/product-market-analysis-code-slice-f-origin-proof-20260727.md`。
- 已验证：
  - `python3 evals/run_product_market_analysis_evals.py --suite all` = `36/36`
  - `python3 evals/run_evals.py --suite default` = `77/77`
  - `python3 evals/run_evals.py --suite deep` = `623/623`
  - `python3 evals/run_evals.py --suite all` = `663/663`
- 边界：本轮 fixture 中的 CBP / USITC 文案仍是静态 eval 样本，不是联网核验真实美国最新规则；导出器仍只搬运已审矩阵，不补法规/税费/COO 事实。
- 下一步建议：提交 Code Slice F；之后进入 Code Slice G（可选）——把 `origin_proof_requirement` 的用户可见表头进一步固化到导出列/Markdown 展示，或开始 Skill 入口接入前的最小路由设计。

## 产品出海市场分析 Code Slice G：Skill 入口与路由最小闭环

- 2026-07-27 已新增 `skills/analyzing-product-outbound-market/SKILL.md` 和 `agents/openai.yaml`，作为产品出海市场分析的独立 Skill 入口。
- 已新增 `shared/references/product-outbound-market-intake.md`，固化首轮四行回应、缺产品/缺国家追问、产品触发项提示、默认出口申报国和待确认边界。
- 已更新 `skills/using-superleads/SKILL.md`、`shared/references/route-map.md`、`shared/references/user-intake.md`：产品出海市场分析与批量客户开发、客户背调并列；“市场分析 + 找客户”拆阶段处理。
- 已新增 `scripts/route_superleads_intake.py` 和 `evals/cases/superleads_route_cases.json`，用确定性 route eval 覆盖：产品市场分析、纯找客户、纯背调、混合请求拆阶段、缺目标国。
- 已新增 `evals/behavioral/product-market-route-prompts.json`，覆盖入口行为提示。
- 已验证：
  - `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market` = `Skill is valid!`
  - `python3 evals/run_product_market_analysis_evals.py --suite all` = `36/36`
  - `python3 evals/run_evals.py --suite default` = `84/84`
  - `python3 evals/run_evals.py --suite deep` = `630/630`
  - `python3 evals/run_evals.py --suite all` = `670/670`
- 边界：路由脚本只是 guardrail，不生成 Brief/graph/事实；真实报告仍走 ProductMarketAnalysisGraph 和 A-F 防错链路。
- 下一步建议：Code Slice H，优化产品出海市场分析的导出列和 Markdown 展示，让 `origin_proof_requirement`、默认出口国/原产国/起运地、未执行模块在用户表格里更顺眼。

## 产品出海市场分析 Code Slice H：导出列与 Markdown 展示优化

- 2026-07-27 已优化 `scripts/export_product_market_workbook.py` 的用户可见字段名：`样本ID` -> `样本编号`，`目的国/地区` -> `目标销售国家/地区`，`候选 HS/HTS` -> `候选 HS/HTS（非最终归类）`，`限制说明/禁止升级` -> `不能推出什么/不能写成什么` 等。
- `市场事实总览` 现在自动补 `贸易前提拆分` 行，把目标销售国家/地区、出口申报国（默认可改）、原产国 / 制造来源（证据状态）、实际起运地 / 起运港、目的节点分开展示。
- Markdown 报告新增顶部 `先看这几个贸易前提`、`原产地证明 / COO 怎么看`、`本轮未执行项`；COO 状态在导出层人话化，例如“条件性需要”“用户未提供；若触发上述规则，需要补”“未能用权威来源核实”。
- 已更新 `evals/cases/product_market_analysis_cases.json` 的导出断言，覆盖字段名、COO 展示、地理拆分和未执行简写。
- 已验证：`python3 evals/run_product_market_analysis_evals.py --suite all` = `36/36`；主 default `84/84`；deep `630/630`；all `670/670`。
- 边界：本轮只优化展示层，不新增真实来源、税率、趋势、价格、法规或物流结论；底层 graph enum 保持不变。

## 产品出海市场分析：Code Slice I Source Pack registry / Query Plan

- 2026-07-27 已新增 `shared/source_packs/product_market_seed_packs.json`，作为产品出海市场分析第一批 seed Source Pack registry。
- Registry 覆盖 10 个 Pack：美国准入、美国税费、美国 COO/proof of origin、中国出口、越南出口、跨太平洋物流、美国市场信号、锂电通用规则、纺织服装通用规则、产品原始资料。
- 已新增 `scripts/plan_product_market_sources.py`：只生成 `source_plan_only` 查询计划；声明 `not_evidence`、`does_not_search_web`、`does_not_open_sources`，每个查询步骤强制 `must_open_source` 与 `reject_if_only_snippet`。
- 已新增 source-plan fixtures：Xing Heng 越南锂电出口美国、UNIQLO 中国纺织品出口美国、只有原产线索但无出口申报国、散杂/RoRo/大宗项目货、缺目标国阻断样本。
- 已新增 `evals/cases/product_market_source_plan_cases.json` 和 `evals/run_product_market_source_plan_evals.py`，验证 Pack 路由、QueryTemplate 覆盖和禁止升级断言。
- 已验证：source-plan suite `6/6`；market suite `36/36`；default `84/84`；deep `630/630`；all `670/670`。
- 边界：本轮不联网、不打开来源、不生成 EvidenceCard/MatrixRow，不输出税率、认证、物流时效、趋势、价格或市场进入建议。
- 下一步建议：Code Slice J，把 Source Plan 与真实采集运行记录衔接：Query Plan -> SearchLog / Source / Observation fixture，但仍先用可审计样本，不直接做默认真实发现。

## 产品出海市场分析：Code Slice J SearchLog / Source / Observation 执行记录

- 已新增 ProductMarketAnalysisGraph 可选 `search_logs`，用于记录 Query Plan 后续执行的搜索过程；SearchLog 仍是 `source_candidate_only`，不是事实来源。
- 已增强 `plan_product_market_sources.py --emit-collection-run-shell`，可输出空的 collection shell，把 pending query steps 映射到未来 SearchLog / Source / Observation 轨道；该 shell 不搜索、不打开来源。
- 已增强 validator：阻断 Query Plan / SearchLog 直接升级事实、搜索结果伪装 Source/Observation、未打开来源支撑 EvidenceCard、受限来源带事实摘录等。
- 已新增 Slice J pass/fail fixtures，market suite 变为 `42/42`。
- 已新增验证记录：`docs/validation/product-market-analysis-code-slice-j-collection-records-20260727.md`。
- 已验证：source-plan `6/6`、market `42/42`、default `84/84`、deep `630/630`、all `670/670`。
- 当前下一步：Code Slice K，可做真实来源采集执行器的“手工 URL 输入 / 打开来源记录”最小桥接；继续保持没有打开来源就不能形成 EvidenceCard。

## 产品出海市场分析 Code Slice K：手工 URL / 已知来源采集桥接

- 已新增 `scripts/collect_product_market_sources.py`，作为手工 URL / 已知来源 -> `Source` / `Observation` 的最小桥接脚本。
- 该脚本只搬运用户明确给定的公开 URL 和已知打开状态，不搜索、不抓取、不下载、不自动打开来源。
- 输出固定声明：`not_evidence=true`、`does_not_search_web=true`、`does_not_open_sources=true`、`does_not_create_evidence_cards=true`、`does_not_create_matrix_rows=true`。
- 已阻断：本地路径 / `file://`、token/API key/signature URL、未打开或受限来源携带事实 `raw_excerpt`、`search.web` 伪装 Observation。
- 已新增 source collection eval runner / cases / fixtures：官方产品页已打开、PDF URL shell、来源受限，以及 3 个失败夹具。
- 验证记录：`docs/validation/product-market-analysis-code-slice-k-manual-source-collection-20260727.md`。
- 已验证：source collection `6/6`、source-plan `6/6`、market `42/42`、default `84/84`、deep `630/630`、all `670/670`。下一步可提交 Code Slice K；之后进入 Code Slice L。

## 产品出海市场分析 Code Slice L：手工 collection 并入正式图谱 / 导出链路

- 2026-07-27 已新增 `scripts/merge_product_market_collection.py`，把 Slice K 的 `Source` / `Observation` collection 输出安全追加到正式 `ProductMarketAnalysisGraph`。
- 合并脚本固定声明并执行边界：`not_evidence=true`、不搜索、不打开来源、不创建 EvidenceCard、不创建 MatrixRow、不新增 SearchLog、不改变事实矩阵。
- 已新增 collection merge eval runner / cases / fixtures：官方产品页已打开、PDF URL shell、来源受限，以及重复 Source ID、夹带事实对象、`not_evidence=false`、Brief version mismatch 等失败夹具。
- 新增验证记录：`docs/validation/product-market-analysis-code-slice-l-collection-merge-export-20260727.md`。
- 已验证：collection merge `7/7`、source collection `6/6`、source-plan `6/6`、market `42/42`、default `84/84`、deep `630/630`、all `670/670`。
- 边界：新增来源只进入“信息来源与待确认事项”导出内容；不会自动升级 UN38.3/SDS、最终税率、物流路线、趋势、价格或市场进入判断。
- 当前下一步：提交 Code Slice L；之后可进入 Code Slice M，把 `collect -> merge -> validate/audit/export` 串成单个用户入口命令或半自动运行剧本。
