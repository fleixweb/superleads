# 产品出海市场分析 Code Slice I：Source Pack registry + Query Plan generator

日期：2026-07-27

## 目标

本轮只做“去哪里找、下一步怎么查”的工程骨架：

- Source Pack registry：来源入口目录，不是事实库；
- Query Plan generator：生成可审计查询计划，不搜索、不打开来源；
- fixtures / evals：验证两个真实样本和边界样本不会把计划升级成事实。

## 本轮实现

### 1. Source Pack registry

新增：`shared/source_packs/product_market_seed_packs.json`

首批覆盖 10 个 seed Pack：

| Pack | 作用 |
|---|---|
| `seed_us_market_access_general` | 美国目的国准入、标签、包装、安全入口 |
| `seed_us_import_tax_general` | 美国官方税则、裁定、贸易救济入口 |
| `seed_us_origin_proof_general` | 美国 COO / proof of origin / rules of origin / origin marking 入口 |
| `seed_cn_export_general` | 中国出口申报、管制、商检/检验检疫入口 |
| `seed_vn_export_general` | 越南出口申报、贸易主管、质量/检验入口 |
| `seed_transpacific_logistics_general` | 中国/越南到美国物流、预申报、港口/承运入口 |
| `seed_market_signal_global_to_us` | 美国 Google Trends、公开报告、平台价格、指数、节假日、外部因素入口 |
| `seed_lithium_battery_common_rules` | 锂电 SDS、UN38.3、包装、危险品运输入口 |
| `seed_textile_apparel_common_rules` | 纺织服装成分、标签、BOM、归类参考入口 |
| `seed_product_original_sources` | 产品官网、PDF、TDS、SDS、BOM、标签照片等原始资料入口 |

registry 内含 SourceEntry、QueryTemplate、ObservationRequirement、PackRouteRule，但只保存入口、槽位、观察要求和边界，不保存税率、认证结论、物流时效、趋势结论、价格区间或市场进入建议。

### 2. Query Plan generator

新增：`scripts/plan_product_market_sources.py`

示例：

```bash
python3 scripts/plan_product_market_sources.py \
  --input evals/fixtures/source_plan_xingheng_lithium_us_brief.json \
  --format json
```

输出边界固定为：

- `route = product_outbound_market_analysis_source_plan`
- `execution_level = source_plan_only`
- `not_evidence = true`
- `does_not_search_web = true`
- `does_not_open_sources = true`
- 每个 query step 都有 `must_open_source = true`、`reject_if_only_snippet = true`、`allowed_output = source_or_query_plan_only`

### 3. fixtures / evals

新增 fixtures：

| fixture | 验证点 |
|---|---|
| `source_plan_xingheng_lithium_us_brief.json` | 越南出口申报国 + 越南原产线索 + 锂电产品出口美国，触发美国准入/税费/COO、越南出口、跨太平洋物流、市场信号、锂电通用和产品原始资料 Pack |
| `source_plan_uniqlo_textile_us_brief.json` | 中国出口申报国 + 中国原产线索 + 纺织服装出口美国，触发美国准入/税费/COO、中国出口、跨太平洋物流、市场信号、纺织通用和产品原始资料 Pack |
| `source_plan_origin_without_export_country_brief.json` | 只有 Made in / 原产线索、没有出口申报国时，不自动触发出口国结论 |
| `source_plan_bulk_roro_brief.json` | 散杂、滚装、大宗/项目货，触发物流、指数/公开市场信号和出口国来源计划，但不承诺路线或港口可操作 |
| `source_plan_missing_target_brief.json` | 缺目标国时 planner 返回 `ok=false`，只能保留计划缺口 |

新增：

- `evals/cases/product_market_source_plan_cases.json`
- `evals/run_product_market_source_plan_evals.py`

## 关键防错

| 防错点 | 本轮做法 |
|---|---|
| Source Pack 被当事实库 | root、pack、query step 均声明 `not_evidence` |
| 搜索摘要升级事实 | query step 强制 `reject_if_only_snippet = true` |
| 没打开来源却输出结论 | planner 显式 `does_not_search_web / does_not_open_sources` |
| 原产国与出口申报国混同 | brief summary 保留目标国、出口申报国、原产国、起运地分列 |
| 只有原产线索无出口国 | 不触发中国/越南出口 Pack，生成出口国待确认 warning |
| 锂电运输越界 | 只生成 SDS / UN38.3 / 包装 / 承运入口计划，不写可运输 |
| 纺织标签越界 | 只生成实物标签 / BOM / 规则入口计划，不写真正合规 |
| 大宗散杂/RoRo 越界 | 只生成物流/指数/公开市场入口，不写最佳路线、船型或时效承诺 |
| 市场信号越界 | Trends / 平台价 / 报告只作为入口计划，不写销量、成交价或建议进入 |

## 已验证命令

```bash
python3 -m py_compile scripts/plan_product_market_sources.py evals/run_product_market_source_plan_evals.py scripts/validate_product_market_analysis.py scripts/audit_product_market_analysis.py scripts/export_product_market_workbook.py
python3 evals/run_product_market_source_plan_evals.py --suite all
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

结果：

- source-plan suite：`6/6`
- market suite：`36/36`
- default suite：`84/84`
- deep suite：`630/630`
- all suite：`670/670`

## 边界

- 本轮没有联网搜索；没有打开任何网页、PDF 或平台页。
- Source Pack / Query Plan 不能生成 EvidenceCard、MatrixRow、税率、认证、物流时效、价格、趋势或行情结论。
- Source Pack 里的维护日期只表示本地 seed registry 创建/维护日期，不是法规、税率、价格或来源观察日期。
- 下一步若进入真实采集，必须从 Query Plan 生成 SearchLog / Source / Observation，再通过现有证据边界进入 EvidenceCard / MatrixRow。
