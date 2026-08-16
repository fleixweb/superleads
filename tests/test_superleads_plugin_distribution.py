#!/usr/bin/env python3
"""Focused regression coverage for the hook-free runtime package."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_superleads_plugin_package import build_package
from check_superleads_plugin_distribution import check_distribution


class SuperleadsPluginDistributionTest(unittest.TestCase):
    def test_built_runtime_package_excludes_legacy_hooks_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "superleads"

            result = build_package(output)

            self.assertTrue(result["ok"])
            self.assertNotIn("hooks", result["included_directories"])
            self.assertFalse((output / "hooks").exists())

    def test_distribution_rejects_hook_directory_with_session_start_remote_manifest_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "superleads"
            build_package(output)
            hook = output / "hooks" / "hooks.json"
            hook.parent.mkdir()
            hook.write_text(
                '{"hooks":{"SessionStart":[{"command":"curl https://raw.githubusercontent.com/fleixweb/superleads/master/.codex-plugin/plugin.json"}]}}',
                encoding="utf-8",
            )

            result = check_distribution(output, ROOT, runtime_package=True)

            self.assertFalse(result["ok"])
            codes = {issue["code"] for issue in result["issues"]}
            self.assertIn("plugin_distribution_hook_directory_forbidden", codes)
            self.assertIn("plugin_distribution_automatic_hook_forbidden", codes)
            self.assertIn("plugin_distribution_automatic_remote_update_forbidden", codes)

    def test_distribution_requires_a_valid_codex_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "superleads"
            build_package(output)
            manifest = output / ".codex-plugin" / "plugin.json"
            manifest.write_text("not json", encoding="utf-8")

            result = check_distribution(output, ROOT, runtime_package=True)

            self.assertFalse(result["ok"])
            self.assertIn(
                "plugin_distribution_manifest_invalid",
                {issue["code"] for issue in result["issues"]},
            )

    def test_runtime_update_script_with_start_event_and_manifest_fetch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "superleads"
            build_package(output)
            script = output / "scripts" / "session-start-update.sh"
            script.write_text(
                "# SessionStart\ncurl https://raw.githubusercontent.com/fleixweb/superleads/master/.codex-plugin/plugin.json\n",
                encoding="utf-8",
            )

            result = check_distribution(output, ROOT, runtime_package=True)

            self.assertFalse(result["ok"])
            self.assertIn(
                "plugin_distribution_automatic_remote_update_forbidden",
                {issue["code"] for issue in result["issues"]},
            )


if __name__ == "__main__":
    unittest.main()
