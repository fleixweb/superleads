#!/usr/bin/env python3
"""Regression coverage for dependency-free bulk delivery exports."""
from __future__ import annotations

import contextlib
import html
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_workbook
import export_product_market_workbook as market_exporter
import validate_product_market_analysis
import validate_research_graph
from audit_delivery import audit_graph
from audit_product_market_analysis import audit_graph as audit_market_graph
from export_superleads_markdown import build_bulk_markdown, build_product_market_markdown
from schema_validation import SchemaResolutionError
from superleads_user_guidance import append_final_footer
from validate_superleads_user_visible_output import validate as validate_user_visible


DISCLOSURE = "本环境未运行确定性校验"
STANDARD_FIXTURE = ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json"
BULK_FIXTURE = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
MARKET_FIXTURE = ROOT / "evals" / "fixtures" / "market_pass_xingheng_minimum_boundary.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_unavailable(*args: object, **kwargs: object) -> list[dict[str, object]]:
    raise SchemaResolutionError("schema profile unavailable for test")


class ZeroConfigExportTest(unittest.TestCase):
    def _run_workbook_export(
        self,
        fixture: Path,
        *,
        mode: str,
        output_format: str,
        output: Path,
        manifest: Path,
    ) -> dict[str, object]:
        stdout = io.StringIO()
        with (
            patch(
                "validate_research_graph.schema_validation_errors",
                side_effect=_schema_unavailable,
            ),
            patch.object(
                sys,
                "argv",
                [
                    "export_workbook.py",
                    str(fixture),
                    "--output-dir",
                    str(output),
                    "--mode",
                    mode,
                    "--format",
                    output_format,
                    "--manifest",
                    str(manifest),
                ],
            ),
            contextlib.redirect_stdout(stdout),
        ):
            return_code = export_workbook.main()

        self.assertEqual(0, return_code, stdout.getvalue())
        return json.loads(stdout.getvalue())

    def test_candidate_pool_csv_and_manifest_disclose_unavailable_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "candidate-csv"
            manifest_path = root / "candidate-manifest.json"
            payload = self._run_workbook_export(
                BULK_FIXTURE,
                mode="initial",
                output_format="csv",
                output=output,
                manifest=manifest_path,
            )

            risk_text = (output / "风险与说明.csv").read_text(encoding="utf-8-sig")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("csv", payload["format"])
            self.assertIn(DISCLOSURE, risk_text)
            self.assertIn(DISCLOSURE, manifest["disclosures"])
            self.assertTrue(payload["audit"]["disclosure_required"])

    def test_standard_csv_xlsx_markdown_and_manifest_disclose_unavailable_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_output = root / "standard-csv"
            csv_manifest = root / "standard-csv-manifest.json"
            csv_payload = self._run_workbook_export(
                STANDARD_FIXTURE,
                mode="standard",
                output_format="csv",
                output=csv_output,
                manifest=csv_manifest,
            )
            self.assertEqual("standard_development_list", csv_payload["audit"]["delivery_status"])
            self.assertIn(
                DISCLOSURE,
                (csv_output / "风险与说明.csv").read_text(encoding="utf-8-sig"),
            )
            self.assertIn(
                DISCLOSURE,
                json.loads(csv_manifest.read_text(encoding="utf-8"))["disclosures"],
            )

            xlsx_output = root / "standard-xlsx"
            xlsx_manifest = root / "standard-xlsx-manifest.json"
            self._run_workbook_export(
                STANDARD_FIXTURE,
                mode="standard",
                output_format="xlsx",
                output=xlsx_output,
                manifest=xlsx_manifest,
            )
            workbook = next(xlsx_output.glob("*.xlsx"))
            with zipfile.ZipFile(workbook) as archive:
                workbook_xml = b"\n".join(
                    archive.read(name) for name in archive.namelist() if name.endswith(".xml")
                )
            self.assertIn(DISCLOSURE, html.unescape(workbook_xml.decode("utf-8")))

            graph = _load(STANDARD_FIXTURE)
            with patch(
                "validate_research_graph.schema_validation_errors",
                side_effect=_schema_unavailable,
            ):
                markdown, issues, delivery_status = build_bulk_markdown(graph)
            self.assertEqual([], issues)
            self.assertEqual("standard_development_list", delivery_status)
            self.assertIsNotNone(markdown)
            assert markdown is not None
            self.assertIn(DISCLOSURE, markdown)
            visible_issues = validate_user_visible(
                append_final_footer(markdown),
                "bulk_customer_development",
                min_tables=6,
                delivery_status=delivery_status,
            )
            self.assertEqual([], visible_issues)

    def test_unavailable_profile_is_minor_for_both_graph_validators(self) -> None:
        with patch(
            "validate_research_graph.schema_validation_errors",
            side_effect=_schema_unavailable,
        ):
            bulk_issues = validate_research_graph.validate_graph(_load(BULK_FIXTURE))
        with patch(
            "validate_product_market_analysis.schema_validation_errors",
            side_effect=_schema_unavailable,
        ):
            market_issues = validate_product_market_analysis.validate_graph(_load(MARKET_FIXTURE))

        for issues in (bulk_issues, market_issues):
            matching = [item for item in issues if item["code"] == "schema_profile_unavailable"]
            self.assertEqual(1, len(matching))
            self.assertEqual("minor", matching[0]["severity"])

    def test_product_market_exports_disclose_unavailable_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            graph = _load(MARKET_FIXTURE)
            output = root / "market-csv"
            markdown_path = root / "market.md"
            manifest_path = root / "market-manifest.json"
            with patch(
                "validate_product_market_analysis.schema_validation_errors",
                side_effect=_schema_unavailable,
            ):
                result = market_exporter.export_graph(
                    graph,
                    output,
                    markdown_path=markdown_path,
                    manifest_path=manifest_path,
                )
                markdown, issues, delivery_status = build_product_market_markdown(graph)
                audit = audit_market_graph(graph)

            self.assertTrue(result["ok"])
            self.assertTrue(audit["disclosure_required"])
            self.assertIn(DISCLOSURE, audit["disclosures"])
            source_csv = next(output.glob("*-信息来源与待确认事项.csv"))
            self.assertIn(DISCLOSURE, source_csv.read_text(encoding="utf-8-sig"))
            self.assertIn(DISCLOSURE, markdown_path.read_text(encoding="utf-8"))
            self.assertIn(
                DISCLOSURE,
                json.loads(manifest_path.read_text(encoding="utf-8"))["disclosures"],
            )
            self.assertEqual([], issues)
            self.assertIsNone(delivery_status)
            self.assertIsNotNone(markdown)
            assert markdown is not None
            self.assertIn(DISCLOSURE, markdown)
            self.assertEqual(
                [],
                validate_user_visible(
                    append_final_footer(markdown),
                    "product_outbound_market_analysis",
                    min_tables=7,
                ),
            )

    def test_schema_layer_converts_missing_jsonschema_to_resolution_error(self) -> None:
        import subprocess

        script = """
import sys
sys.path.insert(0, 'scripts')
from schema_validation import SchemaResolutionError, schema_validation_errors
try:
    schema_validation_errors({}, 'shared/schemas/run.schema.json')
except SchemaResolutionError as exc:
    print(exc)
    raise SystemExit(0)
raise SystemExit(1)
"""
        result = subprocess.run(
            [sys.executable, "-S", "-c", script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("jsonschema is unavailable", result.stdout)

    def test_review_gate_still_rejects_standard_delivery_when_validation_is_unavailable(self) -> None:
        graph = _load(STANDARD_FIXTURE)
        graph["runs"][-1]["review_mode"] = "not_run"
        with patch(
            "validate_research_graph.schema_validation_errors",
            side_effect=_schema_unavailable,
        ):
            audit = audit_graph(graph, requested_delivery_status="standard_development_list")

        self.assertFalse(audit["ok"])
        self.assertEqual("needs_correction", audit["delivery_status"])
        self.assertNotIn("standard_development_list", audit["allowed_delivery_statuses"])
        self.assertIn(
            "requested_delivery_not_allowed_by_review",
            {item["code"] for item in audit["issues"]},
        )

    def test_business_invariants_and_full_review_gate_remain_blocking(self) -> None:
        invalid_graph = _load(STANDARD_FIXTURE)
        invalid_graph["entities"][0]["website"] = "file:///tmp/not-public"
        with patch(
            "validate_research_graph.schema_validation_errors",
            side_effect=_schema_unavailable,
        ):
            invalid_audit = audit_graph(
                invalid_graph,
                requested_delivery_status="standard_development_list",
            )
            full_audit = audit_graph(
                _load(STANDARD_FIXTURE),
                requested_delivery_status="full_review_package",
            )

        self.assertFalse(invalid_audit["ok"])
        self.assertIn(
            "validation_entity_website_url_not_public",
            {item["code"] for item in invalid_audit["issues"]},
        )
        self.assertFalse(full_audit["ok"])
        self.assertIn(
            "full_review_unavailable_in_local_deployment",
            {item["code"] for item in full_audit["issues"]},
        )

    def test_actual_schema_failure_remains_major_and_blocks_export(self) -> None:
        graph = _load(STANDARD_FIXTURE)
        graph["unexpected_root_field"] = "not allowed by the schema"

        validation_issues = validate_research_graph.validate_graph(graph)
        schema_issues = [
            item for item in validation_issues if item["code"] == "schema_validation_failed"
        ]
        self.assertTrue(schema_issues)
        self.assertTrue(all(item["severity"] == "major" for item in schema_issues))

        audit = audit_graph(graph, requested_delivery_status="standard_development_list")
        self.assertFalse(audit["ok"])
        self.assertEqual("needs_correction", audit["delivery_status"])
        self.assertIn(
            "validation_schema_validation_failed",
            {item["code"] for item in audit["issues"]},
        )

    def test_available_schema_adds_no_degraded_validation_disclosure(self) -> None:
        graph = _load(BULK_FIXTURE)
        audit = audit_graph(graph, requested_delivery_status="initial_lead_list")
        sheets = export_workbook.build_sheets(graph, audit, "initial")
        markdown, issues, delivery_status = build_bulk_markdown(graph)

        self.assertTrue(audit["ok"])
        self.assertNotIn(DISCLOSURE, audit.get("disclosures", []))
        self.assertNotIn(DISCLOSURE, json.dumps(sheets, ensure_ascii=False))
        self.assertEqual([], issues)
        self.assertEqual("initial_lead_list", delivery_status)
        self.assertIsNotNone(markdown)
        self.assertNotIn(DISCLOSURE, markdown or "")


if __name__ == "__main__":
    unittest.main()
