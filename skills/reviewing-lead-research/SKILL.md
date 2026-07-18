---
name: reviewing-lead-research
description: "Independently review Superleads lead research for source support, contact ownership, Hypothesis/Claim separation, Assessment overcertainty, identity mismatch, and preserved conflicts. Use before standard delivery, or as self-review fallback when independent review is unavailable."
---

# Reviewing Lead Research

## Purpose

Perform semantic review before formal delivery. Check whether the research graph would mislead a sales user.

## Required references

Read `../../shared/policies/review-and-remediation-policy.md`, `../../shared/policies/contact-intelligence-policy.md`, and `../../shared/references/red-flags.md`.

## Review modes

Set `review_mode` to `independent`, `self_review_fallback`, or `not_run`.
For `independent`, create exactly one current passed `ReviewAttestation` for
the Run/Brief/Plan/review cycle. Use only opaque actor/session IDs; bind every
formally exported Assessment and its Entity; recompute the canonical
`reviewed_subject_hash` before signing off. A failed cycle cannot be reused.
Use `declared_separate_session`. It permits standard output only with the
required disclosure “本次复核由独立会话声明完成，未获得平台身份验证。”.
Different JSON IDs are declarations, not identity proof.

## Checklist

- Does every Claim have supporting Observation evidence?
- Are contact associations reasonable and sourced?
- Did any Hypothesis become a Claim or Assessment basis?
- Is the Assessment too certain for the evidence?
- Are company identities merged or assigned correctly?
- Are conflicts preserved rather than silently discarded?
- Are weak leads labeled instead of overstated?
- Does the retained user language agree with the current Brief's free-text
  direction contract, without importing a default ICP?
- Does the Plan cover each positive and exclusion rule with separate discovery
  and conflict checks?
- Does each positive Entity have a same-Run/Brief in-scope ScopeDecision with
  formal same-Entity evidence for every required rule?
- Did a competitor, brand, manufacturer, or reference seed enter the customer
  pool without current-task permission, or did an unknown become a match?
- Trace user wording -> current rule -> opened public excerpt -> Claim ->
  direction decision -> Assessment. Create a blocking finding for irrelevant
  Claim types, absent markers, hidden conflicts, or unresolved competitor/brand
  aliases promoted to customer.
- For any non-empty target geography, require its geography contract and
  inspect the same-Entity public source literal for the user-provided
  geography. Do not accept a search result, TLD, language, phone code, or
  ranking as location/market proof.

## Output

Create ReviewFinding records with severity, target artifact, issue, required fix, status, reviewer, review mode, and reviewed time.

## Delivery impact

Declared separate-session review and self-review fallback require disclosure.
This local deployment does not provide `full_review_package`. Not-run review
limits output to discovery candidate pools, initial samples, or pending tiers.
Default discovery does not require review unless the user asks for deep
verification or a standard development list.
