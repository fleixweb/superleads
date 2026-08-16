# Public Enrichment Implementation Plan

> **For agentic workers:** Execute the defined tasks with test-first changes and review each task before moving on.

**Goal:** Add public social, map, and third-party trade-aggregator coverage to
bulk-customer discovery using only host-provided public search/open abilities.

**Architecture:** Extend Candidate coverage states and structured public
signal items, preserve the existing Source/Observation contract, project the
states into initial workbook and unified Markdown delivery, and codify the
workflow in the existing research-plan and execution Skills.

**Tech stack:** Python 3 standard library, JSON Schema, existing graph
validator, workbook/Markdown exporters, `unittest`, existing eval runners.

---

### Task 1: Coverage Contract

- Modify `shared/schemas/research-graph.schema.json` and
  `shared/schemas/source-observation.schema.json`.
- Modify `scripts/validate_research_graph.py`.
- Test `tests/test_public_enrichment.py`.

Add social-company, social-person, and map-listing Candidate signals with
required collection status. Keep `trade_record` as the compatibility coverage
state and add optional structured `public_trade_summaries`. Require opened
items to bind a same-candidate Source/Observation; retain search-summary and
restricted states as non-factual clues.

### Task 2: Planning and Collection Boundaries

- Modify `shared/references/default-discovery-reference.md` and its two
  examples.
- Modify `skills/writing-research-plans/SKILL.md`,
  `skills/executing-research-plans/SKILL.md`, and
  `skills/collecting-contact-intelligence/SKILL.md`.

Require all seven default source categories and the requested target fields,
then document object-anchored social, map, and trade queries, budgets,
same-Run URL de-duplication, host capability truthfulness, access-stop rules,
and user-material labeling. No API integration is added.

### Task 3: Workbook and Markdown Delivery

- Modify `scripts/export_workbook.py` and
  `scripts/export_superleads_markdown.py`.
- Modify `scripts/validate_superleads_user_visible_output.py` and its eval
  fixtures/cases.

Project website/contact, social/professional, map, and trade fields into
separate customer-facing sections. Render all non-observed states visibly.
For restrictions use the fixed manual-check language; every trade row says
`第三方贸易数据聚合站公开摘要，非官方海关记录`.

### Task 4: Regression Coverage

- Add `tests/test_public_enrichment.py`.
- Extend the default-discovery fixture and delivery eval cases.

Start each behavior with a failing focused test. Then run focused tests,
route/Markdown/user-visible evals, the full unit suite, `run_evals.py --suite
all`, Python compilation, and `git diff --check` serially. Do not commit or
push as part of this work.
