# Route Map

Default route: `using-superleads` → `scoping-lead-research` → `discovery` → `exporting-lead-workbooks`.

单客户背调入口：`指定一个公司/品牌/域名/地址/邮箱/Candidate/用户材料 → 客户背调报告`，路由为 `using-superleads` → `scoping-lead-research` → `researching-customer-background`。它不产生新客户批量池，不要求预先 Entity 解析，可使用独立轻验证导出背景报告；该报告不进入正式名单 audit 或 manifest。正式标准开发名单仍是独立、明确请求的严格路径。

产品出海市场分析入口：`产品/型号/产品资料 + 目标国家/地区 + 市场/准入/认证/测试/注册/标签/税费/出口/物流/COO/外部因素问题 → 产品出海市场分析`，路由为 `using-superleads` → `analyzing-product-outbound-market`。它使用 `ProductMarketAnalysisGraph`，不产生 Candidate、Lead、客户名单、推荐客户类型或市场进入建议；用户同时要求“分析市场再找客户”时拆成两步，先做产品出海市场分析，待用户确认后再另启批量客户开发。认证类问题先查目标市场要求，再单独核对用户是否已有匹配材料。

`discovery` is the default discovery-first working phase, not a new required
file or formal gate. It internally plans query expansion, records actual
SearchLogs, discovers and de-duplicates Candidates, supplements public signals
and visible contacts, and assigns business-relevance states. Use
`writing-research-plans`, `executing-research-plans`,
`collecting-contact-intelligence`, and `assessing-research-evidence` as
internal or on-demand guidance; do not route every discovery round through
them as four mandatory independent stages.

Conditional additions:

- Use `resolving-company-identity` only when identity conflict needs active investigation or a deep-check output requires an Entity decision.
- Use `reviewing-lead-research` → `verification-before-delivery` only for a formal background check, contact ownership verification, trade/China identity verification, a contactable list, or a standard development list. Default discovery does not expand attestation, hash, Manifest, or full-review work.
- `learning-from-feedback` is cross-cutting after delivery, not a default discovery-round stage.
- Use `export_superleads_markdown.py --route auto` as the unified
  chat-readable Markdown delivery layer after a route has already produced a
  reviewed projection.
- Use `export_product_market_workbook.py`, not `export_workbook.py`, for
  reviewed product outbound market analysis CSV export and its product-market
  Markdown variant.

State machine:

- 默认发现：`scoped` → `planned` → `collecting` → `assessed` → `initial_lead_list`
- 按需深查：`scoped` → `planned` → `collecting` → `assessed` → `under_review` → `remediation_required` → `remediation_submitted` → `re_reviewed` → `checked` → `standard_development_list` / `full_review_package`
- 产品出海市场分析：`briefed` → `source_planned` → `collecting` → `reviewed_matrix` → `ready_with_limitations` / `blocked_needs_input` / `needs_correction`

弱证据不删除有用候选，只降级为业务相关性、未知项或待核查项。误导性错误才阻断交付。
