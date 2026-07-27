# 产品出海市场分析 Code Slice M：手工来源 collection 一键 pipeline

日期：2026-07-27

## 目标

把已经完成的 Slice K / Slice L 链路封装成一个更顺手的单命令入口：

```text
manual collection input
→ collect_product_market_sources
→ merge_product_market_collection
→ validate_product_market_analysis
→ audit_product_market_analysis
→ optional export_product_market_workbook
```

本轮只做“手工 URL / PDF URL shell / 已知来源状态”的管道封装，不做真实搜索、不打开网页、不下载 PDF、不抽取 PDF、不生成事实结论。

## 新增脚本

新增：`scripts/run_product_market_collection_pipeline.py`

示例：

```bash
python3 scripts/run_product_market_collection_pipeline.py \
  --graph evals/fixtures/market_pass_xingheng_minimum_boundary.json \
  --collection-input evals/fixtures/source_collection_official_product_page_input.json \
  --output /tmp/product_market_pipeline/merged.json \
  --collection-output /tmp/product_market_pipeline/collection.json \
  --export-dir /tmp/product_market_pipeline/export \
  --markdown /tmp/product_market_pipeline/report.md \
  --export-manifest /tmp/product_market_pipeline/export_manifest.json \
  --pipeline-manifest /tmp/product_market_pipeline/pipeline_manifest.json
```

输出固定声明：

```json
{
  "route": "product_outbound_market_analysis_collection_pipeline",
  "not_evidence": true,
  "does_not_search_web": true,
  "does_not_open_sources": true,
  "does_not_fetch_or_download_sources": true,
  "does_not_create_search_logs": true,
  "does_not_create_evidence_cards": true,
  "does_not_create_matrix_rows": true,
  "allowed_output": "collection_merge_validate_audit_optional_export_only"
}
```

## Pipeline 做什么

允许：

- 从手工 collection input 生成 Slice K collection output。
- 把 collection output 追加到正式 `ProductMarketAnalysisGraph.sources` / `observations`。
- 合并后执行 validate / audit。
- 可选生成 12 张 CSV、Markdown、export manifest。
- 可选生成 pipeline manifest，记录 collect / merge / export 是否执行。
- 输出 graph count delta，确认只增加 `sources` / `observations`。

禁止：

- 不搜索互联网。
- 不自动打开 URL。
- 不抓取、渲染、下载、解析 PDF。
- 不创建 `SearchLog`。
- 不创建 `EvidenceCard`。
- 不创建 `MatrixRow`。
- 不改写已有事实矩阵。
- 不生成认证、税率、物流、趋势、价格、市场进入判断。

## 新增 fixtures / eval

新增：

- `evals/fixtures/source_collection_fail_scope_mismatch_input.json`
- `evals/cases/product_market_collection_pipeline_cases.json`
- `evals/run_product_market_collection_pipeline_evals.py`

覆盖：

- pass：官方产品页输入，一键生成 collection output、merged graph、12 CSV、Markdown、manifest。
- pass：PDF URL shell 输入，只作为来源入口展示，不抽取 PDF，不升级事实。
- pass：登录墙 / 受限来源输入，只显示“来源受限”和“需打开或复核原始来源”。
- fail：token / API key URL 在 collect 阶段阻断。
- fail：本地路径 / `file://` 在 collect 阶段阻断。
- fail：未打开来源携带 `raw_excerpt` 在 collect 阶段阻断。
- fail：collection input 的 `brief_version_id` 与 graph 不一致时，collect 可通过但 merge 阶段阻断。

## 用户可见导出边界

pipeline 成功后，新增来源只能进入：

- `12-信息来源与待确认事项.csv`
- Markdown 报告的“信息来源与待确认事项”

不会自动出现在：

- 市场事实总览的新事实结论
- 产品准入 / 进口税费 / 物流 / 价格 / 趋势的事实升级
- `EvidenceCard` / `MatrixRow` / `SearchLog`

## 已验证

```bash
python3 -m py_compile \
  scripts/run_product_market_collection_pipeline.py \
  evals/run_product_market_collection_pipeline_evals.py
```

通过。

```bash
python3 evals/run_product_market_collection_pipeline_evals.py --suite all
```

结果：`7/7`。

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

Slice M 只是把现有安全步骤串成一个更方便的入口。它让“用户给 URL / PDF 后进入产品市场分析来源链路”更容易执行，但仍然只停留在来源记录和待确认事项层。后续要形成事实，仍必须进入 EvidenceCard 互证和 MatrixRow 复核流程。

## 下一步建议

Code Slice N 可选方向：

1. 做“EvidenceCard 草稿生成前的人工复核队列”，把已打开 Observation 转成待审核草稿，但默认不发布到矩阵。
2. 做“用户材料包导入清单”，支持把产品手册、证书、SDS、标签照片等归类到待复核队列。
3. 做“端到端示例命令文档”，让产品出海市场分析 Skill 能提示用户如何准备 URL/PDF/材料。
