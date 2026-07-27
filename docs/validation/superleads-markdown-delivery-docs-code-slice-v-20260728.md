# Code Slice V：README / Skill 使用说明 / 常用命令示例验证记录

日期：2026-07-28

## 本次范围

本 Slice 只更新文档与 Skill 使用说明，不改执行逻辑、不新增事实采集能力、不改 schema / validator / exporter 行为。

## 已更新

| 文件 | 变化 |
|---|---|
| `README.md` / `README.zh-CN.md` | 首页改为三条路线说明：批量客户开发、单一客户背调、产品出海市场分析；补充三类首轮提问样例和 Markdown 导出入口 |
| `README.en.md` | 同步英文三路线、首轮请求样例和导出口径 |
| `docs/superleads-common-commands.md` | 新增常用命令：Markdown 交付、CSV/XLSX 导出、产品市场来源计划/collection 链路、eval 回归 |
| `skills/exporting-lead-workbooks/SKILL.md` | 补充统一 Markdown 交付器、三条显式 route、CSV/XLSX 保留命令 |
| `skills/using-superleads/SKILL.md` | 补充对话 / Codex / ChatGPT app 里看 Markdown 报告的路线与三路线不串线要求 |
| `skills/analyzing-product-outbound-market/SKILL.md` | 补充产品出海市场分析 Markdown 与 CSV 导出口径，强调不生成客户名单、不做市场进入判断 |
| `skills/researching-customer-background/SKILL.md` | 补充单客背调 Markdown 交付器命令，保留 background CSV/XLSX 命令 |
| `shared/references/route-map.md` / `shared/references/output-schema.md` | 补充统一 Markdown 交付层定位和导出边界 |

## 用户可见口径

| 关注点 | 本次冻结写法 |
|---|---|
| 三条路线 | 批量客户开发 / 单一客户背调 / 产品出海市场分析并列，不互相替代 |
| Markdown | 适合 Codex / ChatGPT app 直接阅读；写出前执行用户可见输出合同检查 |
| CSV / XLSX | 适合销售团队复核、筛选、归档和交接 |
| 产品出海市场分析 | 客观展示趋势、价格参考、准入、COO、税费、物流和外部因素，不生成客户名单 |
| 禁止价值判断 | 不写采购概率、必买客户、是否值得进入、推荐报价、最终税率或最终合规裁定 |
| COO / 原产地证明 | 先按目标国家/地区要求判断是否需要，再单独展示用户材料状态 |

## 验证

| 命令 | 结果 |
|---|---|
| `python3 -m py_compile scripts/export_superleads_markdown.py evals/run_superleads_markdown_delivery_evals.py evals/run_evals.py` | 通过 |
| `python3 evals/run_superleads_markdown_delivery_evals.py --suite all` | `4/4` 通过 |
| `python3 evals/run_superleads_user_visible_output_evals.py --suite all` | `6/6` 通过 |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `42/42` 通过 |
| `python3 evals/run_evals.py --suite default` | `91/91` 通过 |
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market` | 通过 |
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks` | 通过 |
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads` | 通过 |
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/researching-customer-background` | 通过 |
| `git diff --check` | 通过 |

## 结论

Code Slice V 已把三路线 Markdown 交付器接到 README、Skill 使用说明和常用命令文档。用户入口现在能用更自然的业务语言理解三条路线，开发者也能看到最小可执行命令。执行逻辑保持 Code Slice U 状态，未新增联网搜索、自动抓取、自动事实生成或价值判断。
