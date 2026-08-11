# Superleads 常用命令

这份文档给开发者和本地 Agent 对接用。普通用户可以直接要求 Agent “用表格 / Markdown 给我看报告”，不一定需要自己敲命令。

## 三条路线的 Markdown 交付

| 场景 | 命令 | 适合什么输出 |
|---|---|---|
| 自动识别路线并导出 Markdown | `python3 scripts/export_superleads_markdown.py input.json --route auto --output report.md --format json` | 不确定是批量开发、单客背调还是产品市场分析时使用 |
| 批量客户开发 Markdown | `python3 scripts/export_superleads_markdown.py graph.json --route bulk_customer_development --output bulk-report.md --format json` | 候选客户池、公开业务信号、联系入口、待确认事项 |
| 单一客户背调 Markdown | `python3 scripts/export_superleads_markdown.py graph.json --route customer_background_research --output background-report.md --format json` | 表格化客户背调报告，适合 Codex / ChatGPT app 直接阅读 |
| 产品出海市场分析 Markdown | `python3 scripts/export_superleads_markdown.py market-graph.json --route product_outbound_market_analysis --output market-report.md --format json` | 产品市场与准入矩阵、COO、税费、物流、未执行项、待补材料 |
| 直接把 Markdown 打到终端 | `python3 scripts/export_superleads_markdown.py input.json --route auto --format markdown` | 临时预览，不写文件 |

说明：统一 Markdown 交付器只渲染已经审核过的工作簿 / 矩阵投影。它不搜索、不新增事实、不判断客户会不会买、不判断产品值不值得进入某市场、不推荐报价，也不把候选税号写成最终税率。

## 先检查正式研究能力

三条正式路线（批量客户开发、单一客户背调、产品出海市场分析）都需要本轮环境同时具备 `search.web` 和至少一种来源打开能力：`source.open`、`browser.render` 或 `document.extract`。

```bash
python3 scripts/preflight_capabilities.py --require-formal-research --format json
```

该命令返回非零时，不交付客户池、背调报告、市场报告或“仅计划”替代品；请切换到带 Web Search 和来源打开能力的 Agent/环境。只有对用户已提供文件或文本做的 `资料初审` 可以继续，且不得称为公开来源研究或正式报告。

## CSV / XLSX 表格交付

| 场景 | 命令 | 说明 |
|---|---|---|
| 批量客户开发候选池 CSV | `python3 scripts/export_workbook.py graph.json --output-dir out --mode initial --format csv` | 输出发现候选池、联系方式、来源、待核查项等 |
| 标准开发名单 CSV | `python3 scripts/export_workbook.py graph.json --output-dir out --mode standard --format csv` | 只用于已通过正式检查的标准开发名单 |
| 单一客户背调 CSV | `python3 scripts/export_workbook.py graph.json --output-dir out --mode background --format csv` | 输出客户背调六张表，不进入正式客户名单 audit 链路 |
| 自动选择 XLSX / CSV | `python3 scripts/export_workbook.py graph.json report.xlsx --mode initial --format auto` | 环境支持 XLSX 时写 Excel，否则按脚本能力回退 |
| 产品出海市场分析 CSV + Markdown | `python3 scripts/export_product_market_workbook.py market-graph.json --output-dir out --format csv --markdown market-report.md --manifest manifest.json` | 输出产品市场分析 12 张 CSV、可选 Markdown 和 manifest |

## 产品出海市场分析内部来源计划与手工来源链路

下列命令用于已通过能力门禁后的内部执行、回归或已有来源整理；`source_plan_only` 不是用户交付物。

| 场景 | 命令 | 边界 |
|---|---|---|
| 生成 Source Pack 查询计划 | `python3 scripts/plan_product_market_sources.py --input brief.json --format json` | 只生成去哪里找的计划，不搜索、不产生事实 |
| 校验 Source Pack registry | `python3 scripts/plan_product_market_sources.py --check-registry --format json` | 检查来源入口目录结构 |
| 输出采集壳 | `python3 scripts/plan_product_market_sources.py --input brief.json --emit-collection-run-shell --format json` | 生成后续 SearchLog / Source / Observation 空壳，不打开来源 |
| 手工 URL / 已知来源采集 | `python3 scripts/collect_product_market_sources.py --input source-input.json --format json > collection.json` | 只记录用户明确给定的公开 URL / 来源状态，不自动搜索 |
| 合并 collection 到图谱 | `python3 scripts/merge_product_market_collection.py --graph market-graph.json --collection collection.json --output merged.json --format json` | 只合并来源记录，不自动生成结论 |
| 编译已打开来源的紧凑证据笔记 | `python3 scripts/compile_product_market_evidence.py --graph source-observations.json --notes compact-evidence-notes.json --output compiled-market-graph.json --format json` | 只把已打开 Observation 的逐字摘录、条件、Authority 人工断言和行模板编译为既有对象；不搜索、不打开、不识别官方来源、不升级状态 |
| 一条命令跑手工 collection + merge + 可选导出 | `python3 scripts/run_product_market_collection_pipeline.py --graph market-graph.json --collection-input source-input.json --output merged.json --export-dir out --markdown market-report.md --format json` | 串联已有安全步骤，不抓取网页、不提取 PDF、不创建新事实 |

## 验证与回归

| 场景 | 命令 |
|---|---|
| 编译关键脚本 | `python3 -m py_compile scripts/export_superleads_markdown.py evals/run_superleads_markdown_delivery_evals.py evals/run_evals.py` |
| 产品市场证据编译器回归 | `python3 -m unittest tests/test_product_market_evidence_compiler.py -v` |
| 三路线入口路由 eval | `python3 evals/run_superleads_route_evals.py --suite all` |
| 三路线 Markdown 交付器 + claimed path UAT 回归 | `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` |
| 正式 Skill 调用 Markdown 冒烟检查 | `python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json` |
| 真实业务 UAT claimed path 固定验收 | `python3 scripts/check_superleads_formal_markdown_delivery.py --claimed-graph graph.json --claimed-markdown report.md --claimed-route auto --format json` |
| 用户可见输出静态 eval | `python3 evals/run_superleads_user_visible_output_evals.py --suite all` |
| 产品出海市场分析 eval | `python3 evals/run_product_market_analysis_evals.py --suite all` |
| Source Plan eval | `python3 evals/run_product_market_source_plan_evals.py --suite all` |
| Source Collection eval | `python3 evals/run_product_market_source_collection_evals.py --suite all` |
| Collection Merge eval | `python3 evals/run_product_market_collection_merge_evals.py --suite all` |
| Collection Pipeline eval | `python3 evals/run_product_market_collection_pipeline_evals.py --suite all` |
| 主 default 套件 | `python3 evals/run_evals.py --suite default` |
| 主 deep 套件 | `python3 evals/run_evals.py --suite deep` |
| 主 all 套件 | `python3 evals/run_evals.py --suite all` |
| Markdown / 文档空白检查 | `git diff --check` |

## 构建运行时插件包

开发仓库的 `tmp/`、`evals/` 和验证文档不属于已安装插件。构建工件后，再让本地
marketplace 指向 `dist/superleads/`；不要移动或删除源码 `tmp/stage5_chillys/`。

```bash
python3 scripts/build_superleads_plugin_package.py --format json
python3 scripts/check_superleads_plugin_distribution.py --plugin-root dist/superleads --source-root . --runtime-package --format json
ln -sfnT "$PWD/dist/superleads" "$HOME/plugins/superleads"
codex plugin add superleads@fleix
python3 scripts/check_superleads_plugin_distribution.py --plugin-root "$HOME/.codex/plugins/cache/fleix/superleads/0.1.12" --source-root . --runtime-package --format json
```

运行时工件包含 `.codex-plugin`、Claude manifest、`hooks`、`skills`、`scripts`、
`shared` 和 `spec`。它不应包含 `tmp/`、`evals/`、`tests/`、`docs/` 或 Git 元数据。软链接
命令只适用于 marketplace source 为 `$HOME/plugins/superleads` 的 Linux/macOS 本机布局；其它
本地路径改为对应 source。缓存版本号应替换为本次 manifest 的版本。

真实业务 UAT 中，claimed path 复核是固定验收步骤：最终声明的 Markdown 路径必须与同一个 graph 重新运行 `export_superleads_markdown.py` 得到的内容逐字一致；否则即使 exporter 曾返回 `ok=true`，该轮 UAT 也不通过。`run_superleads_markdown_delivery_evals.py` 已包含正向通过和后处理 mismatch 失败两条回归。

紧凑证据笔记可从 `shared/references/product-market-evidence-notes.example.json` 起步。示例中的 `observation_id`、逐字摘录、来源事实、适用条件和边界必须替换为本轮实际已打开来源；不能原样复用示例文字或把搜索摘要填入该文件。重复矩阵行可先写进 `matrix_row_templates`，再由 `target_row_ids` 引用；一个事实需要落到多张表时可引用多个模板或使用 `rows`。`authority_notes` 只能写人工确认过的可见身份/适用范围事实，必须带逐字摘录；默认是 `candidate_needs_check`，不能根据 URL、域名或机构名称自动写成官方或已核实。

## 常见口径

- Markdown：适合在 Codex / ChatGPT app 中直接读报告。
- CSV / XLSX：适合交给销售、运营或同事做筛选、复核和归档。
- 产品出海市场分析：只给客观市场与准入参考，不生成客户名单。
- Google Trends：只能表示相对搜索兴趣，不等于销量、GMV、进口量或采购需求。
- 平台 / 零售价格：只能作为公开线上价格参考，不等于外贸成交价、批发价或推荐报价。
- COO / 原产地证明：先看目标国法规是否要求，再单独看用户材料是否已准备；不能用“用户没给证书”反推“不需要证书”。
- 认证 / 测试 / 注册 / 标签：先查目标市场可能要求什么，再看用户有没有对应证书或报告；不能用“用户没给证书”反推“不需要认证”，也不能用“用户有证书”直接写“目标国认可 / 产品已合规”。
