# Code Slice AB：多来源互证 / CorroborationRecord 最小闭环

日期：2026-07-28

## 1. 本 Slice 要解决什么

Slice AA 已确认：Superleads 不是强证据二值判定系统，而是弱证据收敛 + 可审计交付系统。

因此 Code Slice AB 把“多来源互证”从设计文字变成产品出海市场分析图谱中的一等结构：

> 多个独立弱来源指向同一方向，可以提高参考价值，但不能自动升级成最终事实、合规结论、最终税率、推荐进入或推荐价格。

## 2. 用户心智

用户不需要看到内部 `CorroborationRecord`，用户需要看到：

| 用户问题 | 应显示 |
|---|---|
| 是不是只有一个来源？ | 单点来源线索 |
| 多个来源是不是同一家搬运？ | 独立来源不足 |
| 多个独立来源是否指向同一方向？ | 多来源一致指向 |
| 有没有反向资料？ | 来源之间有冲突 |
| 这个能不能当最终结论？ | 不能推出什么 |

## 3. 内部字段最小合同

`corroboration_records` 是产品市场图谱的可选数组。旧 fixture 不强制补。

| 字段 | 含义 |
|---|---|
| `corroboration_id` | 互证记录 ID |
| `run_id` / `brief_version_id` | 所属运行与 Brief 版本 |
| `field_domain` / `field_name` | 被互证的信息域和字段 |
| `current_signal` | 当前弱证据共同指向的内容 |
| `corroboration_status` | `multi_source_consistent` / `single_source_only` / `not_enough_independent_sources` / `conflict_present` / `source_restricted` / `not_executed` |
| `source_refs` | 支持互证的已打开来源 |
| `supporting_evidence_card_ids` | 支持方向一致的证据卡 |
| `conflicting_evidence_card_ids` | 反向或冲突证据卡 |
| `independent_source_count` | 独立来源数，按来源 owner/domain 保守计算 |
| `independence_basis` | 为什么认为来源独立 |
| `user_visible_summary` | 用户可见摘要 |
| `cannot_conclude` | 不能推出什么 |
| `next_verification_steps` | 下一步核实 |
| `review_status` | 是否已复核 |

## 4. 状态口径

| 内部状态 | 用户显示 | 边界 |
|---|---|---|
| `multi_source_consistent` | 多来源一致指向 | 仍不是最终事实 |
| `single_source_only` | 单点来源线索 | 只能作为候选参考 |
| `not_enough_independent_sources` | 独立来源不足 | 同域名、同 owner、转载链路不能算多个独立来源 |
| `conflict_present` | 来源之间有冲突 | 必须保留冲突，不能合并为结论 |
| `source_restricted` | 来源受限 | 不能升级 |
| `not_executed` | 未执行 | 不能编造互证 |

## 5. Validator 门禁

| 规则 | 失败码 |
|---|---|
| 互证记录引用不存在的 Run | `market_corroboration_run_missing` |
| 未复核的互证记录进入交付 | `market_corroboration_not_reviewed` |
| 搜索摘要、SearchLog、Source Pack、Query Plan 直接作为互证事实 | `market_corroboration_search_or_plan_source` |
| 引用未打开来源 | `market_corroboration_unopened_source` |
| 声明独立来源数与实际 owner/domain 去重数不一致 | `market_corroboration_source_count_mismatch` |
| `multi_source_consistent` 少于 2 个独立已打开来源 | `market_corroboration_not_independent` |
| 存在同字段冲突却写成多来源一致 | `market_corroboration_conflict_hidden` |
| 多个弱来源一致被写成 verified / 最终事实 / 推荐 / 最终税率 | `market_corroboration_overstated` |

## 6. 导出口径

导出层只增加人话列，不暴露内部对象：

| 人话列 | 内容 |
|---|---|
| 多来源互证情况 | 多来源一致指向 / 单点来源线索 / 独立来源不足 / 来源之间有冲突 |
| 互证边界 | 不能推出什么 |
| 下一步核实 | 需要哪些业务文件、权威来源或专业复核 |

## 7. 非目标

- 不联网补真实来源；
- 不把多来源一致自动升级为 `verified`；
- 不用互证替代官方法规、认证、关税来源；
- 不解决时效降级；
- 不解决 Authority registry。

## 8. 验收样例

| fixture | 预期 |
|---|---|
| `market_pass_multi_source_corroboration_reference.json` | 3 个独立已打开弱来源一致，用户可见为“多来源一致指向”，但矩阵状态仍为 `preliminary_reference` |
| `market_fail_corroboration_single_source_promoted.json` | 单来源却声明多来源一致，失败 |
| `market_fail_corroboration_same_domain_independent.json` | 同域名多页面声明多个独立来源，失败 |
| `market_fail_corroboration_conflict_hidden.json` | 存在冲突却写成多来源一致，失败 |
| `market_fail_corroboration_search_summary_source.json` | 搜索摘要或 SearchLog 冒充互证来源，失败 |
| `market_fail_corroboration_overstated_verified.json` | 多弱来源一致把矩阵行升级为 verified，失败 |
