# Targeting and Scope Policy

## Purpose

Keep an evidence-correct record from becoming a business-direction error. The
current Brief owns one free-text customer selection contract. It is not a
product taxonomy, ICP library, market profile, or cross-Run memory.

## Default discovery relevance

Before formal targeting, default discovery may classify Candidates only by
business relevance to this task:

- `directly_related`
- `possibly_related`
- `explicitly_excluded_or_unrelated`
- `identity_pending`
- `insufficient_information`

This classification is about current business-boundary relevance only. It is
not a purchase-intent, commercial-value, or quality judgment.

`directly_related`, `possibly_related`, and
`explicitly_excluded_or_unrelated` require an `observed` `business_match`
signal with a non-empty summary and a traceable source label or safe public
HTTP(S) URL. The free-text `business_relevance_basis` records why that observed
signal fits or conflicts with this Brief; it is not evidence by itself.
`identity_pending` and `insufficient_information` preserve conflicts, unknowns,
or source gaps without manufacturing a business observation. Neither state is
a reason to silently delete a discovered Candidate or to require formal
Claim/ClaimEvidence work.

## Current-brief contract

For new customer development, `customer_selection_contract` records the
user's wording, offer definition, commercial positioning, application
boundary, desired counterparty, exclusions, and handling of competitor or
brand references. Its business fields and every rule's search hints are free
text. The only fixed values are process controls and `scope_state`:
`explicit`, `inferred_low_risk`, or `provisional`.

Each selection rule says what public signal is needed for a positive result.
Each exclusion rule says what public signal should block it. A missing signal
is not proof of absence. Search hints discover material only; formal inclusion
or exclusion needs a same-Entity Claim with usable formal ClaimEvidence.

Each current rule also declares the permitted generic Claim types and its
visible evidence/conflict markers. These are derived from the current Brief
and Plan, not from a product, industry, application, geography, brand, or
channel dictionary. A Claim supports a rule only if its type is permitted and
the selected marker is present in the supporting public excerpt.

## Geography In The Current Contract

For every new customer-development Brief with any non-empty
`target_country_or_region` literal, the same `customer_selection_contract`
must carry a non-null `geography_contract`: included and excluded geography
literals, a natural-language admission definition, linked selection/exclusion
rule IDs, allowed generic Claim types, and whether a first-party source is
required. The included literals must equal the Brief target's normalized set;
the original user literals remain in the Brief. The Plan records linked
geography query groups. A missing contract is a formal-delivery blocker, not a
reason to treat the task as global. No country list, TLD table, language
dictionary, phone-prefix rule, or default market profile is used.

A formal geography decision needs a same-Entity Claim supported by an eligible
public source whose excerpt contains the current Brief geography literal.
Search results, domains, language, phone codes, keyword matches, rank, and
Candidates do not prove location or market coverage. Whether an address,
service coverage, local branch, or channel coverage qualifies is defined only
by this Brief's admission definition and its linked rules.

## Interaction

First restate, in no more than four user-facing lines:

- 我理解你卖的是
- 本次优先找
- 本次不纳入
- 判断依据将重点看

Ask at most one to three short questions only when a different answer would
reverse the customer direction. When a critical ambiguity remains,
`scope_state=provisional`; provide only three to five 方向样本 and do not create
a standard formal list. A user who has already stated the boundary is
not asked again.

Names supplied as competitors, brands, original manufacturers, or other
references are `reference_only` by default. They may enter the customer pool
only when this Brief explicitly permits it; they still need all normal source,
Claim, fit, review, audit, and delivery gates.

## Scope decisions

`scope_decisions` records a traceable decision for the current Run, Brief, and
Entity (or an unresolved Candidate). It uses only process statuses:
`in_scope`, `out_of_scope`, `needs_confirmation`, and `reference_only`.
Candidate-only decisions can only remain `needs_confirmation` or
`reference_only`.

Every formal Claim supported by an Observation listed as reviewed must be
classified as `supports`, `conflicts`, or `irrelevant`. Supports/conflicts
need same-Entity usable formal support, a permitted Claim type, and a declared
visible marker. A reviewed conflict marker cannot be called irrelevant or
`not_observed`.

Exact normalized names, known domains, and documented EntityRelationships can
keep a competitor/brand as `reference_only`. A related holding, brand, or
legal-name hint is not an identity merge: it is `needs_confirmation`, requires
identity review, and cannot enter a formal list until publicly evidenced as
distinct or explicitly allowed by the user.

Every contract rule must be evaluated. `supported_match` and
`supported_conflict` cite same-Entity Claims with usable assessment evidence.
`not_observed` includes the reviewed Observation IDs and means only that the
reviewed material did not show the signal. `unknown` is never treated as a
match. A competitor reference without explicit permission must remain
`reference_only`.

## Formal delivery

A positive Assessment for a new customer-development Brief requires an
`in_scope` ScopeDecision for the same Run, Brief, contract, and Entity. Every
required positive rule must be `supported_match`; a supported blocking
exclusion or an unknown rule configured to block positive results prevents the
Assessment. Contacts, websites, country alignment, keyword similarity,
mail.read, image.inspect, user material, Candidates, and Hypotheses cannot
substitute for this check.

`task_mode=unknown`, a missing/empty contract, or a contract with no required
selection rule cannot issue a formal positive list. Single-company analysis
and existing-table enrichment are not free-form targeting exceptions: the
first requires a current user statement plus a bound company name, domain, or
user-material reference resolved to exactly one Entity; the second requires a
bound user-provided spreadsheet plus a same-Entity row/cell Observation for
every exported Entity. Neither result may say `符合本次方向`; they are presented
as `单公司分析结果` or `原表补全结果`. Material extraction without a complete
current direction remains initial or material output. `sample_first_required=true`
is enforced as a one-to-five direction sample: a later formal list needs an
updated Brief and fresh review.

Every non-empty single-company identifier is independently binding: a company
name must exactly match the conservative normalized Entity name or legal name;
a domain must exactly match the Entity website/domain; and a user-material
reference needs a visible `entity_literal` in a same-Entity Observation. The
literal must occur verbatim in the material and exactly identify the Entity by
name/legal name or domain. A mismatch between any supplied identifiers blocks
formal delivery. Each existing-table row/cell binding likewise stores an
`entity_literal` that must occur verbatim in that row/cell and exactly identify
the bound Entity. A partial name, brand, holding-company hint, alias, or other
near match is an identity-review task, not a formal exception authorization.

Standard lists export only current positive in-scope Entities and
their eligible contacts. `needs_confirmation`, `out_of_scope`, and
`reference_only` stay out of the customer and contact main tables. Initial
output may show them separately using the business labels `需确认`, `不符合本次
方向`, and `仅作参考`; it must not present them as recommended customers.
