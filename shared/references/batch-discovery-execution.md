# Batch Discovery Execution Rules

Read this reference only after `using-superleads` has determined that the user
made a concrete batch customer-discovery request. Do not read it for a bare
plugin activation, help, metadata, version, capability, feedback, or
material-triage request.

## Required References

Read `superleads-user-guidance.md` for terminal-delivery footer rules and
`user-intake.md` for batch minimum scope. Read
`../policies/tool-capability-policy.md` only when availability affects the
deliverable. For default discovery, read `default-discovery-reference.md`,
starting with `default-discovery-minimal-skeleton.example.json`; open its full
reference only for status, contact, or conflict boundaries. Before a formal
bulk route or real-business UAT, read `using-superleads-formal-delivery.md`.

## Intake and Mode Rules

Run the pure mode classifier before business routing. `metadata` covers help,
installed-version, current-capability, feedback, and explicit update requests;
it returns `operations: []`, creates no Run/Brief, and does not search, open
sources, scan caches, export, or validate. Read a version only from an
explicitly supplied active plugin root; fetch a remote version only for an
explicit update request and report `本次未能确认远端版本` when it cannot be
confirmed.

`material_triage` is the user-visible `资料初审` path for material-only PDF,
Excel/CSV, or screenshot requests. It organizes provided material and pending
checks only; it creates no Run/Brief and starts no public research.
`discovery_snapshot` is the ordinary bounded mode. `formal_research` requires
explicit intent such as `正式开发名单`, `标准交付`, `完整报告`, `深度背调`, or
`联系人归属核验`.

Confirm that the batch request asks for customers, buyers, importers, lead
lists, or prospect development by product/service or keyword plus at least one
scope axis. A named single company, brand, domain, email, address, or material
for background investigation with no second explicit objective must use
`researching-customer-background`. A product-market request about trends,
price, compliance, tax, export, logistics, COO, or external factors with no
second explicit objective must use `analyzing-product-outbound-market`.

For existing-table enrichment, retain the supplied spreadsheet and the rows or
cells being supplemented. It does not create a direction-matched customer list
without a current development contract. Create a Run Context only for
`discovery_snapshot` or `formal_research` and record the entry mode, platform,
capabilities, output mode, and evidence depth. For multi-row or multi-query
enrichment, read `bulk-execution-strategy.md`; single-row supplementation does
not load that reference.

## Fast Candidate Pool

For an unambiguous product + market + customer-type request, inspect the
宿主实际暴露的工具 and use one bounded search through an exposed native provider;
do not guess a Codex, ChatGPT Desktop, Claude, Hermes, or WorkBuddy tool name.
Do not retry the 同一失败适配器. A different provider may be tried only when it
is already present in the host tool inventory. Use a run-wide first batch
target of 10. Per-query-group
limits must not add up beyond that run-wide cap. Cover only website, directory,
document, and search-result sources. Each candidate needs a public website or
search-result reference, a factual business-match reason, and a public-contact
status. Mark social, map, trade-summary, and deep person-contact fields
`未核验` unless the user explicitly requests them. After 10 candidates, ask
`是否继续扩展至 30 家或 50 家？`.

Do not create a full graph, run Audit, or export Markdown in this path. The
candidate pool is not a recommendation, formal development list, or purchase
intent conclusion. Do not promote a search summary into a Claim.

For a new customer-development request, first respond in at most four short
user-facing lines: `我理解你卖的是`、`本次优先找`、`本次不纳入`、`判断依据将重点看`.
Ask at most one to three short questions only when an answer would reverse the
customer direction. When ambiguity remains, return at most three to five
direction samples and await confirmation. Competitors, brands, manufacturers,
and reference websites are search or market references by default, not
automatic prospects.

## Capability and Formal Delivery Gates

Run or emulate `scripts/preflight_capabilities.py --require-formal-research`
only before an explicit formal batch public-source route. It requires
`search.web` plus `source.open`, `browser.render`, or `document.extract`. A
recorded `web__run` 404 or timeout blocks that Codex adapter only: do not retry
the 同一失败适配器 and do not substitute shell/curl search. Before concluding
that the host has no Web capability, check the 宿主实际暴露的 native providers.
For a fast snapshot, an unavailable provider degrades to another exposed native
provider, user-provided material, or a query plan; it does not create a partial
formal graph. A formal route still stops when the completed host capability
inventory has no usable search plus source-opening path. Record only host
operations actually used.

Before a formal validator in real-business UAT, run
`scripts/precheck_superleads_uat_input.py --route bulk_customer_development
--graph <graph> --format json`. It checks source-literal anchors, contact
association, and enum values; it does not replace the formal validator. For a
real-business UAT, build the runtime package, initialize
`scripts/measure_superleads_uat.py` in a durable UTC-named
`.plugin-eval/manual/uat-runs/` directory, record each original gate result,
finalize, and verify both the completed bundle and a copied bundle. A `/tmp`
run can retain a failed diagnostic but cannot establish portable formal success.

An explicit formal request reads the matching files under
`shared/internal-stages/` in dependency order. Strict review and audit apply
only to formal verification, contact ownership verification, a contactable
list, or a standard development list.

## Composite Tasks

Use `composite-task-routing.md` as the single authority for parent/subtask
creation, dependencies, parallel boundaries, evidence isolation, and partial
delivery. Do not duplicate or override that policy here.

Show nontechnical status at actual phase boundaries. State scope, completed
query groups, candidate or opened-source counts, supported facts, pending
items, restricted sources, and unexecuted work. If no live status capability
exists, include the same summary in final delivery without claiming real-time
execution or exposing internal Skill names, run IDs, graph, Claim, or Audit.
The parent report separates scope, customer-background results, market results,
each subtask's restricted/pending/unexecuted items, and source/check time.
Never state that a customer is worth developing, should be prioritized, will
buy, or that a market is worth entering.

## Materials, Output, and Hard Constraints

Classify material as published-source copy, user business dataset,
correspondence export, user-authored note, visual reference, connected inbound
correspondence, or unknown. Product requirements belong in the Brief; pasted
company/contact material is a clue, not a formal fact. If a file is ambiguous,
use `user_business_dataset` or `unknown` and ask only whether it is original
public/other-party material or the user's historical data.

When formal source capability is blocked, organize user material as `资料初审`.
It does not replace public-source research and must not create a candidate pool
or formal report. With explicit approved `mail.read`, capture only inbound mail
in the requested folder, label, time, and filter scope. Never send, reply,
mark read, move, delete, archive, or scan mail by default; without `mail.read`,
request EML/PDF/mail export.

Only terminal delivery appends the shared support and safety footer. Progress
and standalone clarifications do not. A user requesting a chat-readable formal
report must use the unified Markdown delivery layer:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route auto --output report.md --format json
```

Do not hand-render a workbook as a substitute Markdown report, relabel internal
signal statuses as `依据状态`, or claim successful formal export without a saved
graph and a successful exporter result. A formal bulk report starts with
`# 批量客户开发` and includes `发现候选池样表（候选池不是正式开发名单）`.
The claimed Markdown must be exactly the file written by the exporter for the
claimed graph; do not post-process it while retaining an `ok=true` claim.

Do not expose internal graph, Claim, EvidenceCard, SearchLog, rule IDs, eval
names, local paths, or artifact hashes to users. Do not import old industry
defaults or assume ICP, country, company size, channel, platform, commercial
model, product, application, role, exclusion, or customer boundary. Keep weak
evidence labeled rather than deleting it. Native search permits only initial
search capability; source opening requires an actual HTTP(S) URL, source ID,
verbatim text, and locator. Record every source capability actually used and
never use a missing rendering, document, image, or mail capability as formal
support. A shell reader may separately open a public source only after a
recorded successful read-only GET; never use it for logged-in, private, or
restricted pages. Record one canonical lowercase ASCII platform ID and reject
private or legacy numeric IP source paths.
