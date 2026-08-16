#!/usr/bin/env python3
"""Run deterministic Superleads intake route evals."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases" / "superleads_route_cases.json"
ROUTER = ROOT / "scripts" / "route_superleads_intake.py"


def _run_case(py: str, case: dict[str, Any]) -> tuple[bool, str]:
    text = str(case.get("text", ""))
    proc = subprocess.run(
        [py, str(ROUTER), "--text", text, "--format", "json"],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    problems: list[str] = []
    actual: dict[str, Any] | None = None
    try:
        parsed = json.loads(proc.stdout)
        actual = parsed if isinstance(parsed, dict) else None
    except Exception as exc:
        problems.append(f"router output is not JSON: {exc}")

    if actual is not None:
        for key, expected_key in (
            ("route", "expected_route"),
            ("next_skill", "expected_next_skill"),
            ("split_customer_development", "expected_split_customer_development"),
            ("response_contract", "expected_response_contract"),
            ("language", "expected_language"),
        ):
            if expected_key in case and actual.get(key) != case.get(expected_key):
                problems.append(f"{key} expected {case.get(expected_key)!r} got {actual.get(key)!r}")

        for key, expected_key in (
            ("missing_fields", "expected_missing_fields"),
            ("secondary_routes", "expected_secondary_routes"),
            ("route_order", "expected_route_order"),
        ):
            if expected_key in case:
                expected_items = list(case.get(expected_key, []))
                actual_items = list(actual.get(key, [])) if isinstance(actual.get(key), list) else []
                if expected_items != actual_items:
                    problems.append(f"{key} expected {expected_items!r} got {actual_items!r}")

        response = "\n".join(str(item) for item in actual.get("response_lines", []) if item is not None)
        for needle in case.get("response_must_contain", []) if isinstance(case.get("response_must_contain"), list) else []:
            if str(needle) not in response:
                problems.append(f"response missing {needle!r}")

    ok = proc.returncode == 0 and actual is not None and not problems
    if ok:
        return True, f"PASS {case.get('name', text)}"
    detail = proc.stdout if not problems else proc.stdout + "\n" + "; ".join(problems)
    return False, f"FAIL {case.get('name', text)}\n{detail}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["all"], default="all")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    payload = json.loads(CASES.read_text(encoding="utf-8"))
    cases = [case for case in payload.get("cases", []) if isinstance(case, dict)]
    results = []
    for case in cases:
        ok, output = _run_case(sys.executable, case)
        results.append({"name": case.get("name", case.get("text", "")), "ok": ok, "output": output})

    passed = sum(1 for item in results if item["ok"])
    summary = {"passed": passed, "total": len(results), "ok": passed == len(results), "results": results}
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(item["output"])
        print(f"{passed}/{len(results)} route evals passed")
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
