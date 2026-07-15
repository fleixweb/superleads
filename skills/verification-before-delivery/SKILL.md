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

## User labels

Map statuses to: 需修正后交付, 初筛客户名单, 标准开发名单, 完整核查版.

## Hard constraints

Do not formally export when status is `needs_correction`. Initial lead list may contain weak evidence only if status notes are visible.
