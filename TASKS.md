# Tasks

## 已完成

- 产品出海市场分析 Slice 1-13 及 Code Slice A-M 已完成。
- Slice R 产品内核复盘已完成，确认 Superleads 是外贸业务情报产品，不是通用工作流框架。
- Slice S 三路线真实外贸样本已完成。
- Slice T 用户可见输出合同与静态 eval 已完成。
- Code Slice U 三路线用户可见 Markdown 交付器已提交：`43f2ef7 Add Superleads Markdown delivery exporter`。
- Code Slice V README / Skill 使用说明 / 常用命令示例已提交：`8ea336a Document Superleads Markdown delivery usage`。
- Slice W 目的国认证 / 准入要求判断纠偏已提交：`8f6703a Calibrate product market certification requirements`。
- Code Slice X 认证 / 目的国准入要求防错闭环已提交：`85197d7 Add certification requirement guardrails`。
- Slice AA 弱证据外贸场景校准已完成并提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AA 用户交付污染 bug + 路由器修复已完成并提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 多来源互证 / CorroborationRecord 最小闭环已完成并提交：`2073a98 Add weak-source corroboration records`。
- Code Slice AC 资料时效 / freshness 降级最小闭环已提交：`069314d Add product market freshness guardrails`。
- Slice AD 开放世界权威来源识别模型已完成文档冻结：`spec/33-superleads-open-world-authority-source-model-slice-ad.md`。

## Code Slice AC 已完成内容

1. schema
   - `ProductMarketAnalysisGraph` 新增可选 `freshness_records`。
   - `EvidenceCard` / `MatrixRowRecord` 新增可选 `freshness_record_ids`。
   - 新增 `FreshnessRecord` / `FreshnessStatus` / `FreshnessSubjectType`。
2. validator
   - 对关税、出口要求、认证/准入、COO、线上价格、Google Trends、物流、近期外部因素、市场报告、季节窗口建立强时效识别。
   - `current_enough_for_scope` 必须有可解析来源日期或生效日期；`observed_at` 不能单独支撑 current。
   - stale/date unknown 不能写“最新 / 现行 / current / latest”。
   - stale/date unknown 必须写 `cannot_conclude` 和下一步复核动作。
   - verified 强时效矩阵行使用日期未见/过期证据时必须有 freshness 边界，否则失败。
   - 强时效行不能用 `not_time_sensitive` 支撑事实或最新口径。
3. exporter
   - CSV / Markdown 增加：`资料时效`、`复核建议`、`不能当最新结论`。
   - Markdown 顶部增加 `资料时效 / Freshness` 摘要。
4. auditor
   - stale/date unknown freshness 会进入 limitation。
5. evals
   - 新增 pass：`market_pass_freshness_stale_tariff_downgraded.json`、`market_pass_freshness_date_unknown_product_attribute.json`、`market_pass_freshness_current_tariff_rechecked.json`。
   - 新增 fail：`market_fail_freshness_old_tariff_called_latest.json`、`market_fail_freshness_date_unknown_regulation_verified.json`、`market_fail_freshness_recent_factor_without_date_latest.json`、`market_fail_freshness_current_observed_only.json`、`market_fail_freshness_not_time_sensitive_for_tariff.json`。
   - market suite 现为 `65/65`。

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

## 当前下一步

1. 先提交 Slice AD 文档与同步记录。
2. 用户确认后进入 Code Slice AD：开放世界来源权威性防错闭环。
3. 后续再排：状态词压缩、单一客户背调工程资产、批量客户开发内核复盘。

## Code Slice AD 待实现方向

1. schema
   - 增加 AuthorityProfile / AuthorityIdentityEvidence / AuthorityCapability / AuthorityVerificationRecord。
   - 不建立全球国家事实库；少量国家只做 fixture 或加速样例。
2. validator
   - 阻断 keyword-only authority、domain-only authority。
   - 阻断事实域错配、管辖范围错配、Source Pack / registry 直接支撑事实。
   - 阻断行业/商业/媒体/货代来源升级为主管官方来源。
3. query plan
   - 当目标国家/地区没有预置 Pack 时，仍生成动态 authority discovery 查询组。
   - 搜索摘要只进候选来源，不形成 EvidenceCard。
4. exporter / audit
   - 用户可见展示：来源身份、适用范围、可以当作什么、不能当作什么、下一步核实。
   - 权威性待核实、来源身份冲突、事实域不匹配要进入 limitation 或 blocker。
5. fixtures/evals
   - pass：未知国家 plan-only、官方税则只支撑税费、认证机构只作路径参考、货代只作物流线索。
   - fail：博客冒充 required、只靠域名判官方、海关税则支撑认证、出口国来源支撑目的国准入、Source Pack 直接当事实、多弱来源冒充官方确认。

## 当前阻塞 / 注意

- 真实默认发现仍受能力限制：没有可记录的真实搜索/打开来源能力时，默认发现只能停在计划或样本池层；不能伪造 SearchLog / Source / Observation。
- `tmp/stage5_chillys/` 必须保留。
- AC 不联网判断真实最新；只按 graph 中已记录的来源日期、生效日期、观察日期和复核窗口做降级。
