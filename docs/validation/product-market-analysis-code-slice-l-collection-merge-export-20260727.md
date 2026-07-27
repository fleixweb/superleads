# 产品出海市场分析 Code Slice L：手工 collection 并入正式图谱 / 导出链路

日期：2026-07-27

## 目标

把 Slice K 生成的手工来源采集输出，安全追加到正式 `ProductMarketAnalysisGraph`，并串起最小链路：

```text
collection output
→ merge ProductMarketAnalysisGraph.sources / observations
→ validate_product_market_analysis
→ audit_product_market_analysis
→ optional export_product_market_workbook
```

本轮解决的是“用户给 URL / PDF / 已知来源状态后，如何进入正式图谱和用户可见来源表”。它不解决事实抽取、法规判断、关税计算、趋势分析或物流路线生成。

## 新增脚本

新增：`scripts/merge_product_market_collection.py`

输入：

- `--graph`：已有 `ProductMarketAnalysisGraph` JSON。
- `--collection`：Slice K 输出的 `product_outbound_market_analysis_source_collection` JSON。
- `--output`：合并后的图谱输出路径。
- 可选 `--export-dir` / `--markdown` / `--manifest`：合并成功后导出 12 张 CSV、Markdown 和 manifest。

输出固定声明：

```json
{
  "route": "product_outbound_market_analysis_collection_merge",
  "not_evidence": true,
  "does_not_search_web": true,
  "does_not_open_sources": true,
  "does_not_create_evidence_cards": true,
  "does_not_create_matrix_rows": true,
  "allowed_output": "merged_graph_and_optional_exports_only"
}
```

## 合并规则

允许做的事：

- 只追加 `sources`。
- 只追加 `observations`。
- 校验 `run_id` / `brief_id` / `brief_version_id` 与目标图谱一致。
- 合并后立即跑 validator、audit。
- 可选导出，让新增来源出现在“信息来源与待确认事项”。

禁止做的事：

- 不创建 `EvidenceCard`。
- 不创建 `MatrixRow`。
- 不新增 `SearchLog`。
- 不改变已有事实矩阵、税费、认证、物流、趋势、价格或市场判断。
- 不把 URL shell、登录墙、未打开来源写成事实依据。
- 不把搜索摘要写成 Claim 或产品市场事实。

## 新增 fixtures / eval

新增 collection output fixtures：

- `evals/fixtures/source_collection_official_product_page_output.json`
- `evals/fixtures/source_collection_pdf_url_shell_output.json`
- `evals/fixtures/source_collection_restricted_output.json`
- `evals/fixtures/source_collection_output_fail_duplicate_source_id.json`
- `evals/fixtures/source_collection_output_fail_fact_objects.json`
- `evals/fixtures/source_collection_output_fail_not_evidence_false.json`
- `evals/fixtures/source_collection_output_fail_scope_mismatch.json`

新增 eval：

- `evals/cases/product_market_collection_merge_cases.json`
- `evals/run_product_market_collection_merge_evals.py`

覆盖：

- pass：官方产品页已打开来源并入图谱并导出。
- pass：PDF URL shell 并入图谱，但不升级事实。
- pass：登录墙 / 受限来源并入图谱，但只显示“来源受限”。
- fail：重复 Source ID。
- fail：collection 夹带 `evidence_cards` / `matrix_rows`。
- fail：`not_evidence=false`。
- fail：`brief_version_id` 与目标图谱不一致。

## 用户可见导出边界

新增来源只允许出现在：

- `12-信息来源与待确认事项.csv`
- Markdown 报告的“信息来源与待确认事项”表

展示方式：

- 已打开来源：状态显示“已打开”。
- PDF URL shell / 未访问来源：状态显示“来源受限”，待确认事项显示“需打开或复核原始来源”。
- 登录墙来源：状态显示“来源受限”，不带事实摘录。
- 支持字段固定说明：“来源本身仅作可追溯入口；具体支持字段以各矩阵行为准”。

这些来源不会自动改写“市场事实总览”，也不会生成 `UN38.3 已合规`、`最终税率为`、`推荐价格`、`建议进入` 等结论。

## 已验证

```bash
python3 -m py_compile \
  scripts/merge_product_market_collection.py \
  evals/run_product_market_collection_merge_evals.py
```

通过。

```bash
python3 evals/run_product_market_collection_merge_evals.py --suite all
```

结果：`7/7`。

```bash
python3 evals/run_product_market_source_collection_evals.py --suite all
```

结果：`6/6`。

```bash
python3 evals/run_product_market_source_plan_evals.py --suite all
```

结果：`6/6`。

```bash
python3 evals/run_product_market_analysis_evals.py --suite all
```

结果：`42/42`。

```bash
python3 evals/run_evals.py --suite default
```

结果：`84/84`。

```bash
python3 evals/run_evals.py --suite deep
```

结果：`630/630`。

```bash
python3 evals/run_evals.py --suite all
```

结果：`670/670`。

## 边界结论

Slice L 把手工 collection 输出并入正式图谱 / 导出链路，但仍停在“来源入口与待确认事项”层。`Source` / `Observation` 进入图谱后，仍需后续 EvidenceCard 互证与矩阵复核，才能支撑用户可见事实。当前实现没有联网、没有打开来源、没有自动抽取 PDF、没有生成任何产品市场结论。

## 下一步建议

Code Slice M 可以把：

```text
collect_product_market_sources.py
→ merge_product_market_collection.py
→ validate / audit / export
```

封装成一个更顺手的用户入口命令，或者设计“用户给 URL/PDF 后的产品市场分析半自动运行剧本”。
