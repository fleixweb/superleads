# Handoff

- 分支：`master`
- 最新提交：`85197d7 Add certification requirement guardrails`
- 当前工作树：Slice AA / Code Slice AA 已完成并通过回归，待提交；保留 `tmp/stage5_chillys/`，无关目录不处理。

## 已验证

- Slice AA / Code Slice AA：
  - 用户可见输出静态套件：`8/8`
  - 三路线 Markdown 交付器套件：`5/5`
  - 默认套件：`98/98`
  - 深度套件：`644/644`
  - 全量套件：`684/684`
  - market 独立套件：`50/50`
  - `git diff --check` 通过
- 注意：`python3 evals/run_evals.py --suite all` 与 `python3 evals/run_product_market_analysis_evals.py --suite all` 仍是并列套件；前者目前不包含 market 那 50 条。

## 当前结论

Slice AA 已正式把 Superleads 校准为“弱证据收敛 + 可审计交付”系统，而不是沿用 Superpowers 的强证据二值判定。

Code Slice AA 已修复 P0：

1. `export_superleads_markdown.py` 的内部术语替换已加英文词边界，不再破坏 `The Telegraph`、`Photograph`、`paragraph`、`evaluation`。
2. `validate_superleads_user_visible_output.py` 已支持否定语境豁免和英文词边界；“不判断是否值得进入”“不做推荐客户排序，也不给采购概率”“Made in 等于 COO 是错误理解”不再误报；正向“建议进入 / 推荐客户 / 采购概率 / 候选税号就是最终税率”仍失败。
3. `route_superleads_intake.py` 已补真实外贸客户词，修复经销商/批发商/零售商/代理商/连锁/维修商等 bulk 入口；SDS / UN38.3 / 认证 / 关税 / 物流要求进入产品出海市场分析；“后市场”“中性包装”不再因普通 `市场` / `包装` 子串误伤。
4. 产品市场 Markdown 交付器停止补固定 `Google Trends / COO / 海运拼箱 / 国际快递 / 待补材料清单` 样板段；用户可见合同改为通用栏目，具体样本词放在 case 级 `must_contain`。

## 本轮新增关键文件

- `spec/30-superleads-weak-evidence-calibration.md`
- `docs/validation/superleads-weak-evidence-diagnostic-20260728.md`
- `docs/validation/superleads-code-slice-aa-p0-fixes-20260728.md`
- `evals/fixtures/pass_default_discovery_markdown_replacement_boundaries.json`
- `evals/user_visible_outputs/product_market_negated_guardrails_and_source_names.md`
- `evals/user_visible_outputs/fail_user_visible_positive_recommendation.md`

## 下一步建议

1. 先提交 Slice AA + Code Slice AA 当前变更。
2. 提交后进入 P1 中最关键的一项：`Code Slice AB：多来源互证 / CorroborationRecord 最小设计与 eval`。
3. 暂缓展示美化类 Slice，直到多来源互证、时效降级、Authority registry 的方向排清楚。

## 重要边界

- 不删除 `tmp/stage5_chillys/`。
- 不联网核验真实法规、关税、认证或市场信息。
- 不把搜索摘要写成 Claim。
- 没有可记录的真实搜索/打开来源能力时，默认发现仍停在计划、样本池或已审核投影渲染层。
