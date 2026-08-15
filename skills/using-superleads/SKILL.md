---
name: using-superleads
description: "Use when users need overseas B2B customer discovery, public contact collection, lead-list enrichment, foreign-trade prospect research, single-customer background research, or product outbound market analysis intake/routing."
---

# Using Superleads

## Purpose

Activate Superleads, identify the user's entry, create a Run Context, choose the
route, check the minimum target, and hand off to the next Skill. Do not search,
generate leads, write development advice, or export workbooks here.

## Read first

Read these references as needed:

- `../../shared/references/user-intake.md` for intake modes and minimum targets.
- `../../shared/references/route-map.md` for route order and route boundaries.
- `../../shared/references/product-outbound-market-intake.md` for product-market
  intake wording.
- `../../shared/policies/tool-capability-policy.md` when tool availability
  changes the deliverable level.
- `../../shared/references/default-discovery-reference.md` for candidate,
  status, contact, and conflict boundaries. Start with its minimal skeleton.
- `../../shared/references/using-superleads-formal-delivery.md` before any formal
  public-source route or real-business UAT.

## Route

Use `../../shared/references/route-map.md` for the complete state machine and
`../../shared/references/user-intake.md` for intake modes and minimum targets.
Keep these decisions explicit:

- Product + destination + market/access question -> `analyzing-product-outbound-market`.
- Customers, buyers, importers, or lead lists -> bulk customer development.
- One named company/brand/domain/email/address/material for background ->
  `scoping-lead-research` -> `researching-customer-background`.
- Mixed market + customer request -> market analysis first, customer development
  only after separate confirmation.
- Certification describing the customer attribute stays bulk; certification
  describing product/destination requirements goes to market analysis.

Require product/service plus one scope axis for new customer development. Keep
the user's spreadsheet and requested cells for enrichment. Create a Run Context
with `run_id`, timestamp, entry mode, platform, capabilities, output mode, and
evidence depth. Formal gates and delivery checks are in the deferred reference.

When Codex exposes `web__run`, use its successful `search_query` as the native
search capability. Prefer `web__run.open` for public source text. If it cannot
open a discovered public HTML/text page, the next route may use
`../../scripts/capture_public_http_source.py` to perform a credential-free
`curl GET` and emit `source.open` records. The `curl` result complements but
never replaces successful native search; it creates no SearchLog, Claim, or
business conclusion. The Run must retain both adapter reports before formal
research begins.

For a real-business UAT, retain those current-Run operation records together
with the resulting graph as the `source_evidence` gate. Initialize the UAT in
a durable `.plugin-eval/manual/uat-runs/` directory with a built runtime
package, record each gate through `measure_superleads_uat.py --artifact`, and
run `finalize` then `verify`. A `/tmp` ledger, a search summary, or a benchmark
runner exit code cannot establish a portable formal UAT success.

## User-facing intake

For product-market analysis, use these four short lines:

`我理解你要做的是：产品出海市场分析。`
`本轮对象：{产品/品类/候选 HS-HTS} → {目的国/地区}。`
`默认出口申报国/原产口径：{用户指定/中国默认}；缺型号、起运地、最终税号或技术文件时会保留为条件和待确认项，不会先要求补齐。`
`我会整理趋势、公开价格参考、准入/认证要求、税费、出口要求、物流和外部因素；不生成客户名单，也不判断是否值得进入。`

Ask at most three short questions only when product identity or destination is
missing. Do not make export/origin details a first-pass blocker.

For customer development, use at most four lines beginning with `我理解你卖的是`、
`本次优先找`、`本次不纳入`、`判断依据将重点看`. Ask only questions that could
reverse the direction; unresolved ambiguity yields direction samples, not a
standard list. Follow `user-intake.md` for the exact boundary.

## Material intake

Classify supplied files before use; pasted company/contact text is a clue, not a
formal fact. With no formal source capability, handle only user material as
`资料初审`, never a formal plan, candidate pool, or report. For approved mailbox
intake, read scoped inbound mail through `mail.read` into an Inquiry queue; do
not mutate mail. Without it, request an EML/PDF/mail export.

## Output and boundaries

Return a concise Run Context and the next Skill. For formal chat-readable
Markdown, follow `../../shared/references/using-superleads-formal-delivery.md`;
the unified exporter is mandatory.

Keep the three routes separate: bulk discovery -> candidate pool and checks;
background -> one specified object; market analysis -> product matrix only.
Never expose internal graph objects, rule IDs, eval names, paths, or hashes.
Do not import legacy defaults or infer customer boundaries from another Skill or
Run. Search summaries are leads only, never Claims or user-visible facts.
