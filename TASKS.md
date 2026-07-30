# Tasks

## 已完成

- 产品出海市场分析 Slice 1-13 及 Code Slice A-M 已完成。
- Slice R 产品内核复盘已完成，确认 Superleads 是外贸业务情报产品，不是通用工作流框架。
- Slice S 三路线真实外贸样本已完成。
- Slice T 用户可见输出合同与静态 eval 已完成。
- Code Slice U 三路线用户可见 Markdown 交付器已提交：`43f2ef7 Add Superleads Markdown delivery exporter`。
- Code Slice V README / Skill 使用说明 / 常用命令示例已提交：`8ea336a Document Superleads Markdown delivery usage`。
- Slice W 目的国认证 / 准入要求判断纠偏已提交：`8f6703a Calibrate product market certification requirements`。
- Code Slice X 认证 / 目的国准入要求防错闭环已提交：`85197d7 Add certification requirement guardrails`。
- Slice AA 弱证据外贸场景校准已完成并提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 多来源互证 / CorroborationRecord 最小闭环已完成并提交：`2073a98 Add weak-source corroboration records`。
- Code Slice AC 资料时效 / freshness 降级最小闭环已提交：`069314d Add product market freshness guardrails`。
- Slice AD 开放世界权威来源识别模型已完成并提交：`22be247 Document open world authority source model`。
- Code Slice AD 开放世界来源权威性防错闭环已完成并提交：`1b3c040 Add open-world authority verification guardrails`。
- Slice AE 状态词压缩 / 用户可见状态映射已完成并提交：`7caa2e4 Document user-visible status mapping`。
- Code Slice AE 状态投影工具 / 导出列 / 用户可见状态 eval 已完成并提交：`b08f966 Add user-visible status projection`。新增统一状态投影层、产品市场导出 `依据状态` / `依据说明`、用户可见内部状态 token 阻断。
- 状态同步已提交：`e966c27 Update handoff after status projection commit`。
- Code Slice AF 三路线入口路由纠偏 / route eval 已完成并提交：`0f7666e Add Superleads route intent evals`。路由样例扩到 25 条，新增独立 route eval runner，混合任务可校验 `secondary_routes` / `route_order`。
- 状态同步已提交：`2e5d2ed Update handoff after route evals commit`。
- Code Slice AG 单一客户背调工程资产补齐已完成并提交：`c8477d3 Add customer background research guardrails`。补 Skill 入口、专属 spec、专属 eval runner、6 条 graph fixtures、1 条用户可见 fail 样本，并强化轻验证与正式名单链路隔离。
- Slice AH 批量客户开发内核复盘纠偏已提交：`b0fdd53 Calibrate bulk discovery candidate pool`。取消独立 L2 `初筛客户名单` 层级，改为发现候选池内部三分区。
- Code Slice AH 已提交：`26e788f Refine bulk discovery status projection`：堵 `output_mode=初筛客户名单` 绕过口；bulk workbook / Markdown 新增 `分区`、`依据状态`；Markdown 补联系方式汇总、搜索覆盖与收敛、已排除/仅作参考、风险说明；用户可见 eval 阻断缺状态与缺表交付。当前又补了 `可能客户角色` 接入实体 `customer_type`、`observed` 上调为 `已有明确依据`，并新增 `采购意愿待确认` 的误杀回归样本。
- Code Slice AH-FIX 已收口并纳入本提交：修复 bulk 默认发现依据状态降级优先级；`observed + source_restricted` 投影为 `来源受限`，不再升级为 `已有明确依据`；新增用户可见 fail 样本、Markdown case、minimum gate 行级导出断言和验证文档。



## Code Slice AH-FIX 已完成

1. 依据状态降级优先级
   - `scripts/export_workbook.py` 增加共享 `project_default_discovery_basis_status`。
   - 默认发现先处理 `identity_pending` / `source_restricted` / `source_restrictions` / `insufficient_information` 等降级，再允许无降级的 `business_match.observed` 投影为 `已有明确依据`。
   - `scripts/export_superleads_markdown.py` 的回退逻辑复用 workbook 共享函数，避免两份映射漂移。
2. 回归保护
   - `evals/fixtures/pass_default_discovery_candidate_pool.json` 的 `Beta Industrial Supplies` 行必须包含 `来源受限` 且不得含 `已有明确依据`。
   - 新增用户可见 fail 样本 `fail_bulk_customer_source_restricted_promoted_basis.md`，命中 `bulk_basis_status_source_restricted_promoted`。
   - bulk 用户可见样本 / Markdown delivery case 同时要求 `已有明确依据` 与 `来源受限`。
3. 已验证
   - `python3 evals/run_evals.py --suite default` → 121/121。
   - `python3 evals/run_evals.py --suite deep` → 670/670。
   - `python3 evals/run_evals.py --suite all` → 713/713。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 13/13。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 evals/run_superleads_route_evals.py --suite all` → 25/25。
   - `python3 evals/run_product_market_analysis_evals.py --suite all` → 74/74。
   - `python3 evals/run_customer_background_research_evals.py --suite all` → 6/6。

## Code Slice AH 已完成

1. 绕过口修复
   - `scripts/validate_research_graph.py` 将 `初筛客户名单` 纳入默认发现 Candidate 结构检查，并显式报 `initial_screening_output_mode_deprecated`。
   - 新增 `evals/fixtures/fail_initial_screening_output_mode_bypass.json`，复现旧绕过：`output_mode=初筛客户名单` + 删除 `dedupe_basis` / `signal_summary` / `business_relevance_basis` / `unknowns` / `source_restrictions`。
   - 该 fixture 已纳入 default suite，validate / audit / export initial 均 fail。
2. 默认发现展示
   - `scripts/export_workbook.py` 的 `发现候选池` sheet 新增 `分区`、`依据状态`。
   - `scripts/export_superleads_markdown.py` 的 bulk 路线补为 8 张表：方向、候选池、联系方式汇总、搜索覆盖与收敛、待确认事项、已排除 / 仅作参考、来源、风险说明。
   - 主表新增 `国家/地区`、`可能客户角色`、`业务相关性`、`依据状态`，不做价值排序、不写推荐客户。
3. 用户可见 eval
   - bulk 路线要求出现 `依据状态`、可优先人工跟进、待确认、已排除 / 仅作参考、联系方式汇总、搜索覆盖与收敛、风险与说明。
   - 新增 fail 样本 `fail_bulk_customer_missing_basis_status.md`。
4. 已验证
   - `python3 -m py_compile scripts/validate_research_graph.py scripts/export_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py evals/run_evals.py evals/run_superleads_user_visible_output_evals.py evals/run_superleads_markdown_delivery_evals.py` → passed。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 11/11。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 evals/run_evals.py --suite default` → 119/119。
   - `python3 evals/run_evals.py --suite deep` → 668/668。
   - `python3 evals/run_evals.py --suite all` → 711/711。
   - `python3 evals/run_superleads_route_evals.py --suite all` → 25/25。
   - `python3 evals/run_product_market_analysis_evals.py --suite all` → 74/74。
   - `git diff --check` → passed。

## Code Slice AG 已完成

1. Skill / 文档
   - 新增 `skills/researching-customer-background/agents/openai.yaml`，让单一客户背调在 Codex / ChatGPT 侧不再隐形。
   - 新增 `spec/35-superleads-customer-background-code-slice-ag.md`，冻结单客背调边界、用户可见输出合同和禁止项。
2. 轻验证边界
   - `scripts/validate_research_graph.py` 阻断 `customer_background_research` 产生 Assessment、ScopeDecision、ReviewAttestation、DeliveryManifest。
   - 搜索摘要仍不能解析主体，也不能支撑 Claim。
3. 用户可见输出
   - `scripts/background_report.py` 将空表从全行 `未提供` 改为人话缺口说明。
   - `scripts/validate_superleads_user_visible_output.py` 新增采购负责人 / 采购意愿升级短语阻断。
4. evals / fixtures
   - 新增 `evals/run_customer_background_research_evals.py`。
   - 新增 `evals/cases/customer_background_research_cases.json` 共 6 条：resolved、unresolved、无关候选不外泄、搜索摘要解析主体、Assessment 污染、Manifest 污染。
   - 新增用户可见 fail 样本 `fail_customer_background_positive_procurement_person.md`。
   - 主 eval 已纳入单客背调 suite。
5. 已验证
   - `python3 -m py_compile scripts/background_report.py scripts/export_superleads_markdown.py scripts/validate_research_graph.py scripts/validate_superleads_user_visible_output.py evals/run_customer_background_research_evals.py evals/run_evals.py` → passed。
   - `python3 evals/run_customer_background_research_evals.py --suite all` → 6/6。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 10/10。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 evals/run_evals.py --suite default` → 115/115。
   - `python3 evals/run_evals.py --suite all` → 707/707。
   - `python3 evals/run_evals.py --suite deep` → 667/667。
   - `python3 evals/run_product_market_analysis_evals.py --suite all` → 74/74。

## Code Slice AF 已完成

1. 路由器
   - `scripts/route_superleads_intake.py` 区分客户开发、单一客户背调、产品出海市场分析三类入口。
   - 认证 / 合规词按语境分流：描述目标客户属性时走批量客户开发；询问产品进入目标市场要求时走产品出海市场分析。
   - 增加否定条件处理，避免 `不做市场分析` / `不找客户` 反向误触发。
   - 混合任务输出 `secondary_routes` / `route_order`，但不自动执行第二阶段。
2. evals
   - `evals/cases/superleads_route_cases.json` 扩到 25 条真实外贸入口样例。
   - 新增 `evals/run_superleads_route_evals.py`。
   - `evals/run_evals.py` route assertion 支持校验拆阶段字段。
3. 文档
   - 新增验证记录 `docs/validation/superleads-code-slice-af-route-evals-20260729.md`。
   - 更新 route-map、user-intake、using-superleads Skill 和常用命令。
4. 已验证
   - `python3 -m py_compile scripts/route_superleads_intake.py evals/run_superleads_route_evals.py evals/run_evals.py` → passed。
   - `python3 evals/run_superleads_route_evals.py --suite all` → 25/25。
   - `python3 evals/run_evals.py --suite default` → 113/113。
   - `python3 evals/run_evals.py --suite all` → 699/699。
   - `python3 evals/run_evals.py --suite deep` → 659/659。
   - `python3 evals/run_product_market_analysis_evals.py --suite all` → 74/74。
   - `git diff --check` → passed。

## Code Slice AD 已完成

1. schema
   - `EvidenceCard` / `MatrixRowRecord` 新增 `authority_verification_record_ids`。
   - `ProductMarketAnalysisGraph` 新增可选 `authority_profiles`、`authority_identity_evidence`、`authority_capabilities`、`authority_verification_records`。
   - 新增 `AuthorityProfile` / `AuthorityIdentityEvidence` / `AuthorityCapability` / `AuthorityVerificationRecord`。
2. validator
   - 强监管事实域的确定性 row/card 必须有 `AuthorityVerificationRecord`。
   - 阻断 keyword-only authority、domain-only authority。
   - 阻断事实域错配、管辖范围错配、Source Pack / registry / Query Plan / SearchLog 直接支撑事实。
   - 阻断行业、商业、媒体、货代、未知来源升级为主管官方来源。
   - 阻断多弱来源一致被写成官方确认。
3. exporter / audit
   - CSV / Markdown 展示：`来源身份`、`适用范围`、`可以当作什么`、`不能当作什么`、`权威性核实`。
   - Markdown 顶部新增 `来源权威性 / Authority` 摘要区。
   - 权威性待核实、来源身份冲突、事实域不匹配进入 limitation 或 blocker。
4. query plan
   - 当目标国家/地区没有预置 Pack 时，仍生成动态 authority discovery 查询组。
   - 覆盖目的国准入、COO、关税、预申报、食品农检、危险品等触发路径。
   - 搜索摘要只进候选来源，不形成 EvidenceCard。
5. fixtures/evals
   - pass：官方税则只支撑税费、认证机构只作路径参考、货代只作物流线索。
   - fail：博客冒充 required、只靠域名判官方、海关税则支撑认证、出口国/目的国错配、Source Pack 直接当事实、多弱来源冒充官方确认。
   - source plan：泰国食品/农产品开放世界 plan-only。


## Slice AE 已完成

1. 状态词压缩
   - 用户可见状态收口为 11 个：已有明确依据、按已知数据计算、多来源方向一致、可作为线索、需补充资料、需权威/专业复核、资料过旧需复核、来源受限、说法冲突待复核、本轮未执行、暂不适用。
   - 内部状态枚举继续保留，不直接暴露给用户。
2. 状态分层
   - 业务/规则结论、依据状态、用户材料状态分开。
   - COO / 原产地证明、认证 / 目的国准入不得由用户材料状态反推目标国规则。
3. 投影优先级
   - 未执行、不适用、冲突、来源受限、时效过旧、权威未核实、缺材料等降级信号优先于 `verified`。
   - 多来源一致只显示为线索收敛，不升级为官方确认。
4. 后续 Code Slice AE 边界
   - 只做状态投影与用户展示合同，不重构业务图谱、不新增真实来源、不扩国家库。


## Code Slice AE 已完成

1. 状态投影工具
   - 新增 `scripts/user_visible_status_projection.py`。
   - 将内部 row status、CorroborationRecord、FreshnessRecord、AuthorityVerificationRecord 投影为 Slice AE 11 个用户可见状态。
   - 投影优先级覆盖：未执行 / 不适用 / 冲突 / 来源受限 / 时效过旧 / 权威未核实 / 缺材料 优先于 `verified`。
2. 产品市场导出
   - `scripts/export_product_market_workbook.py` 的 CSV / Markdown 增加 `依据状态`、`依据说明`。
   - COO / 原产地证明继续分列 `规则结论` 与 `用户材料状态`。
   - 认证 / 目的国准入专门行分列 `规则结论` 与 `用户材料状态`，并将内部 enum 投影成人话。
   - `SearchLog` 等内部术语在可见内容中替换为业务表述，避免内部对象名外露。
3. 用户可见 eval
   - `scripts/validate_superleads_user_visible_output.py` 要求产品市场分析包含 `依据状态` 和至少一个 Slice AE 用户可见状态。
   - 阻断 `technical_docs_required`、`stale_needs_recheck`、`user_not_provided_but_required` 等内部状态 token 外露。
   - 新增 fail 样本 `evals/user_visible_outputs/fail_product_market_internal_status_tokens.md`。
4. 文档
   - 更新 `shared/references/status-labels.md`。
   - 新增验证记录 `docs/validation/superleads-code-slice-ae-status-projection-20260729.md`。

## 已验证

```bash
python3 -m py_compile scripts/user_visible_status_projection.py scripts/export_product_market_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py evals/run_product_market_analysis_evals.py evals/run_superleads_user_visible_output_evals.py evals/run_superleads_markdown_delivery_evals.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
python3 evals/run_product_market_source_plan_evals.py --suite all  # 7/7（Code Slice AD 时通过，本轮未改 plan）
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 9/9
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 99/99
python3 evals/run_evals.py --suite all  # 685/685
python3 evals/run_evals.py --suite deep  # 645/645
git diff --check  # passed
```

## 当前下一步

1. 不继续开自动 Slice。
2. 进入真实使用 / 验收模式：只在真实交付或明确缺陷暴露后再开下一刀。
3. 若只是状态文字滞后，优先 amend 当前提交，不再制造单独状态同步提交。

## Slice AH 已完成

1. 复盘批量客户开发当前产品边界：默认弱证据交付是发现候选池，不是强制完整核查版，也不是独立“初筛客户名单”。
2. 撤销旧结论：不把 `初筛客户名单` 实现为 L2 弱证据中间档；它当前是会绕过默认发现 Candidate 结构检查的危险枚举。
3. 明确发现候选池内部三分区：可优先人工跟进 / 待确认 / 已排除或仅作参考。
4. 明确用户可见字段：分区、候选客户、国家/地区、可能客户角色、当前看到的业务信号、业务相关性、依据状态、联系入口、待确认项、来源状态。
5. 继续禁止：推荐客户排序、采购概率、把公开入口写成采购负责人、把搜索摘要写成 Claim。
6. 后续 Code Slice AH 再落 validator / fixtures / bulk Markdown 展示 / 用户可见 eval。

## Code Slice AH 后续注意

1. 仍不新增 `initial_screening` exporter mode，不新增 delivery_status，不新增 audit 分支。
2. 不动 Candidate 的 `初筛线索` status；它是候选对象状态，不是 `初筛客户名单` output_mode。
3. 后续若继续优化 bulk，应围绕开放世界客户类型、来源覆盖计划、查询收敛表达，不把弱证据升级成正式客户。

## 当前阻塞 / 注意

- 真实默认发现仍受能力限制：没有可记录的真实搜索/打开来源能力时，默认发现只能停在计划或样本池层；不能伪造 SearchLog / Source / Observation。
- `tmp/stage5_chillys/` 必须保留。
- 不联网判断真实法规、关税、认证或最新行情；只按 graph 中已记录的来源、观察、时效和权威性核验记录做降级。
- Code Slice AD 不建立全球官方机构事实库；它只要求在具体运行中打开来源并记录身份、事实域、管辖范围、时效和边界。
