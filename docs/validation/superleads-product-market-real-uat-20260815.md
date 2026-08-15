# Superleads Product-Market Real UAT: Conditional CPSC GCC Path (2026-08-15)

## Release and Run

- Runtime release identity: `superleads` `0.1.18`, Git head `2aef6ecadb18c709f87b9f86565ba84f03e361f0`.
- UAT Run: `superleads-uat-20260815T095559Z`.
- Evidence directory: `.plugin-eval/manual/uat-runs/superleads-uat-20260815T095559Z`.
- Route: `product_outbound_market_analysis`.
- Scenario: ordinary electric kettle, China export-declaration premise, United States destination, certification module only.

## Fresh Source Evidence

The Run planned sources with `plan_product_market_sources.py`, then performed one
fresh `web__run` search and opened one public CPSC page. The search result at
rank 2 was used only as a source locator. The opened source was
[General Use Products: Certification and Testing | CPSC.gov](https://www.cpsc.gov/Business--Manufacturing/Testing-Certification/General-Use-Products-Certification-and-Testing).

The current Run records one `source.open` Observation using `web__run` and a
verified `codex_cli_web_run` adapter operation. Its URL, title, raw excerpt,
and locator match exactly: identity at `L2` and the conditional general-use
certificate text at `L42`. The pre-compiler validator accepted this
one-to-one binding; no other Observation can reuse the recorded open.

## Delivery Result

The compact input preserved two user-provided preliminary attributes (`220-240
V`, `1500 W`), one conditional CPSC GCC path, and one technical-document Gap.
The compiler, validator, audit, unified Markdown exporter, CSV workbook
exporter, user-visible validator, and claimed-path check all passed on their
first attempt. The delivery status is `ready_with_limitations`.

The claimed-path attestation has `ok=true`, `issue_count=0`, requested route
`product_outbound_market_analysis`, and only these caller-relative paths:

- `.plugin-eval/manual/uat-runs/superleads-uat-20260815T095559Z/compiled-market-graph.json`
- `.plugin-eval/manual/uat-runs/superleads-uat-20260815T095559Z/market-report.md`

The original evidence directory and an independent copied directory both pass
`measure_superleads_uat.py verify` with no verification issues.

## Protocol Result

`uat_metrics.json` reports:

- `formal_uat_protocol_status=passed`
- `first_pass_success=true`
- `repair_cycle_count=0`
- `git_unchanged=true`
- `portable_evidence=true`

## Scope Boundary

This is evidence of one opened CPSC source and its conditional GCC path only.
It does not determine final applicability to the electric-kettle model, product
classification, duties or taxes, compliance, clearance, logistics, or a
market-entry decision. Final model/SKU, electrical design, plug and cord,
materials, applicable rules, labels, test records, and any GCC scope still
need product-specific review.
