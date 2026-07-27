#!/usr/bin/env python3
"""Run static evals for Superleads user-visible output samples."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases" / "superleads_user_visible_output_cases.json"
VALIDATOR = ROOT / "scripts" / "validate_superleads_user_visible_output.py"


def run(cmd: list[str], expect: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    return [case for case in cases if isinstance(case, dict)]


def _assert_contains(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) not in text]


def _assert_absent(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) in text]


def _case(py: str, case: dict[str, Any]) -> dict[str, Any]:
    fixture = ROOT / str(case.get("fixture", ""))
    cmd = [
        py,
        str(VALIDATOR),
        str(fixture),
        "--route",
        str(case.get("route")),
        "--min-tables",
        str(case.get("min_tables", 3)),
        "--format",
        "json",
    ]
    for phrase in case.get("must_contain", []) if isinstance(case.get("must_contain"), list) else []:
        cmd.extend(["--must-contain", str(phrase)])
    expect = 0 if case.get("expected", "pass") == "pass" else 1
    result = run(cmd, expect)
    if case.get("expected_error_codes"):
        missing_codes = [str(code) for code in case.get("expected_error_codes", []) if str(code) not in str(result.get("output", ""))]
        if missing_codes:
            result["ok"] = False
            result["returncode"] = 1
            result["output"] += f"\nmissing expected error codes: {missing_codes}"
    text = fixture.read_text(encoding="utf-8") if fixture.exists() else ""
    missing = _assert_contains(text, list(case.get("must_contain", []))) if case.get("must_contain") else []
    hits = _assert_absent(text, list(case.get("must_not_contain", []))) if case.get("must_not_contain") and expect == 0 else []
    if missing or hits:
        result["ok"] = False
        result["returncode"] = 1
        result["output"] += f"\nuser visible output assertions failed: missing={missing} forbidden_hits={hits}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    results: list[dict[str, Any]] = []
    for case in _load_cases():
        result = _case(py, case)
        result["name"] = str(case.get("name", case.get("fixture")))
        results.append(result)
    total = len(results)
    passed = sum(1 for item in results if item.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
