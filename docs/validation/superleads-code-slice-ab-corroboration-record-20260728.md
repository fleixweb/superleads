# Code Slice AB：多来源互证 / CorroborationRecord 验证记录

日期：2026-07-28

## 1. 本轮目标

把 Slice AA 中的“弱证据收敛”落成最小可执行结构：多个独立弱来源指向同一方向时，可以在用户可见报告中显示“多来源一致指向”，但不能升级成最终事实、推荐、成交价、最终税率、合规结论或市场进入判断。

## 2. 已修改内容

| 文件 | 变化 |
|---|---|
| `shared/schemas/product-market-analysis.schema.json` | 增加可选 `corroboration_records`；新增 `CorroborationRecord` / `CorroborationStatus`；`MatrixRowRecord` 可引用 `corroboration_record_ids` |
| `scripts/validate_product_market_analysis.py` | 增加互证校验：来源必须打开、搜索摘要/Query Plan 不能直接互证、独立来源数按 owner/domain 保守计算、冲突不能隐藏、多弱来源不能让矩阵行变 `verified` |
| `scripts/export_product_market_workbook.py` | 导出层增加人话列：`多来源互证情况`、`互证边界`、`下一步核实`；不暴露内部对象名和 ID |
| `evals/cases/product_market_analysis_cases.json` | market suite 从 50 条扩展到 57 条 |
| `spec/31-superleads-corroboration-record-code-slice-ab.md` | 新增 Code Slice AB 规格文档 |

## 3. 新增 fixtures

| fixture | 预期 | 验收点 |
|---|---|---|
| `market_pass_multi_source_corroboration_reference.json` | pass | 3 个独立已打开公开来源可显示“多来源一致指向”，但状态仍为 `preliminary_reference` |
| `market_fail_corroboration_single_source_promoted.json` | fail | 单一来源不能写成多来源一致 |
| `market_fail_corroboration_same_domain_independent.json` | fail | 同一域名/owner 不能算多个独立来源 |
| `market_fail_corroboration_conflict_hidden.json` | fail | 同字段冲突不能隐藏成一致结论 |
| `market_fail_corroboration_search_summary_source.json` | fail | SearchLog / 搜索摘要不能直接作为互证来源 |
| `market_fail_corroboration_overstated_verified.json` | fail | 多个弱来源一致不能把矩阵行升级为 `verified` |
| `market_fail_corroboration_unopened_source.json` | fail | 未打开来源不能参与互证 |

## 4. 用户可见变化

产品市场分析导出的 CSV / Markdown 行现在可以出现：

| 人话字段 | 说明 |
|---|---|
| 多来源互证情况 | 如“多来源一致指向；3 个独立来源；多个独立公开页面的线上标价都落在相近区间” |
| 互证边界 | 如“不能写成成交价、批发价、外贸目标价或推荐报价” |
| 下一步核实 | 如“结合客户类型、订单量、贸易条款、税费、运费和实时报价复核” |

导出器仍只搬运已审核矩阵和安全字段，不补事实、不猜价格、不推荐进入。

## 5. 已验证命令

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py
python3 evals/run_product_market_analysis_evals.py --suite all  # 57/57
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # 通过
```

说明：`run_evals.py --suite all` 仍不包含 market suite；market suite 需单独运行 `run_product_market_analysis_evals.py --suite all`。

## 6. 边界

本轮不解决：

- 来源时效降级；
- Authority registry；
- 认证/法规官方来源域名精细化；
- 状态词压缩；
- 批量客户开发和单客背调的多来源互证结构。
