# Code Slice AC：资料时效 / Freshness 降级最小闭环

日期：2026-07-28

## 1. 本 Slice 要解决什么

Slice AA 指出：外贸公开信息最常见的错误不是“完全没有来源”，而是把旧资料、无日期资料、只在本轮打开过的资料写成“最新 / 现行 / current / latest”。

Code Slice AC 把“资料时效”从口头要求落成产品出海市场分析图谱中的一等结构：

> 法规、关税、认证、目的国准入、出口要求、线上价格、物流、Google Trends、近期外部因素、行业报告和季节窗口，都必须带资料日期、观察日期和复核窗口。旧资料可以保留为线索，但不能被写成最新结论。

## 2. 用户心智

用户不需要看到内部 `FreshnessRecord`，用户需要看到三句话：

| 用户真正关心的问题 | 用户可见字段 |
|---|---|
| 这条资料新不新？ | 资料时效 |
| 下一次或报关前要怎么复核？ | 复核建议 |
| 现在不能把它当成什么？ | 不能当最新结论 |

用户看到的表达应当像外贸业务提醒，而不是程序状态：

| 场景 | 人话展示 |
|---|---|
| 本轮打开的来源日期在复核窗口内 | 本轮复核日期在当前口径内；仍需报关前/下单前复核 |
| 来源日期未见，但只是产品网页属性 | 来源日期未见，但本轮已观察；不能泛化到实物标签或未来批次 |
| 旧税表 / 旧法规 / 旧物流资料 | 资料偏旧，需重新复核；只能当历史线索 |
| 日期未见的法规 / 关税 / 近期因素 | 来源日期未见，需复核后再当现行信息 |
| 本轮未执行 | 未执行；不形成趋势、价格、税费、物流或最新行情结论 |

## 3. 内部字段最小合同

`freshness_records` 是产品市场图谱的可选数组。旧 fixture 不强制补；但一旦用户可见内容出现“最新 / 现行 / 当前 / current / latest / as of”等话术，必须有通过复核的 `current_enough_for_scope` 时效记录支撑。

| 字段 | 含义 |
|---|---|
| `freshness_id` | 时效记录 ID |
| `run_id` / `brief_version_id` | 所属运行与 Brief 版本 |
| `field_domain` / `field_name` | 被复核的信息域和字段 |
| `subject_type` / `subject_ref_ids` | 指向来源、观察、证据卡、矩阵行、互证记录或模块 |
| `freshness_status` | 时效状态 |
| `freshness_checked_at` | 本轮复核日期 |
| `review_window_days` | 本字段默认复核窗口 |
| `source_date_values` | 来源发布日期、页面日期、版本日期等 |
| `effective_date_values` | 生效日期、适用日期等 |
| `observed_at_values` | 本轮打开/观察日期 |
| `date_basis` | 为什么这样判断时效 |
| `next_review_due_at` | 建议下次复核日期 |
| `user_visible_summary` | 用户可见摘要 |
| `cannot_conclude` | 不能当成什么 |
| `next_verification_steps` | 下一步核实动作 |
| `review_status` | 是否已复核 |

## 4. 状态口径

| 内部状态 | 用户显示 | 边界 |
|---|---|---|
| `current_enough_for_scope` | 本轮复核日期在当前口径内 | 需要可解析的来源日期或生效日期；`observed_at` 不能单独支撑“最新” |
| `date_unknown_recently_observed` | 来源日期未见，但本轮已观察 | 只能作本轮线索，不泛化到现行法规、现行税率、最新价格或未来批次 |
| `stale_needs_recheck` | 资料偏旧，需重新复核 | 可作历史线索，不能写最新/现行 |
| `date_unknown_needs_recheck` | 来源日期未见，需复核后再当现行信息 | 特别适用于法规、关税、认证、近期外部因素 |
| `not_time_sensitive` | 非强时效字段 | 不能用于支撑关税、法规、认证、物流、价格等强时效矩阵行 |
| `not_executed` | 未执行 | 不能编造趋势、价格、行情或时效 |

## 5. 首版默认复核窗口

默认窗口只用于降级门禁，不代表真实世界一定有效；Authority registry 以后可以把窗口精细到国家、机构、货物属性和来源类型。

| 信息域 | 默认窗口 |
|---|---:|
| 近期外部因素 / 港口拥堵 / 战争 / 制裁 / 自然灾害 | 14 天 |
| 进口税费 / 关税 / HTS/TARIC/税率 | 30 天 |
| 出口要求 / 出口管制 / 商检 / 检验检疫 | 30 天 |
| 线上价格 / 平台标价 | 30 天 |
| Google Trends / 搜索趋势 | 90 天 |
| 物流 / 运输 / 预申报 / 承运限制 | 90 天 |
| 目的国认证 / 准入 / 标签 / 包装 / 注册 | 180 天 |
| 原产地证明 / COO / proof of origin | 180 天 |
| 市场报告 / 行业报告 | 365 天 |
| 季节、节日、淡旺季窗口 | 365 天 |

## 6. Validator 门禁

| 规则 | 失败码 |
|---|---|
| 时效记录引用不存在的 Run | `market_freshness_run_missing` |
| 时效记录未复核 | `market_freshness_not_reviewed` |
| 时效记录引用不存在的对象 | `market_freshness_subject_missing` |
| 旧资料 / 日期未见资料没有写“不能当什么” | `market_freshness_missing_boundary` |
| 旧资料 / 日期未见资料没有下一步复核动作 | `market_freshness_missing_next_review` |
| `current_enough_for_scope` 没有复核窗口 | `market_freshness_window_missing` |
| `freshness_checked_at` 不是可解析日期 | `market_freshness_checked_at_invalid` |
| 只靠观察日期、没有来源日期或生效日期，却称 current | `market_freshness_current_without_date` |
| 来源日期超过复核窗口却称 current | `market_freshness_stale_over_window` |
| 用户可见矩阵写“最新/现行/current/latest”但无 current freshness | `market_latest_claim_without_freshness` |
| stale/date unknown 的矩阵行仍保持 verified/final | `market_freshness_stale_row_not_downgraded` |
| verified 强时效矩阵行使用日期未见证据卡且无时效边界 | `market_freshness_missing_for_date_unknown` |
| verified 强时效矩阵行使用过期证据卡且无时效边界 | `market_freshness_missing_for_stale_source` |
| 强时效行误用 `not_time_sensitive` | `market_freshness_not_time_sensitive_mismatch` |
| 矩阵行引用不存在的时效记录 | `market_freshness_record_missing` |

## 7. 导出口径

CSV / Markdown 导出增加三个人话字段：

| 字段 | 展示口径 |
|---|---|
| 资料时效 | 状态 + 复核窗口 + 用户可见摘要 |
| 复核建议 | 下一步重新打开来源、找供应链、报关行、认证机构或承运人确认 |
| 不能当最新结论 | 明确不能当最新税率、现行法规、最终认证、承运承诺、最新行情等 |

Markdown 顶部新增 `资料时效 / Freshness` 摘要区，优先把有时效风险的行放在用户前面。

## 8. 非目标

本轮不做：

- 不联网判断真实最新法规、真实税率、真实物流行情；
- 不内置国家事实库；
- 不替代 Authority registry；
- 不把旧 fixture 全量改造为 freshness-first；
- 不把观察日期当来源发布日期；
- 不给用户做是否值得进入、推荐价格、最终税率或最终合规判断。

## 9. 验收样例

| fixture | 预期 | 验收点 |
|---|---|---|
| `market_pass_freshness_stale_tariff_downgraded.json` | pass | 旧 HTS 资料降级为历史线索，导出显示资料偏旧、复核建议、不能当最新税率 |
| `market_pass_freshness_date_unknown_product_attribute.json` | pass | 产品网页日期未见可作本轮线索，但不能当实物标签或未来批次结论 |
| `market_pass_freshness_current_tariff_rechecked.json` | pass | 有来源日期且在 30 天窗口内，可写“截至本轮复核”，但仍不写最终税率 |
| `market_fail_freshness_old_tariff_called_latest.json` | fail | 旧税表被写成最新税率 |
| `market_fail_freshness_date_unknown_regulation_verified.json` | fail | 日期未见的法规/认证要求被升级为 verified |
| `market_fail_freshness_recent_factor_without_date_latest.json` | fail | 无日期近期外部因素写成最新影响 |
| `market_fail_freshness_current_observed_only.json` | fail | 只用 observed_at 冒充来源日期，声称 current |
| `market_fail_freshness_not_time_sensitive_for_tariff.json` | fail | 关税字段误标为非强时效字段 |
