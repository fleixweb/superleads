# 产品出海市场分析 Code Slice K：手工 URL / 已知来源到 Source / Observation 最小桥接

日期：2026-07-27

## 目标

把用户明确给出的公开 URL、PDF 链接或已知来源状态，安全转换成产品出海市场分析可追溯的 `Source` / `Observation` 记录。

本轮仍然不做自动搜索、不联网抓取、不下载 PDF、不生成事实结论。它只解决一个问题：当用户已经给了 URL 或上游工具已经打开过来源时，系统可以把“这个来源是什么、是否打开、看到的原文片段是什么”记录下来，交给后续 EvidenceCard 互证流程。

## 新增脚本

` scripts/collect_product_market_sources.py `

输入：手工来源采集 JSON。

输出：

```json
{
  "route": "product_outbound_market_analysis_source_collection",
  "execution_level": "manual_source_collection_records_only",
  "not_evidence": true,
  "does_not_search_web": true,
  "does_not_open_sources": true,
  "does_not_create_evidence_cards": true,
  "does_not_create_matrix_rows": true,
  "sources": [],
  "observations": [],
  "collection_manifest": {}
}
```

## 本轮边界

- 不自动搜索。
- 不自动打开、抓取、渲染或下载来源。
- 不创建 EvidenceCard。
- 不创建 MatrixRow。
- 不输出税率、认证、物流时效、趋势、价格或市场进入判断。
- 只接受安全公开 `http(s)` URL。
- 拒绝本地路径、`file://`、localhost/private IP、带 `token` / `api_key` / `signature` 等敏感参数的 URL。
- `opened=false`、`not_accessed`、`login_wall`、`forbidden` 等未打开/受限状态不能带事实 `raw_excerpt`。
- `Source / Observation` 仍只是后续 EvidenceCard 的输入，不是事实卡。

## 新增 eval

新增：

- `evals/cases/product_market_source_collection_cases.json`
- `evals/run_product_market_source_collection_evals.py`

新增 pass fixtures：

- `source_collection_official_product_page_input.json`：官方产品页，用户声明已打开并提供可见摘录。
- `source_collection_pdf_url_shell_input.json`：公开 PDF URL shell，未下载/未打开，只记录 document 来源入口。
- `source_collection_restricted_input.json`：来源安全但登录墙，记录受限状态，不带事实摘录。

新增 fail fixtures：

- `source_collection_fail_local_path_input.json`：本地路径和 `file://` 被阻断。
- `source_collection_fail_token_url_input.json`：URL token / fragment API key 被阻断。
- `source_collection_fail_unopened_with_excerpt_input.json`：未打开来源携带事实摘录被阻断。

## 与现有 ProductMarketAnalysisGraph 的关系

Source collection 输出可以并入现有 `ProductMarketAnalysisGraph.sources` / `observations`，但不会自动让任何矩阵行变成事实。

本轮 eval 对 pass collection 输出做了合并烟测：把输出并入 `market_pass_xingheng_minimum_boundary.json` 后，继续跑 `scripts/validate_product_market_analysis.py`，验证现有市场分析 validator 不会因为手工来源桥接而失控。

## 已验证

```bash
python3 -m py_compile \
  scripts/collect_product_market_sources.py \
  evals/run_product_market_source_collection_evals.py
```

通过。

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

结果：`670/670`.

## 边界结论

Slice K 补的是“用户给 URL 后如何记录来源”的最小桥，不是“自动研究器”。它使真实来源采集从 Query Plan / SearchLog 往 Source / Observation 走通一小步，但仍严格保留：未打开来源不成证据、Source / Observation 不等于最终事实、结论必须等 EvidenceCard 互证和矩阵复核。
