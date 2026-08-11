# Handoff

## 2026-08-11 Phase 1.2 独立真实 UAT 通过

- 新运行目录：`/tmp/superleads-uat-electric-kettle-phase-1-2-20260811T050529Z`；场景为 220–240 V / 1500 W 普通电水壶、中国出口美国。
- 当前 Run 能力门禁通过：`search.web`、`source.open` 均 available，`formal_research_status=ready`。
- 耗时 1504 秒；7 次搜索调用、22 条查询；13 个来源/Observation 成功打开，4 个受限、1 个无可提取结果。
- Phase 1.2 编译输出 13 EvidenceCards、17 MatrixRows、13 Gaps、6 组 Authority skeleton；validator、audit、Markdown、workbook、用户可见检查和 claimed-path 全部通过，交付为 `ready_with_limitations`。
- 与旧基线相比：耗时 -1486 秒，手工输入 1259 行（-752 行）；Source/Observation +5/+5，EvidenceCard +5，MatrixRow +1，Gap +1。该结果证明编译器降低了本场景的重复录入和执行时间，但不外推到所有产品/国家。
- 未发现搜索摘要升级、原产地合并、最终 HS/税率、合规、清关、最佳路线或市场进入建议等边界违规；仓库未修改、未提交。
- 下一步从“减少录入成本”转向“报告收敛质量”：先整理 17 行中的高优先级资料缺口与事实归纳，不新增国家库、validator 或自动搜索编排。详细记录见 `docs/validation/superleads-product-market-evidence-phase-1-2-20260811.md`。

## 2026-08-11 产品市场证据编译器 Phase 1.2

- Plugin-Eval 的通用 benchmark 已替换为 Superleads 专用三场景：无 `search.web/source.open` 时硬停、普通电水壶出口美国盲测、证据边界回归；配置见 `.plugin-eval/benchmark.json`。
- `scripts/compile_product_market_evidence.py` 新增编译器输入 `authority_notes`、`matrix_row_templates`、`target_row_ids` 和 `authority_note_ids`，输出仍为既有 AuthorityProfile / IdentityEvidence / Capability / VerificationRecord / EvidenceCard / MatrixRow / Gap 对象。
- Authority 紧凑输入必须绑定已打开 Observation 和逐字摘录；默认 `candidate_needs_check` / `not_reviewed`，不自动识别官方来源、不升级状态。旧 `row` / `rows` 输入保持兼容。
- 插件版本已 bump 到 `0.1.11`，通过 `codex plugin add superleads@fleix --json` 同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.11`。
- 离线重放盲测输出 8 EvidenceCards、16 MatrixRows、12 Gaps，validator/audit/export/claimed path 全部通过；没有把离线回放当成新的真实搜索 UAT。
- 验证：compiler 7/7、product-market 75/75、plugin distribution 6/6、主 default 126/126、all 719/719、deep 676/676。当前会话 preflight 显示 `search.web` 与 `source.open` 均 unknown，新的联网 UAT 必须在具备正式来源能力的环境重跑。
- 详细记录：`docs/validation/superleads-product-market-evidence-phase-1-2-20260811.md`。

## 2026-08-10 产品市场证据编译器 UAT 跟进

- 用 `/tmp/electric_kettle_us_uat_graph_20260810.json` 重放普通电水壶出口美国 UAT：6 条紧凑证据笔记和 2 个用户属性编译后得到 6 EvidenceCard、13 MatrixRow、10 Gap，产品市场 validator / audit / Markdown 导出均通过，交付仍为 `ready_with_limitations`。
- UAT 发现并修复两个编译器问题：同一矩阵目标的多条笔记现在合并为一行；单个来源事实可用 `rows` 落到多个既有表，且每个表可单独指定 freshness / authority 引用。
- 用户输入 `额定电压`、`额定功率` 现在会将 `额定电压/频率` 收敛为 `频率`，并移除已知的功率项，不再因精确字符串不一致而丢失已知资料。
- 本轮 380 行紧凑 notes 是从既有 UAT graph 回建的结构对比，不是独立计时的盲写测量；不能以此声明最终节省比例。插件 `0.1.10` 已同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.10`。

## 2026-08-10 产品市场证据编译器 Phase 1

- 真实电水壶美国 UAT 已证明：搜索 / 来源打开 / Source / Observation / EvidenceCard / MatrixRow / validator / audit / export 可以连通，但 1547 行手写 JSON 换来 6 Source、6 Observation、6 EvidenceCard、13 MatrixRow，人工转换是当前瓶颈。
- 新增 `scripts/compile_product_market_evidence.py`。它只消费已打开 Observation 和紧凑 `evidence_notes`，自动生成重复的 EvidenceCard / MatrixRow / Gap 引用；不搜索、不打开、不判断 Authority、不升级状态。
- 编译器还支持 `product_attributes` 紧凑输入，把用户提供的电压、功率、容量、材料、型号等写入现有 ProductMarketAnalysisGraph `attributes`，并从产品未知属性列表移除；它不会把用户输入标成 `verified`。
- 安全门：Observation 必须是 opened/captured/extracted/rendered 且有 `raw_excerpt`；`source_excerpt_quote` 必须逐字存在于原文；未打开来源、搜索摘要或未知字段均拒绝。
- Skill / 常用命令已写入编译步骤；`.codex-plugin/plugin.json`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` 已 bump 到 `0.1.9`，并通过 `codex plugin add superleads@fleix --json` 同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.9`。
- 验证记录见 `docs/validation/superleads-product-market-evidence-compiler-20260810.md`。已通过 focused 2/2、产品市场 75/75、插件分发 6/6、主 all 719/719。下一步应使用同一真实 UAT graph 对比手写行数和产品字段保留情况，再决定是否进入 Phase 2 报告收敛。

## 2026-08-10 产品出海市场分析按请求范围输出

- `analysis_modules_requested` 现在驱动 CSV 与 Markdown 的选表：缺失、空、未知、旧 `product_profile` 标记或大于单项范围的请求都输出完整十二表；明确的单项输出三张固定表和对应模块表。
- `SHEET_MODULE_KEYS` 在一处兼容 `certification`、`destination_compliance`、`origin_proof_requirement`、`market_signal` 等新旧词；source planner 也把 `certification` 映射到既有准入/COO 查询组。单项不再把未请求模块加入“本轮未执行项”，并在开头写明本轮范围和未覆盖项目。
- 单项固定“信息来源与待确认事项”仅保留可见模块、产品档案或贸易前提实际引用的来源、Gap 和 Conflict，避免泄漏税费或物流待确认项；既有用户可见校验会识别范围声明，不再要求未覆盖模块的税费/运输文案。
- 完整报告的空表改为说明“本轮未执行该项采集”“已采集但未找到可用公开来源”“按当前产品档案暂不适用”或“来源受限，未能读取”；现有证据边界未放宽。
- 新增 `market_pass_scope_certification.json` 与现有 runner 断言：认证单项不会输出税费、物流、趋势等表，CSV 与 Markdown 都只保留四张表；完整报告的空表原因也有回归覆盖。
- Skill 和 intake 写入模块选择规则；插件版本 bump 到 `0.1.8`，已通过 `codex plugin add superleads@fleix --json` 同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.8`。
- 验证记录：`docs/validation/superleads-product-market-report-scope-20260810.md`。未新增 schema、validator 脚本、错误码或 runner，未改批量客户开发、单客背调或 `tmp/stage5_chillys/`。

## 2026-08-10 批量 Markdown 公开联系人显示

- `scripts/export_superleads_markdown.py` 的批量“联系方式汇总”扩为七列：对象、联系人 / 公开职业线索、联系方式、类型、可用状态、待确认原因、来源 / 链接。
- `person_name` / `job_title` 类型不再把人名或职位放入联系方式列；`needs_manual_association_review` 与 `UnassignedContactLead` 保留值并标为待确认归属，`hold_no_source` / `hold_inferred` 继续全字段脱敏。
- 现有默认发现 pass fixture 增加 Alpha 的公开人员线索，并接入生成式 Markdown 断言；新增既有 hold fixture 的 Markdown 脱敏回归。
- `collecting-contact-intelligence` 与 `writing-research-plans` 增加以公司/人员为锚点的 LinkedIn、官网、展会、行业协会和公开社媒查询模板；公开职位仅作为角色线索，不等于采购权。
- 插件版本 bump 到 `0.1.7`，运行时缓存为 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.7`。
- 详细范围与验证记录见 `docs/validation/superleads-bulk-contact-person-visibility-20260810.md`。

## 2026-08-10 疑似进出口记录能力

- 单客背调新增可选根节点数组 `suspected_trade_records`，独立于 `Claim`、`ClaimEvidence`、`Assessment` 和 `DeliveryManifest`；主体只用 `subject_match_level` 表达，不自动绑定 `entity_id`。
- 覆盖族 E 现在主动执行英文/中文贸易记录查询模板，保留搜索摘要中可见的名称、日期、品名/HS、起运/目的地字段；详情打不开时标 `详情受限`，不绕过登录墙、付费墙或反爬。
- 背景报告在有记录时条件追加 `疑似进出口记录（第三方聚合，待核实）`，Markdown / CSV / XLSX 字段顺序一致；无记录时仍保持原六张固定表，不输出空占位表。
- 版本已 bump 到 `0.1.6`，运行时缓存为 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.6`；插件分发完整性 eval 通过。
- 详细范围与验证记录见 `docs/validation/superleads-customer-background-suspected-trade-records-20260810.md`。

- 分支：`master`
- 最新提交：本次 `Add suspected trade record capture to customer background`
- 当前状态：Source Capability Gate / `0.1.6` 已在工作区完成并通过全量回归。正式客户开发、单客背调、产品出海市场分析统一要求 `search.web` + 至少一个来源打开能力；缺失时硬停并提示切换环境，资料初审是单独的非正式路径。产品链接风险入口、电水壶锂电误触发、贸易前提合并标签、插件 URL 与 hooks 打包检查均已修复。单客背调现可承载公开摘要中的疑似进出口记录，但仍要求第三方来源、主体待确认和用户自行核实。保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已完成

- Source Capability Gate / `0.1.5` 已完成：`preflight_capabilities.py --require-formal-research` 在缺少 `search.web` 或 `source.open` / `browser.render` / `document.extract` 时以稳定状态和用户可见换环境话术失败；技能、策略、README 与常用命令不再把 `research_plan_only` 或候选池描述成无来源能力时的正式交付。用户已提供材料只允许明确标注为 `资料初审`。
- 已修复产品 URL + 目标国 + 风险入口到产品出海市场分析的路由，通用 `electrical` 不再触发锂电 Source Pack，市场报告顶部始终将出口申报国和原产国 / 制造来源分开显示。
- 插件版本升至 `0.1.5`；新增公开隐私/条款页和 manifest URL。插件分发 eval 现在复制 `hooks/`，验证 manifest 声明的 hook 配置和它引用的 Unix/Windows 命令目标；故意删除 hook 配置或脚本会失败。
- 已验证：`python3 -m py_compile`（相关脚本）、route `26/26`、source-plan `12/12`、Markdown delivery `7/7`、plugin distribution `6/6`、`python3 evals/run_evals.py --suite default`、`python3 evals/run_evals.py --suite all` `716/716`（183 秒）、`git diff --check`。系统通用 plugin validator 与本项目既有 Codex hooks 规则冲突，故以仓库分发回归为准。

- Slice AA / Code Slice AA 已提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 已提交：`2073a98 Add weak-source corroboration records`。
- Code Slice AC 已提交：`069314d Add product market freshness guardrails`。
- Slice AD 文档已提交：`22be247 Document open world authority source model`。
- Code Slice AD 已提交：`1b3c040 Add open-world authority verification guardrails`。
- 状态同步已提交：`6ae7bf8 Update handoff after authority guardrails commit`。
- Slice AE 文档已提交：`7caa2e4 Document user-visible status mapping`。
- Code Slice AE 已提交：`b08f966 Add user-visible status projection`。
- 状态同步已提交：`e966c27 Update handoff after status projection commit`。
- Code Slice AF 已提交：`0f7666e Add Superleads route intent evals`。
- 状态同步已提交：`2e5d2ed Update handoff after route evals commit`。
- Code Slice AG 已提交：`c8477d3 Add customer background research guardrails`。单一客户背调补 Skill 入口、专属 spec、专属 eval runner、6 条 graph fixtures、1 条用户可见 fail 样本，并强化轻验证与正式名单链路隔离。
- Slice AH 批量客户开发内核复盘纠偏已提交：`b0fdd53 Calibrate bulk discovery candidate pool`。取消独立 L2 `初筛客户名单` 层级，改为发现候选池内部三分区，并将 `初筛客户名单` 标记为 Code Slice AH 必须堵住的 validator 绕过口。
- Code Slice AH 已提交：`26e788f Refine bulk discovery status projection`：堵 `output_mode=初筛客户名单` 绕过口；bulk workbook / Markdown 新增 `分区`、`依据状态`；Markdown 补联系方式汇总、搜索覆盖与收敛、已排除/仅作参考、风险说明；用户可见 eval 阻断缺状态与缺表交付。当前又补了 `可能客户角色` 接入实体 `customer_type`、`observed` 上调为 `已有明确依据`，并新增 `采购意愿待确认` 的误杀回归样本。
- Code Slice AH-FIX 已收口并纳入本提交：修复 `26e788f` 引入的依据状态升级缺陷；默认发现先扫描 `identity_pending` / `source_restricted` / `source_restrictions` / `insufficient_information` 等降级，再允许无降级的 `business_match.observed` 投影为 `已有明确依据`；新增 `bulk_basis_status_source_restricted_promoted` 用户可见 fail 样本和 `Beta Industrial Supplies` 行级导出断言。
- 正式 Skill 调用 Markdown 交付收口已完成：`using-superleads` / `exporting-lead-workbooks` 明确禁止手工从 workbook/CSV 渲染 Markdown，要求 chat-readable 报告必须走 `export_superleads_markdown.py`；插件缓存 `~/.codex/plugins/cache/fleix/superleads/0.1.3` 已同步；新增 `scripts/check_superleads_formal_markdown_delivery.py` 验证缓存一致、统一导出器输出和 Northshore `来源受限`。
- 真实业务 UAT 正式交付链路补强已完成：新增 `user_visible_basis_status_internal_leak`，阻断手写真实客户表把 `已观察` 等内部公开信号状态写作 `依据状态`；新增真实 UAT fail 样本并接入 user-visible eval；Skill / 插件缓存要求正式交付必须有保存的 graph JSON 和 exporter JSON 成功结果，否则只能称 research draft / source-collection note。
- 真实业务 UAT 声明路径复核补强已完成：`check_superleads_formal_markdown_delivery.py` 新增 `--claimed-graph/--claimed-markdown/--claimed-route`，精确比对用户声明报告与 exporter 输出；冒烟增加 `customer_background_research`，证明单客背调 Markdown 也走统一 exporter。
- 真实业务 UAT 固定验收清单已完成：新增 `docs/validation/superleads-real-business-uat-checklist.md`；claimed path 复核被记录为每次真实业务 UAT 的固定 gate，而不是可选调试步骤。
- claimed path UAT 自动回归已完成：`evals/run_superleads_markdown_delivery_evals.py` 新增正向 exporter 原始输出通过、负向手工后处理 mismatch 失败两条回归；当前 Markdown delivery suite 为 7/7。
- 单客背调 claimed path 真实 UAT 已完成：Chilly’s Bottles `customer_background_research` 路线使用 `/home/fleix/superleads_chillys_bottles_20260731/{chillys_customer_background_uat_graph.json,chillys_customer_background_uat_report.md}` 独立复核通过；claimed path check 与用户可见校验均 `ok=true` / `issue_count=0`。
- 插件发布/安装链路 UAT 已完成：版本从 `0.1.3` bump 到 `0.1.4`，通过 `codex plugin add superleads@fleix --json` 生成 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.4`；新缓存包含 `skills/analyzing-product-outbound-market/`、`shared/references/product-outbound-market-intake.md` 和 `spec/`。新增 `scripts/check_superleads_plugin_distribution.py` 与 `evals/run_superleads_plugin_distribution_evals.py`，已接入 `evals/run_evals.py`，覆盖 skill 缺失和 Skill 相对引用死链两类回归。

## Code Slice AD 已完成内容

1. `shared/schemas/product-market-analysis.schema.json`
   - `EvidenceCard` / `MatrixRowRecord` 新增 `authority_verification_record_ids`。
   - 图谱新增 `authority_profiles`、`authority_identity_evidence`、`authority_capabilities`、`authority_verification_records`。
   - 新增 AuthorityProfile / IdentityEvidence / Capability / VerificationRecord defs。
2. `scripts/validate_product_market_analysis.py`
   - 强监管事实域的确定性 row/card 需要 AuthorityVerificationRecord。
   - 阻断 keyword-only、domain-only 权威性判断。
   - 阻断 fact domain / jurisdiction role / jurisdiction name 错配。
   - 阻断 Source Pack / Query Plan / SearchLog 直接支撑事实。
   - 阻断行业、商业、媒体、货代、未知来源升级为主管官方确定性结论。
   - 阻断多弱来源一致被写成官方确认。
   - 修正 origin proof 文案含 tariff 时误判 import_tax 的问题。
3. `scripts/export_product_market_workbook.py`
   - CSV / Markdown 新增人话字段：`来源身份`、`适用范围`、`可以当作什么`、`不能当作什么`、`权威性核实`。
   - Markdown 顶部新增 `来源权威性 / Authority` 摘要区。
4. `scripts/audit_product_market_analysis.py`
   - authority 限制状态进入 limitation：candidate / secondary / unable / conflicting / not_executed。
5. `scripts/plan_product_market_sources.py`
   - 未预置目标国家/地区生成开放世界 authority discovery 查询组。
   - 覆盖目的国准入、COO、关税、预申报、食品农检、危险品等触发路径。
   - 非美国目的国不再因食品等触发项套用美国 Source Pack。
6. evals
   - market suite 从 65 条扩到 74 条。
   - source plan suite 从 6 条扩到 7 条。
   - 新增 pass/fail authority fixtures 和泰国食品开放世界 plan-only fixture。
7. 文档
   - 新增 `docs/validation/superleads-code-slice-ad-authority-20260729.md`。


## Slice AE 已完成内容

1. 冻结用户可见 11 个状态词：已有明确依据、按已知数据计算、多来源方向一致、可作为线索、需补充资料、需权威/专业复核、资料过旧需复核、来源受限、说法冲突待复核、本轮未执行、暂不适用。
2. 明确三层状态不得混用：业务/规则结论、依据状态、用户材料状态。
3. 明确 COO / 原产地证明、认证 / 目的国准入必须分列目标国规则结论和用户材料状态。
4. 冻结状态投影优先级：未执行、不适用、冲突、来源受限、时效过旧、权威未核实、缺材料等优先于 `verified`。
5. 明确 Code Slice AE 只做状态投影与用户展示合同，不重构图谱、不新增真实来源、不扩国家库。


## Code Slice AE 已完成内容

1. `scripts/user_visible_status_projection.py`
   - 新增内部状态到 11 个用户可见状态的纯投影工具。
   - 支持 row status、corroboration、freshness、authority 的优先级合并。
2. `scripts/export_product_market_workbook.py`
   - CSV / Markdown 输出新增 `依据状态`、`依据说明`。
   - COO / 原产地证明、认证 / 目的国准入分列 `规则结论` 和 `用户材料状态`。
   - `SearchLog` 等内部术语替换为用户可懂的业务表述。
3. `scripts/validate_superleads_user_visible_output.py`
   - 产品市场分析必须出现 `依据状态` 和 Slice AE 用户可见状态。
   - 阻断内部状态 token 外露。
4. evals / fixtures
   - 用户可见 output suite 从 8 条扩到 9 条。
   - 更新产品市场导出断言和 Markdown delivery 断言。
5. 文档
   - 更新 `shared/references/status-labels.md`。
   - 新增 `docs/validation/superleads-code-slice-ae-status-projection-20260729.md`。

## Code Slice AF 已完成内容

1. `scripts/route_superleads_intake.py`
   - 将入口意图区分为客户开发、单一客户背调、产品出海市场分析。
   - 增加否定条件处理：`不做市场分析` / `不找客户` 不再误触发对应路线。
   - 把“认证需求的进口商 / 需要 UL 的客户”识别为客户开发属性；把“产品出口某国是否需要认证 / SDS / UN38.3 / COO / 关税 / 清关文件”识别为产品出海市场分析。
   - 混合任务输出 `secondary_routes` 和 `route_order`，但不自动执行第二阶段。
2. evals
   - `evals/cases/superleads_route_cases.json` 从 11 条扩到 25 条。
   - 新增 `evals/run_superleads_route_evals.py`，可单独快速验证入口路由。
   - 主 eval 的 route assertion 支持校验 `secondary_routes` / `route_order`。
3. 文档
   - 更新 `shared/references/route-map.md`、`shared/references/user-intake.md`、`skills/using-superleads/SKILL.md`、`docs/superleads-common-commands.md`。
   - 新增 `docs/validation/superleads-code-slice-af-route-evals-20260729.md`。


## Code Slice AG 已完成内容

1. `skills/researching-customer-background/agents/openai.yaml`
   - 补齐 Codex / ChatGPT 可见入口：`单一客户背调`。
2. `spec/35-superleads-customer-background-code-slice-ag.md`
   - 冻结单客背调产品边界：一个指定对象 → 客户背调报告。
   - 明确不生成批量客户池、不做推荐客户、不写采购概率、不把公开入口写成采购意愿。
   - 明确 `Assessment` / `ScopeDecision` / `ReviewAttestation` / `DeliveryManifest` 不属于客户背调轻验证报告。
3. `scripts/validate_research_graph.py`
   - `customer_background_research` 阻断 Assessment、ScopeDecision、ReviewAttestation、DeliveryManifest。
   - 保持搜索摘要不能解析主体、不可形成 Claim 的证据纪律。
4. `scripts/background_report.py`
   - 背调空表从全行 `未提供` 改为人话缺口说明。
5. `scripts/validate_superleads_user_visible_output.py`
   - 增加采购负责人 / 采购意愿升级短语阻断，例如 `Founder 就是采购负责人`、`已确认有采购需求`、`wholesale 页面说明有采购意愿`。
6. evals
   - 新增 `evals/run_customer_background_research_evals.py`。
   - 新增 `evals/cases/customer_background_research_cases.json`，共 6 条。
   - 新增 pass/fail graph fixtures：resolved、unresolved、无关候选不外泄、搜索摘要解析主体、Assessment 污染、Manifest 污染。
   - 用户可见 output suite 从 9 条扩到 10 条。
   - 主 eval `all` 从 699 条扩到 707 条，`deep` 从 659 条扩到 667 条，`default` 从 113 条扩到 115 条。
7. 文档
   - 新增 `docs/validation/superleads-code-slice-ag-customer-background-20260729.md`。


## Code Slice AH 已完成内容

1. `scripts/validate_research_graph.py`
   - `初筛客户名单` 不再跳过默认发现 Candidate 结构检查。
   - 显式输出 `initial_screening_output_mode_deprecated`，要求使用 `发现候选池` + 三分区/依据状态表达中间档。
   - 被掏空的 `output_mode=初筛客户名单` fixture 现在 validate / audit / export initial 全部 fail。
2. `scripts/export_workbook.py`
   - 默认发现 `发现候选池` sheet 新增 `分区` 和 `依据状态`。
   - 分区为：可优先人工跟进 / 待确认 / 已排除 / 仅作参考。
   - 依据状态复用 Slice AE 用户可见状态词：可作为线索、需补充资料、来源受限、说法冲突待复核等。
3. `scripts/export_superleads_markdown.py`
   - bulk Markdown 从 4 张表补为 8 张：先把开发方向说清、发现候选池样表、联系方式汇总、搜索覆盖与收敛、待确认事项、已排除 / 仅作参考、信息从哪里来、风险与说明。
   - 主表新增 `分区`、`国家/地区`、`可能客户角色`、`业务相关性`、`依据状态`。
   - 不新增事实、不新增 exporter mode、不新增 delivery_status、不新增 audit 分支。
4. `scripts/validate_superleads_user_visible_output.py`
   - bulk 路线要求 `依据状态`、三分区、联系方式汇总、搜索覆盖与收敛、风险与说明。
   - bulk 路线也必须出现至少一个 Slice AE 用户可见状态。
5. evals / fixtures
   - 新增 `evals/fixtures/fail_initial_screening_output_mode_bypass.json`。
   - 新增 `evals/user_visible_outputs/fail_bulk_customer_missing_basis_status.md`。
   - 更新 bulk 用户可见样本和 Markdown delivery case。
6. 文档
   - 新增 `docs/validation/superleads-code-slice-ah-bulk-discovery-20260730.md`。

## Slice AH 已完成内容

1. `spec/36-superleads-bulk-customer-development-slice-ah.md`
   - 将批量客户开发重新定义为“用户当前卖什么 + 本次想找哪类海外客户 -> 发现候选池；用户明确要求正式核查时 -> 标准开发名单”。
   - 撤销独立 L2 `初筛客户名单` 设计：`初筛客户名单` 当前是 schema 中的危险枚举，不是安全可交付层级。
   - 明确后续 Code Slice AH 必须先堵 `validate_research_graph.py` 中 `初筛客户名单` 绕过默认发现 Candidate 结构检查的问题。
   - 明确发现候选池内部三分区：可优先人工跟进 / 待确认 / 已排除或仅作参考。
   - 明确 bulk Markdown 的真实缺口：缺联系方式汇总、搜索覆盖与收敛、已排除 / 仅作参考、依据状态列和三分区展示。
   - 明确客户类型是开放文本，不用固定 ICP 或静态行业词典；多来源方向一致只提升线索可读性，不能升级为正式事实。
2. `docs/validation/superleads-bulk-customer-development-slice-ah-checklist-20260730.md`
   - 记录本轮文档纠偏验收范围和后续 Code Slice AH 建议。
3. `meta/decision-log.md`
   - 记录 Slice AH 纠偏决策：取消 L2 独立层，发现候选池内部分区，优先堵 `初筛客户名单` 绕过口。

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

# Code Slice AF 验证
python3 -m py_compile scripts/route_superleads_intake.py evals/run_superleads_route_evals.py evals/run_evals.py  # passed
python3 evals/run_superleads_route_evals.py --suite all  # 25/25
python3 evals/run_evals.py --suite default  # 113/113
python3 evals/run_evals.py --suite all  # 699/699
python3 evals/run_evals.py --suite deep  # 659/659
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed

# Code Slice AG 验证
python3 -m py_compile scripts/background_report.py scripts/export_superleads_markdown.py scripts/validate_research_graph.py scripts/validate_superleads_user_visible_output.py evals/run_customer_background_research_evals.py evals/run_evals.py  # passed
python3 evals/run_customer_background_research_evals.py --suite all  # 6/6
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 10/10
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 115/115
python3 evals/run_evals.py --suite all  # 707/707
python3 evals/run_evals.py --suite deep  # 667/667
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed

# Code Slice AH 验证
python3 -m py_compile scripts/validate_research_graph.py scripts/export_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py evals/run_evals.py evals/run_superleads_user_visible_output_evals.py evals/run_superleads_markdown_delivery_evals.py  # passed
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 11/11
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 119/119
python3 evals/run_evals.py --suite deep  # 668/668
python3 evals/run_evals.py --suite all  # 711/711
python3 evals/run_superleads_route_evals.py --suite all  # 25/25
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed

# Code Slice AH-FIX 验证
python3 -m py_compile scripts/export_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py scripts/user_visible_status_projection.py  # passed
python3 evals/run_evals.py --suite default  # 121/121
python3 evals/run_evals.py --suite deep  # 670/670
python3 evals/run_evals.py --suite all  # 713/713
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 13/13
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_superleads_route_evals.py --suite all  # 25/25
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
python3 evals/run_customer_background_research_evals.py --suite all  # 6/6
git diff --check  # passed

# 正式 Skill 调用 Markdown 交付收口验证
python3 -m py_compile scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json  # passed, issue_count=0
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 13/13
git diff --check  # passed

# 真实业务 UAT 正式交付链路补强验证
python3 -m py_compile scripts/validate_superleads_user_visible_output.py scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json  # passed, issue_count=0
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 14/14
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 122/122
python3 evals/run_evals.py --suite all  # 714/714
python3 evals/run_evals.py --suite deep  # 671/671
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks  # passed
git diff --check  # passed

# 真实业务 UAT 声明路径复核验证
python3 -m py_compile scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/researching-customer-background  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json --format json  # passed, issue_count=0
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 14/14
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_graph.json --claimed-markdown /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_report.md --claimed-route bulk_customer_development --format json  # failed as expected: formal_markdown_claimed_output_mismatch
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_us_generator_parts/graph.json --claimed-markdown /home/fleix/superleads_us_generator_parts/report.md --claimed-route bulk_customer_development --format json  # passed, issue_count=0
python3 scripts/export_superleads_markdown.py /home/fleix/superleads_runs/chillys_bottles_2026-07-31/chillys_background_graph.json --route customer_background_research --output /tmp/chillys_reexport.md --format json  # passed, issue_count=0
```

## 当前下一步建议

1. 不继续开自动 Slice。
2. 进入真实使用 / 验收模式：只在真实交付或明确缺陷暴露后再开下一刀。
3. 若只是发现本提交内状态文字不准，优先 amend 当前提交，不再制造单独状态同步提交。

## 重要边界

- 不删除 `tmp/stage5_chillys/`。
- 不联网核验真实法规、关税、认证或市场信息。
- 不把搜索摘要写成 Claim。
- 没有可记录的真实搜索/打开来源能力时，默认发现仍停在计划、样本池或已审核投影渲染层。
- Code Slice AD 不建立全球官方机构事实库；它只要求在具体运行中打开来源并记录身份、事实域、管辖范围、时效和边界。
