#!/usr/bin/env python3
"""Run Product Outbound Market collection merge/export evals."""
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
CASES = ROOT / "evals" / "cases" / "product_market_collection_merge_cases.json"


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
        return None, "merge output root is not object"
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


def _merged_counts(path: Path) -> dict[str, int]:
    return _fixture_counts(path)


def _assert_merge_json(payload: dict[str, Any], case: dict[str, Any], graph_path: Path, merged_path: Path) -> list[str]:
    problems: list[str] = []
    if payload.get("ok") is not case.get("expected_ok"):
        problems.append(f"ok expected {case.get('expected_ok')!r} got {payload.get('ok')!r}")
    if payload.get("route") != "product_outbound_market_analysis_collection_merge":
        problems.append("route must be product_outbound_market_analysis_collection_merge")
    for flag in ("not_evidence", "does_not_search_web", "does_not_open_sources", "does_not_create_evidence_cards", "does_not_create_matrix_rows"):
        if payload.get(flag) is not True:
            problems.append(f"{flag} must be true")
    if payload.get("allowed_output") != "merged_graph_and_optional_exports_only":
        problems.append("allowed_output must be merged_graph_and_optional_exports_only")

    expected_codes = [str(item) for item in case.get("expected_issue_codes", [])] if isinstance(case.get("expected_issue_codes"), list) else []
    actual_codes = {str(item.get("code")) for item in payload.get("issues", []) if isinstance(item, dict)}
    missing_codes = [code for code in expected_codes if code not in actual_codes]
    if missing_codes:
        problems.append(f"missing expected issue codes: {', '.join(missing_codes)}")

    if case.get("expected_ok") is True:
        if not merged_path.exists():
            problems.append("merged graph file was not written")
            return problems
        before = _fixture_counts(graph_path)
        after = _merged_counts(merged_path)
        if "expected_source_delta" in case and after["sources"] - before["sources"] != case["expected_source_delta"]:
            problems.append(f"source delta expected {case['expected_source_delta']} got {after['sources'] - before['sources']}")
        if "expected_observation_delta" in case and after["observations"] - before["observations"] != case["expected_observation_delta"]:
            problems.append(f"observation delta expected {case['expected_observation_delta']} got {after['observations'] - before['observations']}")
        for key in ("evidence_cards", "matrix_rows", "search_logs"):
            if after[key] != before[key]:
                problems.append(f"{key} count changed from {before[key]} to {after[key]}")
        validate = run([sys.executable, str(SCRIPTS / "validate_product_market_analysis.py"), str(merged_path)], 0)
        if not validate["ok"]:
            problems.append("merged graph failed validate_product_market_analysis")
        audit = run([sys.executable, str(SCRIPTS / "audit_product_market_analysis.py"), str(merged_path)], 0)
        if not audit["ok"]:
            problems.append("merged graph failed audit_product_market_analysis")
        export_payload = payload.get("export")
        if case.get("expect_export") and (not isinstance(export_payload, dict) or export_payload.get("ok") is not True):
            problems.append("expected successful export payload")
    elif merged_path.exists():
        problems.append("failed merge must not write merged graph file")
    return problems


def _case(py: str, case: dict[str, Any], tmp_path: Path, index: int) -> dict[str, Any]:
    graph_path = FIXTURES / str(case.get("graph"))
    collection_path = FIXTURES / str(case.get("collection"))
    merged_path = tmp_path / f"merged_{index}.json"
    export_dir = tmp_path / f"export_{index}"
    markdown_path = tmp_path / f"report_{index}.md"
    manifest_path = tmp_path / f"manifest_{index}.json"
    expect = int(case.get("expected_returncode", 0))
    cmd = [
        py,
        str(SCRIPTS / "merge_product_market_collection.py"),
        "--graph",
        str(graph_path),
        "--collection",
        str(collection_path),
        "--output",
        str(merged_path),
    ]
    if case.get("expect_export"):
        cmd.extend(["--export-dir", str(export_dir), "--markdown", str(markdown_path), "--manifest", str(manifest_path)])
    result = run(cmd, expect)
    text = str(result.get("output", ""))
    payload, parse_error = _parse_json(text)
    problems: list[str] = []
    if parse_error:
        problems.append(f"json parse failed: {parse_error}")
    elif payload is not None:
        problems.extend(_assert_merge_json(payload, case, graph_path, merged_path))

    export_text = ""
    if export_dir.exists():
        for item in sorted(export_dir.glob("*.csv")):
            export_text += item.name + "\n" + item.read_text(encoding="utf-8-sig") + "\n"
    if markdown_path.exists():
        export_text += markdown_path.read_text(encoding="utf-8")
    if manifest_path.exists():
        export_text += manifest_path.read_text(encoding="utf-8")

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
            result["output"] = text + "\ncollection merge assertion failed: " + "; ".join(problems)
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
            result["name"] = str(case.get("name", case.get("collection")))
            results.append(result)
    total = len(results)
    passed = sum(1 for item in results if item.get("ok"))
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
