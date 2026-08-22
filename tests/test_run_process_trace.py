#!/usr/bin/env python3
"""TDD coverage for the Run-local process trace contract."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evals"))

from run_evals import _load_fixture_graph  # type: ignore[import-not-found]
from schema_validation import schema_validation_errors
import audit_delivery
import validate_research_graph


def _research_graph_with_trace() -> dict[str, object]:
    graph = _load_fixture_graph(ROOT / "evals/fixtures/pass_default_discovery_candidate_pool.json")
    run = graph["runs"][0]
    run["tool_attempts"] = [{
        "attempt_id": "att-1",
        "sequence": 1,
        "capability": "search.web",
        "adapter_id": "codex_cli_web_run",
        "operation": "search_query",
        "outcome": "verified",
        "failure_class": "not_applicable",
        "search_log_id": graph["search_logs"][0]["search_log_id"],
        "observation_id": None,
        "notes": "internal trace",
    }]
    run["runtime_provenance"] = {
        "interpreter_source": "system",
        "runtime_installation": "not_observed",
        "temporary_dependency_directory": "not_observed",
        "pythonpath_modified": "not_observed",
        "borrowed_environment": "not_observed",
        "provenance_status": "assessed",
        "notes": "internal trace",
    }
    return graph


class TraceSchemaTest(unittest.TestCase):
    def test_legacy_run_without_trace_still_validates(self) -> None:
        graph = json.loads(
            (ROOT / "shared/references/default-discovery-reference.example.json").read_text(encoding="utf-8")
        )
        self.assertEqual([], schema_validation_errors(graph, ROOT / "shared/schemas/research-graph.schema.json"))

    def test_valid_trace_is_optional_and_accepts_system_fallback(self) -> None:
        graph = _research_graph_with_trace()
        errors = schema_validation_errors(graph, ROOT / "shared/schemas/research-graph.schema.json")
        self.assertEqual([], errors)

    def test_trace_rejects_unknown_properties_and_invalid_failure_class(self) -> None:
        graph = _research_graph_with_trace()
        attempt = graph["runs"][0]["tool_attempts"][0]
        attempt["unexpected"] = True
        attempt["failure_class"] = "empty_probe"
        errors = schema_validation_errors(graph, ROOT / "shared/schemas/research-graph.schema.json")
        self.assertTrue(any("additional" in error["message"].lower() for error in errors), errors)
        self.assertTrue(any("failure_class" in error["path"] for error in errors), errors)

    def test_product_market_run_accepts_optional_trace_fields(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/market_pass_codex_web_run_open_source_verified.json")
        run = graph["runs"][0]
        run["tool_attempts"] = [{
            "attempt_id": "att-market-1",
            "sequence": 1,
            "capability": "source.open",
            "adapter_id": "codex_cli_web_run",
            "operation": "open",
            "outcome": "verified",
            "failure_class": "not_applicable",
            "search_log_id": None,
            "observation_id": graph["observations"][0]["observation_id"],
            "notes": None,
        }]
        run["runtime_provenance"] = {"interpreter_source": "host_runtime"}
        errors = schema_validation_errors(graph, ROOT / "shared/schemas/product-market-analysis.schema.json")
        self.assertEqual([], errors)


class TraceSchemaMetadataTest(unittest.TestCase):
    def test_trace_identifier_set_is_derived_from_schema(self) -> None:
        from _superleads_common import trace_schema_metadata

        metadata = trace_schema_metadata()
        self.assertIn("attempt_id", metadata["direct_identifiers"])
        self.assertIn("runtime_installation", metadata["direct_identifiers"])
        for name in metadata["direct_identifiers"]:
            self.assertIn("_", name)
        self.assertIn("capability", metadata["structured_keys"])
        self.assertIn("outcome", metadata["structured_keys"])


class ResearchTraceValidationTest(unittest.TestCase):
    def _assert_trace_issue(self, fixture_name: str, code: str, severity: str) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / fixture_name)
        issues = validate_research_graph.validate_graph(graph)
        matches = [item for item in issues if item.get("code") == code]
        self.assertTrue(matches, f"missing {code}: {issues}")
        self.assertTrue(any(item.get("severity") == severity for item in matches), matches)

    def test_not_found_retry_is_critical(self) -> None:
        self._assert_trace_issue("fail_trace_not_found_retry.json", "adapter_retry_after_failure", "critical")

    def test_missing_tool_retry_is_critical(self) -> None:
        self._assert_trace_issue("fail_trace_missing_tool_retry.json", "adapter_retry_after_failure", "critical")

    def test_timeout_one_retry_then_verified_is_major_only(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_trace_timeout_retry_success.json")
        issues = validate_research_graph.validate_graph(graph)
        retry_issues = [item for item in issues if item.get("code") == "adapter_retry_after_failure"]
        self.assertTrue(retry_issues, issues)
        self.assertTrue(all(item.get("severity") == "major" for item in retry_issues), retry_issues)

    def test_timeout_second_retry_is_major_only(self) -> None:
        self._assert_trace_issue("fail_trace_timeout_retry_over_limit.json", "adapter_retry_after_failure", "major")

    def test_verified_search_attempt_requires_same_run_search_log(self) -> None:
        self._assert_trace_issue("fail_trace_attempt_binding_missing.json", "attempt_result_binding_missing", "major")

    def test_verified_open_attempt_requires_same_run_observation(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "fail_trace_attempt_binding_missing.json")
        paths = [item.get("path", "") for item in validate_research_graph.validate_graph(graph) if item.get("code") == "attempt_result_binding_missing"]
        self.assertTrue(any("observation_id" in path for path in paths), paths)

    def test_empty_verified_probe_used_for_authorization_is_critical(self) -> None:
        self._assert_trace_issue("fail_trace_empty_probe_used.json", "empty_capability_probe", "critical")

    def test_empty_verified_probe_not_used_is_major_and_non_blocking_in_audit(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_trace_empty_probe_unused.json")
        issues = validate_research_graph.validate_graph(graph)
        self.assertTrue(any(item.get("code") == "empty_capability_probe" and item.get("severity") == "major" for item in issues), issues)
        self.assertTrue(audit_delivery.audit_graph(graph)["ok"])

    def test_runtime_other_application_is_critical(self) -> None:
        self._assert_trace_issue("fail_trace_runtime_self_service.json", "runtime_self_service_violation", "critical")

    def test_system_interpreter_is_legal(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_trace_system_fallback.json")
        self.assertNotIn("runtime_self_service_violation", {item.get("code") for item in validate_research_graph.validate_graph(graph)})

    def test_unknown_or_missing_trace_is_not_assessed(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_trace_not_assessed.json")
        codes = {item.get("code") for item in validate_research_graph.validate_graph(graph)}
        self.assertNotIn("runtime_self_service_violation", codes)
        self.assertNotIn("adapter_retry_after_failure", codes)

    def test_claim_cannot_reference_attempt_id(self) -> None:
        self._assert_trace_issue("fail_trace_as_evidence.json", "trace_evidence_reference_forbidden", "critical")

    def test_candidate_pool_only_drops_impacted_search_or_observation_results(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "fail_trace_attempt_binding_missing.json")
        issues = validate_research_graph.validate_graph(graph)
        self.assertTrue(any(item.get("code") == "attempt_result_binding_missing" for item in issues), issues)
        self.assertNotIn("candidate_pool_trace_global_failure", {item.get("code") for item in issues})

    def test_new_trace_property_is_automatically_included(self) -> None:
        from _superleads_common import trace_schema_metadata

        schema = json.loads((ROOT / "shared/schemas/run.schema.json").read_text(encoding="utf-8"))
        schema["$defs"]["toolAttempt"]["properties"]["new_internal_token"] = {"type": "string"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.schema.json"
            path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
            metadata = trace_schema_metadata(path)
        self.assertIn("new_internal_token", metadata["direct_identifiers"])

    def test_future_single_word_property_lands_in_structured_keys(self) -> None:
        from _superleads_common import trace_schema_metadata

        schema = json.loads((ROOT / "shared/schemas/run.schema.json").read_text(encoding="utf-8"))
        schema["$defs"]["toolAttempt"]["properties"]["reason"] = {"type": "string"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.schema.json"
            path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
            metadata = trace_schema_metadata(path)
        self.assertIn("reason", metadata["structured_keys"])
        self.assertNotIn("reason", metadata["direct_identifiers"])

    def test_default_metadata_uses_cache_but_explicit_schema_path_bypasses_it(self) -> None:
        from _superleads_common import trace_schema_metadata

        first = trace_schema_metadata()
        second = trace_schema_metadata()
        self.assertIs(first, second)
        schema = json.loads((ROOT / "shared/schemas/run.schema.json").read_text(encoding="utf-8"))
        schema["$defs"]["toolAttempt"]["properties"]["reason"] = {"type": "string"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.schema.json"
            path.write_text(json.dumps(schema, ensure_ascii=False), encoding="utf-8")
            explicit = trace_schema_metadata(path)
        self.assertIn("reason", explicit["structured_keys"])
        self.assertNotIn("reason", first["structured_keys"])

    def test_single_word_properties_are_never_bare_word_blockers(self) -> None:
        from _superleads_common import trace_schema_metadata

        metadata = trace_schema_metadata()
        for name in metadata["direct_identifiers"]:
            self.assertIn("_", name)
        self.assertIn("capability", metadata["structured_keys"])
        self.assertIn("outcome", metadata["structured_keys"])


if __name__ == "__main__":
    unittest.main()
