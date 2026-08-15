# Adapter Contract Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore source-open contract consistency and ensure runtime distribution contains only tracked runtime content.

**Architecture:** Keep the existing adapter resolver and schemas. Make failed-operation matching explicitly tolerant of omitted optional fields, keep shell-only scanning in the shell branch, and share the existing forbidden-name policy between recursive package build and package validation.

**Tech Stack:** Python 3 standard library, unittest, existing evaluation runners.

---

### Task 1: Failed Open Binding

**Files:**
- Modify: `tests/test_capability_adapter_observation_binding.py`
- Modify: `scripts/_superleads_common.py`

- [ ] Add a test using a schema-valid failed `source.open` operation containing only `status`, `source_id`, and `observation_id`; expect no open-operation mismatch.
- [ ] Run the test and verify it fails because current matching requires `original_url`, title, excerpt, and locator.
- [ ] Make matching require all present operation fields to agree, while requiring an explicit ID binding when the failed record lacks URL metadata; consume a later otherwise-identical verified record before reporting a reused operation.
- [ ] Re-run the focused test and the binding test module.

### Task 2: Shell Validation Scope

**Files:**
- Modify: `tests/test_capability_adapter_observation_binding.py`
- Modify: `scripts/validate_research_graph.py`

- [ ] Add a native-web source-open regression whose text matches the shell sensitive-data pattern; expect no shell-specific issue.
- [ ] Run the test and verify it fails with `codex_shell_http_observation_forbidden_data`.
- [ ] Move the sensitive-data scan back under the shell concrete-tool condition.
- [ ] Re-run the focused test and the binding test module.

### Task 3: Runtime Package Exclusions

**Files:**
- Modify: `tests/test_capture_public_http_source.py` or a focused distribution test module
- Modify: `scripts/build_superleads_plugin_package.py`
- Modify: `scripts/check_superleads_plugin_distribution.py`

- [ ] Add a test that creates a nested `.plugin-eval` directory in a source skill, builds a package, and asserts it is absent; inject the directory into a package and assert the distribution checker rejects it.
- [ ] Run the test and verify current recursive copy/check behavior fails the expected contract.
- [ ] Ignore forbidden runtime names in recursive copying and reject forbidden names at any package depth.
- [ ] Re-run the focused package test and a clean-export distribution build.

### Task 4: Release Records

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `HANDOFF.md`
- Modify: `TASKS.md`

- [ ] Reuse `SOURCE_OPEN_FAILED_ACCESS_STATUSES` for product-market restricted-source excerpt checks, including `login-wall`, and add a focused regression.
- [ ] Add concise version history for 0.1.6 through 0.1.19 from committed repository evidence.
- [ ] Add an up-to-date handoff/task entry containing the adapter-contract repair and required release checks.
- [ ] Verify documentation has no stale claim that the runtime package includes development artifacts.

### Final Verification

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 evals/run_product_market_analysis_evals.py --suite all`
- [ ] `python3 evals/run_evals.py --suite all`
- [ ] Build from a clean `HEAD` archive and run `check_superleads_plugin_distribution.py --runtime-package`.
- [ ] `git diff --check`
