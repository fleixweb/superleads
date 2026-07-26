# 产品出海市场分析 Code Slice A-C 验证记录（2026-07-26）

## 本轮范围

| Slice | 已实现文件 | 范围 |
|---|---|---|
| A：Schema | `shared/schemas/product-market-analysis.schema.json` | 最小 `ProductMarketAnalysisGraph` 骨架，包含 run、brief、product、trade premise、attribute、source、observation、evidence card、matrix row、gap、conflict、handoff、state transition |
| B：Validator | `scripts/validate_product_market_analysis.py` | 静态 JSON fixture 的 schema + 语义边界校验，输出 `{ ok, issue_count, issues }` |
| C：Fixtures / cases | `evals/fixtures/market_*.json`、`evals/cases/product_market_analysis_cases.json` | 首批 6 个 pass、14 个 fail 夹具；case 文件记录预期错误码 |

## 已覆盖错误码

| 错误码 | 覆盖方式 |
|---|---|
| `market_search_summary_promoted` | fail fixture：搜索摘要升级为 verified |
| `market_skill_summary_as_source` | fail fixture：Skill / 模型摘要当来源 |
| `market_qcvn_promoted_to_un38_3` | fail fixture：QCVN / Vietnam Register 升级 UN38.3 / SDS |
| `market_candidate_hs_promoted_to_final` | fail fixture：候选 HTSUS 写成最终税率 |
| `market_web_label_promoted_to_physical_compliance` | fail fixture：网页标签升级实物标签合规 |
| `market_google_trends_sales_claim` | fail fixture：Google Trends 写成销量 / GMV / 采购需求 |
| `market_logistics_commitment_or_best` | fail fixture：物流写成最佳方式 / 承诺交期 |
| `market_guess_departure_port` | fail fixture：起运港未知却默认常用港口 |
| `market_not_executed_row_missing` | fail fixture：未执行模块缺少矩阵行 |
| `market_delivery_internal_leak` | fail fixture：用户可见来源泄露本地路径 |
| `market_matrix_row_missing_status` | fail fixture：矩阵行缺状态 |
| `market_value_judgment` | fail fixture：报告出现建议进入 / 值得开发等价值判断 |
| `market_geo_roles_merged` | fail fixture：出口申报国、原产国、起运国等角色混写 |
| `market_brief_stale_result_delivered` | fail fixture：Brief 改版后旧结果仍交付 |

## 验证命令与结果

```bash
python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_*.json
# ok=true, issue_count=0

python3 scripts/validate_product_market_analysis.py evals/fixtures/market_fail_*.json
# exit=1，按预期阻断；issue_count=18，覆盖首批预期错误码

python3 evals/run_evals.py --suite default
# 77/77 passed

python3 evals/run_evals.py --suite deep
# 623/623 passed

python3 evals/run_evals.py --suite all
# 663/663 passed
```

> 现有套件数量较上一轮多 1，是因为新增 `product-market-analysis.schema.json` 被静态 schema self-check 纳入；产品市场分析 case 文件暂未并入统一 suite，只作为独立 market validator 的 case 合同。

## 边界说明

- 本轮不联网，不接 Google Trends、关税 API、法规库、真实 Source Pack registry。
- 本轮不生成客户名单，不输出客户类型推荐，不判断产品是否值得进入目标市场。
- 导出器和 audit 仍未实现；当前只完成 schema / validator / fixtures 的防错闭环。
- 搜索摘要、Source Pack、Skill 摘要、外部模型摘要仍只能作为候选或交接信息，不能作为用户可见事实来源。
