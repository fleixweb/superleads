---
name: assessing-research-evidence
description: "Convert Superleads Observations into Claims and ClaimEvidence, keep Hypotheses separate, and create Assessments whose qualification basis cites Claims only. Use after source and contact collection when leads need tiering into 重点开发, 推荐跟进, 需人工核查, 暂不建议, or 排除."
---

# Assessing Research Evidence

## Purpose

Default responsibility: classify business relevance, summarize public signals, and separate facts from inferences. Create evidence-backed Claims and formal Assessments only for explicit deep-check tasks.

## Required references

Read `../../shared/policies/claim-and-source-policy.md`, `../../shared/references/status-labels.md`, and `../../shared/schemas/research-graph.schema.json`.

## Workflow

1. For default discovery, classify each Candidate as `directly_related`,
   `possibly_related`, `explicitly_excluded_or_unrelated`,
   `identity_pending`, or `insufficient_information`.
2. Summarize public signals with `observed`, `not_observed`,
   `not_searched`, `identity_pending`, or `source_restricted`.
3. Preserve conflicting observations and exclusion hits instead of deleting
   the Candidate.
4. Only for explicit deep-check tasks, convert each source-supported fact into
   a Claim and link it to ClaimEvidence and Observation.
5. Create Hypotheses only from basis Claim IDs and optional contact claim IDs.
6. Create formal Assessment using `basis_claim_ids` only when standard
   delivery or another explicit deep-check task requires qualification.

## Direction before positive assessment

Evidence validity and current customer direction are separate checks. For a
new customer-development Brief, create a ScopeDecision for the same Run,
Brief, contract, and Entity before assigning `重点开发` or `推荐跟进`. Evaluate
every current free-text selection and exclusion rule. `supported_match` and
`supported_conflict` need same-Entity Claims with usable formal support;
`not_observed` means only the reviewed material did not show a signal;
`unknown` is not a match.

Every required positive rule must be supported. A supported blocking exclusion
or an unknown rule configured to block positives prevents a positive
Assessment. A provisional direction can produce only direction samples or
manual checks. Contact completeness, a similar keyword, user material,
mail.read, image.inspect, Candidate data, and Hypotheses cannot compensate.

For every reviewed Observation, classify its same-Entity formal Claims as
supports, conflicts, or irrelevant. Supports/conflicts require an allowed
generic Claim type and a current-rule marker visible in the supporting excerpt.
Do not hide a reviewed conflict as `not_observed`; each required positive rule
needs a classified supports Claim that also appears in Assessment basis.

## Formal source gate

Formal ClaimEvidence uses either a public HTTP(S) Source with visible excerpt or a `published_source_copy`. The latter is limited to hashed document/spreadsheet Sources and `document.extract` Observations with safe, same-hash page/section/sheet/range locators. `user_business_dataset`, `correspondence_export`, `manual_input`, pasted chat text, visual/OCR output, search snippets, enrichment, and translated-only evidence without its same-Entity original root cannot support qualification or Assessment basis.

`mail.read` and connected inbound correspondence are also excluded from formal Claim and Assessment basis. Mail content can prioritize an Inquiry or express what the sender wrote, but never establishes buyer qualification, purchase authority, company fact, current demand, trademark ownership, or a positive Assessment without independent eligible evidence.

## Default discovery relevance

- directly_related: observed business, service, channel, or application signal
  directly fits the current task boundary.
- possibly_related: useful public clue exists but the exact business relation
  is still unconfirmed.
- explicitly_excluded_or_unrelated: opened material shows a wrong market,
  wrong industry, competitor/manufacturer conflict, or another explicit
  exclusion.
- identity_pending: same-name, domain, address, trade record, or contact
  ownership cannot be safely bound to one entity.
- insufficient_information: discovered clue exists but current public material
  is too thin.

For `directly_related`, `possibly_related`, and
`explicitly_excluded_or_unrelated`, set `signal_summary.business_match.status`
to `observed` and add at least one non-empty business summary with a source
label or safe public HTTP(S) URL. Keep `business_relevance_basis` as the
business-language explanation for this Brief, not as a replacement for the
observed signal. `identity_pending` and `insufficient_information` may instead
preserve matching ambiguity, unknowns, and source gaps; do not manufacture an
observed signal or require Claim/ClaimEvidence merely to keep the Candidate.

## Tiering for deep-check work

- 重点开发: high-trust support, clear match, clearer contact association, actionable angle, no serious identity conflict.
- 推荐跟进: at least one opened source, some product/type/market match, contact or reachable entry.
- 需人工核查: conflicts, unclear contact ownership, uncertain type, unavailable official site but valuable directory/fair lead, same-name uncertainty.
- 暂不建议/排除: clear mismatch, supplier/competitor when excluded, wrong country/channel, wrong entity, no development value.

## Hard constraints

Assessment must not use Hypothesis, Candidate, memory, search summary, or enrichment-only data as qualification evidence. Default discovery relevance is not a purchase-intent or commercial-value judgment.
