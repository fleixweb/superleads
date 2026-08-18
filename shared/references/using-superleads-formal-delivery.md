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

Do not hand-render Markdown from workbook/CSV sheets. Do not manually convert
workbook/CSV rows, rename internal status columns, or fabricate a report when
the exporter fails. Formal delivery requires a saved graph JSON path and a
successful exporter JSON result. With only search notes, source snippets, or a
handwritten table, use the label `research draft` instead of formal delivery. A
bulk report starts with `# 批量客户开发` and includes
`发现候选池样表（候选池不是正式开发名单）` plus `分区`, `业务相关性`, and
`依据状态` columns.

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
