from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evals"))

import export_workbook
import audit_delivery
from run_evals import _load_fixture_graph
from validate_superleads_user_visible_output import validate


class TraceUserBoundaryTest(unittest.TestCase):
    def test_agent_authored_trace_identifier_blocks(self) -> None:
        issues = validate("attempt_id=att-1", "bulk_customer_development", min_tables=0)
        self.assertIn("trace_user_visible_internal_leak", {item["code"] for item in issues})

    def test_structured_keys_are_checked_only_by_shape(self) -> None:
        plain = "The environmental management system is documented."
        structured = "operation: open; sequence=3; notes: internal; interpreter_source=system"
        self.assertNotIn("trace_user_visible_internal_leak", {item["code"] for item in validate(plain, "bulk_customer_development", min_tables=0)})
        self.assertIn("trace_user_visible_internal_leak", {item["code"] for item in validate(structured, "bulk_customer_development", min_tables=0)})

    def test_runtime_enum_is_checked_in_approved_chinese_structure_only(self) -> None:
        plain = "The supplier uses a system for environmental management."
        structured = "解释器来源：system"
        self.assertNotIn("trace_user_visible_internal_leak", {item["code"] for item in validate(plain, "bulk_customer_development", min_tables=0)})
        self.assertIn("trace_user_visible_internal_leak", {item["code"] for item in validate(structured, "bulk_customer_development", min_tables=0)})

    def test_source_projection_trace_collision_is_masked(self) -> None:
        rendered, changed = export_workbook.redact_trace_source_projection({"原文": "observation_id=source-telemetry"})
        self.assertTrue(changed)
        self.assertIn("[已隐藏内部标识]", json.dumps(rendered, ensure_ascii=False))
        self.assertNotIn("observation_id", json.dumps(rendered, ensure_ascii=False))

    def test_exported_source_projection_collision_is_masked(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/pass_trace_source_projection_collision.json")
        audit = audit_delivery.audit_graph(graph)
        sheets = export_workbook.build_sheets(graph, audit, "initial")
        rendered = json.dumps(sheets, ensure_ascii=False)
        self.assertNotIn("observation_id=source-telemetry", rendered)
        self.assertIn("[已隐藏内部标识]", rendered)
        self.assertTrue(audit["ok"], audit)
        self.assertTrue(
            any(
                item.get("code") == "trace_user_visible_internal_leak"
                and item.get("severity") == "major"
                for item in audit.get("issues", [])
            ),
            audit,
        )

    def test_manifest_keeps_source_projection_exemption_narrow(self) -> None:
        manifest = export_workbook.redact_delivery_internals({
            "tool_attempts": [{"attempt_id": "att-1"}],
            "observation_id": "obs-1",
            "source_context": "observation_id=source-telemetry",
        })
        self.assertNotIn("tool_attempts", manifest)
        self.assertNotIn("observation_id", manifest)
        self.assertIn("observation_id=source-telemetry", manifest["source_context"])


if __name__ == "__main__":
    unittest.main()
