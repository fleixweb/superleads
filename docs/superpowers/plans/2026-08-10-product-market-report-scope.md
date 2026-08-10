# Product Market Report Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make product outbound market reports render either a complete 12-table report or a clearly scoped single-module report, driven by the existing `analysis_modules_requested` brief field.

**Architecture:** Define one compatibility mapping from sheet names to both current and legacy module keys. A shared selection helper determines complete versus explicit 1-2 module scope; Markdown and workbook exporters use that helper. Complete reports retain all sheets and explain empty results with existing user-visible status language, while scoped reports add a range declaration and omit unrequested module sheets.

**Tech Stack:** Python exporters, JSON fixtures/evals, Markdown Skill documentation, plugin manifest/cache synchronization.

---

### Task 1: Shared scope-aware market sheet selection and workbook export

**Files:**
- Modify: `scripts/export_product_market_workbook.py`
- Test: existing product-market exporter/source-plan eval suites

- [x] Add the complete compatibility mapping and fixed-sheet constants.
- [x] Add helpers to normalize requested modules and select sheets, treating missing/empty/unknown scope as complete.
- [x] Make empty-sheet notes distinguish not executed, no usable public source, not applicable, and restricted source.
- [x] Use the selected sheet order in CSV and Markdown workbook output without changing complete-report order.
- [x] Run focused compile and exporter checks.

### Task 2: Markdown scoped delivery

**Files:**
- Modify: `scripts/export_superleads_markdown.py`
- Test: existing Markdown delivery and market eval suites

- [x] Remove reverse logic that treats every unrequested module as not executed.
- [x] Reuse the workbook scope-selection helper for market table rendering.
- [x] Add the single-report range declaration with a stable list of uncovered modules.
- [x] Preserve complete-report output and existing evidence-boundary wording.
- [x] Run focused Markdown exporter/eval checks.

### Task 3: Skill, intake, plugin, and validation documentation

**Files:**
- Modify: `skills/analyzing-product-outbound-market/SKILL.md`
- Modify: `shared/references/product-outbound-market-intake.md`
- Modify: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Modify: `HANDOFF.md`, `TASKS.md`
- Create: `docs/validation/superleads-product-market-report-scope-20260810.md`

- [x] Document module selection defaults, explicit single-module routing, range declaration, and evidence boundaries.
- [x] Bump plugin version and synchronize the runtime cache.
- [x] Record implementation and validation results.

### Task 4: Fixtures and full verification

**Files:**
- Create/modify: at most two product-market pass fixtures and existing eval cases

- [x] Add one scoped certification pass case and complete-report empty/no-source reason assertions, reusing existing runners.
- [x] Run focused suites, all/default/deep evals, formal delivery check, skill validation, and `git diff --check`.
- [ ] Review the final diff for route isolation and commit once with `Scope product market report by requested modules`.
