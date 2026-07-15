# Status Labels

Lead dispositions:

- 重点开发
- 推荐跟进
- 需人工核查
- 暂不建议
- 排除

Contact user labels:

- 可直接使用
- 建议核查后使用
- 待确认归属
- 不可导出

Internal delivery statuses:

| Internal | User-facing |
|---|---|
| `needs_correction` | 需修正后交付 |
| `initial_lead_list` | 初筛客户名单 |
| `standard_development_list` | 标准开发名单 |
| `full_review_package` | 完整核查版 |
| `inquiry_followup_queue` | 询盘待办 |

Review modes: `independent`, `self_review_fallback`, `not_run`.

Inquiry statuses: `new`, `triaged`, `needs_entity_resolution`, `ready_for_follow_up`, `closed`. They are workflow states, not qualification, buyer-verification, or purchase-confirmation claims.
# Direction Labels

- `符合本次方向`: current-brief, current-run entity passed the controlled
  direction check; it is a delivery status, not an industry classification.
- `不符合本次方向`: public evidence supports a current-task exclusion or conflict.
- `需确认`: available material does not safely resolve the current direction.
- `仅作参考`: a competitor, brand, seed, or other reference that is not a
  customer prospect in this Run.
