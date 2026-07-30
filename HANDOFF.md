# Handoff

- 分支：`master`
- 最新提交：本提交 `Enforce unified Superleads Markdown delivery in skills`
- 当前状态：正式 Skill 调用 Markdown 交付已收口；本地 Skill 与插件缓存已同步为强制走 `scripts/export_superleads_markdown.py`，并新增正式调用冒烟检查脚本。无强制下一 Slice；等待真实缺陷或明确需求。保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已完成

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
