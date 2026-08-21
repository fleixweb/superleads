# Superleads Formal Delivery And UAT

Use this reference after `using-superleads` has selected a formal public-source
route or a real-business UAT. It contains deferred execution and delivery rules;
the entry Skill should not repeat them.

## Capability gate

Before formal customer development, customer background research, or
product-market analysis, first inventory the search and source-opening
operations actually exposed in the current session. When that inventory is
available, build a capability JSON and run
`scripts/preflight_capabilities.py --require-formal-research --input <capability-json>`.
When no inventory is available, do not run the script bare; use the existing
no-script path to inspect the host's actually exposed capabilities. A
`not_assessed` result is not a host-capability conclusion: do not lower the
delivery tier because of it or present it to the user as an environment
limitation. The current Run must have `search.web` and at least one of
`source.open`, `browser.render`, or `document.extract`. If blocked, stop with:

`本轮环境无法联网检索并打开可记录来源，不能完成 Superleads 正式外贸研究。请切换到具备 Web Search 和来源打开能力的 Agent/环境后重试。若只需整理已有资料，可以继续，但那不是市场分析或客户开发报告。`

Do not substitute a source plan, discovery pool, or formal report when this gate
fails. User-provided files may be handled only as `资料初审`, explicitly labeled
as not replacing public-source research.

For Codex CLI native search, inspect only the currently visible capability and
record actual operation results. A search summary is not a Source or Claim.
Source opening requires an HTTP(S) URL, source identifier, verbatim text, and a
locator obtained in the current Run. A shell reader may perform a read-only GET
only after a successful recorded read; it is not search capability and must not
be used for private, logged-in, or restricted pages.

Keep search, source opening, rendering, document extraction, image inspection,
and mail reading as separate host capability records. Record every capability
actually used in the Run. Platform IDs are lowercase ASCII letters, digits, and
underscores only; reject private or legacy numeric-IP source forms and block
non-global DNS results and redirect targets.

## L2 bulk admission

For 深度核验、联系人归属核验 or `标准开发名单`, admit a bulk candidate only by
the current, reviewable object-and-evidence chain: the entity resolves without
an unresolved name/domain/address conflict; an actually opened source supports
the current business signal; a public contact entry can be attributed to that
entity; and the current graph has a reviewable ScopeDecision, Assessment,
Review, and Audit chain. This is the L2 threshold. It means the candidate fits
the current direction and its source chain is reviewable; it does not claim
purchase intent, commercial value, or conversion likelihood.

The following are not admission conditions: whether the website lists an exact
part number, whether a public page provides 公开可证的进口或海关角色, whether the
company will purchase, or any customer-value ranking. Dealers commonly keep
OEM part numbers in internal parts systems, and public pages normally do not
prove the legal import role. Missing either item is a `接洽核实项`: keep it as a
pending question and do not downgrade, exclude, or call a candidate unqualified
for that reason alone.

## L2 completeness requirements

For every candidate in the deep-verification list, social, map, and third-
party trade-summary collection is mandatory, as is public contact-intelligence
collection and attribution review. Read
`../internal-stages/collecting-contact-intelligence.md` and
`../policies/contact-intelligence-policy.md` before that work. Use a finite
budget, deduplicate the same canonical/final URL within the Run, and retain the
existing five `collection_status` values. A search summary may point to a
candidate page but does not make its visible person, title, phone, address, or
business scene an observed fact. When budget is exhausted or a source is
restricted, record that outcome; do not leave the category blank or portray it
as completed.

Extract contact intelligence only from opened-source Observations and never
guess email formats. ContactPoint records the literal and its source
Observation; ContactClaim requires context that attributes the value to an
entity, person, department, role, or source section. Keep useful but unclear
ownership in UnassignedContactLead. Preserve the existing three user-visible
states: `ready`, `export_with_source_note`, and
`needs_manual_association_review`; ready attribution evidence must name the
resolved entity. Cross-entity mismatches and source-less contacts are never
exportable. This is recall-oriented collection under the existing safety
contract, not a relaxation of it.

When no candidate clears the actual evidence-chain threshold, explain which
chain element is missing and what range was completed. Do not label ordinary
public-information limits as disqualification. Use this user-facing shape:

```text
本次深度核验尚未形成可正式交付的名单。已完成：{已完成范围}；仍缺：{实际缺少的主体、已打开来源、联系归属或审核链条}。
官网未出现精确料号、或未公开进口身份属于首次接洽时核实的项目，不等同于候选不合格。
可继续补充待确认项的公开核验或公开信号；也可依据已打开的业务来源在首次接洽时向对方确认料号适配和实际采购角色。
```

Keep the existing downgrade disclosure and do not use the `标准开发名单` name
when the formal chain did not complete.

## Real-business UAT gates

Before the formal validator, under `../policies/cross-platform-rules.md`, select
the host-provided runtime interpreter and invoke
`scripts/precheck_superleads_uat_input.py` with
`--route <route> --graph <graph> --format json`.

This read-only precheck covers literal source anchors, contact association,
enum values, and product-attribute projection. It does not replace validation,
audit, search, source opening, or evidence review. Product-market compact notes
use it twice: once with `--notes <notes>` before compilation and once on the
compiled graph.

For a timed UAT, initialize `scripts/measure_superleads_uat.py` in a dedicated
`/tmp` run directory immediately before one route and finalize it before the
next route. Record actual preflight, input precheck, compiler, validator, audit,
Markdown export, workbook export, user-visible, and claimed-path gate results.
Product-market compilation requires the ordered gates
`input_precheck_notes -> compiler -> input_precheck_graph`; `compiler` is
required. Record failed attempts with their failure class, close active timing
intervals around waits, and never call a repaired run first-pass success or
estimate tokens when the host did not expose them.

## Formal Markdown delivery

For a chat-readable report, always use the unified exporter after validation and
audit. Under `../policies/cross-platform-rules.md`, select the host-provided
runtime interpreter and invoke `scripts/export_superleads_markdown.py` with
`graph.json --route auto --output report.md --format json`.

For workbook delivery, use `export_workbook.py --format auto` (or omit the
format) unless the user explicitly requires XLSX. Auto produces UTF-8-SIG CSV
when the workbook component is unavailable; an explicit `--format xlsx` request
must fail instead of silently changing the requested file type. When validator
dependencies are unavailable, do not search for or borrow another application's
interpreter: use the no-script path and mark `本环境未运行确定性校验`.

A user who 直接要求 Excel after deep verification, or later requests a format
change, workbook rename, or re-export, is continuing the same formal delivery
chain rather than starting an independent table-generation task. 不得使用其他技能、工具、脚本或代码手工构造替代工作簿，也不得使用自定义工作表、列或分区名称模拟正式交付物。`标准开发名单` may be named only after the current graph, validation,
audit, and unified exporter have all completed successfully.

When that chain cannot complete, respond positively and truthfully: state which
step is missing, what range has been completed, and how the user can continue.
Provide a source-status, unknown, and pending-item 对话内工作表 when useful; mark
`本环境未运行确定性校验` whenever that check did not run. Do not create a file,
call the result `标准开发名单`, or make it look like a formal delivery in this
fallback path.

Do not hand-render Markdown from workbook/CSV sheets. Do not manually convert
workbook/CSV rows, rename internal status columns, or fabricate a report when
the exporter fails. Formal delivery requires a saved graph JSON path and a
successful exporter JSON result. With only search notes, source snippets, or a
handwritten table, use the label `research draft` instead of formal delivery. A
bulk report starts with `# 批量客户开发`; its audited delivery status selects the
table projection. `initial_lead_list` includes
`发现候选池样表（候选池不是正式开发名单）` plus `分区`, `业务相关性`, and
`依据状态`; `standard_development_list` includes the standard workbook's
`客户信息总表`, `联系方式汇总`, `公开信息与待核查事项`, `官网与来源链接`,
`待核查事项`, and `风险与说明`. Never use the initial candidate-pool mapping for
a standard list.

The claimed Markdown path must be the exact file produced by the exporter for
the claimed graph. For verification, rerun the exporter from that graph and
compare the claimed file byte-for-byte/text-for-text; post-processing invalidates
the claim even if an earlier exporter run returned `ok=true`.

Never expose graph names, Claim, EvidenceCard, SearchLog, rule IDs, eval names,
local paths, hashes, or internal public-signal statuses such as `已观察`,
`未检索`, `主体待确认`, `已观察；需确认`, or `已观察；来源受限`.

## Route boundaries

- Bulk customer development: candidate customer pool, public signals, contacts,
  coverage, and pending checks; never a ranked recommendation list.
- Customer background research: one specified company, brand, domain, or
  material anchor; do not import unrelated bulk candidates.
- Product outbound market analysis: product market/access matrix only; never
  customer lists, target-customer recommendations, or market-entry judgments.

Keep weak evidence as labeled candidates rather than silently discarding it.
Search snippets, prior Skill summaries, Source Packs, and model summaries are
leads for collection only; they cannot become Claims or user-visible facts.
