# Status Labels

Internal compatibility lead dispositions (not user-facing recommendations):

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

`标准开发名单` is a mechanical projection of the user's pre-stated rules and
verified public information. It does not express an AI recommendation, a
customer-value ranking, or a follow-up decision.

Default discovery user-visible partitions:

- `公开信号已匹配当前范围`: opened public material contains signals that match
  the user's stated product, market, customer-type, or other scope boundary.
- `待确认`: the current public material leaves the subject, business relation,
  contact association, or other required fact unresolved.
- `已排除 / 仅作参考`: opened material shows an explicit user-boundary mismatch,
  or the record is retained only as a reference. Neither status is a customer
  value judgment.

# Business Relevance Labels

- `directly_related`: 已观察到与本次产品、应用、客户角色、渠道或地域边界直接相符的业务信号。
- `possibly_related`: 有行业、目录、地域、渠道或产品线索，但公开材料不足以确认具体业务关系。
- `explicitly_excluded_or_unrelated`: 已观察到错误行业、错误市场、原厂/同行制造商或命中用户明确排除边界。
- `identity_pending`: 公司名称、域名、地址、贸易记录或联系方式无法可靠归属同一主体。
- `insufficient_information`: 已发现线索，但当前公开材料不足。

主体归属与业务资料是两个正交维度：

- `identity_resolution_status = unresolved` + `business_relevance_status = insufficient_information`：主体信息尚不足以解析，业务资料也不足；用户端分别显示“主体未解析”和“信息不足”，不写成冲突。
- `identity_resolution_status = pending/conflicted` + `business_relevance_status = identity_pending`：现有材料涉及主体待确认或主体冲突；用户端分别显示“主体待确认”或“主体冲突待复核”。
- 只有 `identity_resolution_status = matched` 且 `entity_id` 指向现有 Entity，才能投影 `directly_related`、`possibly_related` 或 `explicitly_excluded_or_unrelated`。

跨来源碎片可以保留并组合成标注清楚的工作判断；工作判断必须列出来源与主体关联状态，且不得把搜索摘要、推断值或未观察值写成已观察事实。两个已解析 Entity 之间沿用 `entity_relationships`；未解析 Candidate 留在 Candidate 级 identity 状态。

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

# Product Market User-Visible Status Projection (Slice AE)

产品出海市场分析、批量客户开发、单一客户背调的用户可见交付层应优先使用以下 11 个状态词；内部枚举仍可保留给 schema、validator、audit 和 Skill 交接使用。

| 用户可见状态 | 人话含义 |
|---|---|
| 已有明确依据 | 已打开/记录的来源能支持当前字段本身，且没有被时效、权威性、冲突或来源限制降级。 |
| 按已知数据计算 | 用已核实数字按明示公式计算，只支持公式结果。 |
| 多来源方向一致 | 多个独立弱来源指向同一方向，但不等于官方确认。 |
| 可作为线索 | 有公开信号或参考来源，可用于下一步核验。 |
| 需补充资料 | 产品出海市场分析中缺用户、产品、技术、实物、订单或供应链材料；发现候选池中则表示主体尚未归并或公开业务资料不足，待 Superleads 在深度核验 / L2 补查。 |
| 需权威/专业复核 | 需要主管机关、报关行、认证机构、承运人、律师、进口商等复核。 |
| 资料过旧需复核 | 来源过旧、日期未知或超过事实域复核窗口。 |
| 来源受限 | 来源未打开、付费墙、摘要页、登录墙或只能看到片段。 |
| 说法冲突待复核 | 不同来源、日期或口径存在冲突。 |
| 本轮未执行 | 本次没有采集或运行该模块；不能补样板事实。 |
| 暂不适用 | 按当前产品档案或贸易路径暂未触发，不泛化到其它场景。 |

投影优先级：未执行 / 不适用 / 冲突 / 来源受限 / 资料过旧 / 权威未核实 / 缺材料 优先于 `verified`。用户可见表格必须分开展示业务/规则结论、依据状态和用户材料状态。

发现候选池里的“需补充资料”不是要求用户交材料：补查方是 Superleads 的深度核验 / L2；具体要核对的主体、公开业务资料和下一步，逐条见候选详情表的「待确认与冲突」列（来自 Candidate 的 `unknowns` 与 `next_verification_steps`）。发现候选池的「依据状态」按降级优先级投影，不能读作“我们对这家了解多少”的排序。例如同一份默认发现样例中，展会名单线索 `Peak Bottle Co` 投影为“来源受限”，而同名主体待归并的 `Summit Trading` 投影为“需补充资料”；前者的 `source_restrictions` 降级规则先命中，并不表示它比后者拥有更多公开资料。

批量客户开发的默认发现候选池同样遵守该优先级：分区只描述公开信号与当前用户边界的关系，
不表示客户价值、跟进优先级或采购意愿。主体状态、业务关联和来源状态分列投影：
`unresolved` 显示“主体未解析”，`pending` 显示“主体待确认”，`conflicted` 显示
“主体冲突待复核”，`insufficient_information` 显示“信息不足”。不能因某一信号为
`identity_pending` 就把未解析或资料不足一律改写为“说法冲突待复核”。任一公开信号为
`source_restricted` 或 Candidate 记录了 `source_restrictions` 时，来源维度显示“来源受限”。
