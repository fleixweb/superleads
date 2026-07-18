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
| `initial_lead_list` | 发现候选池 |
| `standard_development_list` | 标准开发名单 |
| `full_review_package` | 完整核查版 |
| `inquiry_followup_queue` | 询盘待办 |

Review modes: `independent`, `self_review_fallback`, `not_run`.

Inquiry statuses: `new`, `triaged`, `needs_entity_resolution`, `ready_for_follow_up`, `closed`. They are workflow states, not qualification, buyer-verification, or purchase-confirmation claims.

# Business Relevance Labels

- `directly_related`: 已观察到与本次产品、应用、客户角色、渠道或地域边界直接相符的业务信号。
- `possibly_related`: 有行业、目录、地域、渠道或产品线索，但公开材料不足以确认具体业务关系。
- `explicitly_excluded_or_unrelated`: 已观察到错误行业、错误市场、原厂/同行制造商或命中用户明确排除边界。
- `identity_pending`: 公司名称、域名、地址、贸易记录或联系方式无法可靠归属同一主体。
- `insufficient_information`: 已发现线索，但当前公开材料不足。

# Public Signal Status Labels

- `observed`: 已观察
- `not_observed`: 已查未见
- `not_searched`: 未检索
- `identity_pending`: 主体待确认
- `source_restricted`: 来源受限

这些状态只描述本轮公开可见信号与主体归属，不表示采购意向、商业价值或采购概率。
# Direction Labels

- `符合本次方向`: current-brief, current-run entity passed the controlled
  direction check; it is a delivery status, not an industry classification.
- `不符合本次方向`: public evidence supports a current-task exclusion or conflict.
- `需确认`: available material does not safely resolve the current direction.
- `仅作参考`: a competitor, brand, seed, or other reference that is not a
  customer prospect in this Run.
