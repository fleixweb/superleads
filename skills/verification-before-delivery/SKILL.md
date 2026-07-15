---
name: verification-before-delivery
description: "Run deterministic Superleads delivery checks before export: validate the research graph, audit contact sources and ownership, check ClaimEvidence, close ReviewFindings, verify graph hash freshness, and choose needs_correction, initial_lead_list, standard_development_list, or full_review_package."
---

# Verification Before Delivery

## Purpose

Perform deterministic checks immediately before user delivery.

## Required scripts and schemas

Use `../../scripts/validate_research_graph.py`, `../../scripts/audit_delivery.py`, `../../shared/schemas/research-graph.schema.json`, and `../../shared/schemas/delivery-manifest.schema.json`.

## Workflow

1. Validate graph ID closure and artifact boundaries.
2. Audit contact source and association evidence.
3. Confirm Claims have ClaimEvidence and blocked/login-wall pages do not support facts.
4. Confirm every critical/major ReviewFinding is `verified_fixed`. Use `accepted_with_disclosure` only for non-misleading weak evidence or minor limitations.
5. Compute graph hash and ensure `current_graph_hash == audit_graph_hash` before export.
6. Set internal delivery status: `needs_correction`, `initial_lead_list`, `standard_development_list`, or `full_review_package`.

For a user-provided document or spreadsheet, audit the Source/Observation pair through the same purpose-aware source gate used by validation and export. Only `published_source_copy` may support a Claim or ready contact. `user_business_dataset` and `correspondence_export` can only produce `export_with_source_note` contacts with explicit Entity association. Verify SHA-256 format, safe filename, extraction capability, matching `snapshot_ref`, and locator before any allowed use. This validates graph metadata and linkage; it does not re-hash a binary that the run has not retained.

For `inquiry_followup_queue`, use the Inquiry-specific audit instead of treating it as a standard development list. Require inbound direction, qualified `mail.read` or original correspondence-export source, hash/snapshot/excerpt linkage, and bounded user-visible excerpts. Do not require a complete Assessment to process an Inquiry, but do not let its mail content enter formal Claim or Assessment gates.

For a new customer-development Brief, additionally require the current
free-text customer selection contract, Plan coverage of all its rules, and an
in-scope ScopeDecision for every positive Entity. The decision must match the
current Run, Brief, contract, and Entity; every required positive rule needs
formal same-Entity support. A supported blocking exclusion, a blocking unknown,
or a provisional direction stops standard and full delivery. `needs_confirmation`,
`out_of_scope`, and `reference_only` remain outside the customer and contact
main tables. Mail, images, OCR, user material, Candidates, and contacts cannot
bypass this gate.

Also block formal output for `task_mode=unknown`, an absent/empty contract,
all-optional positive rules, or sample-first work. Check that classifications
cover every reviewed formal Claim, permitted Claim types and markers match the
source excerpt, and every required positive support is in Assessment basis.
Material extraction without a complete current direction remains initial only;
unresolved competitor aliases remain identity-review blockers.

For formal single-company analysis, verify the current user statement and the
bound company identifier/material reference resolve to exactly the exported
Entity. For existing-table enrichment, verify every exported Entity maps to a
row/cell Observation in the bound user-provided spreadsheet. Neither output is
presented as `符合本次方向`; use the corresponding analysis or original-table
result label.

## User labels

Map statuses to: 需修正后交付, 初筛客户名单, 标准开发名单, 完整核查版, 询盘待办.

## Hard constraints

Do not formally export when status is `needs_correction`. Initial lead list may contain weak evidence only if status notes are visible.
