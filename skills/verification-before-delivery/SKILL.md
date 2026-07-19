---
name: verification-before-delivery
description: "Use when a Superleads candidate pool, deep check, or standard list needs deterministic pre-delivery validation."
---

# Verification Before Delivery

## Purpose

Perform deterministic checks immediately before user delivery. Use the light branch for default discovery and the strict branch for formal delivery.

Default discovery uses only its initial-candidate-pool validation; strict
Claim, Assessment, Review, Audit, and Manifest checks belong to explicitly
requested deep-check or standard-list delivery.

## Required scripts and schemas

Use `../../scripts/validate_research_graph.py`, `../../scripts/audit_delivery.py`, `../../shared/schemas/research-graph.schema.json`, and `../../shared/schemas/delivery-manifest.schema.json`.

## Workflow

1. Always validate graph ID closure, artifact boundaries, guessed-contact blocking, identity mismatch, and other deterministic anti-fabrication rules.
2. For default discovery, do not require Claim, Assessment, ScopeDecision, ReviewAttestation, or Audit completeness merely to deliver a candidate pool.
3. For explicit deep-check work, audit contact source and association evidence, formal ClaimEvidence, ReviewFinding closure, and graph-hash freshness.
4. Set internal delivery status: `needs_correction`, `initial_lead_list`, `standard_development_list`, or `inquiry_followup_queue`.

For independent formal delivery, recompute and match the current canonical
`reviewed_subject_hash`; require exactly one passed current ReviewAttestation
whose Run/Brief/Plan/review cycle and formal Entity/Assessment coverage match.
Require distinct executor/reviewer opaque actor and session IDs. Verify Audit
and DeliveryManifest reference the same attestation, hash, provenance level,
and cycle. `declared_separate_session` requires the disclosure
“本次复核由独立会话声明完成，未获得平台身份验证。”. This local deployment does
not provide `full_review_package`. Never treat different JSON IDs as proof of
real identity independence.

For a user-provided document or spreadsheet, audit the Source/Observation pair through the same purpose-aware source gate used by validation and export. Only `published_source_copy` may support a Claim or ready contact. `user_business_dataset` and `correspondence_export` can only produce `export_with_source_note` contacts with explicit Entity association. Verify SHA-256 format, safe filename, extraction capability, matching `snapshot_ref`, and locator before any allowed use. This validates graph metadata and linkage; it does not re-hash a binary that the run has not retained.

For `inquiry_followup_queue`, use the Inquiry-specific audit instead of treating it as a standard development list. Require inbound direction, qualified `mail.read` or original correspondence-export source, hash/snapshot/excerpt linkage, and bounded user-visible excerpts. Do not require a complete Assessment to process an Inquiry, but do not let its mail content enter formal Claim or Assessment gates.

For a new customer-development Brief, additionally require the current
free-text customer selection contract, Plan coverage of all its rules, and an
in-scope ScopeDecision for every positive Entity. The decision must match the
current Run, Brief, contract, and Entity; every required positive rule needs
formal same-Entity support. A supported blocking exclusion, a blocking unknown,
or a provisional direction stops standard delivery. `needs_confirmation`,
`out_of_scope`, and `reference_only` remain outside the customer and contact
main tables. Mail, images, OCR, user material, Candidates, and contacts cannot
bypass this gate.

Also block formal output for `task_mode=unknown`, an absent/empty contract,
all-optional positive rules, or sample-first work. Check that classifications
cover every reviewed formal Claim, permitted Claim types and markers match the
source excerpt, and every required positive support is in Assessment basis.
Material extraction without a complete current direction remains initial only;
unresolved competitor aliases remain identity-review blockers.

For every non-empty target geography, first require its geography contract;
then verify the linked Plan query groups and that each formal geography support
is a same-Entity eligible public Claim with the user's literal visible in the
source excerpt. Search results, domains, language, phone prefixes, and query
ranks do not satisfy this gate.

For formal single-company analysis, verify the current user statement and the
bound company identifier/material reference resolve to exactly the exported
Entity. For existing-table enrichment, verify every exported Entity maps to a
row/cell Observation in the bound user-provided spreadsheet. Neither output is
presented as `符合本次方向`; use the corresponding analysis or original-table
result label.

## User labels

Map statuses to: 需修正后交付, 发现候选池, 标准开发名单, 询盘待办.

## Hard constraints

Do not export when status is `needs_correction`. Discovery candidate pools may contain weak evidence only if statuses, unknowns, and restrictions remain visible.
