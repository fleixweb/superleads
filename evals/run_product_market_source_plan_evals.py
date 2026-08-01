#!/usr/bin/env python3
"""Run Product Outbound Market Source Pack / Query Plan evals."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evals" / "fixtures"
CASES = ROOT / "evals" / "cases" / "product_market_source_plan_cases.json"
REGISTRY = ROOT / "shared" / "source_packs" / "product_market_seed_packs.json"


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


def _query_strings_text(payload: dict[str, Any]) -> str:
    strings: list[str] = []
    for step in payload.get("query_plan", []) if isinstance(payload.get("query_plan"), list) else []:
        if not isinstance(step, dict):
            continue
        for query in step.get("query_strings", []) if isinstance(step.get("query_strings"), list) else []:
            strings.append(str(query))
    return "\n".join(strings)


def _parse_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - eval runner reports parse details
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "planner output root is not object"
    return payload, None


def _assert_plan_json(payload: dict[str, Any], case: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if payload.get("ok") is not case.get("expected_ok"):
        problems.append(f"ok expected {case.get('expected_ok')!r} got {payload.get('ok')!r}")
    if payload.get("execution_level") != "source_plan_only":
        problems.append("execution_level must be source_plan_only")
    if payload.get("not_evidence") is not True:
        problems.append("root not_evidence must be true")
    if payload.get("does_not_search_web") is not True or payload.get("does_not_open_sources") is not True:
        problems.append("planner must declare it does not search/open sources")
    selected = set(payload.get("selected_pack_ids", [])) if isinstance(payload.get("selected_pack_ids"), list) else set()
    for pack_id in case.get("must_select_pack_ids", []) if isinstance(case.get("must_select_pack_ids"), list) else []:
        if pack_id not in selected:
            problems.append(f"missing selected pack {pack_id}")
    for pack_id in case.get("must_not_select_pack_ids", []) if isinstance(case.get("must_not_select_pack_ids"), list) else []:
        if pack_id in selected:
            problems.append(f"unexpected selected pack {pack_id}")
    summary = payload.get("brief_summary") if isinstance(payload.get("brief_summary"), dict) else {}
    expected_summary = case.get("brief_summary_must_equal")
    if isinstance(expected_summary, dict):
        for key, expected in expected_summary.items():
            if summary.get(key) != expected:
                problems.append(f"brief_summary.{key} expected {expected!r} got {summary.get(key)!r}")
    warning_codes = {
        item.get("code")
        for item in payload.get("warnings", [])
        if isinstance(item, dict)
    } if isinstance(payload.get("warnings"), list) else set()
    for code in case.get("warning_codes_must_contain", []) if isinstance(case.get("warning_codes_must_contain"), list) else []:
        if code not in warning_codes:
            problems.append(f"missing warning code {code}")
    for code in case.get("warning_codes_must_not_contain", []) if isinstance(case.get("warning_codes_must_not_contain"), list) else []:
        if code in warning_codes:
            problems.append(f"unexpected warning code {code}")
    templates = {item.get("template_id") for item in payload.get("query_plan", []) if isinstance(item, dict)} if isinstance(payload.get("query_plan"), list) else set()
    for template_id in case.get("must_include_template_ids", []) if isinstance(case.get("must_include_template_ids"), list) else []:
        if template_id not in templates:
            problems.append(f"missing query template {template_id}")
    if case.get("emit_collection_run_shell"):
        shell = payload.get("collection_run_shell")
        if not isinstance(shell, dict):
            problems.append("collection_run_shell missing")
        else:
            if shell.get("execution_level") != "collection_record_shell_only":
                problems.append("collection_run_shell execution_level must be collection_record_shell_only")
            if shell.get("not_evidence") is not True:
                problems.append("collection_run_shell not_evidence must be true")
            if shell.get("does_not_search_web") is not True or shell.get("does_not_open_sources") is not True:
                problems.append("collection_run_shell must not search/open sources")
            if shell.get("allowed_output") != "collection_run_shell_only":
                problems.append("collection_run_shell allowed_output must be collection_run_shell_only")
            if shell.get("search_logs") != [] or shell.get("sources") != [] or shell.get("observations") != []:
                problems.append("collection_run_shell must start with empty search_logs/sources/observations")
            pending = shell.get("pending_query_plan_steps")
            if not isinstance(pending, list) or len(pending) != len(payload.get("query_plan", [])):
                problems.append("collection_run_shell pending steps must match query_plan length")
            else:
                for pidx, pending_step in enumerate(pending):
                    if not isinstance(pending_step, dict):
                        problems.append(f"pending_query_plan_steps[{pidx}] is not object")
                        continue
                    if pending_step.get("search_log_allowed_output") != "search_log_or_source_locator_only":
                        problems.append(f"pending_query_plan_steps[{pidx}] missing search_log_or_source_locator_only")
                    if pending_step.get("observation_allowed_only_after_open_source") is not True:
                        problems.append(f"pending_query_plan_steps[{pidx}] missing observation open-source gate")
                    if pending_step.get("not_evidence") is not True:
                        problems.append(f"pending_query_plan_steps[{pidx}] missing not_evidence")

    for idx, step in enumerate(payload.get("query_plan", []) if isinstance(payload.get("query_plan"), list) else []):
        if not isinstance(step, dict):
            problems.append(f"query_plan[{idx}] is not object")
            continue
        if step.get("must_open_source") is not True:
            problems.append(f"query_plan[{idx}] missing must_open_source=true")
        if step.get("reject_if_only_snippet") is not True:
            problems.append(f"query_plan[{idx}] missing reject_if_only_snippet=true")
        if step.get("not_evidence") is not True:
            problems.append(f"query_plan[{idx}] missing not_evidence=true")
        if step.get("allowed_output") != "source_or_query_plan_only":
            problems.append(f"query_plan[{idx}] allowed_output not source_or_query_plan_only")
        if not step.get("blocked_outputs"):
            problems.append(f"query_plan[{idx}] missing blocked_outputs")
    query_text = _query_strings_text(payload)
    missing_queries = _assert_contains(query_text, list(case.get("query_strings_must_contain", []))) if case.get("query_strings_must_contain") else []
    forbidden_queries = _assert_absent(query_text, list(case.get("query_strings_must_not_contain", []))) if case.get("query_strings_must_not_contain") else []
    problems.extend([f"missing query text {item!r}" for item in missing_queries])
    problems.extend([f"forbidden query text present {item!r}" for item in forbidden_queries])
    return problems


def _planner_case(py: str, case: dict[str, Any]) -> dict[str, Any]:
    fixture = str(case.get("fixture"))
    expect = int(case.get("expected_returncode", 0))
    cmd = [py, str(SCRIPTS / "plan_product_market_sources.py"), "--input", str(FIXTURES / fixture), "--format", "json"]
    if case.get("emit_collection_run_shell"):
        cmd.append("--emit-collection-run-shell")
    result = run(cmd, expect)
    payload, parse_error = _parse_json(str(result.get("output", "")))
    problems: list[str] = []
    if parse_error:
        problems.append(f"json parse failed: {parse_error}")
    elif payload is not None:
        problems.extend(_assert_plan_json(payload, case))
    text = str(result.get("output", ""))
    missing = _assert_contains(text, list(case.get("output_must_contain", []))) if case.get("output_must_contain") else []
    hits = _assert_absent(text, list(case.get("output_must_not_contain", []))) if case.get("output_must_not_contain") else []
    problems.extend([f"missing text {item!r}" for item in missing])
    problems.extend([f"forbidden text present {item!r}" for item in hits])
    if problems or not result["ok"]:
        result["ok"] = False
        result["returncode"] = 1
        if problems:
            result["output"] = text + "\nsource plan assertion failed: " + "; ".join(problems)
    return result


def _registry_case(py: str) -> dict[str, Any]:
    result = run([py, str(SCRIPTS / "plan_product_market_sources.py"), "--input", str(FIXTURES / "source_plan_xingheng_lithium_us_brief.json"), "--registry", str(REGISTRY), "--check-registry", "--format", "json"], 0)
    payload, parse_error = _parse_json(str(result.get("output", "")))
    problems: list[str] = []
    if parse_error:
        problems.append(f"json parse failed: {parse_error}")
    elif payload and payload.get("ok") is not True:
        problems.append(f"registry ok expected true got {payload.get('ok')}")
    text = str(result.get("output", ""))
    for forbidden in ["final_duty_rate", "certification_required", "coo_required", "recommended_price", "best_route"]:
        if forbidden in text:
            problems.append(f"registry check output leaked forbidden field {forbidden}")
    if problems or not result["ok"]:
        result["ok"] = False
        result["returncode"] = 1
        if problems:
            result["output"] = text + "\nregistry assertion failed: " + "; ".join(problems)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["registry", "pass", "fail", "all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    results: list[dict[str, Any]] = []
    if args.suite in {"registry", "all"}:
        reg = _registry_case(py)
        reg["name"] = "registry self-check"
        results.append(reg)
    for case in _load_cases():
        expected_ok = bool(case.get("expected_ok"))
        if args.suite == "pass" and not expected_ok:
            continue
        if args.suite == "fail" and expected_ok:
            continue
        if args.suite == "registry":
            continue
        result = _planner_case(py, case)
        result["name"] = str(case.get("name", case.get("fixture")))
        results.append(result)
    total = len(results)
    passed = sum(1 for item in results if item.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
