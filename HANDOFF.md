# Handoff

- 分支：`master`
- 最新提交：`b3145fc Calibrate weak-evidence delivery guardrails`
- 当前工作树：Code Slice AB 已完成并通过回归，待提交；保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已完成

- Slice AA / Code Slice AA 已提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 已完成：产品出海市场分析新增多来源互证 / `CorroborationRecord` 最小闭环。

## Code Slice AB 已完成内容

1. `shared/schemas/product-market-analysis.schema.json`
   - 增加可选 `corroboration_records`。
   - 新增 `CorroborationRecord` / `CorroborationStatus`。
   - `MatrixRowRecord` 可引用 `corroboration_record_ids`。
2. `scripts/validate_product_market_analysis.py`
   - 多来源一致必须来自已打开/已抽取来源。
   - 搜索摘要 / SearchLog / Source Pack / Query Plan 不能直接作为互证来源。
   - 独立来源数按 owner/domain 保守计算；同域名或同 owner 不算多个独立来源。
   - 存在同字段冲突时不能写成多来源一致。
   - 多个弱来源一致不能把用户矩阵行升级为 `verified` 或最终事实。
3. `scripts/export_product_market_workbook.py`
   - 用户可见导出增加人话字段：`多来源互证情况`、`互证边界`、`下一步核实`。
   - 不暴露内部对象名，不新增事实。
4. evals
   - market suite 从 `50` 条扩展到 `57` 条。
   - 新增 1 个 pass / 6 个 fail 互证 fixtures。

## 已验证

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py
python3 evals/run_product_market_analysis_evals.py --suite all  # 57/57
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # 通过
```

注意：`python3 evals/run_evals.py --suite all` 与 `python3 evals/run_product_market_analysis_evals.py --suite all` 仍是并列套件；前者目前不包含 market 那 57 条。

## 当前下一步建议

1. 先提交 Code Slice AB 当前变更。
2. 提交后进入 `Code Slice AC：时效降级 / freshness`。

## 重要边界

- 不删除 `tmp/stage5_chillys/`。
- 不联网核验真实法规、关税、认证或市场信息。
- 不把搜索摘要写成 Claim。
- 没有可记录的真实搜索/打开来源能力时，默认发现仍停在计划、样本池或已审核投影渲染层。
