# Tasks

## 2026-08-11 已完成：真实 UAT 结构化输入预检

- 新增只读 `scripts/precheck_superleads_uat_input.py`，覆盖三条正式路线，优先拦截来源逐字锚定、联系人关联、枚举值和产品属性投影错误；输出 `uat_precheck_*` 诊断，不替代正式 validator / audit。
- 产品市场紧凑 notes 在编译前检查 Observation 打开状态、逐字摘录和 notes 枚举；编译后检查 EvidenceCard 来源引用以及“用户提供产品资料”是否投影到“产品档案与触发项”。不要求旧 source-derived 属性逐行投影，避免误伤既有合法 fixture。
- `using-superleads`、产品市场 Skill、UAT checklist、常用命令和既有静态 suite 已接入 `input_precheck` gate；没有新增 schema、validator 脚本、错误码或 eval runner。
- 插件 manifest 已 bump 到 `0.1.14`；runtime package 已构建为 124 files、1,867,191 bytes，并与 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.14` `diff -qr` 无差异；源码和缓存严格分发检查、插件分发 eval 9/9 均通过。
- 已验证：预检 / 测量 / 编译器单测 13/13；产品市场 75/75；单客背调 7/7；Markdown 交付 9/9；用户可见输出 15/15；`run_evals.py --suite default` 128/128、`--suite all` 721/721、`--suite deep` 678/678；两项 Skill quick validation 和正式 Markdown 冒烟通过。未运行新的联网真实 UAT。

## 2026-08-11 已完成：真实 UAT 测量账本

- 新增 `scripts/measure_superleads_uat.py` 与 3 条回归：记录精确 Git 快照、活动/墙钟耗时、gate 首遍与最终结果、失败分类、修复轮数和 token 可观测性；不执行搜索、不替代任何业务 validator 或 audit。
- 固定 UAT 清单要求新窗口先 `init`，记录实际 preflight / validator / audit（适用时）/ Markdown / workbook / user-visible / claimed-path，再 `finalize`。Git 快照不一致、漏 gate 或未关闭活动区间均为严格 UAT 测量失败。
- `using-superleads` Skill、常用命令、运行时包和插件缓存当前已同步至 `0.1.14`（124 files、1,867,191 bytes）；本条保留的 measurement 3/3、default 127/127、all 720/720、deep 677/677、plugin distribution 9/9 是上一轮 `0.1.13` 历史记录，不把历史指标伪造成当前版本结果。

## 2026-08-11 已完成：精简运行时插件包

- 新增 `scripts/build_superleads_plugin_package.py`：构建 Git 忽略的 `dist/superleads/`，仅复制 Codex/Claude manifest、hooks、skills、scripts、shared 与 spec；`tmp/`、evals、tests、docs、Git 元数据和 Python bytecode 不进入运行时包。
- 分发检查新增 `--runtime-package`，覆盖 49 条 Skill 相对引用（含 scripts），并对开发/历史目录、symlink 和 bytecode 施加包级拒绝。
- 分发 eval 扩为 9/9，已证明缺失 `validate_product_market_analysis.py` 会失败，人工注入 `tmp/old-uat.txt` 也会失败。
- 工件大小为 1,821,708 bytes / 122 files；源码 `tmp/stage5_chillys/` 未移动、未删除。本机 marketplace 已重指向工件并重装 `0.1.12`；实际缓存 2.2 MB，严格检查确认不含 `tmp/`、`evals/`、`tests/` 或 `docs/`。

## 2026-08-11 已完成：Phase 1.2 独立真实 UAT

- 新 UAT 目录：`/tmp/superleads-uat-electric-kettle-phase-1-2-20260811T050529Z`；能力门禁通过，正式搜索和来源打开真实执行。
- 运行 1504 秒，13 Source/Observation、13 EvidenceCard、17 MatrixRow、13 Gap；validator、audit、Markdown、workbook、用户可见和 claimed-path 全部通过。
- 手工输入从旧基线 2011 行降到 1259 行，耗时从 2990 秒降到 1504 秒；只记录本场景绝对差异，不外推普遍百分比。
- Phase 1.2 的效率目标已得到一次独立正向 UAT 支持。下一步不继续压缩 Authority/证据边界，而是评估风险优先级和资料缺口收敛输出。
- UAT 报告与指标保存在 `/tmp/superleads-uat-electric-kettle-phase-1-2-20260811T050529Z/{uat_log.md,uat_metrics.json,compiled_graph.json,report.md,workbook_manifest.json}`。

## 2026-08-11 已完成：产品市场证据编译器 Phase 1.2

- 将 `.plugin-eval/benchmark.json` 从通用 starter 场景改为 Superleads 三场景基准：能力门禁、普通电水壶出口美国盲测、证据边界回归。
- 编译器新增只属于紧凑输入的 `authority_notes`、`matrix_row_templates`、`target_row_ids`、`authority_note_ids`；不改正式 schema、validator、错误码、route 或交付状态。
- `authority_notes` 只接受已打开 Observation 的逐字摘录和人工明确断言，默认保持 `candidate_needs_check` / `not_reviewed`；旧 `row` / `rows` 保持兼容。
- 新增 2 条编译器回归，插件版本 bump 到 `0.1.11` 并同步运行时缓存。
- 验证：compiler 7/7；product-market 75/75；plugin distribution 6/6；default 126/126；all 719/719；deep 676/676；Skill quick validation passed。
- 离线盲测回放保持 8 EvidenceCards、16 MatrixRows、12 Gaps 和 `ready_with_limitations`；没有声称已取得新的耗时降幅。
- 当前会话正式能力门禁为 blocked（`search.web/source.open` unknown），新的独立真实 UAT 待切换到具备 Web Search 和来源打开能力的环境。
- 详细验证：`docs/validation/superleads-product-market-evidence-phase-1-2-20260811.md`。

## 2026-08-10 已完成：产品市场证据编译器 UAT 跟进

- 用同一份电水壶美国 UAT graph 在 `/tmp` 回放编译链路，产出 6 EvidenceCard、13 MatrixRow、10 Gap 和 2 个保留的用户产品属性；validate / audit / Markdown export 全部通过。
- 紧凑笔记现在兼容 `row` / `rows`：同一目标行合并多张卡，单一来源事实可进入多张既有表；行级 freshness / authority 引用避免错误投影。
- 复合未知属性会保留未提供部分，例如 `额定电压/频率` 在提供电压后变为 `频率`，`额定功率` 会清除 `功率` 缺口。
- UAT 回建 notes 为 380 行，只证明结构可编译且交付等价范围可达，不作为独立手写耗时或降本比例结论。插件 `0.1.10` 已同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.10`。

## 2026-08-10 已完成：产品市场证据编译器 Phase 1

- 新增 `scripts/compile_product_market_evidence.py`：消费已有已打开 Source / Observation 与紧凑证据笔记，编译为现有 `EvidenceCard`、`MatrixRow`、`Gap` 和 `ProductAttribute` 对象；不搜索、不打开来源、不新增 schema、不创建新状态。
- 编译器要求引用 Observation 为 `opened` / `captured` / `extracted` / `rendered` 且包含原文摘录；`source_excerpt_quote` 必须逐字出现在原始 Observation 中；未打开来源直接拒绝。
- 用户提供的电压、功率、容量、材料等产品属性以非最终状态写入现有 `attributes`，并从对应产品的未知属性清单中移除，避免已知输入在手写 graph 阶段丢失。
- `analyzing-product-outbound-market` Skill 与常用命令新增编译步骤；插件 manifest / marketplace 版本 bump 至 `0.1.9`。
- 回归：`tests/test_product_market_evidence_compiler.py` 通过 2/2；产品市场 suite 通过 75/75；插件分发 suite 通过 6/6；主 `all` suite 通过 719/719。测试已接入既有 `evals/run_evals.py`，未新增 eval runner。
- 插件 `0.1.9` 已重新安装到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.9`。

## 2026-08-10 已完成：产品出海市场分析按请求范围输出

- `analysis_modules_requested` 现在控制完整十二表或单项报告：缺失、空、未知或意图不确定时完整输出，明确单项仅输出相关表与三张固定表。
- CSV、产品市场 Markdown 和统一 Markdown 交付器使用同一兼容模块映射；source planner 的 `certification` 同时覆盖既有准入和 COO 查询组。未请求模块不会出表或写成“未执行”，单项报告开头明确范围与未覆盖项。
- 单项固定来源表只保留可见模块、产品档案或贸易前提实际引用的来源、Gap 和 Conflict；既有用户可见校验会识别范围声明，不再强制未覆盖模块的税费/运输文案。
- 完整报告空表按未执行、无可用来源、不适用、来源受限分别解释；认证/用户材料、COO/用户材料、候选税号、Trends、物流等既有边界保持不变。
- 新增认证单项 pass fixture 与现有 case/runner 断言；插件版本 `0.1.8` 已重装并同步运行时缓存。
- 未新增 schema、validator 脚本、错误码或 runner，未改批量客户开发、单客背调或 `tmp/stage5_chillys/`。验证记录：`docs/validation/superleads-product-market-report-scope-20260810.md`。

## 2026-08-10 已完成：批量 Markdown 恢复公开联系人

- 批量 Markdown 联系方式汇总扩为七列，显示联系人 / 公开职业线索、待确认原因和来源链接；保留人员型联系方式归位规则。
- 保持 `export_workbook.py`、标准开发名单、单客背调、产品出海市场分析及 `tmp/stage5_chillys/` 不变；`hold_no_source` / `hold_inferred` 仍不显示原值。
- 默认发现 pass fixture 增加带来源观察的 `Jordan Lee / Sales Manager` 人员线索；新增 hold 值脱敏回归 case，未新增 fixture 文件或 runner。
- 联系采集与研究计划 Skill 增加具体公开联系人查询模板，插件版本 bump `0.1.7` 并同步运行时缓存。
- 验证记录：`docs/validation/superleads-bulk-contact-person-visibility-20260810.md`。

## 2026-08-10 已完成：单客背调疑似进出口记录

- `shared/schemas/research-graph.schema.json` 仅新增可选顶层 `suspected_trade_records` 数组；记录字段禁止必填 `entity_id`，并保留 `additionalProperties: false`。
- `skills/researching-customer-background/SKILL.md` 覆盖族 E 增加中英文主动查询模板、摘要字段抓取、详情受限处理；覆盖族 F 明确贸易查询必须锚定当前对象；报告改为六张固定表 + 一张条件表并补措辞红线。
- `scripts/background_report.py` 将记录投影为六列条件表，并把完整 URL 放入“信息从哪里来”；`not_searched` / `searched_not_found` 分别显示“本轮未检索” / “已检索未见”。
- `scripts/export_superleads_markdown.py`、`scripts/export_workbook.py --mode background` 同步输出条件表；无记录时与改动前保持六张表。
- 复用 `user_visible_evidence_upgrade` 错误码，追加阻断“从中国采购”“海关数据显示”“年进口量”。新增 1 个 pass graph fixture、1 个 fail 用户可见样本并接入现有 cases/runner。
- 插件版本 bump `0.1.6` 并同步缓存；保留 `tmp/stage5_chillys/`。

## 已完成

- 2026-08-10 Source Capability Gate / 0.1.5：正式客户开发、单客背调、产品出海市场分析统一要求当前 Run 同时具备 `search.web` 和一个来源打开能力；缺失时硬停并提示切换环境，资料初审保留为非正式独立路径。修复产品链接 + 目标国风险问法路由、电水壶误入锂电 Pack、市场报告顶部合并原产/出口国标签；补齐插件公开 URL 与 hooks 分发/命令目标回归。`evals/run_evals.py --suite all` 为 716/716。
- 后续唯一优先项：在具备真实检索和来源打开能力的环境，限时 30 分钟手工跑“普通电水壶，中国出口美国”真实业务 UAT；记录卡点、手写 JSON 行数、事实/待确认比例、空模块和用户可用性。Observation -> EvidenceCard -> MatrixRow 编译器在该 UAT 前不实现。

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
- 正式 Skill 调用 Markdown 交付收口已完成：本地 Skill 与插件缓存强制 chat-readable 报告走 `scripts/export_superleads_markdown.py`，禁止手工渲染 workbook sheet；新增 `scripts/check_superleads_formal_markdown_delivery.py`。
- 真实业务 UAT 正式交付链路补强已完成：阻断 `依据状态=已观察/已观察；需确认/已观察；来源受限` 等内部状态泄漏；正式交付必须有 graph JSON 路径和 exporter JSON 成功结果。
- 真实业务 UAT 声明路径复核补强已完成：声明的 Markdown 路径必须与该 graph 的 exporter 输出逐字一致；单客背调 Markdown exporter 支持纳入冒烟。
- 真实业务 UAT 固定验收清单已完成：claimed path 复核成为固定验收步骤；新增 `docs/validation/superleads-real-business-uat-checklist.md` 并更新常用命令和验证记录。
- claimed path UAT 自动回归已完成：Markdown delivery eval 新增 claimed path 正向/负向回归，阻断手工后处理 Markdown 冒充 exporter 原始输出。
- 单客背调 claimed path 真实 UAT 已完成：Chilly’s Bottles `customer_background_research` 路线 claimed graph/report 独立复核通过，证明 claimed path 门禁不是 bulk-only。
- 插件发布/安装链路 UAT 已完成：根因确认为 `0.1.3` 缓存由 2026-07-20 源树生成、版本未 bump 导致 2026-07-27 后新增的产品出海市场分析 Skill / intake reference / spec 未进入运行时；版本已 bump 到 `0.1.4` 并重新安装，新增插件分发完整性校验并纳入 `evals/run_evals.py`。






## 真实业务 UAT 声明路径复核补强已完成

1. 声明路径精确复核
   - `scripts/check_superleads_formal_markdown_delivery.py` 新增 `--claimed-graph`、`--claimed-markdown`、`--claimed-route`。
   - 对声明 graph 重新运行 `export_superleads_markdown.py`，并与声明 Markdown 路径做 SHA-256/文本精确比对。
   - 英国保温杯第二轮 UAT 报告命中 `formal_markdown_claimed_output_mismatch`。
2. 单客背调 exporter 冒烟
   - 冒烟脚本新增 `customer_background_research` fixture。
   - 确认 `export_superleads_markdown.py --route customer_background_research` 可输出 `# 单一客户背调` 和“怎么联系、先找谁”。
3. Skill / 插件缓存
   - `using-superleads` / `exporting-lead-workbooks` 要求最终声明路径必须是 exporter 原始输出。
   - `researching-customer-background` 明确不要声称 Markdown exporter 只支持 bulk。
4. 已验证
   - `python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json --format json` → passed, issue_count=0。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 14/14。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/researching-customer-background` → passed。

## 真实业务 UAT 固定验收清单已完成

1. 固定门禁
   - 所有真实业务 UAT 正式 Markdown 交付都必须执行 claimed path 复核。
   - `exporter ok=true` 只证明 graph 可导出；还必须证明最终声明给用户的 Markdown 路径与同一 graph 的重新导出结果逐字一致。
2. 文档
   - 新增 `docs/validation/superleads-real-business-uat-checklist.md`。
   - 更新 `docs/superleads-common-commands.md` 与 `docs/validation/superleads-real-business-formal-delivery-20260731.md`。
3. 固定命令
   - `python3 scripts/check_superleads_formal_markdown_delivery.py --claimed-graph "$GRAPH" --claimed-markdown "$MARKDOWN" --claimed-route auto --format json`。
4. 失败口径
   - `formal_markdown_claimed_output_mismatch` 直接判 UAT fail；不得手工改 Markdown 后复用旧 exporter 成功结果。

## claimed path UAT 自动回归已完成

1. 回归位置
   - `evals/run_superleads_markdown_delivery_evals.py`。
2. 新增覆盖
   - exporter 原始输出作为 claimed Markdown：通过。
   - exporter 输出后追加手工内容再作为 claimed Markdown：失败，并要求错误码包含 `formal_markdown_claimed_output_mismatch`。
3. 已验证
   - `python3 -m py_compile evals/run_superleads_markdown_delivery_evals.py scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py` → passed。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 7/7。

## 单客背调 claimed path 真实 UAT 已完成

1. UAT 对象
   - Chilly’s Bottles / Chilly’s。
   - 路线：`customer_background_research`。
2. 复核路径
   - graph：`/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json`。
   - Markdown：`/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md`。
3. 已验证
   - `python3 scripts/check_superleads_formal_markdown_delivery.py --claimed-graph /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json --claimed-markdown /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md --claimed-route customer_background_research --format json` → passed, issue_count=0。
   - `python3 scripts/validate_superleads_user_visible_output.py /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md --route customer_background_research --min-tables 6 --format json` → passed, issue_count=0，table_count=7。
4. 结论
   - claimed path 门禁已在 bulk 和 `customer_background_research` 两条路线真实 UAT 中通过。

## 真实业务 UAT 正式交付链路补强已完成

1. 用户可见 validator
   - `scripts/validate_superleads_user_visible_output.py` 新增 `user_visible_basis_status_internal_leak`。
   - 阻断 `依据状态` 列或 `依据状态 xxx` 行使用 `已观察`、`未检索`、`主体待确认`、`已解析`、`已观察；需确认`、`已观察；来源受限`。
2. 回归样本
   - 新增 `evals/user_visible_outputs/fail_bulk_customer_real_uat_internal_basis_status.md`。
   - `evals/cases/superleads_user_visible_output_cases.json` 用户可见 suite 从 13/13 扩到 14/14。
3. Skill / 插件缓存
   - `using-superleads` / `exporting-lead-workbooks` 要求真实业务正式交付必须有保存的 graph JSON 和 exporter JSON 成功结果。
   - 只有搜索笔记或手写表格时，只能称 research draft / source-collection note。
   - 插件缓存 `~/.codex/plugins/cache/fleix/superleads/0.1.3/skills/...` 已同步。
4. 已验证
   - `python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json` → passed, issue_count=0。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 14/14。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 evals/run_evals.py --suite default` → 122/122。
   - `python3 evals/run_evals.py --suite all` → 714/714。
   - `python3 evals/run_evals.py --suite deep` → 671/671。

## 正式 Skill 调用 Markdown 交付收口已完成

1. Skill 调用说明
   - `skills/using-superleads/SKILL.md`：正式 Markdown 交付必须调用 `scripts/export_superleads_markdown.py`。
   - `skills/exporting-lead-workbooks/SKILL.md`：禁止手工从 `export_workbook.py` CSV/workbook sheet 渲染 chat-facing Markdown。
   - 插件缓存 `~/.codex/plugins/cache/fleix/superleads/0.1.3/skills/...` 已同步。
2. 正式调用冒烟脚本
   - 新增 `scripts/check_superleads_formal_markdown_delivery.py`。
   - 检查 Skill 源文件与插件缓存一致、包含强制统一 Markdown delivery 说明。
   - 实跑 `export_superleads_markdown.py --route bulk_customer_development`，确认 Northshore 为 `可能相关 / 来源受限`，且没有旧 raw workbook Markdown 主表。
3. 已验证
   - `python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json` → passed, issue_count=0。
   - `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` → 5/5。
   - `python3 evals/run_superleads_user_visible_output_evals.py --suite all` → 13/13。

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
