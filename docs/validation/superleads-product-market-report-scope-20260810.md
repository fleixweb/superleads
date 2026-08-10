# 产品出海市场分析按请求范围输出

日期：2026-08-10

## 改动范围

- `scripts/export_product_market_workbook.py` 新增覆盖十二表的新旧模块兼容映射和三张固定表；同一选表逻辑用于 CSV 与 Markdown。
- `analysis_modules_requested` 缺失、空、未知、旧 `product_profile` 标记或超过单项范围时输出完整十二表；明确单项输出对应模块表和三张固定表。
- 单项 Markdown 在贸易前提前声明范围和未覆盖模块，未请求项既不渲染为表，也不写为“本轮未执行项”。
- `certification` 作为面向 Agent 的 scope key 映射回既有 `destination_compliance` / `origin_proof_requirement` 查询组；美国 Pack 与开放世界权威来源发现都会覆盖准入与 COO 路径。
- 单项的固定“信息来源与待确认事项”只保留可见模块、产品档案或贸易前提实际引用的来源、Gap 和 Conflict，避免泄漏未请求的税费或物流事项。
- 完整报告空表分别说明未执行、无可用公开来源、不适用、来源受限；既有认证/COO 双列、候选税号、Trends、物流证据边界未改。
- 既有用户可见校验会在检测到范围声明时改用单项报告必填项，复用原有检查函数和错误码，不再强制出现未覆盖模块的税费或运输文本。
- 新增 `market_pass_scope_certification.json`，复用既有 market/Markdown runner；现有未执行 fixture 继续覆盖 `not_executed` 行，空表默认覆盖“已采集但未找到可用公开来源”。
- Skill 与 intake 说明整体默认完整、明确单项映射、范围模板和旧查询组兼容；三个插件 manifest 从 `0.1.7` bump 到 `0.1.8`。
- 未新增 schema、validator 脚本、错误码或 eval runner，且未改批量客户开发、单客背调或 `tmp/stage5_chillys/`。

## 验收记录

结果：全部通过。

```text
python3 -m py_compile scripts/export_product_market_workbook.py scripts/export_superleads_markdown.py scripts/plan_product_market_sources.py scripts/validate_product_market_analysis.py scripts/validate_superleads_user_visible_output.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 75/75
python3 evals/run_product_market_source_plan_evals.py --suite all  # 12/12
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 15/15
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 9/9
python3 evals/run_evals.py --suite default  # 125/125
python3 evals/run_evals.py --suite all  # passed
python3 evals/run_evals.py --suite deep  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json --format json  # passed, cache=0.1.8
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market  # passed
python3 evals/run_superleads_plugin_distribution_evals.py --suite all  # 6/6
python3 scripts/check_superleads_plugin_distribution.py --plugin-root /home/fleix/.codex/plugins/cache/fleix/superleads/0.1.8 --source-root /home/fleix/superleads --format json  # passed
git diff --check  # passed
```

## 当前状态

`codex plugin add superleads@fleix --json` 已重新安装本地 marketplace 的
`0.1.8` 快照到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.8`。
缓存与源树的 13 个 Skill、37 个相对引用和 manifest hook 目标均通过分发检查。
