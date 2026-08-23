#!/usr/bin/env python3
"""Regression tests for Codex adapter capability preflight coverage."""
from __future__ import annotations

import json
import io
import os
import tempfile
import sys
import unittest
from contextlib import redirect_stdout
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

    def test_missing_capability_is_a_real_blocked_assessment(self) -> None:
        result = preflight_capabilities.preflight({
            "capabilities": {"search.web": "missing"},
        })

        self.assertEqual("blocked", result["formal_research_status"])
        self.assertEqual("blocked", result["discovery_snapshot_status"])
        self.assertIn(
            "formal_research_search_capability_missing",
            [issue["code"] for issue in result["formal_research_issues"]],
        )

    def test_complete_empty_inventory_is_a_real_blocked_assessment(self) -> None:
        result = preflight_capabilities.preflight({
            "host_tool_inventory_complete": True,
            "capabilities": {},
        })

        self.assertEqual("blocked", result["formal_research_status"])
        self.assertEqual("blocked", result["discovery_snapshot_status"])
        self.assertEqual("formal_research_blocked", result["max_output_without_manual_sources"])

    def test_no_capability_input_is_not_assessed(self) -> None:
        result = preflight_capabilities.preflight(None)

        self.assertEqual("not_assessed", result["formal_research_status"])
        self.assertEqual("not_assessed", result["discovery_snapshot_status"])
        self.assertEqual("formal_research_not_assessed", result["max_output_without_manual_sources"])
        self.assertEqual([], result["formal_research_issues"])
        self.assertNotIn(preflight_capabilities.FORMAL_RESEARCH_MESSAGE, result["formal_research_message"])

    def test_metadata_only_payload_is_not_assessed(self) -> None:
        result = preflight_capabilities.preflight({"platform": "chatgpt_desktop"})

        self.assertEqual("not_assessed", result["formal_research_status"])
        self.assertEqual("not_assessed", result["discovery_snapshot_status"])

    def test_empty_capabilities_wrapper_is_not_assessed_without_inventory_completion(self) -> None:
        result = preflight_capabilities.preflight({"capabilities": {}})

        self.assertEqual("not_assessed", result["formal_research_status"])
        self.assertEqual("not_assessed", result["discovery_snapshot_status"])

    def test_require_formal_research_uses_three_status_exit_codes(self) -> None:
        expected_exit_codes = {
            "ready": 0,
            "blocked": 1,
            "not_assessed": 2,
        }
        for status, expected_exit_code in expected_exit_codes.items():
            with self.subTest(status=status):
                output = io.StringIO()
                with patch.object(
                    preflight_capabilities,
                    "preflight",
                    return_value={
                        "formal_research_status": status,
                        "max_output_without_manual_sources": f"formal_research_{status}",
                        "downgrade_notes": [],
                    },
                ), patch.object(
                    sys,
                    "argv",
                    ["preflight_capabilities.py", "--require-formal-research", "--format", "text"],
                ), redirect_stdout(output):
                    self.assertEqual(expected_exit_code, preflight_capabilities.main())

                if status == "not_assessed":
                    self.assertIn("formal_research_status: not_assessed", output.getvalue())

    def test_require_file_delivery_blocks_when_session_artifact_dir_is_unavailable(self) -> None:
        output = io.StringIO()
        with patch.object(
            preflight_capabilities,
            "preflight",
            return_value={
                "formal_research_status": "ready",
                "max_output_without_manual_sources": "formal_research_ready",
                "downgrade_notes": [],
                "file_delivery": {"status": "unavailable", "message": "chat only"},
            },
        ), patch.object(
            sys,
            "argv",
            ["preflight_capabilities.py", "--require-file-delivery", "--format", "text"],
        ), redirect_stdout(output):
            self.assertEqual(1, preflight_capabilities.main())
        self.assertIn("file_delivery_status: unavailable", output.getvalue())

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

    def test_web_run_http_404_is_one_shot_capability_failure(self) -> None:
        payload = {
            "platform": "codex_cli",
            "capability_adapter_report": {
                "platform": "codex_cli",
                "adapter": {"adapter_id": "codex_cli_web_run", "adapter_version": "1"},
                "detected_at": "2026-08-17T00:00:00Z",
                "detection": "current_session_web__run_search_query",
                "host_tools": {
                    "web__run": {
                        "status": "failed",
                        "error": "HTTP 404",
                        "operations": {
                            "search_query": {"status": "failed", "http_status": 404, "error": "HTTP 404"},
                            "open": {"status": "not_verified"},
                        },
                    }
                },
                "canonical_capabilities": {"search.web": "missing", "source.open": "unknown"},
            },
        }

        result = preflight_capabilities.preflight(payload)

        self.assertEqual("missing", result["capabilities"]["search.web"]["status"])
        self.assertEqual("http_404", result["capability_failure"]["reason"])
        self.assertFalse(result["capability_failure"]["retry"])
        self.assertIn("404", result["formal_research_message"])

    def test_web_run_timeout_is_one_shot_capability_failure(self) -> None:
        payload = {
            "platform": "codex_cli",
            "capability_adapter_report": {
                "platform": "codex_cli",
                "adapter": {"adapter_id": "codex_cli_web_run", "adapter_version": "1"},
                "detected_at": "2026-08-17T00:00:00Z",
                "detection": "current_session_web__run_search_query",
                "host_tools": {
                    "web__run": {
                        "status": "failed",
                        "error": "timeout",
                        "operations": {
                            "search_query": {"status": "failed", "error": "timeout"},
                            "open": {"status": "not_verified"},
                        },
                    }
                },
                "canonical_capabilities": {"search.web": "missing", "source.open": "unknown"},
            },
        }

        result = preflight_capabilities.preflight(payload)

        self.assertEqual("timeout", result["capability_failure"]["reason"])
        self.assertFalse(result["capability_failure"]["retry"])

    def test_chatgpt_desktop_native_capabilities_are_not_overridden_by_codex_probe_failure(self) -> None:
        result = preflight_capabilities.preflight({
            "platform": "chatgpt_desktop",
            "task_mode": "discovery_snapshot",
            "capabilities": {
                "search.web": "available",
                "source.open": "available",
            },
            "capability_adapter_report": {
                "platform": "codex_cli",
                "adapter": {"adapter_id": "codex_cli_web_run", "adapter_version": "1"},
                "detected_at": "2026-08-17T00:00:00Z",
                "detection": "wrong_platform_probe",
                "host_tools": {
                    "web__run": {
                        "status": "failed",
                        "operations": {
                            "search_query": {"status": "failed", "http_status": 404},
                            "open": {"status": "not_verified"},
                        },
                    }
                },
                "canonical_capabilities": {"search.web": "missing", "source.open": "unknown"},
            },
        })

        self.assertEqual("available", result["capabilities"]["search.web"]["status"])
        self.assertEqual("available", result["capabilities"]["source.open"]["status"])
        self.assertEqual("ready", result["discovery_snapshot_status"])
        self.assertEqual("ready", result["formal_research_status"])
        self.assertNotIn("capability_failure", result)

    def test_codex_404_does_not_globally_block_fast_discovery_before_host_inventory_is_complete(self) -> None:
        payload = {
            "platform": "codex_cli",
            "task_mode": "discovery_snapshot",
            "host_tool_inventory_complete": False,
            "capability_adapter_report": {
                "platform": "codex_cli",
                "adapter": {"adapter_id": "codex_cli_web_run", "adapter_version": "1"},
                "detected_at": "2026-08-17T00:00:00Z",
                "detection": "current_session_web__run_search_query",
                "host_tools": {
                    "web__run": {
                        "status": "failed",
                        "operations": {
                            "search_query": {"status": "failed", "http_status": 404},
                            "open": {"status": "not_verified"},
                        },
                    }
                },
                "canonical_capabilities": {"search.web": "missing", "source.open": "unknown"},
            },
        }

        result = preflight_capabilities.preflight(payload)

        self.assertEqual("blocked", result["formal_research_status"])
        self.assertEqual("needs_host_capability_check", result["discovery_snapshot_status"])
        self.assertIn("宿主实际暴露", result["discovery_snapshot_message"])
        self.assertNotIn("停止快速候选池", result["discovery_snapshot_message"])

    def test_artifact_directory_from_host_field_is_required_for_file_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as artifact_dir:
            result = preflight_capabilities.preflight({
                "platform": "chatgpt_desktop",
                "capabilities": {"search.web": "available", "source.open": "available"},
                "session_artifact_dir": artifact_dir,
            })

        self.assertEqual("available", result["file_delivery"]["status"])
        self.assertEqual(artifact_dir, result["file_delivery"]["directory"])
        self.assertEqual("host_field", result["file_delivery"]["source"])
        self.assertEqual("formal_research_ready", result["max_output_without_manual_sources"])

    def test_artifact_directory_environment_variable_is_used_when_host_field_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as artifact_dir, patch.dict(
            os.environ, {"SUPERLEADS_SESSION_ARTIFACT_DIR": artifact_dir}, clear=False
        ):
            result = preflight_capabilities.preflight({"capabilities": {"search.web": "available", "source.open": "available"}})

        self.assertEqual("available", result["file_delivery"]["status"])
        self.assertEqual(artifact_dir, result["file_delivery"]["directory"])
        self.assertEqual("environment", result["file_delivery"]["source"])

    def test_writable_workspace_cwd_is_used_when_no_explicit_artifact_directory_exists(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, patch.dict(
            os.environ, {}, clear=True
        ), patch.object(
            preflight_capabilities.Path, "cwd", return_value=Path(workspace_dir)
        ):
            result = preflight_capabilities.preflight({
                "capabilities": {"search.web": "available", "source.open": "available"},
            })

        self.assertEqual("available", result["file_delivery"]["status"])
        self.assertEqual(workspace_dir, result["file_delivery"]["directory"])
        self.assertEqual("workspace_cwd", result["file_delivery"]["source"])
        self.assertIsNone(result["file_delivery"]["fallback"])

    def test_invalid_explicit_artifact_directory_falls_back_to_writable_workspace_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, patch.dict(
            os.environ, {}, clear=True
        ), patch.object(
            preflight_capabilities.Path, "cwd", return_value=Path(workspace_dir)
        ):
            result = preflight_capabilities.preflight({
                "capabilities": {"search.web": "available", "source.open": "available"},
                "session_artifact_dir": "/path/that/does/not/exist",
            })

        self.assertEqual("available", result["file_delivery"]["status"])
        self.assertEqual(workspace_dir, result["file_delivery"]["directory"])
        self.assertEqual("workspace_cwd", result["file_delivery"]["source"])

    def test_unwritable_workspace_cwd_defaults_to_chat_only(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_dir, patch.dict(
            os.environ, {}, clear=True
        ), patch.object(
            preflight_capabilities.Path, "cwd", return_value=Path(workspace_dir)
        ), patch.object(
            preflight_capabilities.os, "access", return_value=False
        ):
            result = preflight_capabilities.preflight({
                "capabilities": {"search.web": "available", "source.open": "available"},
            })

        self.assertEqual("unavailable", result["file_delivery"]["status"])
        self.assertEqual("chat_only", result["file_delivery"]["fallback"])
        self.assertIn("工作区根目录均不存在或不可写", result["file_delivery"]["message"])

    def test_unavailable_workspace_cwd_defaults_to_chat_only(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch.object(
            preflight_capabilities.Path, "cwd", side_effect=OSError("cwd unavailable")
        ):
            result = preflight_capabilities.preflight({
                "capabilities": {"search.web": "available", "source.open": "available"},
            })

        self.assertEqual("unavailable", result["file_delivery"]["status"])
        self.assertEqual("chat_only", result["file_delivery"]["fallback"])


if __name__ == "__main__":
    unittest.main()
