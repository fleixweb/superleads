#!/usr/bin/env python3
"""Run Superleads plugin distribution integrity evals."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_superleads_plugin_distribution.py"
BUILDER = ROOT / "scripts" / "build_superleads_plugin_package.py"
SUITES = ("all",)


def _run(cmd: list[str], expect: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _build_distribution(target: Path) -> dict[str, Any]:
    result = _run([
        sys.executable,
        str(BUILDER),
        "--output",
        str(target),
        "--format",
        "json",
    ], 0)
    if not result["ok"]:
        raise RuntimeError(f"runtime package build failed: {result['output']}")
    return result


def _parse(output: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _checker(py: str, plugin_root: Path, expect: int, *, runtime_package: bool = False) -> dict[str, Any]:
    command = [
        py,
        str(CHECKER),
        "--plugin-root",
        str(plugin_root),
        "--source-root",
        str(ROOT),
        "--format",
        "json",
    ]
    if runtime_package:
        command.append("--runtime-package")
    return _run(command, expect)


def _assert_result(result: dict[str, Any], *, expected_codes: list[str] | None = None, require_ok_payload: bool | None = None) -> dict[str, Any]:
    payload = _parse(str(result.get("output", "")))
    problems: list[str] = []
    if require_ok_payload is not None and payload.get("ok") is not require_ok_payload:
        problems.append(f"payload ok expected {require_ok_payload!r} got {payload.get('ok')!r}")
    if require_ok_payload is True:
        if payload.get("plugin_skill_count") != payload.get("source_skill_count"):
            problems.append("skill count mismatch in positive payload")
        if "analyzing-product-outbound-market" not in payload.get("plugin_skills", []):
            problems.append("product-market skill not reported in positive payload")
        if int(payload.get("checked_skill_relative_reference_count", 0) or 0) <= 0:
            problems.append("no skill relative references were checked")
        if payload.get("manifest_hook_path") is not None:
            problems.append("manifest must not register a startup hook")
        if int(payload.get("checked_hook_command_target_count", 0) or 0) != 0:
            problems.append("manifest must not check startup hook command targets")
    codes = [item.get("code") for item in payload.get("issues", []) if isinstance(item, dict)]
    for code in expected_codes or []:
        if code not in codes and code not in str(result.get("output", "")):
            problems.append(f"missing expected code {code}")
    if problems:
        result["ok"] = False
        result["returncode"] = 1
        result["output"] = str(result.get("output", "")) + "\nplugin distribution assertion failed: " + "; ".join(problems)
    return result


def run_suite() -> dict[str, Any]:
    py = sys.executable
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        repo_positive = _assert_result(_checker(py, ROOT, 0), require_ok_payload=True)
        repo_positive["name"] = "source tree plugin distribution passes"
        results.append(repo_positive)

        dist = tmp_path / "dist"
        build_result = _build_distribution(dist)
        nested_eval = dist / "skills" / "using-superleads" / ".plugin-eval"
        if nested_eval.exists():
            build_result["ok"] = False
            build_result["returncode"] = 1
            build_result["output"] = str(build_result.get("output", "")) + "\nruntime package retained nested .plugin-eval data"
        build_result["name"] = "runtime package build passes"
        results.append(build_result)
        copied_positive = _assert_result(_checker(py, dist, 0, runtime_package=True), require_ok_payload=True)
        copied_positive["name"] = "materialized runtime package passes"
        results.append(copied_positive)

        missing_skill = tmp_path / "missing_skill"
        _build_distribution(missing_skill)
        shutil.rmtree(missing_skill / "skills" / "analyzing-product-outbound-market")
        missing_skill_result = _assert_result(
            _checker(py, missing_skill, 1, runtime_package=True),
            expected_codes=["plugin_distribution_skill_count_mismatch", "plugin_distribution_required_skill_missing"],
            require_ok_payload=False,
        )
        missing_skill_result["name"] = "missing product-market skill is caught"
        results.append(missing_skill_result)

        dead_ref = tmp_path / "dead_reference"
        _build_distribution(dead_ref)
        (dead_ref / "shared" / "references" / "product-market-runtime.md").unlink()
        dead_ref_result = _assert_result(
            _checker(py, dead_ref, 1, runtime_package=True),
            expected_codes=["plugin_distribution_reference_missing"],
            require_ok_payload=False,
        )
        dead_ref_result["name"] = "dead Skill runtime reference is caught"
        results.append(dead_ref_result)

        missing_runtime_script = tmp_path / "missing_runtime_script"
        _build_distribution(missing_runtime_script)
        (missing_runtime_script / "scripts" / "validate_product_market_analysis.py").unlink()
        missing_runtime_script_result = _assert_result(
            _checker(py, missing_runtime_script, 1, runtime_package=True),
            expected_codes=["plugin_distribution_reference_missing"],
            require_ok_payload=False,
        )
        missing_runtime_script_result["name"] = "missing Skill-referenced script is caught"
        results.append(missing_runtime_script_result)

        missing_internal_stage = tmp_path / "missing_internal_stage"
        _build_distribution(missing_internal_stage)
        (missing_internal_stage / "shared" / "internal-stages" / "verification-before-delivery.md").unlink()
        missing_internal_stage_result = _assert_result(
            _checker(py, missing_internal_stage, 1, runtime_package=True),
            expected_codes=["plugin_distribution_internal_stage_missing"],
            require_ok_payload=False,
        )
        missing_internal_stage_result["name"] = "missing on-demand internal stage is caught"
        results.append(missing_internal_stage_result)

        forbidden_tmp = tmp_path / "forbidden_tmp"
        _build_distribution(forbidden_tmp)
        (forbidden_tmp / "tmp").mkdir()
        (forbidden_tmp / "tmp" / "old-uat.txt").write_text("must not ship", encoding="utf-8")
        forbidden_tmp_result = _assert_result(
            _checker(py, forbidden_tmp, 1, runtime_package=True),
            expected_codes=["plugin_distribution_forbidden_path"],
            require_ok_payload=False,
        )
        forbidden_tmp_result["name"] = "runtime package rejects historical tmp files"
        results.append(forbidden_tmp_result)

        forbidden_nested_eval = tmp_path / "forbidden_nested_eval"
        _build_distribution(forbidden_nested_eval)
        nested_dir = forbidden_nested_eval / "skills" / "using-superleads" / ".plugin-eval"
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / "benchmark.json").write_text("{}\n", encoding="utf-8")
        forbidden_nested_eval_result = _assert_result(
            _checker(py, forbidden_nested_eval, 1, runtime_package=True),
            expected_codes=["plugin_distribution_forbidden_path"],
            require_ok_payload=False,
        )
        forbidden_nested_eval_result["name"] = "runtime package rejects nested plugin evaluation data"
        results.append(forbidden_nested_eval_result)

    passed = sum(1 for item in results if item.get("ok"))
    failed = [item for item in results if not item.get("ok")]
    return {"suite": "all", "total": len(results), "passed": passed, "failed": len(failed), "results": results}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=SUITES, default="all")
    return parser.parse_args()


def main() -> int:
    parse_args()
    payload = run_suite()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
