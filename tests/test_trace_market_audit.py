from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "evals"))

from run_evals import _load_fixture_graph
import audit_delivery
import audit_product_market_analysis
import validate_product_market_analysis


class TraceMarketAuditTest(unittest.TestCase):
    def test_market_trace_cannot_support_evidence_card_or_matrix_row(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/fail_market_trace_as_evidence.json")
        codes = {item.get("code") for item in validate_product_market_analysis.validate_graph(graph)}
        self.assertIn("trace_evidence_reference_forbidden", codes)

    def test_research_audit_still_blocks_unrelated_major_issue(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/fail_trace_unrelated_major.json")
        self.assertFalse(audit_delivery.audit_graph(graph)["ok"])

    def test_research_audit_does_not_block_attempt_binding_major(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/fail_trace_attempt_binding_missing.json")
        self.assertTrue(audit_delivery.audit_graph(graph)["ok"])

    def test_market_audit_keeps_ready_with_limitations_for_trace_quality_major(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/market_pass_trace_binding_quality.json")
        audit = audit_product_market_analysis.audit_graph(graph)
        self.assertEqual("ready_with_limitations", audit["delivery_status"], audit)

    def test_critical_trace_issue_blocks_both_audits(self) -> None:
        graph = _load_fixture_graph(ROOT / "evals/fixtures/fail_trace_runtime_self_service.json")
        self.assertFalse(audit_delivery.audit_graph(graph)["ok"])


if __name__ == "__main__":
    unittest.main()
