#!/usr/bin/env python3
"""Run generated Markdown delivery evals for the three Superleads routes."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases" / "superleads_markdown_delivery_cases.json"
DELIVERER = ROOT / "scripts" / "export_superleads_markdown.py"
VALIDATOR = ROOT / "scripts" / "validate_superleads_user_visible_output.py"
FORMAL_CHECKER = ROOT / "scripts" / "check_superleads_formal_markdown_delivery.py"


def run(cmd: list[str], expect: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    return [case for case in payload.get("cases", []) if isinstance(case, dict)]


def _assert_contains(text: str, needles: list[Any]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) not in text]


def _assert_absent(text: str, needles: list[Any]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) in text]


def _parse_json_output(output: str) -> dict[str, Any]:
    try:
        payload = json.loads(output)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _validate_generated_markdown(py: str, markdown: Path, route: str, case: dict[str, Any]) -> dict[str, Any]:
    cmd = [
        py,
        str(VALIDATOR),
        str(markdown),
        "--route",
        route,
        "--min-tables",
        str(case.get("min_tables", 3)),
        "--format",
        "json",
    ]
    for phrase in case.get("must_contain", []) if isinstance(case.get("must_contain"), list) else []:
        cmd.extend(["--must-contain", str(phrase)])
    result = run(cmd, 0)
    text = markdown.read_text(encoding="utf-8") if markdown.exists() else ""
    missing = _assert_contains(text, list(case.get("must_contain", []))) if case.get("must_contain") else []
    hits = _assert_absent(text, list(case.get("must_not_contain", []))) if case.get("must_not_contain") else []
    if missing or hits:
        result["ok"] = False
        result["returncode"] = 1
        result["output"] += f"\ngenerated Markdown assertions failed: missing={missing} forbidden_hits={hits}"
    return result


def _case(py: str, case: dict[str, Any], tmp_path: Path, index: int) -> dict[str, Any]:
    fixture = ROOT / str(case.get("fixture", ""))
    out = tmp_path / f"markdown_delivery_{index}.md"
    expect = 0 if case.get("expected", "pass") == "pass" else 1
    cmd = [py, str(DELIVERER), str(fixture), "--route", str(case.get("route", "auto")), "--output", str(out), "--format", "json"]
    delivery = run(cmd, expect)
    parsed = _parse_json_output(str(delivery.get("output", "")))
    problems: list[str] = []
    expected_route = case.get("expected_route")
    if expected_route and parsed.get("route") != expected_route:
        problems.append(f"route expected {expected_route!r} got {parsed.get('route')!r}")
    if expect == 0:
        if not out.exists():
            problems.append("Markdown output was not written")
        validator = _validate_generated_markdown(py, out, str(expected_route or parsed.get("route")), case) if out.exists() else {"ok": False, "output": "missing output"}
    else:
        validator = {"ok": True, "output": "skipped because delivery is expected to fail"}
        for code in case.get("expected_error_codes", []) if isinstance(case.get("expected_error_codes"), list) else []:
            if str(code) not in str(delivery.get("output", "")):
                problems.append(f"missing expected error code {code}")
        if out.exists():
            problems.append("failed delivery should not write Markdown output")
    if problems:
        delivery["ok"] = False
        delivery["returncode"] = 1
        delivery["output"] += "\nmarkdown delivery case assertion failed: " + "; ".join(problems)
    return {
        "name": str(case.get("name", fixture.name)),
        "fixture": str(case.get("fixture")),
        "delivery": delivery,
        "validator": validator,
        "ok": bool(delivery.get("ok")) and bool(validator.get("ok")),
    }


def _claimed_path_positive_case(py: str, tmp_path: Path) -> dict[str, Any]:
    fixture = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
    out = tmp_path / "claimed_path_uat_positive.md"
    delivery = run([
        py,
        str(DELIVERER),
        str(fixture),
        "--route",
        "bulk_customer_development",
        "--output",
        str(out),
        "--format",
        "json",
    ], 0)
    claimed_check = run([
        py,
        str(FORMAL_CHECKER),
        "--skip-cache",
        "--claimed-graph",
        str(fixture),
        "--claimed-markdown",
        str(out),
        "--claimed-route",
        "auto",
        "--format",
        "json",
    ], 0) if out.exists() else {"ok": False, "output": "missing exported Markdown"}
    parsed = _parse_json_output(str(claimed_check.get("output", "")))
    problems: list[str] = []
    if parsed and (parsed.get("ok") is not True or parsed.get("issue_count") != 0):
        problems.append(f"claimed path check payload not clean: ok={parsed.get('ok')} issue_count={parsed.get('issue_count')}")
    if problems:
        claimed_check["ok"] = False
        claimed_check["returncode"] = 1
        claimed_check["output"] += "\nclaimed path positive assertion failed: " + "; ".join(problems)
    return {
        "name": "real UAT claimed path check passes for exporter output",
        "fixture": str(fixture.relative_to(ROOT)),
        "delivery": delivery,
        "claimed_path_check": claimed_check,
        "ok": bool(delivery.get("ok")) and bool(claimed_check.get("ok")),
    }


def _claimed_path_mismatch_case(py: str, tmp_path: Path) -> dict[str, Any]:
    fixture = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
    original = tmp_path / "claimed_path_uat_original.md"
    mutated = tmp_path / "claimed_path_uat_mutated.md"
    delivery = run([
        py,
        str(DELIVERER),
        str(fixture),
        "--route",
        "bulk_customer_development",
        "--output",
        str(original),
        "--format",
        "json",
    ], 0)
    if original.exists():
        mutated.write_text(original.read_text(encoding="utf-8") + "\n<!-- manual post-processing drift -->\n", encoding="utf-8")
    claimed_check = run([
        py,
        str(FORMAL_CHECKER),
        "--skip-cache",
        "--claimed-graph",
        str(fixture),
        "--claimed-markdown",
        str(mutated),
        "--claimed-route",
        "auto",
        "--format",
        "json",
    ], 1) if mutated.exists() else {"ok": False, "output": "missing mutated Markdown"}
    if "formal_markdown_claimed_output_mismatch" not in str(claimed_check.get("output", "")):
        claimed_check["ok"] = False
        claimed_check["returncode"] = 0
        claimed_check["output"] += "\nclaimed path mismatch assertion failed: missing formal_markdown_claimed_output_mismatch"
    return {
        "name": "real UAT claimed path check rejects post-processed Markdown",
        "fixture": str(fixture.relative_to(ROOT)),
        "delivery": delivery,
        "claimed_path_check": claimed_check,
        "ok": bool(delivery.get("ok")) and bool(claimed_check.get("ok")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, case in enumerate(_load_cases(), start=1):
            results.append(_case(py, case, tmp_path, index))
        results.append(_claimed_path_positive_case(py, tmp_path))
        results.append(_claimed_path_mismatch_case(py, tmp_path))
    total = len(results)
    passed = sum(1 for result in results if result.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
