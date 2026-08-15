#!/usr/bin/env python3
"""Regression coverage for the real-business UAT measurement ledger."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MEASURER = ROOT / "scripts" / "measure_superleads_uat.py"
PORTABLE_REQUIRED_GATES = ("preflight", "source_evidence", "validator")


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

    def _durable_run_dir(self, tmp: str, name: str) -> Path:
        root = ROOT / ".plugin-eval" / "manual" / "uat-test-runs" / Path(tmp).name
        run_dir = root / name
        run_dir.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        return run_dir

    def _runtime_package(self, directory: Path, version: str = "0.1.18") -> Path:
        manifest = directory / ".codex-plugin" / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({"name": "superleads", "version": version}), encoding="utf-8")
        payload = directory / "skills" / "sample.txt"
        payload.parent.mkdir(parents=True)
        payload.write_text("runtime payload\n", encoding="utf-8")
        return directory

    def _record_passing_gate(self, run_dir: Path, external_dir: Path, gate: str) -> Path:
        external_dir.mkdir(parents=True, exist_ok=True)
        artifact = external_dir / f"{gate}.json"
        artifact.write_text(json.dumps({"gate": gate, "ok": True}) + "\n", encoding="utf-8")
        self._run(
            "record-gate",
            "--run-dir",
            str(run_dir),
            "--gate",
            gate,
            "--result",
            "passed",
            "--artifact",
            str(artifact),
        )
        return artifact

    def _record_required_passes(self, run_dir: Path, external_dir: Path) -> dict[str, Path]:
        return {
            gate: self._record_passing_gate(run_dir, external_dir, gate)
            for gate in PORTABLE_REQUIRED_GATES
        }

    def _finalize_portable_required_gates(self, run_dir: Path, *, expected: int = 0) -> dict[str, object]:
        args = ["finalize", "--run-dir", str(run_dir)]
        for gate in PORTABLE_REQUIRED_GATES:
            args.extend(("--required-gate", gate))
        return self._run(*args, expected=expected)

    def test_finalize_records_first_pass_failure_and_exact_clean_git_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "bulk-uat")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            external_dir = run_dir.parent / "external-artifacts"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "bulk_customer_development",
                "--runtime-package",
                str(runtime_package),
                "--token-usage-availability",
                "unavailable",
            )
            self._run("active-start", "--run-dir", str(run_dir), "--note", "source collection")
            self._run("active-stop", "--run-dir", str(run_dir), "--note", "source collection complete")
            self._record_passing_gate(run_dir, external_dir, "preflight")
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
            self._record_passing_gate(run_dir, external_dir, "validator")
            for gate in ("audit", "markdown_export", "workbook_export", "user_visible", "claimed_path"):
                self._record_passing_gate(run_dir, external_dir, gate)

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
            run_dir = self._durable_run_dir(tmp, "background-uat")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            external_dir = run_dir.parent / "external-artifacts"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "customer_background_research",
                "--runtime-package",
                str(runtime_package),
            )
            (run_dir / "git-before.txt").write_bytes(b"\n")
            for gate in ("preflight", "validator", "markdown_export", "workbook_export", "user_visible", "claimed_path"):
                self._record_passing_gate(run_dir, external_dir, gate)

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
            run_dir = self._durable_run_dir(tmp, "market-uat")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_passing_gate(run_dir, run_dir.parent / "external-artifacts", "preflight")
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

    def test_optional_recorded_gate_failure_still_breaks_first_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "market-uat")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            external_dir = run_dir.parent / "external-artifacts"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_passing_gate(run_dir, external_dir, "preflight")
            self._run(
                "record-gate",
                "--run-dir",
                str(run_dir),
                "--gate",
                "compiler",
                "--result",
                "failed",
                "--failure-class",
                "graph_contract",
            )
            self._record_passing_gate(run_dir, external_dir, "compiler")
            payload = self._run(
                "finalize",
                "--run-dir",
                str(run_dir),
                "--required-gate",
                "preflight",
            )

            self.assertEqual(payload["formal_uat_protocol_status"], "passed")
            self.assertFalse(payload["first_pass_success"])
            self.assertEqual(payload["first_pass_failure_classes"], ["graph_contract"])

    def test_finalize_seals_staged_artifacts_with_release_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "portable-success")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_required_passes(run_dir, run_dir.parent / "external-artifacts")

            payload = self._finalize_portable_required_gates(run_dir)

            self.assertEqual(payload["formal_uat_protocol_status"], "passed")
            self.assertTrue(payload["portable_evidence"])
            self.assertEqual(payload["release_identity"]["plugin_version"], "0.1.18")
            self.assertTrue((run_dir / "release_identity.json").is_file())
            self.assertTrue((run_dir / "evidence_manifest.json").is_file())
            self.assertTrue((run_dir / "runtime_package").is_dir())
            self.assertTrue((run_dir / "artifacts").is_dir())
            verify = self._run("verify", "--run-dir", str(run_dir))
            self.assertTrue(verify["ok"])

    def test_finalize_rejects_temporary_run_directory_even_when_gates_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "ephemeral-uat"
            runtime_package = self._runtime_package(root / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_required_passes(run_dir, root / "external-artifacts")

            payload = self._finalize_portable_required_gates(run_dir, expected=1)

            self.assertEqual(payload["formal_uat_protocol_status"], "failed")
            self.assertIn("evidence_run_dir_ephemeral", payload["measurement_issues"])
            self.assertFalse(payload["portable_evidence"])

    def test_record_gate_stages_artifact_before_original_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "staged-artifact")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            artifacts = self._record_required_passes(run_dir, run_dir.parent / "external-artifacts")
            artifacts["preflight"].unlink()

            payload = self._finalize_portable_required_gates(run_dir)
            verify = self._run("verify", "--run-dir", str(run_dir))

            self.assertTrue(verify["ok"])
            self.assertEqual(payload["formal_uat_protocol_status"], "passed")

    def test_record_gate_stages_directory_with_relative_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "staged-directory")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            source_bundle = run_dir.parent / "external-source-bundle"
            source_bundle.mkdir(parents=True)
            (source_bundle / "adapter.json").write_text('{"operation": "open"}\n', encoding="utf-8")
            nested = source_bundle / "graph" / "current-run.json"
            nested.parent.mkdir(parents=True)
            nested.write_text('{"observations": ["obs-1"]}\n', encoding="utf-8")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_passing_gate(run_dir, run_dir.parent / "external-artifacts", "preflight")
            self._run(
                "record-gate",
                "--run-dir",
                str(run_dir),
                "--gate",
                "source_evidence",
                "--result",
                "passed",
                "--artifact",
                str(source_bundle),
            )
            self._record_passing_gate(run_dir, run_dir.parent / "external-artifacts", "validator")

            self._finalize_portable_required_gates(run_dir)
            manifest = json.loads((run_dir / "evidence_manifest.json").read_text(encoding="utf-8"))

            staged = [item for item in manifest["artifacts"] if item["gate"] == "source_evidence"]
            self.assertEqual(len(staged), 1)
            self.assertEqual(staged[0]["kind"], "directory")
            self.assertFalse(Path(staged[0]["relative_path"]).is_absolute())
            self.assertEqual(len(staged[0]["files"]), 2)
            self.assertTrue(self._run("verify", "--run-dir", str(run_dir))["ok"])

    def test_verify_and_finalize_reject_tampered_staged_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "tampered-artifact")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._record_required_passes(run_dir, run_dir.parent / "external-artifacts")
            matches = list((run_dir / "artifacts").glob("*-validator-*"))
            self.assertEqual(len(matches), 1, "validator artifact must be staged exactly once")
            staged = matches[0]
            staged.write_text('{"ok": false}\n', encoding="utf-8")
            issue = "evidence_artifact_hash_mismatch:" + staged.relative_to(run_dir).as_posix()

            verify = self._run("verify", "--run-dir", str(run_dir), expected=1)
            payload = self._finalize_portable_required_gates(run_dir, expected=1)

            self.assertIn(issue, verify["verification_issues"])
            self.assertIn(issue, payload["measurement_issues"])

    def test_finalize_rejects_missing_runtime_package_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "missing-runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
            )
            self._record_required_passes(run_dir, run_dir.parent / "external-artifacts")

            payload = self._finalize_portable_required_gates(run_dir, expected=1)

            self.assertEqual(payload["formal_uat_protocol_status"], "failed")
            self.assertIn("release_identity_runtime_package_missing", payload["measurement_issues"])

    def test_init_rejects_runtime_manifest_that_differs_from_supplied_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "runtime-manifest-mismatch")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package", version="0.1.18")
            source_manifest = run_dir.parent / "source-plugin.json"
            source_manifest.write_text(
                json.dumps({"name": "superleads", "version": "0.1.17"}),
                encoding="utf-8",
            )

            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--plugin-manifest",
                str(source_manifest),
                "--runtime-package",
                str(runtime_package),
                expected=2,
            )

    def test_init_rejects_runtime_package_without_its_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "runtime-manifest-missing")
            runtime_package = run_dir.parent / "runtime-package"
            runtime_package.mkdir(parents=True)

            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
                expected=2,
            )

    def test_init_rejects_symlinked_runtime_package_and_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "symlink-rejection")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            runtime_link = run_dir.parent / "runtime-package-link"
            runtime_link.symlink_to(runtime_package, target_is_directory=True)

            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_link),
                expected=2,
            )

            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            artifact = run_dir.parent / "original.json"
            artifact.write_text('{"ok": true}\n', encoding="utf-8")
            artifact_link = run_dir.parent / "artifact-link.json"
            artifact_link.symlink_to(artifact)

            self._run(
                "record-gate",
                "--run-dir",
                str(run_dir),
                "--gate",
                "preflight",
                "--result",
                "passed",
                "--artifact",
                str(artifact_link),
                expected=2,
            )

    def test_init_overwrite_replaces_unstarted_staged_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "overwrite-unstarted")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            init_args = (
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self._run(*init_args)
            payload = self._run(*init_args, "--overwrite")

            self.assertTrue(payload["ok"])
            self.assertTrue((run_dir / "runtime_package" / ".codex-plugin" / "plugin.json").is_file())

    def test_ledger_and_metrics_store_only_relative_evidence_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self._durable_run_dir(tmp, "relative-paths")
            runtime_package = self._runtime_package(run_dir.parent / "runtime-package")
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--route",
                "product_outbound_market_analysis",
                "--runtime-package",
                str(runtime_package),
            )
            self.assertEqual(
                json.loads((run_dir / "uat_measurement.json").read_text(encoding="utf-8"))["git_before"]["path"],
                "git-before.txt",
            )
            self._record_required_passes(run_dir, run_dir.parent / "external-artifacts")
            payload = self._finalize_portable_required_gates(run_dir)
            ledger = json.loads((run_dir / "uat_measurement.json").read_text(encoding="utf-8"))

            self.assertEqual(payload["git_before"]["path"], "git-before.txt")
            self.assertEqual(payload["git_after"]["path"], "git-after.txt")
            self.assertEqual(ledger["final_metrics_path"], "uat_metrics.json")


if __name__ == "__main__":
    unittest.main()
