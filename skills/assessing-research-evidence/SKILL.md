---
name: assessing-research-evidence
description: "Convert Superleads Observations into Claims and ClaimEvidence, keep Hypotheses separate, and create Assessments whose qualification basis cites Claims only. Use after source and contact collection when leads need tiering into 重点开发, 推荐跟进, 需人工核查, 暂不建议, or 排除."
---

# Assessing Research Evidence

## Purpose

Create evidence-backed Claims, business Hypotheses, and lead Assessments while preserving the boundary between facts and inferences.

## Required references

Read `../../shared/policies/claim-and-source-policy.md`, `../../shared/references/status-labels.md`, and `../../shared/schemas/research-graph.schema.json`.

## Workflow

1. Convert each source-supported fact into a Claim.
2. Link every Claim to ClaimEvidence and Observation.
3. Preserve conflicting observations as contradicting or contextual evidence.
4. Create Hypotheses only from basis Claim IDs and optional contact claim IDs.
5. Create Assessment using `basis_claim_ids` only for qualification.
6. Use `related_hypothesis_ids_for_outreach` only for development angle or next checks.

## Tiering

- 重点开发: high-trust support, clear match, clearer contact association, actionable angle, no serious identity conflict.
- 推荐跟进: at least one opened source, some product/type/market match, contact or reachable entry.
- 需人工核查: conflicts, unclear contact ownership, uncertain type, unavailable official site but valuable directory/fair lead, same-name uncertainty.
- 暂不建议/排除: clear mismatch, supplier/competitor when excluded, wrong country/channel, wrong entity, no development value.

## Hard constraints

Assessment must not use Hypothesis, Candidate, memory, search summary, or enrichment-only data as qualification evidence.
