#!/usr/bin/env python3
"""Run the dedicated product outbound market analysis regression suite."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evals" / "fixtures"
CASES = ROOT / "evals" / "cases" / "product_market_analysis_cases.json"


def run(cmd: list[str], expect: int) -> dict[str, object]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def _load_cases() -> list[dict[str, object]]:
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    cases = payload.get("cases", [])
    return [case for case in cases if isinstance(case, dict)]


def _materialize_fixture(path: Path, tmp_path: Path, index: int) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "extends" not in payload:
        return str(path)
    sys.path.insert(0, str(ROOT / "evals"))
    from run_evals import _load_fixture_graph  # type: ignore  # noqa: WPS433,E402
    graph = _load_fixture_graph(path)
    target = tmp_path / f"fixture_{index}_{path.name}"
    target.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


def _assert_contains(text: str, needles: list[str]) -> list[str]:
    missing = []
    for needle in needles:
        if str(needle) not in text:
            missing.append(str(needle))
    return missing


def _assert_absent(text: str, needles: list[str]) -> list[str]:
    hits = []
    for needle in needles:
        if str(needle) in text:
            hits.append(str(needle))
    return hits


def _validate_case(py: str, fixture: str, expected: str, tmp_path: Path, index: int) -> dict[str, object]:
    path = _materialize_fixture(FIXTURES / fixture, tmp_path, index)
    result = run([py, str(SCRIPTS / "validate_product_market_analysis.py"), path], 0 if expected == "pass" else 1)
    return result


def _audit_case(py: str, fixture: str, expected: str, tmp_path: Path, index: int) -> dict[str, object]:
    path = _materialize_fixture(FIXTURES / fixture, tmp_path, index)
    result = run([py, str(SCRIPTS / "audit_product_market_analysis.py"), path], 0 if expected == "pass" else 1)
    if result["ok"]:
        try:
            payload = json.loads(result["output"])
            actual_status = payload.get("delivery_status")
            expected_status = "ready_with_limitations" if expected == "pass" else "blocked_needs_input" if expected == "blocked" else "needs_correction"
            result["ok"] = actual_status == expected_status
            if not result["ok"]:
                result["output"] += f"\nexpected delivery_status={expected_status} got={actual_status}"
                result["returncode"] = 1
        except Exception as exc:
            result["ok"] = False
            result["returncode"] = 1
            result["output"] += f"\njson parse failed: {exc}"
    return result


def _export_case(py: str, fixture: str, expected: str, tmp_path: Path, index: int, case: dict[str, object]) -> dict[str, object]:
    if expected == "skip":
        return {"cmd": ["skip"], "returncode": 0, "expected": 0, "ok": True, "output": "skipped"}
    path = _materialize_fixture(FIXTURES / fixture, tmp_path, index)
    out_dir = tmp_path / f"market_export_{index}"
    markdown_path = out_dir / "report.md" if str(case.get("market_export_markdown", "skip")) == "pass" else None
    cmd = [py, str(SCRIPTS / "export_product_market_workbook.py"), path, "--output-dir", str(out_dir), "--format", "csv", "--manifest", str(out_dir / "manifest.json")]
    if markdown_path is not None:
        cmd.extend(["--markdown", str(markdown_path)])
    if expected == "pass":
        result = run(cmd, 0)
        if not result["ok"]:
            return result
        combined = ""
        csv_text = ""
        for file in sorted(out_dir.glob("*.csv")):
            text = file.read_text(encoding="utf-8-sig")
            combined += text
            csv_text += text
        if markdown_path is not None and markdown_path.exists():
            combined += markdown_path.read_text(encoding="utf-8")
        manifest = (out_dir / "manifest.json").read_text(encoding="utf-8") if (out_dir / "manifest.json").exists() else ""
        combined += manifest
        missing = _assert_contains(combined, list(case.get("market_export_present", []))) if case.get("market_export_present") else []
        absent = _assert_absent(combined, list(case.get("market_export_absent", []))) if case.get("market_export_absent") else []
        result["ok"] = not missing and not absent
        if not result["ok"]:
            result["returncode"] = 1
            result["output"] += f"\nmissing={missing} absent_hits={absent}"
        return result
    result = run(cmd, 1)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=["pass", "fail", "all"], default="all")
    args = parser.parse_args()
    py = sys.executable
    tests: list[tuple[str, dict[str, object]]] = []
    for case in _load_cases():
        fixture = str(case.get("fixture"))
        market_validate = str(case.get("market_validate", ""))
        if args.suite == "pass" and market_validate != "pass":
            continue
        if args.suite == "fail" and market_validate == "pass":
            continue
        tests.append((fixture, case))

    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for index, (fixture, case) in enumerate(tests):
            expected = str(case.get("market_validate", "pass"))
            validate = _validate_case(py, fixture, expected, tmp_path, index)
            audit = _audit_case(py, fixture, str(case.get("market_audit", expected)), tmp_path, index)
            export = _export_case(py, fixture, str(case.get("market_export_csv", expected)), tmp_path, index, case)
            result = {
                "fixture": fixture,
                "validate": validate,
                "audit": audit,
                "export": export,
                "ok": bool(validate["ok"]) and bool(audit["ok"]) and bool(export["ok"]),
            }
            results.append(result)

    total = len(results)
    passed = sum(1 for item in results if item["ok"])
    summary = {"suite": args.suite, "total": total, "passed": passed, "failed": total - passed, "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
