# Code Slice AA：用户交付污染 bug + 路由器修复验证记录

日期：2026-07-28

## 1. 本轮目标

本轮在 Slice AA 文档校准后，先修 P0：直接污染用户交付或导致入口走错的问题。

## 2. 已修改内容

| 文件 | 变化 |
|---|---|
| `scripts/export_superleads_markdown.py` | 内部术语替换改为英文词边界匹配，避免 `The Telegraph`、`Photograph`、`paragraph`、`evaluation` 被改坏；新增 lead fixture `extends/patches` 最小解析；停止补 Google Trends / COO / 海运拼箱 / 国际快递 / 待补材料清单样板段 |
| `scripts/validate_superleads_user_visible_output.py` | 黑名单改为带英文词边界和否定语境豁免；`graph` / `eval` 不再命中普通英文单词；“不判断是否值得进入”“不做推荐客户排序，也不给采购概率”“Made in 等于 COO 是错误理解”可通过 |
| `scripts/route_superleads_intake.py` | 增加真实外贸客户词：经销商、批发商、零售商、代理商、连锁、维修商、distributor、wholesaler、retailer、dealer 等；SDS / UN38.3 / 认证 / 关税 / 物流要求优先进入产品出海市场分析；降低普通 `市场` / `包装` 子串误伤 |
| `evals/cases/superleads_route_cases.json` | 增加 5 个 Claude Code 复现路由样例 |
| `evals/cases/superleads_user_visible_output_cases.json` | 增加否定句/来源名通过样本与正向推荐失败样本 |
| `evals/cases/superleads_markdown_delivery_cases.json` | 增加 Markdown 生成替换边界样本；产品市场生成样本不再要求固定补 `海运拼箱/国际快递` 样板行 |
| `evals/user_visible_outputs/product_market_xingheng_lifepo4_us.md` | 补“信息来源与待确认事项”表以符合通用产品市场输出合同 |

## 3. 新增 fixtures

| fixture | 用途 |
|---|---|
| `evals/fixtures/pass_default_discovery_markdown_replacement_boundaries.json` | 验证 Markdown 生成时保留 `The Telegraph`、`Photograph`、`paragraph`、`evaluation`，同时替换独立内部词 `graph` / `eval` / `EvidenceCard` |
| `evals/user_visible_outputs/product_market_negated_guardrails_and_source_names.md` | 验证否定句和来源名不误报 |
| `evals/user_visible_outputs/fail_user_visible_positive_recommendation.md` | 验证“建议进入 / 推荐客户 / 采购概率 / 最终税率”仍会失败 |

## 4. 路由样例验收

| 输入 | 期望 | 结果 |
|---|---|---|
| 我要开发美国的柴油发电机配件经销商 | 批量客户开发 | 通过 |
| 我们工厂做汽车配件，想开发中东市场 | 批量客户开发 | 通过 |
| 帮我找美国做户外家具的零售连锁 | 批量客户开发 | 通过 |
| 客户问我要 SDS 和 UN38.3，美国那边到底要不要 | 产品出海市场分析 | 通过 |
| 中性包装柴油发电机后市场配件，美国，维修商/零件渠道/经销商 | 批量客户开发 | 通过 |

## 5. 已验证命令

```bash
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all    # 5/5
python3 evals/run_evals.py --suite default                             # 98/98
python3 evals/run_product_market_analysis_evals.py --suite all          # 50/50
python3 evals/run_evals.py --suite all                                  # 684/684
python3 evals/run_evals.py --suite deep                                 # 644/644
git diff --check                                                        # 通过
```

备注：首次并行跑 `deep` 时因和 `all` 同时执行超出 180s timeout；随后单独重跑 `deep`，结果为 `644/644`。

## 6. 边界

本轮不解决：

- 多来源互证对象；
- 时效降级；
- Authority registry；
- 状态词压缩；
- 单一客户背调工程资产补齐；
- 批量客户开发内核复盘；
- `run_evals.py --suite all` 与 market suite 合并。

这些进入后续 P1/P2。
