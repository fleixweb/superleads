#!/usr/bin/env python3
"""Regression tests for Codex adapter capability preflight coverage."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import preflight_capabilities


class PreflightCapabilitiesTest(unittest.TestCase):
    def load_fixture(self, name: str) -> dict:
        with (FIXTURES / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_empty_adapter_reports_invalidate_codex_owned_capabilities(self) -> None:
        result = preflight_capabilities.preflight({
            "platform": "codex_cli",
            "capabilities": {
                "search.web": "available",
                "source.open": "available",
            },
            "capability_adapter_reports": [],
        })

        self.assertEqual("unknown", result["capabilities"]["search.web"]["status"])
        self.assertEqual("unknown", result["capabilities"]["source.open"]["status"])
        self.assertEqual("blocked", result["formal_research_status"])
        self.assertIn(
            "capability_adapter_reports_empty",
            [issue["code"] for issue in result["adapter_report"]["issues"]],
        )

    def test_shell_only_report_does_not_authorize_self_reported_search(self) -> None:
        payload = self.load_fixture("preflight_codex_shell_http_source_open.json")
        payload["capabilities"]["search.web"] = "available"

        result = preflight_capabilities.preflight(payload)

        self.assertEqual("unknown", result["capabilities"]["search.web"]["status"])
        self.assertEqual("available", result["capabilities"]["source.open"]["status"])
        self.assertEqual("blocked", result["formal_research_status"])

    def test_invalid_extra_report_does_not_erase_valid_web_run_mapping(self) -> None:
        payload = self.load_fixture("preflight_codex_web_run_open_source_verified.json")
        valid_report = payload.pop("capability_adapter_report")
        payload["capability_adapter_reports"] = [valid_report, {}]

        result = preflight_capabilities.preflight(payload)

        self.assertEqual("available", result["capabilities"]["search.web"]["status"])
        self.assertEqual("available", result["capabilities"]["source.open"]["status"])
        self.assertEqual("ready", result["formal_research_status"])
        self.assertIn(
            "capability_adapter_run_platform_mismatch",
            [issue["code"] for issue in result["adapter_report"]["issues"]],
        )

    def test_missing_adapter_report_invalidates_all_known_adapter_capabilities(self) -> None:
        payload = {
            "platform": "codex_cli",
            "capabilities": {"source.capture": "available"},
        }

        with patch.object(
            preflight_capabilities,
            "CODEX_CLI_ADAPTER_OWNED_CAPABILITIES",
            ("source.capture",),
            create=True,
        ):
            result = preflight_capabilities.preflight(payload)

        self.assertEqual("unknown", result["capabilities"]["source.capture"]["status"])
        self.assertEqual("codex_native_capability_adapter_required", result["adapter_report"]["issues"][0]["code"])


if __name__ == "__main__":
    unittest.main()
