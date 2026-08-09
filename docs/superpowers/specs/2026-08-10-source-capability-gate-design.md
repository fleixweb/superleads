# Source Capability Gate and First-Stage Delivery Design

## Goal

Make Superleads honest about execution capability: formal foreign-trade research
requires recorded search and source-opening capability. A missing capability must
stop formal delivery and tell the user to switch to a capable Agent/session.

This first stage also fixes two deterministic user-visible defects already found:
the broad electrical trigger for the lithium-battery pack and the merged trade
premise label in the product-market workbook.

## Scope

In scope:

- Preflight classification for formal research capability.
- A user-visible hard-stop contract for missing search/source opening.
- Deterministic intake routing for a product URL plus target market risk question.
- Correct lithium trigger selection for battery products only.
- Separate export-declaration and origin labels in market output.
- Plugin manifest metadata and distribution checks, including the declared hook.
- Regression fixtures and documentation.

Out of scope until a search-enabled real-business UAT:

- EvidenceCard/MatrixRow compiler implementation.
- Country-specific Source Pack expansion.
- Removing or changing the certification/COO split or geographic-role model.
- Redesigning all twelve market tables or internal status enums.
- Further claimed-path hardening.

## Capability Contract

Formal research requires `search.web` plus at least one source-opening capability:
`source.open`, `browser.render`, or `document.extract`. Search summaries alone
remain discovery clues and never support a Claim.

When the requirement is not met, the router/preflight returns
`formal_research_blocked_no_source_capability`, does not authorize a formal
workbook or Markdown report, and presents this user-facing boundary:

> 本轮环境无法联网检索并打开可记录来源，不能完成 Superleads 正式外贸研究。请切换到具备 Web Search 和来源打开能力的 Agent/环境后重试。若只需整理已有资料，可以继续，但那不是市场分析或客户开发报告。

User-provided files and explicitly opened URLs remain a separate, limited
materials-review path; they must not be mislabeled as public-source research.

## Routing and Output

Product URL + target-country + risk/requirement language routes to
`product_outbound_market_analysis` and records the URL as product material.
Battery packs require battery-specific trigger words; generic `electrical` must
not activate lithium transport rules.

The trade-premise output keeps these labels distinct:
`出口申报国（默认可改）` and `原产国 / 制造来源（证据状态）`.

## Verification

The first stage is accepted only when targeted route/preflight/output/distribution
evals pass, then the existing full suite passes. A real source-enabled UAT is a
separate gate; no claim is made that this stage implements the missing
Observation -> EvidenceCard -> MatrixRow bridge.
