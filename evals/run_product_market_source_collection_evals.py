#!/usr/bin/env python3
"""Run Product Outbound Market manual source collection evals."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evals" / "fixtures"
CASES = ROOT / "evals" / "cases" / "product_market_source_collection_cases.json"


def run(cmd: list[str], expect: int) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    return [case for case in payload.get("cases", []) if isinstance(case, dict)]


def _parse_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(text)
    except Exception as exc:  # noqa: BLE001 - eval runner reports parse details
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "collector output root is not object"
    return payload, None


def _assert_contains(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) not in text]


def _assert_absent(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) in text]


def _assert_collection_json(payload: dict[str, Any], case: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if payload.get("ok") is not case.get("expected_ok"):
        problems.append(f"ok expected {case.get('expected_ok')!r} got {payload.get('ok')!r}")
    if payload.get("route") != "product_outbound_market_analysis_source_collection":
        problems.append("route must be product_outbound_market_analysis_source_collection")
    if payload.get("execution_level") != "manual_source_collection_records_only":
        problems.append("execution_level must be manual_source_collection_records_only")
    for flag in ("not_evidence", "does_not_search_web", "does_not_open_sources", "does_not_create_evidence_cards", "does_not_create_matrix_rows"):
        if payload.get(flag) is not True:
            problems.append(f"{flag} must be true")
    if payload.get("allowed_output") != "source_and_observation_records_only":
        problems.append("allowed_output must be source_and_observation_records_only")
    if payload.get("search_logs"):
        problems.append("manual collector must not emit search_logs")
    if payload.get("evidence_cards"):
        problems.append("manual collector must not emit evidence_cards")
    if payload.get("matrix_rows"):
        problems.append("manual collector must not emit matrix_rows")

    sources = payload.get("sources") if isinstance(payload.get("sources"), list) else []
    observations = payload.get("observations") if isinstance(payload.get("observations"), list) else []
    manifest = payload.get("collection_manifest") if isinstance(payload.get("collection_manifest"), dict) else {}
    if "expected_source_count" in case and len(sources) != case["expected_source_count"]:
        problems.append(f"source count expected {case['expected_source_count']} got {len(sources)}")
    if "expected_observation_count" in case and len(observations) != case["expected_observation_count"]:
        problems.append(f"observation count expected {case['expected_observation_count']} got {len(observations)}")
    for key in ("expected_opened_observation_count", "expected_restricted_or_not_accessed_count"):
        manifest_key = key.replace("expected_", "")
        if key in case and manifest.get(manifest_key) != case[key]:
            problems.append(f"{manifest_key} expected {case[key]} got {manifest.get(manifest_key)}")
    for status in case.get("must_have_access_statuses", []) if isinstance(case.get("must_have_access_statuses"), list) else []:
        if status not in {obs.get("access_status") for obs in observations if isinstance(obs, dict)}:
            problems.append(f"missing access_status {status}")
    for medium in case.get("must_have_media", []) if isinstance(case.get("must_have_media"), list) else []:
        if medium not in {source.get("medium") for source in sources if isinstance(source, dict)}:
            problems.append(f"missing source medium {medium}")
    if case.get("expected_ok") is True:
        for idx, source in enumerate(sources):
            if source.get("provenance") != "manual_input":
                problems.append(f"sources[{idx}].provenance must be manual_input")
            if source.get("medium") == "search_result":
                problems.append(f"sources[{idx}] must not be search_result")
        for idx, obs in enumerate(observations):
            if obs.get("capability") == "search.web":
                problems.append(f"observations[{idx}] must not use search.web")
            if obs.get("access_status") in {"not_accessed", "login_wall", "forbidden", "blocked", "restricted"} and obs.get("raw_excerpt"):
                problems.append(f"observations[{idx}] restricted/not_accessed source has raw_excerpt")
    expected_codes = [str(item) for item in case.get("expected_issue_codes", [])] if isinstance(case.get("expected_issue_codes"), list) else []
    actual_codes = {str(item.get("code")) for item in payload.get("issues", []) if isinstance(item, dict)}
    missing_codes = [code for code in expected_codes if code not in actual_codes]
    if missing_codes:
        problems.append(f"missing expected issue codes: {', '.join(missing_codes)}")
    return problems


def _materialize_merged_graph(collection_payload: dict[str, Any], case: dict[str, Any], tmp_path: Path, index: int) -> Path | None:
    fixture = case.get("merge_market_fixture")
    if not isinstance(fixture, str):
        return None
    graph = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    if not isinstance(graph, dict):
        raise ValueError("merge_market_fixture root must be object")
    graph = deepcopy(graph)
    existing_sources = {item.get("source_id") for item in graph.get("sources", []) if isinstance(item, dict)}
    for source in collection_payload.get("sources", []) if isinstance(collection_payload.get("sources"), list) else []:
        if isinstance(source, dict) and source.get("source_id") not in existing_sources:
            graph.setdefault("sources", []).append(source)
    existing_observations = {item.get("observation_id") for item in graph.get("observations", []) if isinstance(item, dict)}
    for obs in collection_payload.get("observations", []) if isinstance(collection_payload.get("observations"), list) else []:
        if isinstance(obs, dict) and obs.get("observation_id") not in existing_observations:
            graph.setdefault("observations", []).append(obs)
    target = tmp_path / f"merged_market_collection_{index}.json"
    target.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def _collector_case(py: str, case: dict[str, Any], tmp_path: Path, index: int) -> dict[str, Any]:
    fixture = str(case.get("fixture"))
    expect = int(case.get("expected_returncode", 0))
    result = run([py, str(SCRIPTS / "collect_product_market_sources.py"), "--input", str(FIXTURES / fixture), "--format", "json"], expect)
    text = str(result.get("output", ""))
    payload, parse_error = _parse_json(text)
    problems: list[str] = []
    if parse_error:
        problems.append(f"json parse failed: {parse_error}")
    elif payload is not None:
        problems.extend(_assert_collection_json(payload, case))
        if result["ok"] and case.get("merge_market_fixture") and payload.get("ok") is True:
            merged = _materialize_merged_graph(payload, case, tmp_path, index)
            if merged is not None:
                validate = run([py, str(SCRIPTS / "validate_product_market_analysis.py"), str(merged)], 0)
                if not validate["ok"]:
                    problems.append("merged ProductMarketAnalysisGraph did not validate")
                    text += "\nmerged validation output:\n" + str(validate.get("output", ""))
    missing = _assert_contains(text, list(case.get("output_must_contain", []))) if case.get("output_must_contain") else []
    hits = _assert_absent(text, list(case.get("output_must_not_contain", []))) if case.get("output_must_not_contain") else []
    problems.extend([f"missing text {item!r}" for item in missing])
    problems.extend([f"forbidden text present {item!r}" for item in hits])
    if problems or not result["ok"]:
        result["ok"] = False
        result["returncode"] = 1
        if problems:
            result["output"] = text + "\nsource collection assertion failed: " + "; ".join(problems)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["pass", "fail", "all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, case in enumerate(_load_cases()):
            expected_ok = bool(case.get("expected_ok"))
            if args.suite == "pass" and not expected_ok:
                continue
            if args.suite == "fail" and expected_ok:
                continue
            result = _collector_case(py, case, tmp_path, index)
            result["name"] = str(case.get("name", case.get("fixture")))
            results.append(result)
    total = len(results)
    passed = sum(1 for item in results if item.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
