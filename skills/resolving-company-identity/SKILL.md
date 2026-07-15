---
name: resolving-company-identity
description: "Resolve Superleads company, brand, legal entity, domain, branch, dealer, platform seller, acquisition, rename, and ownership conflicts. Use when names are similar, domains conflict, email domains mismatch, sources disagree, or entity merge/split decisions need evidence-backed handling."
---

# Resolving Company Identity

## Purpose

Analyze whether company names, brands, legal entities, domains, branches, dealers, and platform sellers refer to the same Entity or require split/manual review.

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
