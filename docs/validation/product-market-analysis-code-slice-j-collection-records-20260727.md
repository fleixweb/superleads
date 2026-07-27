# 产品出海市场分析 Code Slice J：Query Plan 到 SearchLog / Source / Observation 最小执行记录

日期：2026-07-27

## 目标

把 Code Slice I 的 `Query Plan` 往真实采集链路下游衔接一层，但仍保持“不联网、不打开来源、不自动生成事实”的边界：

```text
Source Pack / Query Plan
  -> SearchLog：记录查什么、用什么 query、候选来源是什么
  -> Source：记录已打开或待打开的来源入口
  -> Observation：只允许来自已打开来源的观察摘录
  -> EvidenceCard：后续互证后才能形成事实卡
```

## 本轮实现

### Schema

更新 `shared/schemas/product-market-analysis.schema.json`：

- 新增可选 `search_logs` 数组。
- 新增 `MarketSearchLogRecord`：
  - `source_plan_route = product_outbound_market_analysis_source_plan`
  - `capability = search.web`
  - `result_use = source_candidate_only`
  - `must_open_source = true`
  - `reject_if_only_snippet = true`
  - `not_evidence = true`
  - `allowed_output = search_log_or_source_locator_only`
- `SourceRef` 可带 `search_log_id` / `query_plan_id`，但只能作为候选交接引用，不能支撑事实。

### Planner

更新 `scripts/plan_product_market_sources.py`：

- 新增 `--emit-collection-run-shell`。
- 输出 `collection_run_shell`：
  - `execution_level = collection_record_shell_only`
  - `does_not_search_web = true`
  - `does_not_open_sources = true`
  - `not_evidence = true`
  - `search_logs/sources/observations` 均为空。
  - 每个 pending step 明确 `search_log_allowed_output = search_log_or_source_locator_only` 与 `observation_allowed_only_after_open_source = true`。

### Validator

更新 `scripts/validate_product_market_analysis.py`：

新增边界检查：

- SearchLog 必须绑定当前 Run / Brief / Brief version。
- SearchLog 必须保留 source-plan 边界。
- SearchLog 查询词和 result locator 不能含本地路径、file URI、token/API key 等敏感信息。
- 搜索结果不能写成 `Source.medium = search_result`。
- `Observation.capability = search.web` 被阻断；搜索输出只能进 SearchLog。
- `SearchLog.opened_source_id` 必须能追到已打开 Source Observation。
- `not_accessed` / restricted observation 不能带事实摘录。
- factual EvidenceCard 必须引用已打开来源 Observation；`derived_calculation` 例外，但仍应追到派生来源卡。
- Query Plan / SearchLog 不能直接升级为 factual EvidenceCard。

新增错误码覆盖：

- `market_query_plan_or_searchlog_promoted`
- `market_evidence_without_open_observation`
- `market_search_result_as_source`
- `market_search_result_as_observation`
- `market_source_without_open_observation`
- `market_restricted_source_has_observation_excerpt`

### Fixtures / evals

新增 pass fixtures：

- `market_pass_searchlog_to_opened_observation_minimal.json`
- `market_pass_source_restricted_searchlog_no_observation.json`

新增 fail fixtures：

- `market_fail_searchlog_promoted_to_verified.json`
- `market_fail_search_result_as_source_observation.json`
- `market_fail_unopened_source_supports_evidence.json`
- `market_fail_query_plan_direct_evidence.json`

更新：

- `market_pass_search_summary_candidate_only.json`：从旧的 search-result Source / search.web Observation 改为正式 SearchLog 候选记录。
- `evals/cases/product_market_analysis_cases.json`：market case 从 36 增加到 42。
- `evals/run_product_market_source_plan_evals.py`：校验 collection-run shell。
- `evals/cases/product_market_source_plan_cases.json`：Xing Heng source-plan case 覆盖 shell 输出。

## 已验证

```bash
python3 -m py_compile \
  scripts/plan_product_market_sources.py \
  scripts/validate_product_market_analysis.py \
  evals/run_product_market_source_plan_evals.py \
  evals/run_product_market_analysis_evals.py
```

通过。

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

Slice J 只是建立采集审计轨道：SearchLog 记录“怎么找”，Source 记录“来源入口”，Observation 记录“打开后看到什么”。本轮不联网、不真实打开来源、不产生新的产品事实、税率、认证、物流、趋势、价格或市场判断。
