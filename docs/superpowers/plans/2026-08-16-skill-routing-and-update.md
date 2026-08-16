# Superleads Skill Routing And Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make three public Superleads routes predictable, keep internal stages context-bound, and make version/update behavior explicit, local-first, and non-blocking.

**Architecture:** Preserve the existing deterministic intake router and evidence model. Add pure helpers for invocation contracts, user-facing stage summaries, and structured explicit update results; route all lightweight requests before research detection. Package only runtime dependencies and reject legacy startup/update hook scripts.

**Tech Stack:** Python 3 standard library, JSON/YAML/Markdown plugin metadata, `unittest`, existing `scripts/` distribution checks, and `evals/` route suites.

---

## File Map

| File | Responsibility |
| --- | --- |
| `scripts/superleads_task_modes.py` | Pure metadata detection, active-root version reads, explicit structured update checks, one-time terminal update notices. |
| `scripts/route_superleads_intake.py` | One-route intake priority, metadata/status/contact/export/feedback routing and static-stage responses. |
| `scripts/superleads_invocation_contract.py` | Pure validation of internal-stage prerequisite context and concise stop responses. |
| `scripts/superleads_execution_state.py` | Recorded-state-only, user-facing stage summary without internal identifiers. |
| `scripts/superleads_composite_tasks.py` | Pure parent/subroute planning, dependency gating, evidence-use isolation, and aggregate status. |
| `scripts/superleads_user_guidance.py` | Static public guidance with exactly three business routes and non-decision boundaries. |
| `scripts/export_superleads_markdown.py`, `scripts/export_workbook.py` | Append recorded terminal stage summary and at-most-once cached update notice outside business evidence. |
| `scripts/build_superleads_plugin_package.py`, `scripts/check_superleads_plugin_distribution.py` | Exclude legacy hooks and reject automatic remote-update hook artifacts. |
| `skills/*/agents/openai.yaml`, `skills/*/SKILL.md`, `.codex-plugin/plugin.json` | Three public entries; explicit internal-stage labels, triggers, and prerequisite stops. |
| `docs/TERMS.md`, `docs/INSTALL-AND-UPDATE.md`, `docs/INSTALL-AND-UPDATE.en.md`, `docs/PRIVACY.md` | Document explicit-only update behavior and no customer-data update cache. |
| `tests/`, `evals/cases/superleads_route_cases.json`, `evals/run_superleads_plugin_distribution_evals.py` | Regression proof for all new contracts and package contents. |

### Task 1: Structured Explicit Update Contract And Hook-Free Runtime Package

**Files:**
- Modify: `tests/test_superleads_task_modes.py`
- Modify: `scripts/superleads_task_modes.py`
- Modify: `tests/test_superleads_plugin_distribution.py`
- Modify: `scripts/build_superleads_plugin_package.py`
- Modify: `scripts/check_superleads_plugin_distribution.py`
- Delete: `hooks/session-start`, `hooks/codex-session-start.ps1`, `hooks/hooks.json`, `hooks/codex-hooks.json`
- Modify: `docs/TERMS.md`, `docs/INSTALL-AND-UPDATE.md`, `docs/INSTALL-AND-UPDATE.en.md`, `docs/PRIVACY.md`

- [ ] **Step 1: Write failing update and package tests**

```python
def test_explicit_update_returns_structured_release_result_and_reuses_host_cache(self):
    cache = {}
    calls = []
    result = check_latest_version(
        lambda: calls.append(True) or {
            "version": "0.2.0", "source_kind": "github_release",
            "source_url": "https://github.com/fleixweb/superleads/releases/tag/v0.2.0",
        },
        cache,
        local_version="0.1.20",
        checked_at="2026-08-16T00:00:00Z",
    )
    self.assertEqual("update_available", result["status"])
    self.assertEqual(1, len(calls))
    self.assertEqual(result, check_latest_version(None, cache, local_version="0.1.20"))

def test_branch_manifest_is_repository_version_not_latest_stable(self):
    result = normalize_remote_version({"version": "0.2.0", "branch": "master"})
    self.assertEqual("repository_version", result["source_kind"])
    self.assertFalse(result["stable"])
```

Add distribution tests that expect `hooks/` to be absent from a built package and reject a source/runtime package containing a SessionStart/resume hook or a command fetching a remote manifest automatically.

- [ ] **Step 2: Run the focused RED tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_task_modes.py tests/test_superleads_plugin_distribution.py -v`

Expected: failures identifying the legacy string-only version result and shipped hook directory.

- [ ] **Step 3: Implement minimal explicit-only update and package behavior**

Add a `VersionCheckResult`-shaped dictionary containing `local_version`, `remote_version`, `source_kind`, `source_url`, `checked_at`, `status`, and optional `release_url`. Read local version only through `read_active_plugin_version(active_root)`. Cache the structured result only in the supplied mutable session mapping, never module-global state. Treat a failing/missing fetch as `check_failed`/`not_checked`; only label a GitHub Release result as stable.

Remove the legacy hook directory from source. Change `RUNTIME_DIRECTORIES` to omit `hooks`, make runtime validation forbid it, and scan any remaining hook configuration for SessionStart/resume or remote-manifest fetches. Keep normal metadata/research paths fetch-free.

- [ ] **Step 4: Run GREEN tests and refactor**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_task_modes.py tests/test_superleads_plugin_distribution.py -v`

Expected: all selected tests pass. Keep the remote parser injected and free of live GitHub dependency.

### Task 2: Invocation Contract And Deterministic Route Priority

**Files:**
- Create: `tests/test_superleads_invocation_contract.py`
- Create: `scripts/superleads_invocation_contract.py`
- Modify: `tests/test_superleads_task_modes.py`
- Modify: `scripts/route_superleads_intake.py`
- Modify: `evals/cases/superleads_route_cases.json`

- [ ] **Step 1: Write failing context and priority tests**

```python
def test_export_stage_stops_without_current_validated_graph(self):
    verdict = validate_internal_invocation("exporting-lead-workbooks", {"route": "batch_discovery"})
    self.assertFalse(verdict["allowed"])
    self.assertIn("当前可导出的", verdict["user_message"])

def test_contact_stage_requires_opened_current_run_source(self):
    verdict = validate_internal_invocation("collecting-contact-intelligence", {
        "route": "customer_background_research", "run_id": "run-1", "brief": True,
    })
    self.assertFalse(verdict["allowed"])

def test_one_object_contact_beats_batch_and_export_help_stays_metadata(self):
    self.assertEqual("single_object_contact", classify("只找这家公司的公开邮箱 example.com")["route"])
    self.assertEqual("metadata", classify("How do I export?")["route"])
```

Add route cases for current status, a single-company contact check, export with and without `current_result_valid`, correction-only feedback, explicit durable feedback consent, and all existing public business routes.

- [ ] **Step 2: Run RED tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_invocation_contract.py tests/test_superleads_task_modes.py -v`

Expected: import failures or incorrect `unknown`/table-enrichment routes.

- [ ] **Step 3: Implement the pure contract and ordered route branches**

Create `validate_internal_invocation(stage, context)` with a declarative prerequisite mapping. It must not read files, call tools, construct research objects, or mutate feedback. Return `{"allowed": False, "missing": [...], "user_message": ...}` on invalid context. In the router, evaluate metadata first, then provided-material triage, specified object/contact, batch discovery, market analysis, table enrichment, legal export, and formal mode. Ensure an export word does not choose table enrichment and feedback defaults to a current-run correction unless explicit persistent-save consent is present.

- [ ] **Step 4: Run GREEN route and contract tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_invocation_contract.py tests/test_superleads_task_modes.py -v && PYTHONDONTWRITEBYTECODE=1 python3 evals/run_superleads_route_evals.py --suite all`

Expected: all selected tests and route cases pass with exactly one primary route per request.

### Task 3: Composite Parent Tasks, Dependencies, And Isolated Delivery

**Files:**
- Create: `scripts/superleads_composite_tasks.py`
- Create: `tests/test_superleads_composite_tasks.py`
- Modify: `scripts/route_superleads_intake.py`
- Modify: `scripts/superleads_execution_state.py`
- Modify: `scripts/export_superleads_markdown.py`
- Modify: `tests/test_superleads_execution_state.py`, `tests/test_export_superleads_markdown.py`
- Modify: `evals/cases/superleads_route_cases.json`

- [ ] **Step 1: Write failing composite route and evidence-isolation tests**

```python
def test_company_and_market_request_creates_two_independent_subroutes(self):
    parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")
    self.assertEqual("composite", parent["route"])
    self.assertEqual(
        ["customer_background_research", "product_market_analysis"],
        [item["route"] for item in parent["subtasks"]],
    )

def test_missing_market_input_does_not_block_background_subroute(self):
    parent = plan_composite_task("调查 ABC GmbH，并分析出口市场准入")
    background, market = parent["subtasks"]
    self.assertEqual("ready", background["status"])
    self.assertEqual("waiting_for_required_input", market["status"])

def test_source_use_is_scoped_and_cannot_cross_promote_fact_domains(self):
    use = register_subtask_source_use("company", "https://abc.example", "company_business")
    self.assertFalse(source_use_can_support(use, "market_access"))
```

Add route/eval cases for company plus market, batch plus contact, market plus candidate discovery, background plus supplied table, a restricted subroute alongside a completed subroute, and no decision or intent wording in the combined output.

- [ ] **Step 2: Run RED tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_composite_tasks.py tests/test_superleads_task_modes.py -v`

Expected: absent composite planner or an incorrectly singular route result.

- [ ] **Step 3: Implement minimal composite orchestration**

Implement a pure `plan_composite_task(text, supplied_context=None)` that returns a parent with independent declared subtasks, their explicit dependencies, required-input gaps, and valid scheduling hints. It must never infer a product, country, company relationship, or evidence. Extend router output to carry a composite parent only when more than one explicit business subroute is detected. Reuse opened URL references by normalized URL but require a distinct `subtask_id`, `purpose`, `fact_domain`, and observation boundary for every subtask use. Add parent-status and Markdown-section helpers that aggregate recorded subtask states without changing evidence status or exposing internal fields.

- [ ] **Step 4: Run GREEN composite tests and refactor**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_composite_tasks.py tests/test_superleads_task_modes.py tests/test_superleads_execution_state.py tests/test_export_superleads_markdown.py -v && PYTHONDONTWRITEBYTECODE=1 python3 evals/run_superleads_route_evals.py --suite all`

Expected: all selected tests pass. Confirm the host-facing result describes scheduling as a capability-gated plan, not fictitious concurrent execution.

### Task 4: Public Skill Surface And Internal-Stage Preconditions

**Files:**
- Create: `tests/test_superleads_skill_exposure.py`
- Modify: `.codex-plugin/plugin.json`
- Modify: `skills/using-superleads/agents/openai.yaml`, `skills/researching-customer-background/agents/openai.yaml`, `skills/analyzing-product-outbound-market/agents/openai.yaml`
- Modify: `skills/{assessing-research-evidence,collecting-contact-intelligence,executing-research-plans,exporting-lead-workbooks,learning-from-feedback,resolving-company-identity,reviewing-lead-research,scoping-lead-research,verification-before-delivery,writing-research-plans}/agents/openai.yaml`
- Modify: corresponding internal `SKILL.md` files and `skills/using-superleads/SKILL.md`

- [ ] **Step 1: Write failing exposure tests and pressure scenarios**

```python
def test_only_three_skill_configs_are_described_as_public_business_entries(self):
    configs = read_skill_interfaces(ROOT / "skills")
    self.assertEqual({"using-superleads", "researching-customer-background", "analyzing-product-outbound-market"}, public_skill_names(configs))

def test_internal_stage_configs_state_parent_route_and_no_bare_prompt(self):
    interface = read_yaml_interface("collecting-contact-intelligence")
    self.assertIn("内部阶段", interface["display_name"])
    self.assertIn("不要直接", interface["default_prompt"])
```

Record the baseline generic default-prompt behavior for a bare internal export/contact request in the test fixture or test documentation before changing the Skill text.

- [ ] **Step 2: Run RED test and existing Skill/package checks**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_skill_exposure.py -v`

Expected: current generic internal descriptions/default prompts fail the public/internal distinction.

- [ ] **Step 3: Implement consistent user and internal Skill metadata**

Make the plugin default prompt name the three public business entries and their non-decision evidence limits. Narrow `using-superleads` to batch discovery. Give the two other public skills foreign-trade, fact-bound descriptions. Label every other `openai.yaml` “内部阶段”, state its exact parent-route trigger and prerequisite context, and say a bare direct call must stop rather than create a report. Align SKILL.md precondition wording with the new invocation contract; do not create an English duplicate Skill.

- [ ] **Step 4: Run GREEN Skill tests and validators**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_skill_exposure.py -v && python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads`

Expected: tests and Skill structure validation pass.

### Task 5: Recorded User-Visible Stage Summary And Terminal Notice Placement

**Files:**
- Modify: `tests/test_superleads_execution_state.py`
- Modify: `scripts/superleads_execution_state.py`
- Modify: `scripts/superleads_user_guidance.py`
- Modify: `scripts/export_superleads_markdown.py`
- Modify: `scripts/export_workbook.py`
- Modify: `tests/test_export_superleads_markdown.py`, `tests/test_export_workbook.py`

- [ ] **Step 1: Write failing projection and placement tests**

```python
def test_user_stage_summary_uses_only_recorded_counts_and_hides_internal_fields(self):
    summary = user_visible_stage_summary({
        "phase": "source_open", "run_id": "run-secret", "opened_sources": 3,
        "source_restricted": 1, "unexecuted": 2,
    }, language="zh")
    self.assertIn("已打开来源 3", summary)
    self.assertNotIn("run-secret", summary)

def test_terminal_notice_is_once_and_not_written_to_graph_or_basis_rows(self):
    rendered = append_terminal_update_notice("报告正文", update_result, session_cache={})
    self.assertIn("发现可用更新", rendered)
    self.assertNotIn("Claim", rendered)
```

Cover no-state fallback, English language choice, material-triage wording without “Run/Brief”, and no false streaming claims.

- [ ] **Step 2: Run RED tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_execution_state.py tests/test_export_superleads_markdown.py tests/test_export_workbook.py -v`

Expected: missing formatter/notice APIs or leakage failures.

- [ ] **Step 3: Implement projection-only delivery behavior**

Add a pure formatter that emits only observed counts and permitted fact-status language. Give static material triage a non-technical response. Extend terminal exporters only when execution state exists, placing a short stage summary and a cached one-time update notice after user delivery and outside graph/evidence structures. Do not add fake real-time status, network calls, or new persistent state.

- [ ] **Step 4: Run GREEN tests**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_superleads_execution_state.py tests/test_export_superleads_markdown.py tests/test_export_workbook.py -v`

Expected: selected delivery tests pass with no internal-token leakage.

### Task 6: End-To-End Regression, Distribution, And Scope Review

**Files:**
- Modify only test/eval fixtures needed after Tasks 1-4.

- [ ] **Step 1: Add failing boundary regression cases**

Add fixture cases proving no startup/help/version/ordinary-research fetch; active-root version ignores old temporary manifests; search snippets cannot become Claims; restricted sources stay restricted; guessed/cross-subject contacts are rejected; market requests execute only requested modules; checkpoint restoration preserves Run boundaries.

- [ ] **Step 2: Run RED cases before any corresponding compatibility adjustment**

Run: targeted `unittest` module or evaluation runner for each new fixture.

Expected: failure only on the absent contract, not environmental network availability.

- [ ] **Step 3: Make minimal compatibility adjustments**

Adjust only the modules established above. Preserve schemas, evidence validators, existing public source restrictions, and all user worktree changes. Do not change plugin version, install a cache, or touch historical runtime data.

- [ ] **Step 4: Run full verification**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 python3 evals/run_evals.py --suite all
PYTHONDONTWRITEBYTECODE=1 python3 evals/advanced_gate_tests.py --suite all
PYTHONDONTWRITEBYTECODE=1 python3 evals/run_superleads_route_evals.py --suite all
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_superleads_plugin_distribution.py --plugin-root . --source-root . --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build_superleads_plugin_package.py --output /tmp/superleads-routing-package --format json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/check_superleads_plugin_distribution.py --plugin-root /tmp/superleads-routing-package --source-root . --runtime-package --format json
git diff --check
```

Expected: all commands exit zero, the source and temporary runtime package validate, and the final diff has no whitespace errors. Inspect `git status --short` to verify no installed cache, backup, temporary research data, version change, commit, or push was created.
