# Superleads UX Routing and Evidence Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Route lightweight requests without research side effects, make discovery work bounded and recoverable, and ensure every user-visible delivery describes evidence rather than commercial value.

**Architecture:** Add a side-effect-free interaction-mode classifier ahead of the existing business router while retaining its three route identifiers. Add optional Run/Plan execution-state contracts for phase reporting, same-Run URL reuse and recovery, rather than fabricating a concurrent executor. Keep formal evidence gates and internal disposition enums intact; replace only their user-visible projections.

**Tech Stack:** Python 3 standard library, JSON Schema Draft 2020-12, unittest, existing eval runners.

---

### Task 1: Lightweight Intake and Metadata

**Files:**
- Create: `scripts/superleads_task_modes.py`
- Modify: `scripts/route_superleads_intake.py`, `scripts/superleads_user_guidance.py`, `.codex-plugin/plugin.json`, `hooks/codex-hooks.json`, `hooks/hooks.json`
- Modify: `skills/using-superleads/SKILL.md`, `shared/references/user-intake.md`, `shared/references/route-map.md`
- Modify: `tests/test_superleads_user_guidance.py`, `evals/cases/superleads_route_cases.json`, `evals/run_superleads_route_evals.py`, `evals/run_superleads_plugin_distribution_evals.py`
- Test: `tests/test_superleads_task_modes.py`

- [ ] **Step 1: Write failing routing and no-I/O tests.**

  Add tests that assert Chinese and English current/installed-version and help prompts produce `interaction_mode == "metadata"`, `operations == []`, and do not call a supplied preflight/network/cache callback. Add material-only PDF/Excel/screenshot cases producing `material_triage` / `资料初审`, concrete bulk/background/market cases retaining their existing `route`, and `完整报告` / `正式开发名单` selecting `formal_research` while ordinary bulk discovery selects `discovery_snapshot`.

- [ ] **Step 2: Run the focused test to verify RED.**

  Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_task_modes.py -v`

  Expected: failure because no task-mode classifier or active-manifest-only metadata reader exists.

- [ ] **Step 3: Implement the pure classifier and update check boundary.**

  Implement a pure `classify_task_mode(text)` with exactly `metadata`, `material_triage`, `discovery_snapshot`, and `formal_research`. Implement `read_active_plugin_version(active_root)` by reading only `active_root/.codex-plugin/plugin.json`. Implement `check_latest_version(fetch, session_cache)` so it is called only for explicit update requests, memoizes by session, and returns `本次未能确认远端版本` on exception. The router must invoke the classifier before marker matching and must use token-safe English matching so `Superleads` does not match `leads`.

- [ ] **Step 4: Disable default startup networking.**

  Remove the packaged `SessionStart` hook registration, leaving the standalone hook scripts uncalled. Update distribution eval assumptions to accept a manifest with no hook configuration. Do not invoke an update check from help, current-version, installed-version, or any session startup path.

- [ ] **Step 5: Update route documentation and verify GREEN.**

  State that metadata/help and material triage do not create Run/Brief objects, preflight, search, source opens, cache scans, or exports. State that the normal bulk path is a bounded discovery snapshot and formal research requires explicit user intent. Run the focused unit, route, and distribution suites.

### Task 2: Bounded Phase State, Reuse, and Recovery Contract

**Files:**
- Create: `scripts/superleads_execution_state.py`
- Modify: `shared/schemas/run.schema.json`, `shared/schemas/plan.schema.json`, `shared/schemas/research-graph.schema.json`
- Modify: `shared/references/default-discovery-reference.md`, `shared/references/status-labels.md`, `shared/references/output-schema.md`
- Modify: `skills/writing-research-plans/SKILL.md`, `skills/executing-research-plans/SKILL.md`, `skills/scoping-lead-research/SKILL.md`, `skills/analyzing-product-outbound-market/SKILL.md`
- Test: `tests/test_superleads_execution_state.py`

- [ ] **Step 1: Write failing state tests.**

  Add focused tests for: normalized same-Run URLs are opened once and referenced by two independent query groups; completed search/open work is retained in a serializable checkpoint and resumed work excludes it; cross-Run cached data is labeled `历史参考，需重新核验` and cannot be returned as a current observation/Claim; capability preflight is cached once per Run; incomplete work records `本轮未执行` or `来源受限`, never `未发现`.

- [ ] **Step 2: Run the focused test to verify RED.**

  Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_execution_state.py -v`

  Expected: failure because no execution-state module or compatible schema fields exist.

- [ ] **Step 3: Implement minimal host-neutral state helpers.**

  Implement deterministic helpers for phase transitions (`breadth_search`, `source_verification`, `supplement`, `serial_decision`), finite budgets, URL normalization, per-Run cache entries, query-group/source association, checkpoint serialization and restoration, and counts-only phase metrics. Permit query groups to be marked `independent` / `serial`; do not create threads, async workers, fake streaming events, or any cross-session profile.

- [ ] **Step 4: Extend schemas additively.**

  Add optional `execution_state` fields that record mode, phase, capabilities, budgets, group completion, URL cache fields (`normalized_url`, `content_hash`, `observed_at`, `source_subject`, `fact_domain`), checkpoint, recovery count, and counts-only metrics. Preserve all existing required formal graph fields and validation behavior.

- [ ] **Step 5: Update route-specific guidance and verify GREEN.**

  Document finite scope, stage-boundary status, independent-query planning, serial identity/Claim/Audit decisions, source limits, stop conditions, and explicit host limitation: phase summaries are reliable, actual concurrent streaming depends on an available host capability. Run focused tests plus schema/skill validation.

### Task 3: Request-Scoped Product Market Analysis

**Files:**
- Modify: `scripts/route_superleads_intake.py`, `scripts/plan_product_market_sources.py`, `shared/references/product-outbound-market-intake.md`
- Modify: `skills/analyzing-product-outbound-market/SKILL.md`, `skills/using-superleads/SKILL.md`
- Modify: `tests/test_superleads_task_modes.py`, `evals/cases/superleads_route_cases.json`, `evals/run_superleads_route_evals.py`

- [ ] **Step 1: Write failing scope tests.**

  Add cases where tariff, certification, public-price and logistics-only prompts select one requested module and render every other module as `本轮未执行`; an explicit `整体` / `完整市场分析` selects the complete module set; a market prompt without an expressed topic asks a short scope question rather than promising a full report.

- [ ] **Step 2: Run the route suite to verify RED.**

  Run: `PYTHONDONTWRITEBYTECODE=1 python3 evals/run_superleads_route_evals.py --suite all --format json`

  Expected: failure because market responses currently promise full coverage unless they contain narrow `只/仅` wording.

- [ ] **Step 3: Implement module selection without changing evidence rules.**

  Derive requested modules from a single concrete market domain even if it lacks `只/仅`; derive all modules only from complete-analysis intent; return a short clarification for broad market analysis with no requested domain. Keep candidate discovery separate from market analysis and retain unknown product, HS, origin, source and access limitations.

- [ ] **Step 4: Verify GREEN.**

  Run the route eval suite and the product-market analysis suite. Confirm no response claims absent modules were searched or discovered.

### Task 4: User-Visible Evidence Projection

**Files:**
- Modify: `scripts/export_workbook.py`, `scripts/export_superleads_markdown.py`, `scripts/background_report.py`, `scripts/validate_superleads_user_visible_output.py`
- Modify: `shared/references/output-schema.md`, `shared/references/status-labels.md`
- Modify: `skills/assessing-research-evidence/SKILL.md`, `skills/researching-customer-background/SKILL.md`, `skills/exporting-lead-workbooks/SKILL.md`
- Modify: `evals/cases/superleads_user_visible_output_cases.json`, `evals/cases/superleads_markdown_delivery_cases.json`, `evals/user_visible_outputs/*.md`
- Test: `tests/test_user_visible_boundary_projection.py`

- [ ] **Step 1: Write failing projection tests.**

  Render initial discovery, full workbook, Markdown and background CSV/XLSX projections. Assert they do not contain `重点开发`, `推荐跟进`, `暂不建议`, `开发建议`, `值不值得继续跟`, `可优先人工跟进` or equivalent positive English commercial judgments. Assert a negated policy boundary such as `不替用户推荐跟进` remains valid. Assert standard-list delivery explains mechanical filtering using user-provided rules and verified public information.

- [ ] **Step 2: Run the focused test to verify RED.**

  Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_user_visible_boundary_projection.py -v`

  Expected: failure because current exporters and background reports emit the legacy decision wording.

- [ ] **Step 3: Replace visible decision language at the source.**

  Keep internal disposition enums untouched. Map output partitions to evidence labels such as `公开信号已匹配当前范围`, `主体待确认`, `公开信号不足`, `来源受限`, and `命中用户明确排除条件`. Rename visible sheets and headings to `公开信息与待核查事项` and `是否具备继续核验基础`. Do not emit outreach priority, recommendation, or customer-value conclusions in CSV/XLSX/Markdown.

- [ ] **Step 4: Strengthen the visible-output validator and fixtures.**

  Forbid the Chinese and English positive recommendation expressions with the existing negated-context allowance. Update positive fixtures and delivery assertions to require factual evidence states instead of a follow-up recommendation.

- [ ] **Step 5: Verify GREEN.**

  Run focused tests, user-visible-output evals and Markdown-delivery evals. Confirm direct background workbook output does not rely on Markdown sanitization.

### Task 5: Integration and Package Validation

**Files:**
- Modify only files identified by failures from Tasks 1-4.

- [ ] **Step 1: Review the changed surface for spec compliance.**

  Check that metadata/help/material paths remain zero-I/O, no installed cache or temporary directory is read, no version changed, and no formal evidence gate was weakened.

- [ ] **Step 2: Run integration verification.**

  Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
  PYTHONDONTWRITEBYTECODE=1 python3 evals/run_evals.py --suite all
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_superleads_plugin_distribution.py --root . --format json
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_superleads_plugin_package.py --output /tmp/superleads-ux-package
  PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_superleads_plugin_distribution.py --root /tmp/superleads-ux-package --runtime-package --format json
  git diff --check
  ```

  Expected: all commands succeed; the temporary package contains no enabled SessionStart update hook.

- [ ] **Step 3: Do not commit, push, bump a version, or touch caches.**

  Preserve unrelated untracked `.superpowers/`, `tmp85wn8sri/`, and `tmp/stage5_chillys/` content.
