---
name: analyzing-product-outbound-market
description: "Use when the user asks for objective outbound market analysis for a specific product and target country/region, including Google Trends/search-interest signals, public market and price references, destination compliance, import duties/taxes, export-country requirements, logistics routes, customs pre-filing nodes, COO/proof-of-origin requirements, and recent external factors. Do not use for customer discovery, lead lists, single-company background research, or market-entry recommendations."
---

# 产品出海市场分析

## Purpose

Route and run the Superleads product outbound market analysis path:

`产品 / 品类 / 候选 HS-HTS + 目标国家/地区 + 贸易前提 -> 产品出海市场分析 -> 客观市场与准入信息矩阵`

This skill is parallel to bulk customer development and single-customer background research. It does not create Leads, customer lists, recommended customer types, market-entry advice, recommended prices, or best shipping choices.

## Required references and scripts

Read these only as needed:

- `../../shared/references/product-outbound-market-intake.md` for the entry response, missing-info questions, and route boundaries.
- `../../shared/references/product-market-evidence-notes.example.json` when preparing compact evidence notes from opened sources.
- `../../spec/10-product-outbound-market-analysis-contract.md` for product boundaries.
- `../../spec/13-product-outbound-market-analysis-workbook-contract.md` for workbook sheets and user-visible fields.
- `../../spec/14-product-outbound-market-analysis-evidence-boundary-rules.md` for forbidden evidence upgrades.
- `../../spec/24-product-outbound-market-analysis-origin-proof-requirements.md` when COO / proof of origin appears.
- `../../spec/29-product-outbound-market-analysis-certification-requirement-calibration.md` when certification, test, registration, labeling, packaging, SDS, UN38.3, or compliance-file requirements appear.
- Run `../../scripts/preflight_capabilities.py --require-formal-research` before a formal analysis. It requires `search.web` plus `source.open`, `browser.render`, or `document.extract`; if blocked, give the prescribed switch-environment message and do not issue a market report or source plan as a substitute delivery.
- Plan source collection with `../../scripts/plan_product_market_sources.py` before any real search/open step. Its output is `source_plan_only`, an internal execution artifact rather than evidence or a formal user delivery.
- After real sources have been opened and recorded as Source / Observation, use `../../scripts/compile_product_market_evidence.py` to compile concise evidence notes into the existing EvidenceCard / MatrixRow / Gap graph objects. It does not search, open URLs, decide authority, or promote a status.
- Validate and audit existing graphs with `../../scripts/validate_product_market_analysis.py` and `../../scripts/audit_product_market_analysis.py`.
- Export reviewed graphs with `../../scripts/export_product_market_workbook.py`.

## Intake workflow

1. Confirm the route in human terms: `我理解你要做的是：产品出海市场分析。`
2. Model the Brief internally; do not turn these fields into a user questionnaire:
   - product name / model / version;
   - target country or region;
   - export declaration country, defaulting visibly to China only when the user did not set another country;
   - origin country, departure node, destination node, and trade term if known;
   - product triggers: battery, powered, magnetic, liquid, powder, chemical, dangerous goods, skin contact, food contact, child use, textile, animal/plant material, agricultural/cold-chain, bulk/breakbulk/RoRo/oversized, dual-use/export-control sensitivity.
   - optional user materials: certificates, test reports, SDS, UN38.3, labels, BOM, registration files, invoices, packing lists, or COO. These help scope matching; they are not prerequisites for analyzing destination requirements.
3. Ask at most three short questions only when missing information changes the route or blocks useful analysis. The only first-pass blocking questions are product identity and target country/region. A product name, category, use description, URL/PDF/image clue, or HS/HTS code is enough to start category-level analysis; a missing model/version lowers precision but does not stop the run.
4. First-pass intake must not ask the user for IOR/importer of record, Incoterms/trade term, transaction value or quantity, expected entry date, customs broker, BOM, product photos, actual departure port, original certificates, test reports, SDS, or UN38.3. Ask for these only when the user explicitly requests final duty, formal customs filing, clearance readiness, or actual shipment arrangement.
5. If the user also asks to find customers, split the job into two stages: do product market analysis first; only start customer development after the user separately confirms.
6. If the user asks whether the market is worth entering, translate it into objective analysis and state that the business decision is theirs.
7. If the user asks about certification without having certificates, do not block on the missing certificates. First analyze what the destination market may require, then list which user/supplier/professional materials are needed to verify applicability.
8. Category-level analysis changes only the object granularity. It does not lower the evidence standard: every user-visible fact still needs current-run source support, visible gap/conflict status, or an explicit not-executed row; never use category-level analysis to output final classification, final duty, no-certification, general-cargo, clearance-ready, or transportability conclusions.

### Requested analysis scope

Set the existing Brief field `analysis_modules_requested` before writing the
source plan. It is the sole scope selector for the report; do not add another
scope field.

- An overall request such as “产品出海市场分析”, “出口某国分析”, or “进入某国市场分析” uses the complete report: include every module. Missing or empty `analysis_modules_requested`, an unrecognised value, or any uncertain intent also defaults to the complete report.
- A clearly single-item request may select only the relevant module(s):
  - certification, tests, registration, labels, SDS, UN38.3, CE, UL, SABER -> `certification`;
  - tariff, duty, tax rate, HS/HTS tax question -> `import_tax`;
  - COO / proof of origin -> `certification` (the origin-proof row is included in that table);
  - clearance, shipping, transport, pre-filing -> `logistics`;
  - export declaration, inspection, export controls -> `export_requirements`;
  - trends, prices, or “好不好卖” -> `google_trends`, `online_price`, and `market_reports`.
- Keep existing planner vocabulary such as `destination_compliance`,
  `origin_proof_requirement`, and `market_signal` when they are already present
  in a Brief; exporters map those legacy keys to the corresponding table.

The three fixed tables are always included: `市场事实总览`, `产品档案与触发项`,
and `信息来源与待确认事项`. A scoped report is not a partial complete report:
it renders only the selected module tables plus these fixed tables. Its opening
must state the boundary, for example:

```text
本轮范围：只做了「目标国准入与认证要求」一项。
未覆盖：进口税费、出口国要求、物流与申报、市场趋势与价格、季节窗口、近期外部因素。
需要哪一项可以继续要求。
```

The complete report renders all twelve tables in the order below. Empty tables
must explain whether collection was not run, ran without a usable public source,
was not applicable to the current product triggers, or was source-restricted;
do not use an unexplained “本表暂无矩阵行”. In a scoped report, unrequested
modules are omitted rather than listed as individual not-executed items.

Canonical source-planning Brief field names are: `product_name`, `target_country_or_region` / `destination_country_or_region`, `candidate_hs_hts`, `export_declaration_country`, `origin_country_or_region`, `manufacturing_country_clue`, `departure_country_or_region`, `departure_node`, `destination_node`, `product_trigger_tags`, `model_or_sku`, and `manufacturer_or_brand`. Treat other common words such as `hs_code` or `hts_code` as user clues to map into the canonical field before running source planning. Do not map `made_in_country`, `production_country`, `manufacturing_country`, or `coo_country` into `origin_country_or_region`; keep them as manufacturing clues unless the user explicitly states a customs-origin premise.

## Evidence workflow

Use `ProductMarketAnalysisGraph`, not Candidate / Claim / Assessment. Every user-visible fact must come from current-run Source / Observation / EvidenceCard, a visible Gap, a visible Conflict, or an explicit not-executed row.

Keep these statuses visible instead of filling blanks: `verified`, `derived_calculation`, `candidate`, `preliminary_reference`, `business_confirmation_required`, `technical_docs_required`, `physical_verification_required`, `professional_confirmation_required`, `source_restricted`, `not_executed`, `not_applicable`, `not_provided`, `conflict_pending_review`.

Search summaries, Source Packs, previous Skill summaries, and model summaries are leads for where to look, not facts.

If formal source capability is unavailable, stop before this workflow. You may
perform a clearly labeled `资料初审` of files or text the user already supplied,
but it is not a product outbound market analysis and must not be exported as
one.

Before collecting live sources, use the Source Pack registry to generate a Query Plan. The plan may list packs, source entries, query strings, required authority levels, and observation requirements; it must not create EvidenceCards, MatrixRows, tax rates, certification conclusions, logistics times, trends, prices, or market-entry judgments.

### Compact evidence compilation

Do not hand-author repeated graph IDs, source references, row links, and gap
links for every opened page. Once a Source / Observation already exists in the
current graph, put only the decision-bearing fields into a compact notes JSON:

- `product_attributes`: user-provided, known product fields such as voltage,
  wattage, capacity, material, or model. Keep their non-final status; do not
  silently turn user input into verified source evidence.
- `evidence_notes`: one item per source fact, with an existing opened
  `observation_id`, a `source_excerpt_quote` copied verbatim from that
  Observation, field domain/name/value, applicability, what it supports and
  does not support, boundary rules, and one target matrix row.
- an optional compact Gap when the same fact identifies a missing document,
  product attribute, or professional confirmation.

Run the compiler before validation:

```bash
python3 scripts/compile_product_market_evidence.py \
  --graph source-observations.json \
  --notes compact-evidence-notes.json \
  --output compiled-market-graph.json \
  --format json
```

The compiler rejects a missing, restricted, or unopened Observation and a
quote that is not present in the cited original excerpt. It only carries the
caller-supplied status; `verified`, authority, tax, classification, or
compliance conclusions still pass through the existing validator and audit.
Search summaries remain in SearchLog only and cannot be compiler input.

Certification/compliance rows must split two objects:

- destination requirement: what the target market may require and under what
  conditions;
- user material status: whether the user has matching certificates, test
  reports, SDS, UN38.3, labels, BOM, registrations, or declarations.

Do not infer either object from the other.

## Output shape

Prefer tables over long prose. Complete reports group information into these
twelve tables:

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
- Do not treat missing user certificates as proof that destination certification is not required.
- Do not treat user-provided certificates, test reports, SDS, UN38.3, labels, BOM, or registrations as proof that the target country accepts them or that the product is fully compliant.
- Do not treat a product-page certificate download link as a verified certification without opening and scope-checking the file.
- Do not treat marketplace, retailer, or customer certification requirements as destination-country legal requirements unless an authoritative source supports that.
- Do not turn Made in / Production / origin marking into COO / proof-of-origin documents.
- Do not turn preferential proof-of-origin requirements into all-import COO requirements.
- Do not turn user-provided COO, invoice, packing list, or bill of lading into customs final origin rulings.
- Do not guess departure port, best route, guaranteed transit time, or commodity shipping availability.
- Do not expose graph IDs, EvidenceCard IDs, hashes, local paths, file URIs, tokens, or internal rule IDs in user-facing output.
