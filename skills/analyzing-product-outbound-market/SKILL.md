---
name: analyzing-product-outbound-market
description: "Use when the user asks for objective outbound market analysis for a specific product and target country/region, including Google Trends/search-interest signals, public market and price references, destination compliance, import duties/taxes, export-country requirements, logistics routes, customs pre-filing nodes, COO/proof-of-origin requirements, and recent external factors. Do not use for customer discovery, lead lists, single-company background research, or market-entry recommendations."
---

# 产品出海市场分析

## Purpose

Route and run the Superleads product outbound market analysis path:

`产品版本 + 目标国家/地区 + 贸易前提 -> 产品出海市场分析 -> 客观市场与准入信息矩阵`

This skill is parallel to bulk customer development and single-customer background research. It does not create Leads, customer lists, recommended customer types, market-entry advice, recommended prices, or best shipping choices.

## Required references and scripts

Read these only as needed:

- `../../shared/references/product-outbound-market-intake.md` for the entry response, missing-info questions, and route boundaries.
- `../../spec/10-product-outbound-market-analysis-contract.md` for product boundaries.
- `../../spec/13-product-outbound-market-analysis-workbook-contract.md` for workbook sheets and user-visible fields.
- `../../spec/14-product-outbound-market-analysis-evidence-boundary-rules.md` for forbidden evidence upgrades.
- `../../spec/24-product-outbound-market-analysis-origin-proof-requirements.md` when COO / proof of origin appears.
- Plan source collection with `../../scripts/plan_product_market_sources.py` before any real search/open step. Its output is `source_plan_only`, not evidence.
- Validate and audit existing graphs with `../../scripts/validate_product_market_analysis.py` and `../../scripts/audit_product_market_analysis.py`.
- Export reviewed graphs with `../../scripts/export_product_market_workbook.py`.

## Intake workflow

1. Confirm the route in human terms: `我理解你要做的是：产品出海市场分析。`
2. Capture the minimum Brief:
   - product name / model / version;
   - target country or region;
   - export declaration country, defaulting visibly to China only when the user did not set another country;
   - origin country, departure node, destination node, and trade term if known;
   - product triggers: battery, powered, magnetic, liquid, powder, chemical, dangerous goods, skin contact, food contact, child use, textile, animal/plant material, agricultural/cold-chain, bulk/breakbulk/RoRo/oversized, dual-use/export-control sensitivity.
3. Ask at most three short questions only when missing information changes the route or blocks useful analysis. Target country and product identity are the first two blocking questions.
4. If the user also asks to find customers, split the job into two stages: do product market analysis first; only start customer development after the user separately confirms.
5. If the user asks whether the market is worth entering, translate it into objective analysis and state that the business decision is theirs.

## Evidence workflow

Use `ProductMarketAnalysisGraph`, not Candidate / Claim / Assessment. Every user-visible fact must come from current-run Source / Observation / EvidenceCard, a visible Gap, a visible Conflict, or an explicit not-executed row.

Keep these statuses visible instead of filling blanks: `verified`, `derived_calculation`, `candidate`, `preliminary_reference`, `business_confirmation_required`, `technical_docs_required`, `physical_verification_required`, `professional_confirmation_required`, `source_restricted`, `not_executed`, `not_applicable`, `not_provided`, `conflict_pending_review`.

Search summaries, Source Packs, previous Skill summaries, and model summaries are leads for where to look, not facts.

Before collecting live sources, use the Source Pack registry to generate a Query Plan. The plan may list packs, source entries, query strings, required authority levels, and observation requirements; it must not create EvidenceCards, MatrixRows, tax rates, certification conclusions, logistics times, trends, prices, or market-entry judgments.

## Output shape

Prefer tables over long prose. The default report groups information into:

1. 市场事实总览
2. 产品档案与触发项
3. 长期需求与搜索趋势
4. 公开市场资料与行业信息
5. 线上市场与价格参考
6. 季节、节日与销售窗口
7. 产品准入与合规要求
8. 进口税费
9. 出口国要求
10. 运输方式、路线、港口与申报节点
11. 近期外部因素
12. 信息来源与待确认事项

For a chat-readable / Codex / ChatGPT app report, prefer the unified
Superleads Markdown delivery command after the graph has passed validation and
audit:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route product_outbound_market_analysis --output market-report.md --format json
```

For product-market CSV sheets plus optional Markdown / manifest, use:

```bash
python3 scripts/export_product_market_workbook.py graph.json --output-dir out --format csv --markdown market-report.md --manifest manifest.json
```

Both exporters only move reviewed user-visible matrix rows and safe
source/gap/conflict fields. They must not search, create customer lists,
recommend target customers, judge whether the product should enter the market,
recommend quotations, or finalize classification / duties / compliance.

## Hard constraints

- Do not generate customer lists, prospect pools, buyer recommendations, or target customer types.
- Do not say `建议进入`, `值得开发`, `市场潜力高`, or similar market-entry judgments.
- Do not turn Google Trends into sales, GMV, import volume, or purchasing demand.
- Do not turn platform/list prices into transaction prices, wholesale target prices, or recommended quotations.
- Do not turn candidate HS/HTS into final classification, final duty rate, or payable tax.
- Do not turn Made in / Production / origin marking into COO / proof-of-origin documents.
- Do not turn preferential proof-of-origin requirements into all-import COO requirements.
- Do not turn user-provided COO, invoice, packing list, or bill of lading into customs final origin rulings.
- Do not guess departure port, best route, guaranteed transit time, or commodity shipping availability.
- Do not expose graph IDs, EvidenceCard IDs, hashes, local paths, file URIs, tokens, or internal rule IDs in user-facing output.
