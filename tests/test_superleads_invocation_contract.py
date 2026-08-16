#!/usr/bin/env python3
"""Regression tests for context-bound internal Superleads stages."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from superleads_invocation_contract import validate_internal_invocation


class SuperleadsInvocationContractTest(unittest.TestCase):
    def test_contact_stage_stops_without_opened_current_run_source(self) -> None:
        verdict = validate_internal_invocation(
            "collecting-contact-intelligence",
            {
                "route": "customer_background_research",
                "run_id": "run-1",
                "brief_present": True,
            },
        )

        self.assertFalse(verdict["allowed"])
        self.assertIn("opened_source", verdict["missing"])
        self.assertIn("已打开", verdict["user_message"])

    def test_export_stage_stops_without_current_validated_graph(self) -> None:
        verdict = validate_internal_invocation(
            "exporting-lead-workbooks",
            {"route": "bulk_customer_development", "run_id": "run-1", "brief_present": True},
        )

        self.assertFalse(verdict["allowed"])
        self.assertIn("validated_graph", verdict["missing"])
        self.assertIn("可导出的", verdict["user_message"])

    def test_export_stage_allows_valid_current_context(self) -> None:
        verdict = validate_internal_invocation(
            "exporting-lead-workbooks",
            {
                "route": "bulk_customer_development",
                "run_id": "run-1",
                "brief_present": True,
                "validated_graph": True,
                "allowed_output_modes": ["initial"],
                "requested_output_mode": "initial",
            },
        )

        self.assertTrue(verdict["allowed"])
        self.assertEqual([], verdict["missing"])

    def test_feedback_save_requires_explicit_consent_and_classification(self) -> None:
        verdict = validate_internal_invocation(
            "learning-from-feedback",
            {
                "route": "bulk_customer_development",
                "run_id": "run-1",
                "feedback_target": "candidate-1",
                "feedback_action": "persistent_save",
            },
        )

        self.assertFalse(verdict["allowed"])
        self.assertEqual({"feedback_save_consent", "feedback_class"}, set(verdict["missing"]))

    def test_current_run_feedback_correction_does_not_require_durable_consent(self) -> None:
        verdict = validate_internal_invocation(
            "learning-from-feedback",
            {
                "route": "bulk_customer_development",
                "run_id": "run-1",
                "feedback_target": "candidate-1",
                "feedback_action": "current_run_correction",
            },
        )

        self.assertTrue(verdict["allowed"])


if __name__ == "__main__":
    unittest.main()
