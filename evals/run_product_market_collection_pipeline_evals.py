#!/usr/bin/env python3
"""Run Product Outbound Market collection pipeline evals."""
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
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evals" / "fixtures"
CASES = ROOT / "evals" / "cases" / "product_market_collection_pipeline_cases.json"


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
        return None, "pipeline output root is not object"
    return payload, None


def _assert_contains(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) not in text]


def _assert_absent(text: str, needles: list[str]) -> list[str]:
    return [str(needle) for needle in needles if str(needle) in text]


def _fixture_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "sources": len(payload.get("sources", [])) if isinstance(payload.get("sources"), list) else 0,
        "observations": len(payload.get("observations", [])) if isinstance(payload.get("observations"), list) else 0,
        "evidence_cards": len(payload.get("evidence_cards", [])) if isinstance(payload.get("evidence_cards"), list) else 0,
        "matrix_rows": len(payload.get("matrix_rows", [])) if isinstance(payload.get("matrix_rows"), list) else 0,
        "search_logs": len(payload.get("search_logs", [])) if isinstance(payload.get("search_logs"), list) else 0,
    }


def _assert_pipeline_json(
    payload: dict[str, Any],
    case: dict[str, Any],
    graph_path: Path,
    merged_path: Path,
    collection_output_path: Path,
    pipeline_manifest_path: Path,
) -> list[str]:
    problems: list[str] = []
    if payload.get("ok") is not case.get("expected_ok"):
        problems.append(f"ok expected {case.get('expected_ok')!r} got {payload.get('ok')!r}")
    if payload.get("stage") != case.get("expected_stage"):
        problems.append(f"stage expected {case.get('expected_stage')!r} got {payload.get('stage')!r}")
    if payload.get("route") != "product_outbound_market_analysis_collection_pipeline":
        problems.append("route must be product_outbound_market_analysis_collection_pipeline")
    for flag in (
        "not_evidence",
        "does_not_search_web",
        "does_not_open_sources",
        "does_not_fetch_or_download_sources",
        "does_not_create_search_logs",
        "does_not_create_evidence_cards",
        "does_not_create_matrix_rows",
    ):
        if payload.get(flag) is not True:
            problems.append(f"{flag} must be true")
    if payload.get("allowed_output") != "collection_merge_validate_audit_optional_export_only":
        problems.append("allowed_output must be collection_merge_validate_audit_optional_export_only")

    collection = payload.get("collection") if isinstance(payload.get("collection"), dict) else {}
    merge = payload.get("merge") if isinstance(payload.get("merge"), dict) else {}
    pipeline_manifest = payload.get("pipeline_manifest") if isinstance(payload.get("pipeline_manifest"), dict) else {}
    if collection.get("ok") is not case.get("expected_collection_ok"):
        problems.append(f"collection.ok expected {case.get('expected_collection_ok')!r} got {collection.get('ok')!r}")
    if merge.get("ok") is not case.get("expected_merge_ok"):
        problems.append(f"merge.ok expected {case.get('expected_merge_ok')!r} got {merge.get('ok')!r}")
    if pipeline_manifest.get("records_are_not_evidence") is not True:
        problems.append("pipeline_manifest.records_are_not_evidence must be true")
    for flag in ("does_not_create_search_logs", "does_not_create_evidence_cards", "does_not_create_matrix_rows"):
        if case.get("expected_ok") is True and pipeline_manifest.get(flag) is not True:
            problems.append(f"pipeline_manifest.{flag} must be true")

    expected_codes = [str(item) for item in case.get("expected_issue_codes", [])] if isinstance(case.get("expected_issue_codes"), list) else []
    actual_codes = {str(item.get("code")) for item in payload.get("issues", []) if isinstance(item, dict)}
    missing_codes = [code for code in expected_codes if code not in actual_codes]
    if missing_codes:
        problems.append(f"missing expected issue codes: {', '.join(missing_codes)}")

    if not collection_output_path.exists():
        problems.append("collection output file was not written")
    else:
        collection_payload = json.loads(collection_output_path.read_text(encoding="utf-8"))
        if collection_payload.get("search_logs"):
            problems.append("collection output must not contain search_logs")
        if collection_payload.get("evidence_cards"):
            problems.append("collection output must not contain evidence_cards")
        if collection_payload.get("matrix_rows"):
            problems.append("collection output must not contain matrix_rows")

    if not pipeline_manifest_path.exists():
        problems.append("pipeline manifest file was not written")

    before = _fixture_counts(graph_path)
    if case.get("expected_ok") is True:
        if not merged_path.exists():
            problems.append("merged graph file was not written")
            return problems
        after = _fixture_counts(merged_path)
        if "expected_source_delta" in case and after["sources"] - before["sources"] != case["expected_source_delta"]:
            problems.append(f"source delta expected {case['expected_source_delta']} got {after['sources'] - before['sources']}")
        if "expected_observation_delta" in case and after["observations"] - before["observations"] != case["expected_observation_delta"]:
            problems.append(f"observation delta expected {case['expected_observation_delta']} got {after['observations'] - before['observations']}")
        for key in ("evidence_cards", "matrix_rows", "search_logs"):
            if after[key] != before[key]:
                problems.append(f"{key} count changed from {before[key]} to {after[key]}")
        graph_delta = payload.get("graph_count_delta") if isinstance(payload.get("graph_count_delta"), dict) else {}
        for key in ("evidence_cards", "matrix_rows", "search_logs"):
            if graph_delta.get(key) != 0:
                problems.append(f"graph_count_delta.{key} must be 0")
        validate = run([sys.executable, str(SCRIPTS / "validate_product_market_analysis.py"), str(merged_path)], 0)
        if not validate["ok"]:
            problems.append("merged graph failed validate_product_market_analysis")
        audit = run([sys.executable, str(SCRIPTS / "audit_product_market_analysis.py"), str(merged_path)], 0)
        if not audit["ok"]:
            problems.append("merged graph failed audit_product_market_analysis")
        export_payload = merge.get("export")
        if case.get("expect_export") and (not isinstance(export_payload, dict) or export_payload.get("ok") is not True):
            problems.append("expected successful export payload")
    elif merged_path.exists():
        problems.append("failed pipeline must not write merged graph file")
    return problems


def _case(py: str, case: dict[str, Any], tmp_path: Path, index: int) -> dict[str, Any]:
    graph_path = FIXTURES / str(case.get("graph"))
    collection_input_path = FIXTURES / str(case.get("collection_input"))
    merged_path = tmp_path / f"pipeline_merged_{index}.json"
    collection_output_path = tmp_path / f"pipeline_collection_{index}.json"
    export_dir = tmp_path / f"pipeline_export_{index}"
    markdown_path = tmp_path / f"pipeline_report_{index}.md"
    export_manifest_path = tmp_path / f"pipeline_export_manifest_{index}.json"
    pipeline_manifest_path = tmp_path / f"pipeline_manifest_{index}.json"
    expect = int(case.get("expected_returncode", 0))
    cmd = [
        py,
        str(SCRIPTS / "run_product_market_collection_pipeline.py"),
        "--graph",
        str(graph_path),
        "--collection-input",
        str(collection_input_path),
        "--output",
        str(merged_path),
        "--collection-output",
        str(collection_output_path),
        "--pipeline-manifest",
        str(pipeline_manifest_path),
    ]
    if case.get("expect_export"):
        cmd.extend(["--export-dir", str(export_dir), "--markdown", str(markdown_path), "--export-manifest", str(export_manifest_path)])
    result = run(cmd, expect)
    text = str(result.get("output", ""))
    payload, parse_error = _parse_json(text)
    problems: list[str] = []
    if parse_error:
        problems.append(f"json parse failed: {parse_error}")
    elif payload is not None:
        problems.extend(_assert_pipeline_json(payload, case, graph_path, merged_path, collection_output_path, pipeline_manifest_path))

    export_text = ""
    if export_dir.exists():
        for item in sorted(export_dir.glob("*.csv")):
            export_text += item.name + "\n" + item.read_text(encoding="utf-8-sig") + "\n"
    if markdown_path.exists():
        export_text += markdown_path.read_text(encoding="utf-8")
    if export_manifest_path.exists():
        export_text += export_manifest_path.read_text(encoding="utf-8")
    if pipeline_manifest_path.exists():
        text += "\n" + pipeline_manifest_path.read_text(encoding="utf-8")

    missing = _assert_contains(text, list(case.get("output_must_contain", []))) if case.get("output_must_contain") else []
    hits = _assert_absent(text, list(case.get("output_must_not_contain", []))) if case.get("output_must_not_contain") else []
    export_missing = _assert_contains(export_text, list(case.get("export_must_contain", []))) if case.get("export_must_contain") else []
    export_hits = _assert_absent(export_text, list(case.get("export_must_not_contain", []))) if case.get("export_must_not_contain") else []
    problems.extend([f"missing output text {item!r}" for item in missing])
    problems.extend([f"forbidden output text present {item!r}" for item in hits])
    problems.extend([f"missing export text {item!r}" for item in export_missing])
    problems.extend([f"forbidden export text present {item!r}" for item in export_hits])

    if problems or not result["ok"]:
        result["ok"] = False
        result["returncode"] = 1
        if problems:
            result["output"] = text + "\ncollection pipeline assertion failed: " + "; ".join(problems)
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
            result = _case(py, case, tmp_path, index)
            result["name"] = str(case.get("name", case.get("collection_input")))
            results.append(result)
    total = len(results)
    passed = sum(1 for item in results if item.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
