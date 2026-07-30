# Code Slice AH：批量客户开发默认发现防绕过与 Markdown 展示补齐

日期：2026-07-30

## 本轮目标

落实 Slice AH 纠偏结论：不把 `初筛客户名单` 做成独立 L2，而是保持默认弱证据交付为 `发现候选池`，并把“初筛价值”放在候选池内部的分区、依据状态、联系方式状态、搜索覆盖和待确认项中表达。

本轮优先级：

1. 先堵 `output_mode=初筛客户名单` 绕过默认发现 Candidate 结构检查的口子；
2. 再补 bulk Markdown 发现候选池展示，让聊天交付与 workbook 的 7 张表对齐；
3. 不新增 `delivery_status`、不新增 exporter mode、不新增 audit 分支。

## 改动范围

| 类型 | 文件 | 说明 |
|---|---|---|
| Validator | `scripts/validate_research_graph.py` | `初筛客户名单` 不再跳过默认发现 Candidate 结构检查，并被显式判为弃用输出模式 |
| Workbook 导出 | `scripts/export_workbook.py` | 默认发现主表新增 `分区`、`依据状态`，与 Markdown 共享候选池展示语义 |
| Markdown 导出 | `scripts/export_superleads_markdown.py` | bulk 从 4 张表补到 8 张表：方向、候选池、联系方式、搜索覆盖、待确认、已排除/仅作参考、来源、风险说明 |
| 用户可见检查 | `scripts/validate_superleads_user_visible_output.py` | bulk 路线必须出现 `依据状态`、三分区、联系方式汇总、搜索覆盖与收敛、风险与说明；并要求至少一个 Slice AE 用户可见状态 |
| Graph fixture | `evals/fixtures/fail_initial_screening_output_mode_bypass.json` | 用 `output_mode=初筛客户名单` + 破坏 Candidate 字段复现旧绕过口，现必须 fail |
| Eval cases | `evals/cases/minimum_gate_cases.json` | 将绕过口 fail fixture 纳入 default suite |
| Markdown eval | `evals/cases/superleads_markdown_delivery_cases.json` | bulk 生成交付要求 7+ 表和新列/分区 |
| 用户可见样本 | `evals/user_visible_outputs/bulk_customer_development_us_generator_aftermarket.md` | 更新为三分区 + 依据状态 + 7 类信息块 |
| 用户可见 fail 样本 | `evals/user_visible_outputs/fail_bulk_customer_missing_basis_status.md` | 缺 `依据状态` / 三分区 / 缺失表时必须 fail |

## 关键行为

| 场景 | 结果 |
|---|---|
| `output_mode=发现候选池` 且 Candidate 结构完整 | pass |
| `output_mode=发现候选池` 且缺 `dedupe_basis` / `signal_summary` / `unknowns` 等 | fail |
| `output_mode=初筛客户名单` 且 Candidate 被掏空 | fail，命中 `initial_screening_output_mode_deprecated` 和 Candidate 结构错误 |
| bulk Markdown 生成 | 输出 8 个 Markdown 表格，不新增事实、不输出推荐客户/采购概率/采购意愿 |
| bulk 用户可见样本缺 `依据状态` 或缺三分区/联系方式/搜索覆盖/风险说明 | fail |

## 已验证

```bash
python3 -m py_compile scripts/validate_research_graph.py scripts/export_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py evals/run_evals.py evals/run_superleads_user_visible_output_evals.py evals/run_superleads_markdown_delivery_evals.py  # passed
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 11/11
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 119/119
python3 evals/run_evals.py --suite deep  # 668/668
python3 evals/run_evals.py --suite all  # 711/711
python3 evals/run_superleads_route_evals.py --suite all  # 25/25
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed
```

## 验收结论

Code Slice AH 已完成。`初筛客户名单` 不再是可端到端绕过默认发现纪律的活口；批量客户开发 Markdown 交付现在能展示发现候选池的三分区、依据状态、联系方式汇总、搜索覆盖与收敛、已排除/仅作参考和风险说明。

## 已知限制

- `可能客户角色` 依赖实体级 `customer_type` / `customer_role` 等字段；无公开依据时仍可留空或写 `待确认`。
- `依据状态` 现在通过统一人话投影层展示，`observed` 类公开信号在默认发现中优先呈现为 `已有明确依据`，以便区分“已被公开来源直接支持”和“仅作线索”。
- `采购意愿待确认` 这类词语不应再被 bulk 路线的裸词禁用误杀；真正禁止的是把它写成已确认采购意愿或采购负责人已确认。

## 20260730 复核发现的缺陷与修复

复核发现：上一轮提交 `26e788f Refine bulk discovery status projection` 虽然把 `observed` 业务信号接入了 `已有明确依据`，但实现顺序错误：`business_match.status = observed` 先把行状态设为 `verified`，后续来源受限、主体待确认等降级检查被 `candidate` 分支短路。

实际后果是目录级弱线索会被升级。例如 `shared/references/default-discovery-reference.example.json` 中 `Northshore Drinkware Distributors` 同时具备：

- `business_relevance_status = possibly_related`
- `signal_summary.business_match.status = observed`
- `signal_summary.trade_record.status = source_restricted`
- `source_restrictions = ["目录详情页需登录"]`

修复方式：bulk 默认发现依据状态改为先扫描全部 `signal_summary` 兄弟信号和 `source_restrictions`，先处理 `identity_pending` / `source_restricted` / `insufficient_information` 等降级，再在无降级时才允许 `business_match.status = observed` 投影为 `已有明确依据`；Markdown 回退逻辑改为复用 workbook 共享函数。

人工渲染核对后，Northshore 主表行为：

```markdown
| 待确认 | Northshore Drinkware Distributors | United Kingdom | 经销商 / 分销商 | drinkware distributor 目录条目；公开电话 | 可能相关 | 来源受限 | 442070002222（建议核查后使用） | 补开官网产品页确认保温杯；产品线是否包含 insulated bottle 待确认；目录详情页需登录 | 公开目录列表；搜索组:uk_directory；Northshore Drinkware Distributors；https://directory.example/northshore |
```

新增回归：

- graph/export 断言：`Beta Industrial Supplies` 行必须为 `来源受限`，不得含 `已有明确依据`。
- 用户可见 fail 样本：来源受限行若写成 `已有明确依据`，命中 `bulk_basis_status_source_restricted_promoted`。
- bulk 用户可见样本和 Markdown delivery case 同时要求出现 `已有明确依据` 与 `来源受限`。

本轮复核验证：

```bash
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
```
