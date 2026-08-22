# Batch Discovery Execution Rules

Read this reference only after `using-superleads` has determined that the user
made a concrete batch customer-discovery request. Do not read it for a bare
plugin activation, help, metadata, version, capability, feedback, or
material-triage request.

## Required References

Read `superleads-user-guidance.md` for terminal-delivery footer rules and
`user-intake.md` for batch minimum scope. Read
`../policies/tool-capability-policy.md`; its deterministic-validation dependency
rule at `tool-capability-policy.md:7` is mandatory before any recovery attempt:
不得运行时安装依赖、创建临时依赖目录或设置 `PYTHONPATH`，不得借用其他应用程序的 Python 环境、虚拟环境或解释器；缺少所需能力时走既有无脚本路径。 This prohibition
is inlined here and does not depend on waiting until availability affects the
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
宿主实际暴露的工具 and use one bounded, actual business search through an exposed
native provider; do not guess a Codex, ChatGPT Desktop, Claude, Hermes, or
WorkBuddy tool name, and do not make an empty capability probe first. Do not
retry the 同一失败适配器. A different provider may be tried only when it is already
present in the current-session host tool inventory; otherwise follow
`../policies/tool-capability-policy.md` to lower the delivery tier. Use a run-wide first batch
target of 10. Per-query-group
limits must not add up beyond that run-wide cap. Cover only website, directory,
document, and search-result sources. Each candidate needs a public website or
search-result reference, a factual business-match reason, and a public-contact
status. Mark social, map, trade-summary, and deep person-contact fields
`未核验` unless the user explicitly requests them.

At every discovery-snapshot delivery boundary with at least ten candidates,
show this non-blocking next-step menu. It is a statement of available paths,
not a request to select a number or an instruction to wait for a reply:

```
## 下一步可选

- 继续扩展（可指定 30 / 50 / 100 家，或直接说数量）
- 换搜索组合再找一批（换产品词 / 换客户类型，国家不变）
- 对上述名单做深度核验 → 标准开发名单（含社媒 / 地图 / 贸易记录 + 联系人归属核验；交付表格文件 + 配套报告；较慢；产量降、耗时增；可分批产出）
- 只补社媒 / 地图 / 贸易记录信号（不做主体与联系人核验；较快，仍属候选池，不升级为已验证）
- 选 1 家做单一客户背调
```

Show the expansion line only while `expansion_scale_chosen` is unset for the
current Run. Once the user chooses a quantity, hide that line permanently for
the Run; do not replace it with a later fixed-quantity prompt. The other four
lines remain available. `深度核验` applies to the whole list rather than a
user-selected subset: L1 does not rank candidate value, and asking the user to
pick five to ten subjects would force unsupported intuitive ranking. State the
lower output and higher time cost, allow batched delivery, and retain unverified
or source-restricted rows as such. Reuse only the existing formal-route terms
`深度核验`, `标准开发名单`, and `联系人归属核验`; do not add trigger words.

`补社媒 / 地图 / 贸易记录信号` is an explicit L1 supplement only: it updates
bounded public-signal collection states and does not perform entity or contact
association verification. The L1 supplement keeps only the status rules in
`default-discovery-reference.md`; it is not a substitute for deep verification.

## Deep-Verification Completeness

For `深度核验` / `标准开发名单`, collecting social, map, and third-party trade
summaries for the entire list is mandatory L2 work, alongside entity and
contact association review. Give every category a finite budget, deduplicate
the same canonical/final URL within the Run, and record the existing five
`collection_status` states truthfully. A search summary's person, title,
phone, address, or business context is still not an observed fact. When the
budget is exhausted or a source is restricted, mark that outcome truthfully;
do not leave a category blank or present it as completed.

The full-list contact-intelligence collection and attribution review is also
mandatory L2 work. Read `../internal-stages/collecting-contact-intelligence.md`
and `../policies/contact-intelligence-policy.md`: extract only from opened
Observations, never guess email formats, keep ContactPoint literals separate
from ContactClaim attribution, and retain useful ambiguous values as
UnassignedContactLead. Preserve the existing ready / source-note / manual-
association export states. Cross-entity mismatches and source-less contacts
are never exportable. These requirements raise recall through sourced work;
they do not lower contact safety thresholds.

`expansion_scale_chosen` accepts a user-specified positive integer from 1 to
500. The ceiling bounds one Run's finite execution state; it is not a market
coverage limit. If the target cannot be reached without relaxing current
business-relevance rules, state the shortfall and use only observed coverage
signals: `本组合已产出 N 家，距目标 M 家还差 M-N 家；继续检索的新增主体与已有池重合度约 X%，接近该组合当前公开检索可见范围。要补足到 M 家，建议换搜索组合（换产品词 / 换客户类型）。` Fill `N` and `X` only from this Run's recorded coverage; do not invent them. Point to the recorded `尚未覆盖的组合` hints where present. Do not pad the result by lowering relevance, and do not call the combination exhausted, complete, or globally exhaustive.

For `standard_development_list`, the 标准开发名单的默认主产物 is the official
workbook, accompanied by a 配套 Markdown 报告. Generate both from the same
audited graph through `scripts/export_workbook.py --mode standard --format
auto --manifest <manifest>` and `scripts/export_superleads_markdown.py --route
bulk_customer_development`; do not hand-build or substitute either artifact.
List the workbook filename and type separately from the Markdown report
filename and type. If workbook output falls back to UTF-8-SIG CSV, describe it
only as a CSV table in business language. `initial_lead_list` discovery-pool
delivery is unchanged.

File output still depends on the current host's actually available file-write
capability. If it is absent, deliver through the existing in-chat fallback,
state only the affected delivery tier or capability gap, and never promise an
unavailable file. If validation, audit, or export cannot run, describe the
completed evidence range and continuation path without naming the result
`标准开发名单`. Disclose `本环境未运行确定性校验` only when no deterministic
script validation ran. When the core business-rule validation completed but
only the supplemental structure check did not run, use the accurate disclosure
`本次已完成核心业务规则校验；补充结构检查未运行。` Do not use another skill, tool,
script, or custom sheet structure to simulate a formal deliverable. A later
format conversion, workbook rename, or re-export is a continuation of the same
delivery chain, not an independent table-generation task.

For honest coverage and omitted-combination wording, follow
`default-discovery-reference.md` rather than promising an exhaustive result.

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

Before an explicit formal batch public-source route, first inventory the
search and source-opening operations actually exposed in the current session.
When that inventory is available, build a capability JSON and run or emulate
`scripts/preflight_capabilities.py --require-formal-research --input <capability-json>`.
When no inventory is available, do not run the script bare; use the existing
no-script path to inspect the host's actually exposed capabilities. A
`not_assessed` result is not a host-capability conclusion: do not lower the
delivery tier because of it or present it to the user as an environment
limitation. Formal research requires `search.web` plus `source.open`,
`browser.render`, or `document.extract`. A
recorded `web__run` 404 or timeout blocks that Codex adapter only: do not retry
the 同一失败适配器 and do not substitute shell/curl search. Before concluding
that the host has no Web capability, follow `../policies/tool-capability-policy.md`:
check current-session exposed operations and use an already exposed different
native operation for the next actual search or source opening. For a fast
snapshot, no remaining provider degrades to user-provided material or a bounded
query plan; it does not create a partial formal graph. A formal route still
stops when the completed host capability inventory has no usable search plus
source-opening path. Record only host operations actually used.

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
list, or a standard development list. 内部阶段文件不得枚举、不得翻译成用户可见的功能清单，也不得用于回答帮助或能力类问题。

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
report must use the unified Markdown delivery layer. Under
`../policies/cross-platform-rules.md`, select the host-provided runtime
interpreter and invoke `scripts/export_superleads_markdown.py` with
`graph.json --route auto --output report.md --format json`.

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
