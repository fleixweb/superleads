# Preflight Adapter Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure Codex preflight degrades every capability owned by a recognized Codex CLI adapter when its required adapter report is absent or invalid.

**Architecture:** Define one ordered aggregate of the ownership constants for the native web-search, `web__run`, and shell HTTP adapters. Consume that aggregate at each preflight downgrade point so future adapters only need to join the aggregate, rather than duplicate ownership unions in preflight.

**Tech Stack:** Python 3 standard library, `unittest`, existing Superleads capability-report helpers.

---

### Task 1: Centralize Preflight Adapter Ownership

**Files:**
- Modify: `scripts/_superleads_common.py:168-184`
- Modify: `scripts/preflight_capabilities.py:8-113`
- Test: `tests/test_preflight_capabilities.py`

- [x] **Step 1: Write the failing regression test**

```python
with patch.object(
    preflight_capabilities,
    "CODEX_CLI_ADAPTER_OWNED_CAPABILITIES",
    ("source.capture",),
    create=True,
):
    result = preflight_capabilities.preflight({
        "platform": "codex_cli",
        "capabilities": {"source.capture": "available"},
    })

self.assertEqual("unknown", result["capabilities"]["source.capture"]["status"])
```

- [x] **Step 2: Verify the test is red before the implementation**

Run: `python3 -m unittest tests/test_preflight_capabilities.py -v`

Expected: the preflight result preserves `source.capture` as `available`, proving that the hard-coded native/shell union does not cover a future single-capability adapter.

- [x] **Step 3: Add the aggregate ownership constant**

```python
CODEX_CLI_ADAPTER_OWNED_CAPABILITIES = tuple(dict.fromkeys((
    *CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES,
    *CODEX_WEB_RUN_OWNED_CAPABILITIES,
    *CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES,
)))
```

- [x] **Step 4: Use the aggregate in every preflight downgrade path**

Replace the native/shell set unions in `_missing_codex_adapter_result()`, `_invalid_platform_result()`, and the `codex_cli` self-reported-available capability check with `CODEX_CLI_ADAPTER_OWNED_CAPABILITIES`. Preserve the existing error code for compatibility while making its message adapter-neutral.

- [x] **Step 5: Verify the regression is green**

Run: `python3 -m unittest tests/test_preflight_capabilities.py -v`

Expected: `test_missing_adapter_report_invalidates_all_known_adapter_capabilities` passes and reports the existing adapter-report-required error code.

- [x] **Step 6: Cover an explicit but unusable report collection**

Add a second regression whose payload declares `capability_adapter_reports: []` together with self-reported available `search.web` and `source.open`. It must retain `capability_adapter_reports_empty` as diagnostics while both capabilities become `unknown`; an explicit empty collection is not evidence that the self-reported capabilities are available.

- [x] **Step 7: Reconcile adapter ownership per capability**

Use the aggregate as the Codex mapping scope even when some adapter reports are present. A shell-only report must not authorize a self-reported `search.web=available`, while an explicit `search.web=missing` remains a useful missing state.

- [x] **Step 8: Preserve valid providers in mixed report collections**

Add a regression with one valid `web__run` report and one malformed extra report. Retain the invalid-report diagnostic without erasing the valid report's `search.web` and `source.open` mappings.

### Task 2: Record and Verify the Patch Release

**Files:**
- Modify: `.codex-plugin/plugin.json:3`
- Modify: `.claude-plugin/plugin.json:3`
- Modify: `.claude-plugin/marketplace.json:11`
- Modify: `CHANGELOG.md:13-18`
- Modify: `HANDOFF.md:3-6`
- Modify: `TASKS.md:3-6`

- [x] **Step 1: Bump the source manifests to `0.1.20`**

Set the `version` value in all three manifests to `0.1.20`.

- [x] **Step 2: Record the observable behavior change**

Add a `0.1.20` changelog entry stating that absent adapter reports degrade capabilities owned by every recognized adapter, including future single-capability adapters. Update the top entries in `HANDOFF.md` and `TASKS.md` with the uncommitted state, verification scope, cache state, and preservation of `tmp/stage5_chillys/`.

- [x] **Step 3: Run focused and repository-wide verification**

Run:

```bash
python3 -m unittest tests/test_preflight_capabilities.py -v
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/_superleads_common.py scripts/preflight_capabilities.py
python3 evals/run_evals.py --suite all
python3 scripts/build_superleads_plugin_package.py --output /home/fleix/superleads/dist/superleads --format json
python3 scripts/check_superleads_plugin_distribution.py --plugin-root /home/fleix/superleads/dist/superleads --source-root /home/fleix/superleads --runtime-package --format json
git diff --check
```

Expected: every command exits `0`; the runtime package reports `ok: true`; no whitespace errors are reported.
