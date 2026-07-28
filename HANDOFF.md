# Handoff

- 分支：`master`
- 最新提交：`22be247 Document open world authority source model`
- 当前状态：Code Slice AD 开放世界来源权威性防错闭环已完成实现与验证，待提交；保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已完成

- Slice AA / Code Slice AA 已提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 已提交：`2073a98 Add weak-source corroboration records`。
- Code Slice AC 已提交：`069314d Add product market freshness guardrails`。
- Slice AD 文档已提交：`22be247 Document open world authority source model`。
- Code Slice AD 已完成：开放世界 AuthorityProfile / AuthorityVerificationRecord 防错闭环。

## Code Slice AD 已完成内容

1. `shared/schemas/product-market-analysis.schema.json`
   - `EvidenceCard` / `MatrixRowRecord` 新增 `authority_verification_record_ids`。
   - 图谱新增 `authority_profiles`、`authority_identity_evidence`、`authority_capabilities`、`authority_verification_records`。
   - 新增 AuthorityProfile / IdentityEvidence / Capability / VerificationRecord defs。
2. `scripts/validate_product_market_analysis.py`
   - 强监管事实域的确定性 row/card 需要 AuthorityVerificationRecord。
   - 阻断 keyword-only、domain-only 权威性判断。
   - 阻断 fact domain / jurisdiction role / jurisdiction name 错配。
   - 阻断 Source Pack / Query Plan / SearchLog 直接支撑事实。
   - 阻断行业、商业、媒体、货代、未知来源升级为主管官方确定性结论。
   - 阻断多弱来源一致被写成官方确认。
   - 修正 origin proof 文案含 tariff 时误判 import_tax 的问题。
3. `scripts/export_product_market_workbook.py`
   - CSV / Markdown 新增人话字段：`来源身份`、`适用范围`、`可以当作什么`、`不能当作什么`、`权威性核实`。
   - Markdown 顶部新增 `来源权威性 / Authority` 摘要区。
4. `scripts/audit_product_market_analysis.py`
   - authority 限制状态进入 limitation：candidate / secondary / unable / conflicting / not_executed。
5. `scripts/plan_product_market_sources.py`
   - 未预置目标国家/地区生成开放世界 authority discovery 查询组。
   - 覆盖目的国准入、COO、关税、预申报、食品农检、危险品等触发路径。
   - 非美国目的国不再因食品等触发项套用美国 Source Pack。
6. evals
   - market suite 从 65 条扩到 74 条。
   - source plan suite 从 6 条扩到 7 条。
   - 新增 pass/fail authority fixtures 和泰国食品开放世界 plan-only fixture。
7. 文档
   - 新增 `docs/validation/superleads-code-slice-ad-authority-20260729.md`。

## 已验证

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py scripts/plan_product_market_sources.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
python3 evals/run_product_market_source_plan_evals.py --suite all  # 7/7
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # passed
```

## 当前下一步建议

1. 提交 Code Slice AD。
2. 后续优先级：状态词压缩、单一客户背调工程资产、批量客户开发内核复盘。
3. 若继续产品出海市场分析路线，可进入 Code Slice AE：状态词压缩 / 输出合同状态映射。

## 重要边界

- 不删除 `tmp/stage5_chillys/`。
- 不联网核验真实法规、关税、认证或市场信息。
- 不把搜索摘要写成 Claim。
- 没有可记录的真实搜索/打开来源能力时，默认发现仍停在计划、样本池或已审核投影渲染层。
- Code Slice AD 不建立全球官方机构事实库；它只要求在具体运行中打开来源并记录身份、事实域、管辖范围、时效和边界。
