---
name: writing-research-plans
description: "Generate Superleads research plans from a Research Brief: query groups, source categories, contact collection targets, lead tiering criteria, claim evidence requirements, stop conditions, and downgrade strategy. Use before opening sources or collecting leads."
---

# Writing Research Plans

## Purpose

Turn a Research Brief into a plan for searching, opening sources, collecting contacts, and evaluating evidence. Default to discovery breadth first. Do not produce customers, open pages, judge commercial value, or write final advice.

## Required references

Read `../../shared/policies/tool-capability-policy.md`, `../../shared/policies/claim-and-source-policy.md`, and `../../shared/schemas/plan.schema.json`.

## Plan components

1. Query groups tied to the current brief only.
2. Source categories: website, social visible page, registry, directory, map, document, spreadsheet, search result.
3. Contact collection targets covering emails, phones, forms, portals, LinkedIn visible pages, names, titles, addresses, PDFs, directories, and maps when relevant.
4. Default business-relevance criteria for `directly_related`, `possibly_related`, `explicitly_excluded_or_unrelated`, `identity_pending`, and `insufficient_information`.
5. Public-signal collection targets and statuses for website/contact, trade record, China relation, and product description/HS.
6. Claim evidence requirements only for explicit deep-check tasks, including which claims need first-party or high-authority sources.
7. Stop conditions and downgrade strategy when tools or evidence are missing.

## Current-direction coverage

When the Brief has a customer selection contract, bind the Plan to that Brief
and list every selection and exclusion rule ID. Each query group must carry
the relevant rule IDs and a plain-language `query_purpose`. Build positive
discovery and exclusion checks separately. A query can discover risk only;
it cannot permanently exclude an Entity without an opened public Observation,
same-Entity Claim, and ClaimEvidence.

Plan explicit candidate checks for the public signal needed to match each
positive rule, the public signal that would support each exclusion, and the
fallback to `需确认` when evidence is insufficient. If the Brief is
provisional, set a sample-first limit from one to five and do not plan a
formal expansion. Search terms come only from the current Brief; a competitor
or brand is reference material unless the current Brief explicitly allows it
as a prospect.

For each rule, derive permitted generic Claim types and visible markers from
the current Brief and Plan. Plan to classify every formal Claim supported by a
reviewed Observation as support, conflict, or irrelevant. Do not use an
address, registration, or company identity as product/application/channel
evidence unless the current rule expressly permits that Claim type and marker.

When `target_country_or_region` has any non-empty literal, its required
geography contract must have query-group IDs on the Plan and link each to the
geography selection rule. Use exactly the user's included/excluded literals
and admission definition; do not generate defaults from country, TLD,
language, phone code, or legacy ICP material. Plan an opened same-Entity
public-source check for every geography inclusion decision.

## Hard constraints

- Search results can only feed initial clues and logs.
- Plan for opened sources before Claims.
- Do not use memory or legacy examples as evidence.
- Do not lock in any default industry ICP.
- Similar keywords, a reachable contact, or a well-known company never count
  as current-direction evidence.
- Do not stop after one page or one source merely because a few matches were
  found. Plan coverage expansion across product terms, roles, geography, and
  source categories before calling discovery converged.
