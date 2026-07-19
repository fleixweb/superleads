---
name: scoping-lead-research
description: "Use after Superleads intake when a foreign-trade research request needs a concise Brief and scope boundary."
---

# Scoping Lead Research

## Purpose

Create a Research Brief that captures the user's task without turning optional context into core ICP rules, and decide whether the run is default discovery or explicit deep verification.

## Required references

Read `../../shared/references/user-intake.md` and `../../shared/references/product-profile-input.md`. Use `../../shared/schemas/brief.schema.json` for fields.

## Brief fields

Populate `product_or_service`, `scope_axis`, `task_mode`, `contact_detail_level`, `output_mode`, `application_context`, `target_country_or_region`, `target_customer_type`, `target_channel`, `keywords`, `seed_companies`, `seed_urls`, `existing_table`, `competitors_or_brands`, `excluded_targets`, `must_verify_claims`, `evidence_depth`, `target_count`, and optional `business_context`. For formal single-company analysis, bind every supplied structured identifier to one resolved Entity; a user-material source also needs the visible `entity_literal` from its same-Entity Observation. For formal existing-table enrichment, bind the user-provided spreadsheet and each supplemented Entity to its row/cell Observation plus its visible `entity_literal`.

For new customer development, populate `customer_selection_contract` from
the current user's language. Its offer, commercial positioning, application
boundary, desired counterparty, exclusions, competitor handling, and all rule
content are free text. Do not use product, industry, application, brand, or
customer-role enums. `scope_state` is only a workflow state:
`explicit`, `inferred_low_risk`, or `provisional`.

## Scoping rules

- For new customer development, require product/service plus at least one scope axis.
- When `target_country_or_region` has any non-empty user literal for new customer development, require a non-null `geography_contract`. Preserve the user's literal in the Brief, bind the contract to it by normalized comparison, and do not silently downgrade the task to global research.
- For single-company analysis, require a current user statement and a company identifier, URL/domain, or user-material reference that resolves to the only output Entity. Every supplied identifier must agree exactly; do not accept an alias, partial name, brand, group, or approximate domain as proof. For existing-table enrichment, require the user-provided spreadsheet plus the source row/cell and visible exact Entity literal for every output Entity. These results are not labelled as direction-matched customers.
- Record desired contact depth explicitly: standard or contact priority. A full-review request is unavailable in this local deployment.
- Use user-facing output modes: 发现候选池, 标准开发名单, 联系方式优先, 补全已有表格. This local deployment does not provide `full_review_package`.
- Record the material's declared role without treating it as an ICP default or external verification. User product/capability/target information remains Brief input, not Source Claim evidence.
- For connected-mail intake, record the user-approved mailbox reference, folders/labels, inbound-only scope, time window/filters, read-only boundary, and allowed create-only actions. A one-shot query needs a time window; continuous filtering needs explicit user approval and host scheduling support.
- Start with the four business lines: what is offered, what to find, what not
  to find, and which public signals will decide. Ask no more than three short
  questions only for a direction-reversing ambiguity. If unresolved, retain
  the question in the contract, set it provisional, and limit output to three
  to five direction samples.
- Default output is a discovery candidate pool plus public-signal补充. Only
  when the user explicitly asks for formal verification or a standard
  development list should this Brief require the full deep-check route.
- Treat named competitors, brands, manufacturers, and seed companies as
  `reference_only` unless this Brief explicitly permits them as prospects.
- For every current rule, record allowed generic Claim types plus current
  visible evidence/conflict markers. This is a rule-local relevance boundary,
  never a product or industry dictionary. A formal list needs at least one
  required positive rule. `sample_first_required=true` means one to five
  samples only, followed by an updated Brief and fresh review before formality.

## Inquiry routing

An incoming RFQ, quotation, sample, MOQ, delivery, certification, or similar message may create an Inquiry even before the sender Entity is resolved. Use mail wording only as “邮件中提及”; create entity-resolution and external-verification tasks separately. Do not turn this into a default market, country, industry, customer type, size, or ICP.

## Output

Return a valid Brief object plus unresolved questions. Keep questions minimal and specific.

## Hard constraints

Do not classify the user as factory/OEM/industrial/consumer by default. Do not add legacy country, size, or customer-type assumptions.
