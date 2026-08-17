# Route Map

The pure intake layer runs before business routing and emits exactly one mode: `metadata`, `material_triage`, `discovery_snapshot`, or `formal_research`. `metadata` keeps `@superleads`, help, current-capability questions, and the feedback entry static with `operations: []`; current/installed version reads use only an explicitly supplied active plugin root, never an installed cache. `material_triage` is user-visible as `资料初审` for material-only PDF, Excel/CSV, and screenshot requests, and creates no Run/Brief or public-research work. Ordinary bulk customer development is a bounded `discovery_snapshot`; `完整报告`, `正式开发名单`, `标准交付`, `深度背调`, and `联系人归属核验` select `formal_research`. These modes do not replace business route values such as `bulk_customer_development`, `customer_background_research`, or `product_outbound_market_analysis`.

Default batch route: `using-superleads` → bounded `discovery`. Scope, planning, collection, verification, and export guidance live under `shared/internal-stages/` and are read only when the current route and delivery mode require them.

单客户背调入口：`指定一个公司/品牌/域名/地址/邮箱/Candidate/用户材料 → researching-customer-background`。它不产生新客户批量池，不要求预先 Entity 解析，可使用独立轻验证导出背景报告；该报告不进入正式名单 audit 或 manifest。

产品出海市场分析入口：`产品/型号/产品资料 + 目标国家/地区 + 市场/准入/认证/税费/出口/物流问题 → analyzing-product-outbound-market`。它使用 `ProductMarketAnalysisGraph`，不产生 Candidate、Lead、客户名单、推荐客户类型或市场进入建议。认证类问题先查目标市场要求，再单独核对用户是否已有匹配材料。

路由细分：`找需要 CE/UL 的进口商/客户` 属于批量客户发现，因为认证词在描述客户范围；`出口某国是否需要 CE/UL/SDS/UN38.3/COO/关税/清关文件` 属于产品市场分析。同时明确多个目标时遵循 `composite-task-routing.md`，不等待用户为内部架构拆分请求。用户明确否定某路线时应尊重。

`discovery` is the default discovery-first working phase, not a new required
file or formal gate. It internally plans query expansion, records actual
SearchLogs, discovers and de-duplicates Candidates, supplements public signals
and visible contacts, and assigns business-relevance states. Use
  the matching files under `shared/internal-stages/` as on-demand guidance;
  do not route every discovery round through them as mandatory independent
  user-visible Skills.

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
