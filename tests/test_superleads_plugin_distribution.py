#!/usr/bin/env python3
"""Focused regression coverage for the hook-free runtime package."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_superleads_plugin_package import build_package
from check_superleads_plugin_distribution import check_distribution


class SuperleadsPluginDistributionTest(unittest.TestCase):
    def test_repo_marketplaces_point_to_tracked_runtime_package(self) -> None:
        codex_marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        claude_marketplace = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )

        self.assertEqual(
            {"source": "local", "path": "./plugins/superleads"},
            codex_marketplace["plugins"][0]["source"],
        )
        self.assertEqual("./plugins/superleads", claude_marketplace["plugins"][0]["source"])

        package = ROOT / "plugins" / "superleads"
        result = check_distribution(package, ROOT, runtime_package=True)
        self.assertTrue(result["ok"], result["issues"])

    def test_tracked_runtime_package_matches_a_fresh_build(self) -> None:
        tracked_package = ROOT / "plugins" / "superleads"
        with tempfile.TemporaryDirectory() as directory:
            rebuilt_package = Path(directory) / "superleads"
            build_package(rebuilt_package)

            tracked_files = {
                path.relative_to(tracked_package): path.read_bytes()
                for path in tracked_package.rglob("*")
                if path.is_file()
            }
            rebuilt_files = {
                path.relative_to(rebuilt_package): path.read_bytes()
                for path in rebuilt_package.rglob("*")
                if path.is_file()
            }

        self.assertEqual(rebuilt_files, tracked_files)

    def test_built_runtime_package_includes_the_source_dependency_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "superleads"

            result = build_package(output)

            self.assertTrue(result["ok"])
            self.assertIn("requirements.txt", result["included_files"])
            self.assertEqual(
                (ROOT / "requirements.txt").read_text(encoding="utf-8"),
                (output / "requirements.txt").read_text(encoding="utf-8"),
            )

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
