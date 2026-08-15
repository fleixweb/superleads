# Codex Web Run Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Superleads formally use Codex's built-in `web__run.search_query` and `web__run.open` operations without weakening the current source-evidence gates.

**Architecture:** Add a dedicated `codex_cli_web_run` capability adapter beside the existing native `web_search` and shell HTTP adapters. It maps only verified `search_query` and `open` operations to `search.web` and `source.open`; existing SearchLog and Observation authorization continues to use the adapter's explicit concrete-tool allowlist.

**Tech Stack:** Python standard library, JSON Schema, JSON fixtures, existing Superleads eval runners.

---

### Task 1: Specify And Test The Adapter Contract

**Files:**
- Create: `evals/fixtures/preflight_codex_web_run_open_source_verified.json`
- Create: `evals/fixtures/preflight_codex_web_run_search_only.json`
- Create: `evals/fixtures/preflight_codex_web_run_open_incomplete.json`
- Modify: `evals/cases/capability_adapter_cases.json`

- [x] Add a passing preflight fixture using this exact provider shape:

```json
{
  "adapter": {"adapter_id": "codex_cli_web_run", "adapter_version": "1"},
  "host_tools": {"web__run": {"status": "available", "operations": {
    "search_query": {"status": "verified"},
    "open": {"status": "verified", "original_url": "https://example.com", "source_title": "Example", "raw_excerpt": "Visible source text.", "excerpt_locator": "main"}
  }}},
  "canonical_capabilities": {"search.web": "available", "source.open": "available"}
}
```

- [x] Add a search-only fixture that maps `source.open` to `unknown` and remains blocked.
- [x] Add a fixture whose verified `open` operation lacks a required verbatim excerpt; it must be rejected.
- [x] Run `python3 scripts/preflight_capabilities.py --input evals/fixtures/preflight_codex_web_run_open_source_verified.json --require-formal-research --format json`.
- [x] Confirm it fails before implementation because `codex_cli_web_run` is unsupported.

### Task 2: Implement And Schema The Adapter

**Files:**
- Modify: `scripts/_superleads_common.py`
- Modify: `shared/schemas/run.schema.json`

- [x] Add constants for `codex_cli_web_run` version `1`, its two owned capabilities, and concrete tool `web__run`.
- [x] Implement resolver rules: `search_query.status=verified` is required for `search.web`; `open.status=verified` plus public URL, title, verbatim excerpt, and locator is required for `source.open`.
- [x] Register the resolver without changing existing adapter behavior.
- [x] Add an equivalent JSON Schema branch requiring only `web__run`, `search_query`, and `open` operation fields.
- [x] Run the three preflight fixtures and confirm ready, blocked, and rejected outcomes respectively.

### Task 3: Verify Formal Graph Authorization

**Files:**
- Create: `evals/fixtures/pass_codex_web_run_open_source_verified_standard_delivery.json`
- Modify: `evals/cases/targeting_contract_cases.json`

- [x] Extend the existing standard-delivery graph fixture with `concrete_tool: "web__run"` and a matching verified adapter report.
- [x] Refresh only the fixture's deterministic review hashes after the semantic fixture change.
- [x] Run the existing targeting contract suite and confirm a verified adapter authorizes the graph without changing Claim, Source, or contact evidence rules.

### Task 4: Document The Native Workflow And Ship The Runtime Package

**Files:**
- Modify: `shared/policies/platform-adapters.md`
- Modify: `shared/references/codex-native-web-search-host-acceptance.md`
- Modify: `skills/analyzing-product-outbound-market/SKILL.md`

- [x] Document `web__run.search_query` and `web__run.open` as the preferred Codex-native pathway when exposed.
- [x] State that `click`, `find`, `screenshot`, and `image_query` do not independently grant a formal capability.
- [x] Run capability, product-market, route, markdown, and default regressions.
- [x] Rebuild `dist/superleads`, validate distribution, reinstall local `superleads@fleix`, and compare the runtime package with the cache.
