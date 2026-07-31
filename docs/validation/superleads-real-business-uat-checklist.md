# Superleads 真实业务 UAT 固定验收清单

日期：2026-07-31

## 定义

UAT = User Acceptance Testing，即用户验收测试。这里特指：用真实业务输入在新窗口 / 黑盒调用 Superleads 后，验收最终交付物是否真的来自统一导出链路，而不是 Agent 手写或后处理出来的“看起来像正式报告”的 Markdown。

## 固定门禁

凡是真实业务 UAT 声称完成正式 Markdown 交付，都必须把 claimed path 复核作为固定验收步骤。只看到 exporter `ok=true` 不够；还必须证明最终报给用户的 Markdown 路径，和同一个 graph 重新导出的 canonical Markdown 逐字一致。

## UAT 必交字段

真实业务 UAT 交付记录至少包含：

| 字段 | 要求 |
|---|---|
| route | `auto`、`bulk_customer_development`、`customer_background_research` 或 `product_outbound_market_analysis` |
| graph JSON path | 已保存、可读取的 graph JSON 文件路径 |
| Markdown path | 最终声明给用户的 Markdown 报告路径 |
| exporter result | `export_superleads_markdown.py` 的 JSON 结果，必须 `ok=true` / `issue_count=0` |
| claimed path check result | `check_superleads_formal_markdown_delivery.py --claimed-graph ... --claimed-markdown ...` 的 JSON 结果，必须 `ok=true` / `issue_count=0` |

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
