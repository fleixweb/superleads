# Superleads 弱证据诊断复核记录（Slice AA）

日期：2026-07-28

## 1. 复核方式

本记录针对外部诊断中提出的问题做本地静态复核，不联网，不验证真实国家法规、关税或认证事实。

已查看：

- `scripts/export_superleads_markdown.py`
- `scripts/validate_superleads_user_visible_output.py`
- `scripts/route_superleads_intake.py`
- `scripts/validate_product_market_analysis.py`
- `evals/cases/superleads_route_cases.json`
- `evals/cases/superleads_user_visible_output_cases.json`
- `evals/cases/superleads_markdown_delivery_cases.json`
- `shared/references/route-map.md`
- `shared/references/status-labels.md`
- `meta/open-questions.md`

## 2. 复核结论

| 诊断点 | 结论 | 复核说明 |
|---|---|---|
| 缺少多来源互证一等对象 | 成立 | 现有实现以单来源、单 observation、单矩阵行为主；没有 `CorroborationRecord` |
| 状态词通胀 | 大体成立 | 内部状态较多，用户可见输出主要依赖少数中文状态；需后续压缩映射 |
| 没有时效降级 | 成立 | `meta/open-questions.md` 仍列“法规与关税记录的默认复核周期”为开放问题 |
| 认证权威来源门 substring | 成立 | `CERT_AUTHORITY_MARKERS` 仍包含 `official` / `regulation` 等普通词 |
| 必备短语写死 | 部分成立 | 用户可见合同和 Markdown delivery case 要求 `候选 HTSUS`、`海运拼箱`、`国际快递`；需后续参数化 |
| 导出器补样板段 | 成立 | `export_superleads_markdown.py` 会补 Google Trends / COO / 海运拼箱 / 国际快递 / 待补材料清单段落 |
| 无边界替换污染正文 | 成立 | `_safe_text` 对 `graph` / `eval` 做普通 `replace` |
| 用户可见黑名单否定句误报 | 成立 | validator 对价值判断和内部词做普通 `phrase in text` |
| 路由器客户词不足 | 成立 | 当前 `CUSTOMER_MARKERS` 缺经销商/批发商/零售商/代理商/连锁等真实外贸词 |
| 主 all 不含 market suite | 成立 | `evals/run_evals.py` 未调用 `run_product_market_analysis_evals.py`，market suite 独立运行 |

## 3. P0 修复范围

Code Slice AA 只修 P0：

1. Markdown 交付器替换加边界；
2. 用户可见 validator 增加否定语境和词边界；
3. 路由器补真实外贸词并降低 `市场/包装` substring 误伤；
4. 调整用户可见合同，先停止为固定运输方式注水；
5. 增加对应 eval case。

## 4. 暂不处理项

以下进入后续切片：

- 多来源互证数据结构；
- 时效降级；
- Authority registry；
- 状态词压缩；
- 单一客户背调工程资产；
- Bulk 内核复盘；
- 完整核查版/初筛名单枚举清理。

## 5. 验收命令规划

Code Slice AA 完成后至少运行：

```bash
python3 evals/run_superleads_user_visible_output_evals.py --suite all
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
python3 evals/run_product_market_analysis_evals.py --suite all
git diff --check
```

说明：`run_evals.py --suite all` 与 `run_product_market_analysis_evals.py --suite all` 仍是两个并列套件，不能把前者数字写成覆盖全部市场路线。
