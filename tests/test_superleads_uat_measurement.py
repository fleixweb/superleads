#!/usr/bin/env python3
"""Regression coverage for the real-business UAT measurement ledger."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEASURER = ROOT / "scripts" / "measure_superleads_uat.py"


class SuperleadsUatMeasurementTest(unittest.TestCase):
    def _run(self, *args: str, expected: int = 0) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(MEASURER), *args, "--format", "json"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.assertEqual(result.returncode, expected, result.stdout)
        payload = json.loads(result.stdout)
        self.assertIsInstance(payload, dict)
        return payload

    def test_finalize_records_first_pass_failure_and_exact_clean_git_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "bulk-uat"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "bulk_customer_development",
                "--token-usage-availability",
                "unavailable",
            )
            self._run("active-start", "--run-dir", str(run_dir), "--note", "source collection")
            self._run("active-stop", "--run-dir", str(run_dir), "--note", "source collection complete")
            self._run("record-gate", "--run-dir", str(run_dir), "--gate", "preflight", "--result", "passed")
            self._run(
                "record-gate",
                "--run-dir",
                str(run_dir),
                "--gate",
                "validator",
                "--result",
                "failed",
                "--failure-class",
                "graph_contract",
                "--note",
                "missing literal anchor",
            )
            self._run("record-gate", "--run-dir", str(run_dir), "--gate", "validator", "--result", "passed")
            for gate in ("audit", "markdown_export", "workbook_export", "user_visible", "claimed_path"):
                self._run("record-gate", "--run-dir", str(run_dir), "--gate", gate, "--result", "passed")

            payload = self._run(
                "finalize",
                "--run-dir",
                str(run_dir),
                "--required-gate",
                "preflight",
                "--required-gate",
                "validator",
                "--required-gate",
                "audit",
                "--required-gate",
                "markdown_export",
                "--required-gate",
                "workbook_export",
                "--required-gate",
                "user_visible",
                "--required-gate",
                "claimed_path",
            )

            self.assertEqual(payload["formal_uat_protocol_status"], "passed")
            self.assertFalse(payload["first_pass_success"])
            self.assertEqual(payload["repair_cycle_count"], 1)
            self.assertEqual(payload["first_pass_failure_classes"], ["graph_contract"])
            self.assertTrue(payload["git_unchanged"])
            self.assertEqual(payload["token_usage_availability"], "unavailable")
            self.assertGreaterEqual(payload["active_elapsed_seconds"], 0)
            self.assertEqual(
                (run_dir / "git-before.txt").read_bytes(),
                (run_dir / "git-after.txt").read_bytes(),
            )

    def test_finalize_treats_a_newline_in_git_capture_as_a_measurement_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "background-uat"
            self._run("init", "--run-dir", str(run_dir), "--route", "customer_background_research")
            (run_dir / "git-before.txt").write_bytes(b"\n")
            for gate in ("preflight", "validator", "markdown_export", "workbook_export", "user_visible", "claimed_path"):
                self._run("record-gate", "--run-dir", str(run_dir), "--gate", gate, "--result", "passed")

            payload = self._run(
                "finalize",
                "--run-dir",
                str(run_dir),
                "--required-gate",
                "preflight",
                "--required-gate",
                "validator",
                "--required-gate",
                "markdown_export",
                "--required-gate",
                "workbook_export",
                "--required-gate",
                "user_visible",
                "--required-gate",
                "claimed_path",
                expected=1,
            )

            self.assertEqual(payload["formal_uat_protocol_status"], "failed")
            self.assertFalse(payload["git_unchanged"])
            self.assertIn("git_capture_mismatch", payload["measurement_issues"])

    def test_finalize_marks_missing_required_gate_as_not_first_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "market-uat"
            self._run("init", "--run-dir", str(run_dir), "--route", "product_outbound_market_analysis")
            self._run("record-gate", "--run-dir", str(run_dir), "--gate", "preflight", "--result", "passed")
            payload = self._run(
                "finalize",
                "--run-dir",
                str(run_dir),
                "--required-gate",
                "preflight",
                "--required-gate",
                "validator",
                expected=1,
            )

            self.assertFalse(payload["first_pass_success"])
            self.assertIn("required_gate_missing:validator", payload["measurement_issues"])


if __name__ == "__main__":
    unittest.main()
