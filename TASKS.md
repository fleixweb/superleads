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
- Code Slice AF 三路线入口路由纠偏 / route eval 已完成，待提交：路由样例扩到 25 条，新增独立 route eval runner，混合任务可校验 `secondary_routes` / `route_order`。

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

1. 完整运行 Code Slice AF 验证并提交。
2. 后续再排：Code Slice AG 单一客户背调工程资产补齐；Slice AH 批量客户开发内核复盘。

## 当前阻塞 / 注意

- 真实默认发现仍受能力限制：没有可记录的真实搜索/打开来源能力时，默认发现只能停在计划或样本池层；不能伪造 SearchLog / Source / Observation。
- `tmp/stage5_chillys/` 必须保留。
- 不联网判断真实法规、关税、认证或最新行情；只按 graph 中已记录的来源、观察、时效和权威性核验记录做降级。
- Code Slice AD 不建立全球官方机构事实库；它只要求在具体运行中打开来源并记录身份、事实域、管辖范围、时效和边界。
