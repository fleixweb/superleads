#!/usr/bin/env python3
"""Run generated Markdown delivery evals for the three Superleads routes."""
from __future__ import annotations

import argparse
import hashlib
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
SUPPORT_FOOTER_MARKER = "<!-- superleads-support-and-safety -->"


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


def _claimed_path_attestation_problems(
    payload: dict[str, Any],
    *,
    graph: str,
    markdown: str,
    route: str,
    expected_ok: bool,
    expected_issue_codes: list[str],
    graph_sha256: str,
    markdown_sha256: str | None,
) -> list[str]:
    attestation = payload.get("claimed_path_attestation")
    if not isinstance(attestation, dict):
        return ["missing claimed_path_attestation"]
    problems: list[str] = []
    expected_values = {
        "graph": graph,
        "markdown": markdown,
        "requested_route": route,
        "ok": expected_ok,
        "issue_count": len(expected_issue_codes),
        "graph_sha256": graph_sha256,
        "markdown_sha256": markdown_sha256,
    }
    for key, expected in expected_values.items():
        if attestation.get(key) != expected:
            problems.append(f"attestation {key} expected {expected!r} got {attestation.get(key)!r}")
    issue_codes = [item.get("code") for item in attestation.get("issues", []) if isinstance(item, dict)]
    if issue_codes != expected_issue_codes:
        problems.append(f"attestation issue codes expected {expected_issue_codes!r} got {issue_codes!r}")
    serialized_attestation = json.dumps(attestation, ensure_ascii=False)
    if str(ROOT) in serialized_attestation:
        problems.append("attestation exposed an absolute workspace path")
    if "expected.md" in serialized_attestation:
        problems.append("attestation exposed the temporary exporter path")
    for key in ("fixture", "cache_root", "export", "background_export", "northshore_row"):
        if key in payload:
            problems.append(f"claimed-path output unexpectedly contains legacy smoke alias {key}")
    return problems


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
    footer_count = text.count(SUPPORT_FOOTER_MARKER)
    if missing or hits or footer_count != 1:
        result["ok"] = False
        result["returncode"] = 1
        result["output"] += (
            "\ngenerated Markdown assertions failed: "
            f"missing={missing} forbidden_hits={hits} footer_count={footer_count}"
        )
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
    fixture = ROOT / "evals" / "fixtures" / "market_pass_xingheng_minimum_boundary.json"
    out = tmp_path / "claimed_path_uat_positive.md"
    graph_arg = str(fixture.relative_to(ROOT))
    markdown_arg = str(out.relative_to(ROOT))
    route = "product_outbound_market_analysis"
    delivery = run([
        py,
        str(DELIVERER),
        str(fixture),
        "--route",
        route,
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
        graph_arg,
        "--claimed-markdown",
        markdown_arg,
        "--claimed-route",
        route,
        "--format",
        "json",
    ], 0) if out.exists() else {"ok": False, "output": "missing exported Markdown"}
    parsed = _parse_json_output(str(claimed_check.get("output", "")))
    problems: list[str] = []
    if parsed and (parsed.get("ok") is not True or parsed.get("issue_count") != 0):
        problems.append(f"claimed path check payload not clean: ok={parsed.get('ok')} issue_count={parsed.get('issue_count')}")
    problems.extend(_claimed_path_attestation_problems(
        parsed,
        graph=graph_arg,
        markdown=markdown_arg,
        route=route,
        expected_ok=True,
        expected_issue_codes=[],
        graph_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        markdown_sha256=hashlib.sha256(out.read_bytes()).hexdigest() if out.exists() else "",
    ))
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
    fixture = ROOT / "evals" / "fixtures" / "market_pass_xingheng_minimum_boundary.json"
    original = tmp_path / "claimed_path_uat_original.md"
    mutated = tmp_path / "claimed_path_uat_mutated.md"
    graph_arg = str(fixture.relative_to(ROOT))
    markdown_arg = str(mutated.relative_to(ROOT))
    route = "product_outbound_market_analysis"
    delivery = run([
        py,
        str(DELIVERER),
        str(fixture),
        "--route",
        route,
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
        graph_arg,
        "--claimed-markdown",
        markdown_arg,
        "--claimed-route",
        route,
        "--format",
        "json",
    ], 1) if mutated.exists() else {"ok": False, "output": "missing mutated Markdown"}
    parsed = _parse_json_output(str(claimed_check.get("output", "")))
    top_level_issue_codes = [item.get("code") for item in parsed.get("issues", []) if isinstance(item, dict)]
    if "formal_markdown_claimed_output_mismatch" not in top_level_issue_codes:
        claimed_check["ok"] = False
        claimed_check["returncode"] = 0
        claimed_check["output"] += "\nclaimed path mismatch assertion failed: top-level issues missing formal_markdown_claimed_output_mismatch"
    problems = _claimed_path_attestation_problems(
        parsed,
        graph=graph_arg,
        markdown=markdown_arg,
        route=route,
        expected_ok=False,
        expected_issue_codes=["formal_markdown_claimed_output_mismatch"],
        graph_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        markdown_sha256=hashlib.sha256(mutated.read_bytes()).hexdigest() if mutated.exists() else "",
    )
    if problems:
        claimed_check["ok"] = False
        claimed_check["returncode"] = 0
        claimed_check["output"] += "\nclaimed path mismatch attestation assertion failed: " + "; ".join(problems)
    return {
        "name": "real UAT claimed path check rejects post-processed Markdown",
        "fixture": str(fixture.relative_to(ROOT)),
        "delivery": delivery,
        "claimed_path_check": claimed_check,
        "ok": bool(delivery.get("ok")) and bool(claimed_check.get("ok")),
    }


def _claimed_path_directory_case(py: str, tmp_path: Path) -> dict[str, Any]:
    fixture = ROOT / "evals" / "fixtures" / "market_pass_xingheng_minimum_boundary.json"
    graph_arg = str(fixture.relative_to(ROOT))
    markdown_arg = str(tmp_path.relative_to(ROOT))
    route = "product_outbound_market_analysis"
    claimed_check = run([
        py,
        str(FORMAL_CHECKER),
        "--skip-cache",
        "--claimed-graph",
        graph_arg,
        "--claimed-markdown",
        markdown_arg,
        "--claimed-route",
        route,
        "--format",
        "json",
    ], 1)
    parsed = _parse_json_output(str(claimed_check.get("output", "")))
    problems: list[str] = []
    if "Traceback" in str(claimed_check.get("output", "")):
        problems.append("directory claimed Markdown produced a traceback")
    top_level_issue_codes = [item.get("code") for item in parsed.get("issues", []) if isinstance(item, dict)]
    if "formal_markdown_claimed_markdown_not_readable" not in top_level_issue_codes:
        problems.append("top-level issues missing formal_markdown_claimed_markdown_not_readable")
    problems.extend(_claimed_path_attestation_problems(
        parsed,
        graph=graph_arg,
        markdown=markdown_arg,
        route=route,
        expected_ok=False,
        expected_issue_codes=["formal_markdown_claimed_markdown_not_readable"],
        graph_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        markdown_sha256=None,
    ))
    if problems:
        claimed_check["ok"] = False
        claimed_check["returncode"] = 0
        claimed_check["output"] += "\nclaimed path directory assertion failed: " + "; ".join(problems)
    return {
        "name": "real UAT claimed path check reports an unreadable Markdown path as JSON",
        "fixture": str(fixture.relative_to(ROOT)),
        "claimed_path_check": claimed_check,
        "ok": bool(claimed_check.get("ok")),
    }


def _legacy_smoke_alias_case(py: str) -> dict[str, Any]:
    smoke_check = run([
        py,
        str(FORMAL_CHECKER),
        "--skip-cache",
        "--format",
        "json",
    ], 0)
    parsed = _parse_json_output(str(smoke_check.get("output", "")))
    smoke = parsed.get("smoke_check")
    problems: list[str] = []
    if not isinstance(smoke, dict):
        problems.append("missing smoke_check")
    else:
        for key in ("fixture", "cache_root", "export", "background_export", "northshore_row"):
            if parsed.get(key) != smoke.get(key):
                problems.append(f"legacy smoke alias {key} does not match smoke_check")
    if "claimed_path_attestation" in parsed:
        problems.append("no-claim smoke output unexpectedly contains claimed_path_attestation")
    if problems:
        smoke_check["ok"] = False
        smoke_check["returncode"] = 1
        smoke_check["output"] += "\nlegacy smoke alias assertion failed: " + "; ".join(problems)
    return {
        "name": "legacy no-claim smoke output keeps top-level aliases",
        "smoke_check": smoke_check,
        "ok": bool(smoke_check.get("ok")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        tmp_path = Path(tmp)
        for index, case in enumerate(_load_cases(), start=1):
            results.append(_case(py, case, tmp_path, index))
        results.append(_claimed_path_positive_case(py, tmp_path))
        results.append(_claimed_path_mismatch_case(py, tmp_path))
        results.append(_claimed_path_directory_case(py, tmp_path))
        results.append(_legacy_smoke_alias_case(py))
    total = len(results)
    passed = sum(1 for result in results if result.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
