# Code Slice U：三路线用户可见 Markdown 交付器

日期：2026-07-28

## 1. 本 Slice 解决什么

Slice T 已经把三条路线的用户可见输出合同固化为静态 Markdown 样本，但真实运行时仍需要一个稳定入口，把已有 graph / workbook / 产品矩阵变成用户在 Codex、ChatGPT app 里能直接看的 Markdown 表格。

Code Slice U 的目标：新增一个统一 Markdown 交付器，让三条路线都能走同一个命令输出用户可见 Markdown，并在写出前自动执行 Slice T 用户可见校验。

## 2. 三条路线

| 路线 | 输入 | 复用链路 | Markdown 重点 |
|---|---|---|---|
| 批量客户开发 | Superleads ResearchGraph | `audit_delivery` + `export_workbook.build_sheets(..., initial)` | 开发方向四行、候选客户池、待确认事项、来源状态 |
| 单一客户背调 | Superleads ResearchGraph，`task_mode=customer_background_research` | `background_report.validate_background_report` + `build_background_report_sheets` | 一句话先说清、客户一眼看懂、主体关系、联系入口、风险和来源 |
| 产品出海市场分析 | `ProductMarketAnalysisGraph` | `audit_product_market_analysis` + `export_product_market_workbook` | 贸易前提、COO、未执行模块、运输方式、待补材料清单、市场矩阵 |

## 3. 新增命令

```bash
python3 scripts/export_superleads_markdown.py <graph.json> --route auto --output report.md --format json
```

也可显式指定路线：

```bash
--route bulk_customer_development
--route customer_background_research
--route product_outbound_market_analysis
```

## 4. 交付边界

| 边界 | 规则 |
|---|---|
| 不新增事实 | Markdown 只渲染已审核 sheets / matrix，不联网、不搜索、不打开来源 |
| 不做价值主张 | 不输出推荐客户、采购概率、值得进入、推荐报价、最佳路线、承诺交期 |
| 不暴露内部对象 | 不暴露 EvidenceCard、SearchLog、Claim、MatrixRow、graph、eval、本地路径等 |
| 弱证据保留 | 待确认、未执行、来源受限、候选、不能推出什么继续显示 |
| 失败先阻断 | 底层 audit / background validation / product market audit 不通过时，不写 Markdown |

## 5. 产品市场分析的额外兜底

`export_product_market_workbook.py` 已有 Markdown 能力，但早期最小 fixture 不一定包含完整市场模块。因此统一交付器会在人话层补充这些“未执行 / 待确认”的展示区：

| 补充区 | 目的 |
|---|---|
| Google Trends / 长期搜索趋势 | 明确未执行时不编造成销量或需求 |
| COO / 原产地证明 | 明确目标国要求与用户材料状态要分开 |
| 运输方式补充：海运拼箱 / 国际快递 | 明确这些只是待确认运输方式，不是固定路线或时效 |
| 待补材料清单 | 把 graph gaps 变成业务人员能看懂的补料项 |

## 6. 验收

新增生成型 eval：

```bash
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
```

并接入主套件：

```bash
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

最小验收样本：

| 样本 | 路线 | 期望 |
|---|---|---|
| `pass_default_discovery_candidate_pool.json` | 批量客户开发 | 生成 Markdown 并通过 Slice T validator |
| `pass_customer_background_chillys_markdown.json` | 单一客户背调 | 生成 Markdown 并通过 Slice T validator |
| `market_pass_xingheng_minimum_boundary.json` | 产品出海市场分析 | 生成 Markdown 并通过 Slice T validator |
| `market_fail_candidate_htsus_as_final_rate.json` | 产品出海市场分析 | 因候选税号升级最终结论被阻断，不写 Markdown |
