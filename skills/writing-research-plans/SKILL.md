---
name: writing-research-plans
description: "Use when a Superleads Research Brief needs a query and coverage plan before discovery or deep research."
---

# Writing Research Plans

## Purpose

Turn a Research Brief into a plan for searching, opening sources, collecting contacts, and evaluating evidence. Default to discovery breadth first. Do not produce customers, open pages, judge commercial value, or write final advice.

For default discovery, this is an internal/on-demand guide within the single
`discovery` phase, not a mandatory separately routed stage for every round.

Every plan must state finite query-group, candidate, and core-source-open limits; whether contacts, trade summaries, or historical references are included; and coverage/low-increment stop conditions. Mark only independent search/open groups `execution_order: independent`. Entity merge, conflict treatment, Claim promotion, Review, Audit, and formal export remain `serial`. Record stage checkpoints for Brief, groups, SearchLogs, opened sources, Observations, dedupe results, and incomplete work. Reuse a same-Run normalized URL by recording a group association rather than reopening it; older Run material is only “历史参考，需重新核验”.

## Required references

Read `../../shared/policies/tool-capability-policy.md`, `../../shared/policies/claim-and-source-policy.md`, and `../../shared/schemas/plan.schema.json`.

## Plan components

1. Query groups tied to the current brief only.
2. Default bulk-discovery source categories: `website`, `directory`, `document`, `social`, `map`, `trade_aggregator`, and `search_result`. A social or map category means a normally accessible public page, not an assumed platform API.
3. Default contact/public-information targets: `email`, `phone`, `contact_form`, `social_company`, `social_person`, `person_name`, `job_title`, `address`, `map_phone`, and `public_trade_summary`.
4. Default business-relevance criteria for `directly_related`, `possibly_related`, `explicitly_excluded_or_unrelated`, `identity_pending`, and `insufficient_information`.
5. Public-signal collection targets and statuses for website/contact, trade record, China relation, and product description/HS.
6. Claim evidence requirements only for explicit deep-check tasks, including which claims need first-party or high-authority sources.
7. Stop conditions and downgrade strategy when tools or evidence are missing.

For every Candidate in the current output scope, plan the same public-information
coverage categories. Do not enrich only candidates that appear more valuable.
Set a finite per-candidate query/open budget for each category, dedupe the same
canonical/final URL in the current Run, and mark an unexecuted over-budget path
as `not_searched` / 本轮未检索. It is not `not_observed` and never means the
information does not exist.

For social, map, and third-party trade aggregation paths, plan the collection
status separately: 本轮未检索, 已检索未见, 仅搜索摘要可见, 公开页面已打开,
来源受限, or 主体待确认. Social/map search snippets may retain only an
unverified URL clue, never a person, title, address, phone, or business scene.
For trade, plan a same-Run SearchLog `visible_excerpt` binding before retaining
any visible direction, counterparty, date, product/HS, or origin/destination;
those fields remain an unverified third-party summary, not an Observation,
contact, or formal evidence. Third-party trade material is always planned for
user-facing labeling as “第三方贸易数据聚合站公开摘要，非官方海关记录”.

For `contact_collection_targets`, include concrete, object-anchored queries when
public people or role clues are requested:

- `site:linkedin.com/in "<公司名>"`
- `"<公司名>" founder OR owner OR CEO OR "managing director" OR "purchasing manager"`
- `"<公司名>" 邮箱 OR 联系方式 OR contact OR "get in touch"`
- `"<公司名>" + <展会名> / <行业协会> / <公开目录站>`
- `"<人名>" "<公司名>"` for same-person cross-checking
- Public Facebook / Instagram / X / YouTube company and personal pages

For maps and third-party trade aggregation, anchor the query to company/brand,
domain, city, country, address, or public phone. Do not plan a paid API,
account login, Cookie, Token, API Key, proxy, or access-control workaround.

Collect public founders, shareholders, general managers, sales staff, and
technical leads as well as purchasing contacts. A job title is a role clue only;
it never establishes purchasing authority. Queries must stay tied to the
current object and do not become product-plus-country batch discovery.

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
- A page needing login, CAPTCHA, 403, Cloudflare or equivalent verification,
  payment, an explicit automation restriction, or unreadable dynamic content
  is a stop condition for that URL, not a retry target. Plan it as 来源受限
  with a manual-check action.
