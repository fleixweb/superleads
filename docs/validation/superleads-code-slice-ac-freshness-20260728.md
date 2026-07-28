# Code Slice AC：资料时效 / Freshness 降级验证记录

日期：2026-07-28

## 1. 本轮目标

把 Slice AA 中“没有时效降级”的问题落成最小可执行闭环：法规、关税、认证、出口要求、线上价格、物流、近期外部因素等强时效信息，不能只因为来源被打开过就写成“最新 / 现行 / current / latest”。

## 2. 已修改内容

| 文件 | 变化 |
|---|---|
| `shared/schemas/product-market-analysis.schema.json` | 新增可选 `freshness_records`；新增 `FreshnessRecord` / `FreshnessStatus` / `FreshnessSubjectType`；`EvidenceCard` 和 `MatrixRowRecord` 可引用 `freshness_record_ids` |
| `scripts/validate_product_market_analysis.py` | 新增时效识别、默认复核窗口、latest/current 话术门禁、stale/date unknown 降级门禁、observed_at 不可单独支撑 current 的规则 |
| `scripts/export_product_market_workbook.py` | CSV / Markdown 新增人话字段：`资料时效`、`复核建议`、`不能当最新结论`；Markdown 顶部新增 `资料时效 / Freshness` 摘要区 |
| `scripts/audit_product_market_analysis.py` | 将 stale/date unknown freshness 作为交付 limitation 暴露给 audit 结果 |
| `evals/cases/product_market_analysis_cases.json` | market suite 从 57 条扩展到 65 条 |
| `spec/32-superleads-freshness-code-slice-ac.md` | 新增 Code Slice AC 规格文档 |

## 3. 新增 fixtures

| fixture | 预期 | 验收点 |
|---|---|---|
| `market_pass_freshness_stale_tariff_downgraded.json` | pass | 旧版 HTS 资料降级为历史线索；导出显示资料偏旧、复核建议、不能当最新税率 |
| `market_pass_freshness_date_unknown_product_attribute.json` | pass | 产品网页日期未见仍可作为网页属性线索；不能当实物标签或未来批次结论 |
| `market_pass_freshness_current_tariff_rechecked.json` | pass | 有来源日期且在窗口内，可写“本轮复核日期在当前口径内”；仍不能写最终税率 |
| `market_fail_freshness_old_tariff_called_latest.json` | fail | 旧税表写成“最新税率”被阻断 |
| `market_fail_freshness_date_unknown_regulation_verified.json` | fail | 日期未见的认证/法规要求被升级为 verified 被阻断 |
| `market_fail_freshness_recent_factor_without_date_latest.json` | fail | 无日期近期外部因素写成“最新影响”被阻断 |
| `market_fail_freshness_current_observed_only.json` | fail | 只用 `observed_at` 冒充来源日期支撑 current 被阻断 |
| `market_fail_freshness_not_time_sensitive_for_tariff.json` | fail | 关税字段误标 `not_time_sensitive` 被阻断 |

## 4. 用户可见变化

产品出海市场分析导出的 CSV / Markdown 会在强时效相关表中出现：

| 人话字段 | 说明 |
|---|---|
| 资料时效 | 比如“资料偏旧，需重新复核；复核窗口约 30 天；旧版 HTS 只能当历史线索” |
| 复核建议 | 比如“报关前重新打开报关日适用 HTS/关税来源，并由报关专业方复核” |
| 不能当最新结论 | 比如“不能当最新税率；不能当最终税额；不能替代报关日归类复核” |

Markdown 顶部新增 `资料时效 / Freshness` 摘要，先提醒用户哪些资料会过期、哪些只是本轮观察线索。

## 5. 首版默认复核窗口

| 信息域 | 默认窗口 |
|---|---:|
| 近期外部因素 | 14 天 |
| 进口税费 / 出口要求 / 线上价格 | 30 天 |
| Google Trends / 物流 | 90 天 |
| 目的国认证准入 / 原产地证明 | 180 天 |
| 市场报告 / 季节节日窗口 | 365 天 |

这些窗口只用于本地门禁和降级，不等于真实世界承诺；后续 Authority registry 可覆盖到国家、机构和来源级别。

## 6. 已验证命令

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 65/65
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # passed
```

注意：`run_evals.py --suite all` 仍不包含产品出海市场分析 market suite；market suite 需要单独运行 `python3 evals/run_product_market_analysis_evals.py --suite all`。

## 7. 边界

本轮不做：

- 不联网核验真实法规、关税、认证、价格、物流或近期行情；
- 不把 Source Pack / Query Plan / 搜索摘要变成事实；
- 不用 `observed_at` 替代来源发布日期或生效日期；
- 不输出是否值得进入市场、推荐价格、推荐客户、采购概率、最终税率或最终合规结论。
