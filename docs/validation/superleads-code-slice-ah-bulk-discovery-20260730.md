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
