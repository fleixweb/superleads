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
SUITES = ("all",)


def _run(cmd: list[str], expect: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _copy_distribution(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for rel in (".codex-plugin", "skills", "shared", "spec"):
        src = ROOT / rel
        if src.is_dir():
            shutil.copytree(src, target / rel)
        elif src.exists():
            shutil.copy2(src, target / rel)


def _parse(output: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _checker(py: str, plugin_root: Path, expect: int) -> dict[str, Any]:
    return _run([
        py,
        str(CHECKER),
        "--plugin-root",
        str(plugin_root),
        "--source-root",
        str(ROOT),
        "--format",
        "json",
    ], expect)


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
        _copy_distribution(dist)
        copied_positive = _assert_result(_checker(py, dist, 0), require_ok_payload=True)
        copied_positive["name"] = "materialized plugin distribution passes"
        results.append(copied_positive)

        missing_skill = tmp_path / "missing_skill"
        _copy_distribution(missing_skill)
        shutil.rmtree(missing_skill / "skills" / "analyzing-product-outbound-market")
        missing_skill_result = _assert_result(
            _checker(py, missing_skill, 1),
            expected_codes=["plugin_distribution_skill_count_mismatch", "plugin_distribution_required_skill_missing"],
            require_ok_payload=False,
        )
        missing_skill_result["name"] = "missing product-market skill is caught"
        results.append(missing_skill_result)

        dead_ref = tmp_path / "dead_reference"
        _copy_distribution(dead_ref)
        (dead_ref / "spec" / "10-product-outbound-market-analysis-contract.md").unlink()
        dead_ref_result = _assert_result(
            _checker(py, dead_ref, 1),
            expected_codes=["plugin_distribution_reference_missing"],
            require_ok_payload=False,
        )
        dead_ref_result["name"] = "dead Skill spec reference is caught"
        results.append(dead_ref_result)

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
