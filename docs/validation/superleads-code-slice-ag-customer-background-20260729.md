# Code Slice AG：单一客户背调工程资产补齐验证记录

日期：2026-07-29

## 本轮目标

补齐单一客户背调路线的工程资产，让它和批量客户开发、产品出海市场分析一样有独立入口、规格文档、fixtures 和 eval。重点不是扩功能，而是防止边界污染：

- 不生成批量客户名单；
- 不把背调对象写成推荐客户；
- 不写采购概率、采购意愿、推荐报价；
- 不把 Founder / Owner / 董事升级成采购负责人；
- 不让搜索摘要解析主体；
- 不让 `Assessment` / `ScopeDecision` / `ReviewAttestation` / `DeliveryManifest` 污染客户背调报告。

## 改动范围

| 类型 | 文件 | 说明 |
|---|---|---|
| Skill 入口 | `skills/researching-customer-background/agents/openai.yaml` | 补 Codex / ChatGPT 可见入口 |
| 规格文档 | `spec/35-superleads-customer-background-code-slice-ag.md` | 冻结单客背调产品边界、输出合同和禁止项 |
| Validator | `scripts/validate_research_graph.py` | `customer_background_research` 阻断 Assessment、ScopeDecision、ReviewAttestation、DeliveryManifest；搜索摘要不能解析主体 |
| 导出 | `scripts/background_report.py` | 空表不再输出整行 `未提供`，改为人话缺口说明 |
| 用户可见检查 | `scripts/validate_superleads_user_visible_output.py` | 增加采购负责人 / 采购意愿升级短语阻断 |
| Evals | `evals/run_customer_background_research_evals.py` | 新增单客背调专属 eval runner |
| Cases | `evals/cases/customer_background_research_cases.json` | 6 条 pass/fail 背调用例 |
| Fixtures | `evals/fixtures/pass_customer_background_unresolved_minimal.json` 等 | 覆盖 unresolved、无关候选不外泄、搜索摘要解析主体、Assessment/Manifest 污染 |
| 用户可见样本 | `evals/user_visible_outputs/fail_customer_background_positive_procurement_person.md` | 阻断 `Founder 就是采购负责人` / `已确认有采购需求` |
| 主 eval | `evals/run_evals.py` | 将单客背调专属 suite 纳入静态总回归 |

## 新增关键用例

| 用例 | 期望 | 保护点 |
|---|---|---|
| `pass_customer_background_chillys_markdown.json` | pass | 已解析主体可生成背调报告 |
| `pass_customer_background_unresolved_minimal.json` | pass | 未解析主体仍能导出缺口表格，不强行造 Entity |
| `pass_customer_background_ignores_unrelated_candidates.json` | pass | 图谱中残留批量候选不会泄漏到单客背调报告 |
| `fail_customer_background_search_result_resolution.json` | fail | 搜索摘要不能作为主体解析依据 |
| `fail_customer_background_assessment_not_allowed.json` | fail | 单客背调不能生成 Assessment / 推荐跟进 |
| `fail_customer_background_manifest_not_allowed.json` | fail | 单客背调不能生成 DeliveryManifest |
| `fail_customer_background_positive_procurement_person.md` | fail | 用户可见文本不得升级采购负责人或采购需求 |

## 已验证

```bash
python3 -m py_compile scripts/background_report.py scripts/export_superleads_markdown.py scripts/validate_research_graph.py scripts/validate_superleads_user_visible_output.py evals/run_customer_background_research_evals.py evals/run_evals.py
python3 evals/run_customer_background_research_evals.py --suite all  # 6/6
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 10/10
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 115/115
python3 evals/run_evals.py --suite all  # 707/707
python3 evals/run_evals.py --suite deep  # 667/667
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed
```

## 验收结论

Code Slice AG 已完成。单一客户背调现在具备：

1. 独立 Skill 入口；
2. 独立规格文档；
3. 专属 runner / cases / fixtures；
4. 用户可见采购负责人与采购意愿升级阻断；
5. 轻验证报告与正式名单链路隔离；
6. unresolved 情况下的人话表格展示。
