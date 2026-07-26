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

