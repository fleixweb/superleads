# Handoff

- 分支：`master`
- 最新提交：`069314d Add product market freshness guardrails`
- 当前状态：Slice AD 开放世界权威来源识别模型已完成文档冻结，待提交；保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已完成

- Slice AA / Code Slice AA 已提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 已提交：`2073a98 Add weak-source corroboration records`。
- Code Slice AC 已提交：`069314d Add product market freshness guardrails`。
- Slice AD 已完成文档：`spec/33-superleads-open-world-authority-source-model-slice-ad.md`。

## Code Slice AC 已完成内容

1. `shared/schemas/product-market-analysis.schema.json`
   - 增加可选 `freshness_records`。
   - 新增 `FreshnessRecord` / `FreshnessStatus` / `FreshnessSubjectType`。
   - `EvidenceCard` 与 `MatrixRowRecord` 可引用 `freshness_record_ids`。
2. `scripts/validate_product_market_analysis.py`
   - 识别关税、出口要求、认证/准入、COO、线上价格、Google Trends、物流、近期外部因素、市场报告、季节窗口等强时效字段。
   - 阻断旧资料或日期未见资料写成“最新 / 现行 / current / latest”。
   - 阻断只用 `observed_at` 冒充来源日期或生效日期支撑 current。
   - 阻断强时效行误用 `not_time_sensitive`。
   - stale/date unknown 必须说明不能当什么和下一步怎么复核。
3. `scripts/export_product_market_workbook.py`
   - 导出新增人话列：`资料时效`、`复核建议`、`不能当最新结论`。
   - Markdown 顶部新增 `资料时效 / Freshness` 摘要区。
4. `scripts/audit_product_market_analysis.py`
   - 将 stale/date unknown freshness 纳入交付 limitation。
5. evals
   - market suite 从 `57` 条扩展到 `65` 条。
   - 新增 3 个 pass/fail freshness 基础样例：旧税表降级、日期未见产品属性、本轮税表窗口内复核。
   - 新增 5 个 fail 样例：旧税表称最新、日期未见法规升级 verified、无日期近期因素称最新、仅 observed_at 支撑 current、关税误标非强时效。
6. 文档
   - 新增 `spec/32-superleads-freshness-code-slice-ac.md`。
   - 新增 `docs/validation/superleads-code-slice-ac-freshness-20260728.md`。
   - `meta/open-questions.md` 中“法规与关税记录默认复核周期”已用 AC 首版窗口收口。

## 已验证

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 65/65
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # passed
```

## 当前下一步建议

1. 先提交 Slice AD 文档与同步记录。
2. 用户确认后进入 Code Slice AD：开放世界来源权威性防错闭环。
3. 后续优先级：状态词压缩、单一客户背调工程资产、批量客户开发内核复盘。

## Slice AD 冻结要点

- 不按国家/地区穷举官方来源；Superleads 必须支持任意出口国、原产国、起运国和目标销售国家/地区。
- Source Pack / registry 只能作为入口目录和动态查询加速器，不能直接支撑 EvidenceCard 或 MatrixRow 事实。
- 权威性必须由来源身份、事实域、管辖范围、可见身份核验证据和 freshness 共同判断。
- 无法核验来源身份或事实域能力时，只能输出候选来源、待查路径、来源受限或下一步核实，不能写确定性法规、关税、认证、COO 或出口要求结论。
- 少量国家/地区只允许作为 fixture / eval / 加速样例，不作为产品覆盖边界。

## 重要边界

- 不删除 `tmp/stage5_chillys/`。
- 不联网核验真实法规、关税、认证或市场信息。
- 不把搜索摘要写成 Claim。
- 没有可记录的真实搜索/打开来源能力时，默认发现仍停在计划、样本池或已审核投影渲染层。
- Code Slice AC 不判断真实“最新”，只按已有来源日期、生效日期、观察日期和复核窗口做交付降级。
- Slice AD 不联网核验真实官方机构，也不新增国家事实库；它只冻结开放世界权威来源识别模型和后续 Code Slice AD 的防错方向。
