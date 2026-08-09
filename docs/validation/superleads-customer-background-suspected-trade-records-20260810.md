# Superleads 单客背调疑似进出口记录验证记录（2026-08-10）

## 范围

本次只增强 `customer_background_research`：从公开贸易数据聚合站的搜索摘要或可打开公开页抓取疑似记录字段，使用独立顶层 `suspected_trade_records` 承载，并在有记录时追加条件表。未修改批量客户开发、产品出海市场分析、正式交付状态、audit 分支或 `tmp/stage5_chillys/`。

## 实现要点

- 记录字段：方向、对方名称、日期、品名/HS、起运/目的地、主体匹配级别、聚合站来源、可见性、状态、不能推出什么、用户下一步。
- 搜索摘要仍不是 `Observation` / `Claim` / `ClaimEvidence`；详情受限只保留摘要可见字段并显示“详情受限”。
- 背景报告表名固定为 `疑似进出口记录（第三方聚合，待核实）`，最多六列；完整 URL 只出现在“信息从哪里来”。
- `subject_match_level != name_exact_address_match` 的行显示“疑似，主体待确认”；`not_searched` 与 `searched_not_found` 分别显示“本轮未检索”和“已检索未见”。
- 用户下一步固定为“请用你自己的海关数据渠道按上述字段核实”，不推荐任何数据服务商。

## Fixtures / Evals

- Pass：`evals/fixtures/pass_customer_background_suspected_trade_records.json`，含两条记录，覆盖地址不同和搜索摘要可见情形；条件表出现在 Markdown / CSV / XLSX。
- Fail：`evals/user_visible_outputs/fail_customer_background_suspected_trade_claim.md`，使用“该客户从中国采购”，复用 `user_visible_evidence_upgrade` 阻断。
- 接入现有 `customer_background_research_cases.json` 与 `superleads_user_visible_output_cases.json`，未新增 runner。

## 验证结果

```text
python3 evals/run_customer_background_research_evals.py --suite all  # 7/7
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 15/15
python3 evals/run_superleads_plugin_distribution_evals.py --suite all  # 6/6
python3 scripts/check_superleads_plugin_distribution.py --plugin-root /home/fleix/.codex/plugins/cache/fleix/superleads/0.1.6 --source-root /home/fleix/superleads --format json  # ok=true
```

完整回归和最终提交前的结果以本提交验证命令输出为准。
