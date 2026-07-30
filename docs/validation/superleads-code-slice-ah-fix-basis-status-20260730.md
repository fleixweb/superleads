# Code Slice AH-FIX：修复 bulk 发现候选池依据状态降级优先级

日期：2026-07-30

## 本轮目标

修复 `26e788f Refine bulk discovery status projection` 引入的弱证据升级缺陷：bulk 默认发现中，`business_match.status = observed` 曾被先投影成 `verified`，随后 `source_restricted` / `identity_pending` 等兄弟信号降级检查被短路，导致目录级弱线索可显示为 `已有明确依据`。

本轮只修复依据状态降级优先级，不新增 output_mode、delivery_status、export_workbook mode 或 audit 分支。

## 修复方式

- `scripts/export_workbook.py`
  - 新增共享投影入口 `project_default_discovery_basis_status(...)`，先扫描 Candidate 的全部 `signal_summary` 信号键和 `source_restrictions`，再决定是否可投影 `verified`。
  - 降级顺序：`identity_pending` / 主体冲突 → `conflict_pending_review`；任一 `source_restricted` 或 `source_restrictions` 非空 → `source_restricted`；`insufficient_information` → `not_provided`；只有无降级且 `business_match.status = observed` 时才进入 `verified`。
  - 仍统一调用 `project_market_row_status(...)` 输出 11 个用户可见状态词。
- `scripts/export_superleads_markdown.py`
  - `_candidate_basis_status` 继续优先使用 workbook 行里的 `依据状态`；缺列回退时调用 workbook 共享投影函数，不保留第二份手写映射。
- `scripts/validate_superleads_user_visible_output.py`
  - bulk 路线新增用户可见一致性检查：同一 Markdown 主表行含来源受限/登录墙/摘要页等限制信号时，不得把 `依据状态` 写成 `已有明确依据`。

## 回归保护

- `evals/cases/minimum_gate_cases.json`
  - 对 `pass_default_discovery_candidate_pool.json` 增加行级导出断言：`Beta Industrial Supplies` 这一行必须包含 `来源受限`，且不得包含 `已有明确依据`。
- `evals/user_visible_outputs/fail_bulk_customer_source_restricted_promoted_basis.md`
  - 新增 fail 样本：某候选 `业务相关性 = 可能相关`、来源状态含 `来源受限`，但 `依据状态 = 已有明确依据`，必须命中 `bulk_basis_status_source_restricted_promoted`。
- `evals/user_visible_outputs/bulk_customer_development_us_generator_aftermarket.md`
  - pass 样本同时保留 `已有明确依据` 和 `来源受限`，证明 `依据状态` 列有区分度。
- `evals/cases/superleads_user_visible_output_cases.json` / `evals/cases/superleads_markdown_delivery_cases.json`
  - 更新 must_contain，覆盖 `来源受限`。

## 人工渲染核对

命令：

```bash
python3 -c "import json,sys; sys.path.insert(0,'scripts'); from export_superleads_markdown import build_bulk_markdown; g=json.load(open('shared/references/default-discovery-reference.example.json')); t,i=build_bulk_markdown(g); print(t)"
```

关键行：

```markdown
| 待确认 | Northshore Drinkware Distributors | United Kingdom | 经销商 / 分销商 | drinkware distributor 目录条目；公开电话 | 可能相关 | 来源受限 | 442070002222（建议核查后使用） | 补开官网产品页确认保温杯；产品线是否包含 insulated bottle 待确认；目录详情页需登录 | 公开目录列表；搜索组:uk_directory；Northshore Drinkware Distributors；https://directory.example/northshore |
```

结论：Northshore 不再因 `business_match = observed` 被升级为 `已有明确依据`；其兄弟信号 `trade_record.status = source_restricted` 和 `source_restrictions = ["目录详情页需登录"]` 先触发降级，最终显示为 `来源受限`，分区保持为 `待确认`。

## 已验证

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

## 验收结论

Code Slice AH-FIX 已完成。默认发现 / bulk Markdown 的依据状态投影恢复 Slice AE 优先级：先降级，再判断是否 `verified`；`observed + source_restricted` 不再被渲染为 `已有明确依据`。
