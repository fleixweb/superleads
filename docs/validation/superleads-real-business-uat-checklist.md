# Superleads 真实业务 UAT 固定验收清单

日期：2026-07-31

## 定义

UAT = User Acceptance Testing，即用户验收测试。这里特指：用真实业务输入在新窗口 / 黑盒调用 Superleads 后，验收最终交付物是否真的来自统一导出链路，而不是 Agent 手写或后处理出来的“看起来像正式报告”的 Markdown。

## 固定门禁

凡是真实业务 UAT 声称完成正式 Markdown 交付，都必须把 claimed path 复核作为固定验收步骤。只看到 exporter `ok=true` 不够；还必须证明最终报给用户的 Markdown 路径，和同一个 graph 重新导出的 canonical Markdown 逐字一致。

## 固定测量账本

每轮真实 UAT 在研究开始前必须初始化独立运行目录。测量器只记录过程和
原始 gate 结果，不替代 `preflight_capabilities.py`、路线 validator、audit 或 exporter。
它解决的是“最终修正后通过”被误说成“首遍通过”、Git 空输出换行误判、以及
墙钟耗时混入等待时间的问题。

三条路线需要比较耗时时，必须严格顺序执行：一条路线完成
`init -> active-start -> 全部 gate -> active-stop -> finalize` 后，才能开始下一条。
不得一次初始化多个 RUN_DIR，也不得让多个 active interval 覆盖同一段工作时间；
否则各路线的 `active_elapsed_seconds` 和 `wall_elapsed_seconds` 只能标为
“并行运行，不可横向比较”。RUN_DIR 名称也必须使用实际 UTC 时间，不能写固定的
`T000000Z` 占位值。

```bash
python3 scripts/measure_superleads_uat.py init \
  --run-dir "$RUN_DIR" \
  --route product_outbound_market_analysis \
  --token-usage-availability unavailable \
  --format json
```

只有宿主实际提供 input/output/total token usage 或其可读取日志时，才可把
`--token-usage-availability` 写为 `available` 并记录证据路径；不得用静态 token
估算、文件行数或墙钟耗时替代真实 token。

在实际做研究、录入或修复时开始/结束活动区间；等待页面、等待用户或会话中断不计入
`active_elapsed_seconds`，但仍会留在 `wall_elapsed_seconds` 中。

```bash
python3 scripts/measure_superleads_uat.py active-start --run-dir "$RUN_DIR" --note "公开来源采集" --format json
python3 scripts/measure_superleads_uat.py active-stop --run-dir "$RUN_DIR" --note "采集完成" --format json
```

每个真实 gate 完成后记录其原始 JSON 或日志路径。失败必须按实际原因分类：
`capability_adapter`、`command_invocation`、`graph_contract`、`evidence_contract`、
`exporter_completeness`、`measurement_protocol` 或 `other`。不能把业务资料缺口、
来源受限或未执行模块伪装成工具失败。

在正式 validator 前必须先运行输入预检。它不是 validator 的替代品：只提前定位
来源原文锚定、联系人关联、枚举和产品属性可见投影错误。产品市场使用紧凑 notes 时，
先对 `graph + notes` 预检，再编译，并对编译图谱再预检一次。

```bash
python3 scripts/precheck_superleads_uat_input.py \
  --route "$ROUTE" --graph "$GRAPH" --format json

python3 scripts/measure_superleads_uat.py record-gate \
  --run-dir "$RUN_DIR" --gate input_precheck --result passed \
  --artifact "$RUN_DIR/input_precheck.json" --format json
```

```bash
python3 scripts/measure_superleads_uat.py record-gate \
  --run-dir "$RUN_DIR" --gate preflight --result passed \
  --artifact "$RUN_DIR/preflight_result.json" --format json

python3 scripts/measure_superleads_uat.py record-gate \
  --run-dir "$RUN_DIR" --gate validator --result failed \
  --failure-class graph_contract --artifact "$RUN_DIR/validator-attempt-1.json" \
  --format json
```

最后由测量器原样执行 `git status --porcelain=v1` 并以字节比较 `git-before.txt` /
`git-after.txt`。不能再用 `echo`、手工换行或摘要文本比较 Git 状态。

```bash
python3 scripts/measure_superleads_uat.py finalize \
  --run-dir "$RUN_DIR" \
  --required-gate preflight \
  --required-gate input_precheck \
  --required-gate validator \
  --required-gate audit \
  --required-gate markdown_export \
  --required-gate workbook_export \
  --required-gate user_visible \
  --required-gate claimed_path \
  --format json
```

单客背调没有 audit gate 时不传 `--required-gate audit`。`finalize` 在任何必需 gate
最终未通过、活动区间未关闭或 Git 快照不一致时返回非零，但仍会写
`$RUN_DIR/uat_metrics.json`。该文件中的 `first_pass_success`、
`repair_cycle_count`、`active_elapsed_seconds`、`wall_elapsed_seconds` 与
`first_pass_failure_classes` 是跨路线比较的唯一测量口径。

产品出海市场分析若使用 `compile_product_market_evidence.py`，必须将 `compiler`
作为已记录且必需的 gate，位于编译前紧凑 notes 预检和编译后 graph 预检之间：

```text
preflight -> input_precheck_notes -> compiler -> input_precheck_graph ->
validator -> audit -> markdown_export -> workbook_export -> user_visible -> claimed_path
```

即使调用方误漏了 `compiler` 的 `--required-gate`，只要 ledger 已记录其首遍失败，
测量器也会将 `first_pass_success` 设为 `false`。这不会改变 required gate 的最终
通过判定，但会阻止“最终修复后通过”被写成端到端首遍通过。

## UAT 必交字段

真实业务 UAT 交付记录至少包含：

| 字段 | 要求 |
|---|---|
| route | `auto`、`bulk_customer_development`、`customer_background_research` 或 `product_outbound_market_analysis` |
| graph JSON path | 已保存、可读取的 graph JSON 文件路径 |
| Markdown path | 最终声明给用户的 Markdown 报告路径 |
| exporter result | `export_superleads_markdown.py` 的 JSON 结果，必须 `ok=true` / `issue_count=0` |
| claimed path check result | `check_superleads_formal_markdown_delivery.py --claimed-graph ... --claimed-markdown ...` 的 JSON 结果，必须 `ok=true` / `issue_count=0` |
| input precheck result | `precheck_superleads_uat_input.py` 的 JSON 结果，必须 `ok=true` / `issue_count=0`；产品市场若使用 compact notes，保存编译前与编译后两份结果 |
| UAT metrics JSON | `measure_superleads_uat.py finalize` 写出的 `$RUN_DIR/uat_metrics.json`；必须说明首遍状态、修复轮数、活动/墙钟耗时、Git 一致性与 token 可观测性 |

没有 graph JSON 的搜索笔记、截图整理、手写表格或临时 Markdown，只能算 research draft / source-collection note，不能算正式 UAT 通过。

## 固定命令

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py \
  --claimed-graph "$GRAPH" \
  --claimed-markdown "$MARKDOWN" \
  --claimed-route auto \
  --format json
```

如果路线已知，可以把 `auto` 换成：

- `bulk_customer_development`
- `customer_background_research`
- `product_outbound_market_analysis`

## 自动回归

claimed path 门禁已接入 Markdown delivery eval：

```bash
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
```

该 suite 除三路线 Markdown 生成外，还包含两条真实 UAT claimed path 回归：

| 回归项 | 期望 |
|---|---|
| exporter 原始输出作为 claimed Markdown | 通过，`ok=true` / `issue_count=0` |
| exporter 输出后追加手工内容再作为 claimed Markdown | 失败，错误码包含 `formal_markdown_claimed_output_mismatch` |

## 通过标准

必须同时满足：

1. `ok=true`
2. `issue_count=0`
3. 不出现 `formal_markdown_claimed_output_mismatch`
4. 不出现 `formal_markdown_claimed_graph_missing`
5. 不出现 `formal_markdown_claimed_markdown_missing`
6. 不出现 `formal_markdown_claimed_graph_export_failed`
7. 用户可见报告不泄漏内部依据状态，例如 `已观察`、`已观察；需确认`、`已观察；来源受限`

## 失败处理

| 失败类型 | 处理 |
|---|---|
| `formal_markdown_claimed_output_mismatch` | UAT 不通过；不要手工修改报告后继续声称通过。用同一个 graph 重新运行 `export_superleads_markdown.py --output "$MARKDOWN"` 覆盖报告，再复跑 claimed path check。 |
| claimed graph 缺失 | UAT 不通过；先补保存 graph JSON，不能用搜索笔记替代 graph。 |
| claimed Markdown 缺失 | UAT 不通过；先用统一 exporter 写出 Markdown。 |
| claimed graph export failed | UAT 不通过；先修 graph / route / 用户可见输出问题。 |
| Skill / 插件缓存不一致 | UAT 不通过；先同步 Skill / 插件缓存或明确使用仓库源文件复核。 |

## 最小 UAT 汇报模板

```text
1. exporter: ok=true, issue_count=0
2. claimed path check: ok=true, issue_count=0
3. route: auto
4. graph JSON: /path/to/graph.json
5. Markdown: /path/to/report.md
6. 抽样核对：第一张候选池/背调/市场矩阵表前 3 行已读取；不做推荐排序或采购概率判断。
```

## 本次真实 UAT 经验固化

- 英国保温杯客户池曾出现：graph 可正确导出，但 claimed Markdown 路径不是 exporter 原始输出，命中 `formal_markdown_claimed_output_mismatch`。这类情况必须算 UAT fail。
- 美国 generator parts 样本通过 claimed path check，可作为正向 UAT 样例。
- Chilly’s 单客背调已确认统一 Markdown exporter 支持 `customer_background_research`；不得再声称 Markdown exporter 只支持 bulk。

## 2026-08-01 单客背调 claimed path UAT

Chilly’s Bottles / Chilly’s 的 `customer_background_research` 真实 UAT 已独立复核通过：

| 项目 | 结果 |
|---|---|
| route | `customer_background_research` |
| graph JSON | `/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json` |
| Markdown | `/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md` |
| claimed path check | `ok=true` / `issue_count=0` |
| 用户可见校验 | `ok=true` / `issue_count=0` / `table_count=7` |

复核命令：

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py \
  --claimed-graph /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json \
  --claimed-markdown /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md \
  --claimed-route customer_background_research \
  --format json
```

该结果证明 claimed path 门禁不是 bulk-only。
