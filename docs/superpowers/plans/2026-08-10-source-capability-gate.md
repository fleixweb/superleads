# Source Capability Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enforce source-capable formal research boundaries and fix the two confirmed deterministic product-market defects without pretending that the missing evidence compiler exists.

**Architecture:** Keep the existing preflight, deterministic router, exporter, and distribution checker boundaries. Add a narrow formal-research capability projection, route only the new URL/risk intake shape, tighten the product trigger inference, and preserve existing schemas and internal validation rules.

**Tech Stack:** Python 3 standard library, JSON fixtures, Markdown Skill/ policy files, Codex plugin manifest.

---

### Task 1: Add failing capability-gate regressions

**Files:**
- Modify: `evals/cases/capability_adapter_cases.json`
- Modify: `evals/cases/superleads_route_cases.json`
- Modify: `evals/cases/product_market_source_plan_cases.json`
- Modify: `evals/run_superleads_route_evals.py` only if an assertion field is required

- [x] Add a no-search formal-research case requiring the blocked status/message and no formal delivery authorization.
- [x] Add a search-without-source-open case requiring the same formal block.
- [x] Add a product URL + target country + risk prompt expecting the market route and product material anchor.
- [x] Add an electric-kettle trigger case asserting no lithium-battery pack is selected.
- [x] Run the focused evals and confirm the new cases fail before implementation.

### Task 2: Implement the capability contract

**Files:**
- Modify: `scripts/preflight_capabilities.py`
- Modify: `scripts/validate_product_market_analysis.py` if formal delivery status needs a shared guard
- Modify: `shared/policies/tool-capability-policy.md`
- Modify: `skills/using-superleads/SKILL.md`
- Modify: `skills/analyzing-product-outbound-market/SKILL.md`

- [x] Add a pure `formal_research_capability_status` projection that distinguishes full source capability, search-only, and no-search states.
- [x] Make no-search and search-only formal research fail closed with a stable error code and user-visible switch-environment text.
- [x] Keep user-provided-material review as a limited separate path.
- [x] Remove `research_plan_only` from formal user delivery guidance while retaining it for internal plan artifacts.
- [x] Run the capability cases and verify they turn green.

### Task 3: Fix deterministic routing and trigger projection

**Files:**
- Modify: `scripts/route_superleads_intake.py`
- Modify: `scripts/plan_product_market_sources.py`
- Modify: `evals/cases/superleads_route_cases.json`
- Modify: `evals/cases/product_market_source_plan_cases.json`

- [x] Recognize a concrete product URL plus country and “风险/要求/能否销售” as market analysis with a product material anchor.
- [x] Remove generic `electrical` from battery-pack selection and infer it only when the product text actually indicates a battery/electrical trigger required by the rule.
- [x] Run focused routing and source-plan evals.

### Task 4: Fix labels and plugin distribution metadata

**Files:**
- Modify: `scripts/export_product_market_workbook.py`
- Modify: `.codex-plugin/plugin.json`
- Modify: `evals/run_superleads_plugin_distribution_evals.py`
- Modify: `scripts/check_superleads_plugin_distribution.py`

- [x] Ensure the top trade-premise label never merges export declaration country and origin country.
- [x] Add the three interface URLs to the Codex manifest.
- [x] Make the distribution smoke copy and validate the manifest-declared `hooks/` target.
- [x] Run output and distribution regressions.

### Task 5: Verify and document the boundary

**Files:**
- Modify: `docs/superleads-common-commands.md` if command guidance needs the gate wording
- Modify: `TASKS.md` and `HANDOFF.md` only after verification, with a concise status entry

- [x] Run focused Python compilation and route/source/output/distribution suites.
- [x] Run `python3 evals/run_evals.py --suite all` and record the result.
- [x] Run `git diff --check`.
- [x] Explicitly record that the Observation -> EvidenceCard -> MatrixRow compiler remains unimplemented pending source-enabled real-business UAT.
