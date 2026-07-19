---
name: resolving-company-identity
description: "Use when Superleads research has company, brand, domain, branch, or legal-entity identity conflicts."
---

# Resolving Company Identity

## Purpose

Analyze whether company names, brands, legal entities, domains, branches, dealers, and platform sellers refer to the same Entity or require split/manual review.

This is an on-demand identity/deep-check skill. Default discovery may retain
`identity_pending` Candidates without resolving them into Entity records.

## Required references

Read `../../shared/policies/claim-and-source-policy.md` and `../../shared/references/red-flags.md` before deciding whether identity ambiguity blocks delivery.

## Triggers

Use this skill for similar names, brand/legal entity differences, site conflicts, email-domain mismatch, multi-country branches, franchise/dealer ambiguity, directory/official source conflict, acquisition, rename, or holding-company relations.

## Workflow

1. List each identity signal and its Observation/ClaimEvidence.
2. Separate official source evidence from third-party or contextual hints.
3. Propose `EntityRelationship` records such as same_as, brand_of, legal_entity_of, branch_of, dealer_of, formerly_known_as, acquired_by, unrelated_same_name, or needs_manual_review.
4. Recommend merge, split, or manual check with confidence and rationale.
5. Route unresolved major conflicts to review and verification.

## Hard constraints

Do not use `entity.dedupe`, normalized domain similarity, or name similarity alone as final identity proof.

For a formal single-company or existing-table exception, an `entity_literal`
must be verbatim in the bound user material and exactly match the resolved
Entity name/legal name or domain. A brand, holding-company name, old name,
partial name, or similar-looking identifier must remain an identity-resolution
or manual-review task until evidence establishes the relation.

`normalize_entities.py` emits an external identity-review report and a
schema-compatible graph copy. Its normalized names/domains and duplicate flags
are routing hints only; do not write them into Entity records or treat them as
an EntityRelationship, Claim, merge, split, or delivery authorization.
