#!/usr/bin/env python3
"""Regression tests for per-Observation Codex source-open provenance."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
sys.path.insert(0, str(ROOT / "scripts"))

from run_evals import _load_fixture_graph  # type: ignore[import-not-found]
import capture_public_http_source
import validate_product_market_analysis
import validate_research_graph


FIXTURE = ROOT / "evals" / "fixtures" / "market_pass_codex_web_run_open_source_verified.json"
BACKGROUND_FIXTURE = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"


class CapabilityAdapterObservationBindingTest(unittest.TestCase):
    def test_open_operation_must_match_observation_source_metadata(self) -> None:
        graph = _load_fixture_graph(FIXTURE)
        operation = graph["runs"][0]["capability_adapter_report"]["host_tools"]["web__run"]["operations"]["open"][0]
        operation["original_url"] = "https://unrelated.example/source"

        issues = validate_product_market_analysis.validate_graph(graph)

        self.assertIn("market_codex_observation_open_operation_mismatch", {item["code"] for item in issues})

    def test_multi_run_observation_must_declare_run_id(self) -> None:
        graph = _load_fixture_graph(FIXTURE)
        second_run = copy.deepcopy(graph["runs"][0])
        second_run["run_id"] = "run-other"
        graph["runs"].append(second_run)
        graph["observations"][0]["run_id"] = None

        issues = validate_product_market_analysis.validate_graph(graph)

        self.assertIn("market_observation_run_id_missing", {item["code"] for item in issues})

    def test_one_open_operation_cannot_be_reused_for_two_observations(self) -> None:
        graph = _load_fixture_graph(FIXTURE)
        operations = graph["runs"][0]["capability_adapter_report"]["host_tools"]["web__run"]["operations"]["open"]
        del operations[1]
        graph["sources"][1]["canonical_url"] = graph["sources"][0]["canonical_url"]
        graph["sources"][1]["final_url"] = graph["sources"][0]["final_url"]
        for field in ("title", "raw_excerpt", "page_or_dom_locator"):
            graph["observations"][1][field] = graph["observations"][0][field]

        issues = validate_product_market_analysis.validate_graph(graph)

        self.assertIn("market_codex_observation_open_operation_reused", {item["code"] for item in issues})

    def test_batch_capture_emits_one_open_operation_per_observation(self) -> None:
        pages = {
            "https://a.example/one": (200, "https://a.example/one", "text/html", b"<html><title>A</title><body>first text</body></html>"),
            "https://b.example/two": (200, "https://b.example/two", "text/html", b"<html><title>B</title><body>second text</body></html>"),
        }

        with patch.object(capture_public_http_source, "_run_curl", side_effect=lambda url: pages[url]):
            result = capture_public_http_source.capture(list(pages))

        operations = result["capability_adapter_reports"][0]["host_tools"]["shell_http"]["operations"]["open_source"]
        self.assertIsInstance(operations, list)
        self.assertEqual(len(operations), len(result["observations"]))
        self.assertEqual({item["original_url"] for item in operations}, set(pages))

    def test_forbidden_observation_requires_its_own_failed_open_operation(self) -> None:
        graph = _load_fixture_graph(BACKGROUND_FIXTURE)
        sources = {item["source_id"]: item for item in graph["sources"]}
        opened_observations = [
            item for item in graph["observations"]
            if item["capability"] == "source.open" and item["access_status"] == "ok"
        ]
        forbidden = next(item for item in graph["observations"] if item["access_status"] == "forbidden")

        def operation(observation: dict[str, object], status: str) -> dict[str, object]:
            source = sources[observation["source_id"]]
            record = {
                "status": status,
                "request_method": "GET",
                "original_url": source["canonical_url"],
                "final_url": source["final_url"],
                "source_id": observation["source_id"],
                "observation_id": observation["observation_id"],
                "source_title": observation["title"],
                "raw_excerpt": observation["raw_excerpt"],
                "excerpt_locator": observation["page_or_dom_locator"],
            }
            if status == "verified":
                record["http_status"] = observation["http_status"]
            return record

        graph["runs"][0]["capability_adapter_report"]["host_tools"]["shell_http"]["operations"]["open_source"] = [
            *(operation(item, "verified") for item in opened_observations),
            operation(forbidden, "failed"),
        ]

        issues = validate_research_graph.validate_graph(graph)

        self.assertNotIn("codex_observation_open_operation_mismatch", {item["code"] for item in issues})


if __name__ == "__main__":
    unittest.main()
