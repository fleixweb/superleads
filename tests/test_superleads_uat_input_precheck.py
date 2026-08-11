#!/usr/bin/env python3
"""Regression coverage for the fast real-business UAT input precheck."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRECHECK = ROOT / "scripts" / "precheck_superleads_uat_input.py"
FIXTURES = ROOT / "evals" / "fixtures"


class SuperleadsUatInputPrecheckTest(unittest.TestCase):
    def _write(self, directory: Path, name: str, payload: dict[str, object]) -> Path:
        path = directory / name
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _run(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(PRECHECK), *args, "--format", "json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.assertEqual(result.returncode, expected, result.stdout)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        return payload

    def test_all_three_routes_accept_existing_pass_graphs(self) -> None:
        cases = (
            ("bulk_customer_development", FIXTURES / "pass_default_discovery_candidate_pool.json"),
            ("customer_background_research", FIXTURES / "pass_customer_background_chillys_markdown.json"),
            ("product_outbound_market_analysis", FIXTURES / "market_pass_xingheng_minimum_boundary.json"),
        )
        for route, graph in cases:
            with self.subTest(route=route):
                payload = self._run("--route", route, "--graph", str(graph))
                self.assertTrue(payload["ok"])
                self.assertTrue(payload["precheck_only"])
                self.assertEqual(payload["issue_count"], 0)

    def test_research_contact_literal_association_and_enum_fail_before_validator(self) -> None:
        graph = json.loads((FIXTURES / "pass_default_discovery_candidate_pool.json").read_text(encoding="utf-8"))
        graph["contact_points"][0]["source_literal"] = "not present in the opened source"
        graph["contact_points"][0]["contact_type"] = "invented_contact_type"
        graph["contact_claims"][0]["association_evidence_text"] = "not present association evidence"

        with tempfile.TemporaryDirectory() as tmp:
            path = self._write(Path(tmp), "bad-bulk.json", graph)
            payload = self._run("--route", "bulk_customer_development", "--graph", str(path), expected=1)

        codes = {item["code"] for item in payload["issues"]}
        self.assertIn("uat_precheck_enum_invalid", codes)
        self.assertIn("uat_precheck_contact_literal_not_in_observation", codes)
        self.assertIn("uat_precheck_contact_association_not_in_observation", codes)
        self.assertIn("uat_precheck_contact_association_entity_name_missing", codes)

    def test_market_notes_and_attribute_projection_fail_before_compile_or_validator(self) -> None:
        graph = json.loads((FIXTURES / "market_pass_xingheng_minimum_boundary.json").read_text(encoding="utf-8"))
        graph["attributes"][0]["attribute_name"] = "未投影属性"
        graph["attributes"][0]["attribute_family"] = "用户提供产品资料"
        notes = {
            "product_attributes": [],
            "evidence_notes": [
                {
                    "evidence_note_id": "note-precheck-quote",
                    "observation_id": "observation-xh-product-spec",
                    "status": "preliminary_reference",
                    "source_excerpt_quote": "not visible in source",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            graph_path = self._write(directory, "market.json", graph)
            notes_path = self._write(directory, "notes.json", notes)
            payload = self._run(
                "--route",
                "product_outbound_market_analysis",
                "--graph",
                str(graph_path),
                "--notes",
                str(notes_path),
                expected=1,
            )

        codes = {item["code"] for item in payload["issues"]}
        self.assertIn("uat_precheck_market_note_quote_not_in_observation", codes)
        self.assertIn("uat_precheck_product_attribute_not_projected", codes)


if __name__ == "__main__":
    unittest.main()
