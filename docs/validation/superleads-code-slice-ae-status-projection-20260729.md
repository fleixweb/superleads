# Code Slice AE：状态投影与用户可见状态校验验证记录

日期：2026-07-29

## 范围

本次 Code Slice AE 落地 Slice AE 的“状态词压缩 / 用户可见状态映射”设计：

- 新增统一状态投影工具，把产品市场分析内部状态投影为 11 个用户可见人话状态；
- 产品出海市场分析 CSV / Markdown 导出新增 `依据状态`、`依据说明`，并把 COO / 认证规则结论与用户材料状态分列；
- 用户可见 validator 阻断产品市场分析最终 Markdown 泄露内部状态 token；
- 更新用户可见静态样本、Markdown 生成 eval 和 product market export assertions。

## 已验证命令

```bash
python3 -m py_compile scripts/user_visible_status_projection.py scripts/export_product_market_workbook.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py evals/run_product_market_analysis_evals.py evals/run_superleads_user_visible_output_evals.py evals/run_superleads_markdown_delivery_evals.py
python3 evals/run_product_market_analysis_evals.py --suite all       # 74/74
python3 evals/run_superleads_user_visible_output_evals.py --suite all # 9/9
python3 evals/run_superleads_markdown_delivery_evals.py --suite all   # 5/5
python3 evals/run_evals.py --suite default                           # 99/99
python3 evals/run_evals.py --suite all                               # 685/685
python3 evals/run_evals.py --suite deep                              # 645/645
git diff --check                                                     # passed
```

说明：一次串行运行 default/all/deep 时命令整体超过 240s 超时；其中 default 与 all 已完成并通过，deep 随后单独重跑通过。

## 重点验收

| 验收项 | 结果 |
|---|---|
| 内部 `verified / candidate / technical_docs_required` 等不直接作为产品市场用户状态展示 | 通过 |
| `stale_needs_recheck` 可把原本已打开/已核实的行投影为 `资料过旧需复核` | 通过 |
| `secondary_reference_only`、`unable_to_verify` 等权威性限制不会显示为强确定依据 | 通过 |
| COO / 原产地证明规则结论与用户材料状态分列展示 | 通过 |
| 认证 / 目的国准入规则结论与用户材料状态分列展示 | 通过 |
| 多来源一致显示为 `多来源方向一致`，不升级为官方确认 | 通过 |
| 未执行模块保留为 `本轮未执行`，不补样板事实 | 通过 |
| 用户可见静态 Markdown 出现内部状态 token 时失败 | 通过 |
