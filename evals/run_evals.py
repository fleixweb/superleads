#!/usr/bin/env python3
"""Run minimal Superleads eval suite."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evals" / "fixtures"
CASES = ROOT / "evals" / "cases"
BEHAVIORAL = ROOT / "evals" / "behavioral"
INTEGRATION = ROOT / "evals" / "integration"
LEGACY_DERIVED = ROOT / "evals" / "legacy-derived"
SCHEMAS = ROOT / "shared" / "schemas"


def run(cmd: list[str], expect: int) -> dict[str, object]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return {"cmd": cmd, "returncode": proc.returncode, "expected": expect, "ok": proc.returncode == expect, "output": proc.stdout}


def run_export_assertions(py: str, fixture_path: str, tmp_path: Path, index: int, case: dict[str, object]) -> dict[str, object]:
    out_dir = tmp_path / f"export_assert_{index}"
    manifest_path = out_dir / "manifest.json"
    cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(out_dir), "--mode", "standard", "--format", "csv", "--manifest", str(manifest_path)]
    result = run(cmd, 0)
    if not result["ok"]:
        return result
    haystack = ""
    for item in sorted(out_dir.glob("*.csv")):
        haystack += item.name + "\n" + item.read_text(encoding="utf-8-sig") + "\n"
    if manifest_path.exists():
        haystack += manifest_path.read_text(encoding="utf-8")
    missing = [needle for needle in case.get("export_absent", []) if str(needle) in haystack]
    present_missing = [needle for needle in case.get("export_present", []) if str(needle) not in haystack]
    ok = not missing and not present_missing
    result["ok"] = ok
    result["export_absent_failures"] = missing
    result["export_present_failures"] = present_missing
    if not ok:
        result["returncode"] = 1
        result["output"] += f"\nexport assertion failed absent={missing} present_missing={present_missing}"
    return result


def run_audit_status(py: str, fixture_path: str, expected_status: str) -> dict[str, object]:
    cmd = [py, str(SCRIPTS / "audit_delivery.py"), fixture_path, "--format", "json"]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = False
    actual_status = None
    try:
        payload = json.loads(proc.stdout)
        actual_status = payload.get("delivery_status")
        ok = proc.returncode == 0 and actual_status == expected_status
    except Exception:
        ok = False
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "expected": 0,
        "expected_delivery_status": expected_status,
        "actual_delivery_status": actual_status,
        "ok": ok,
        "output": proc.stdout,
    }


def add_case_tests(py: str, tests: list[tuple[str, list[str], int]]) -> None:
    for case_file in sorted(CASES.glob("*.json")):
        payload = json.loads(case_file.read_text(encoding="utf-8"))
        for case in payload.get("cases", []):
            fixture = case.get("fixture")
            if not fixture:
                continue
            path = str(FIXTURES / fixture)
            if case.get("validate"):
                tests.append((f"case {fixture} validate {case['validate']}", [py, str(SCRIPTS / "validate_research_graph.py"), path], 0 if case["validate"] == "pass" else 1))
            if case.get("audit"):
                tests.append((f"case {fixture} audit {case['audit']}", [py, str(SCRIPTS / "audit_delivery.py"), path], 0 if case["audit"] == "pass" else 1))
            if case.get("audit_delivery_status"):
                tests.append((f"case {fixture} audit_delivery_status {case['audit_delivery_status']}", ["__AUDIT_STATUS__", path, case["audit_delivery_status"]], 0))
            if case.get("audit_standard"):
                tests.append((f"case {fixture} audit_standard {case['audit_standard']}", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", "standard_development_list"], 0 if case["audit_standard"] == "pass" else 1))
            if case.get("export_standard"):
                expect = 0 if case["export_standard"] == "pass" else 1
                tests.append((f"case {fixture} export_standard {case['export_standard']}", ["__EXPORT_STANDARD__", path], expect))
            if case.get("export_absent") or case.get("export_present"):
                tests.append((f"case {fixture} export assertions", ["__EXPORT_ASSERT__", path, json.dumps(case, ensure_ascii=False)], 0))


def add_static_suite_tests(py: str, tests: list[tuple[str, list[str], int]]) -> None:
    for schema_file in sorted(SCHEMAS.glob("*.schema.json")):
        tests.append((f"schema self-check {schema_file.name}", ["__SCHEMA_CHECK__", str(schema_file)], 0))
    for prompt_file in sorted(BEHAVIORAL.glob("*.json")):
        tests.append((f"behavioral guardrail file {prompt_file.name}", ["__BEHAVIORAL_CHECK__", str(prompt_file)], 0))
    for integration_file in sorted(INTEGRATION.glob("*.json")):
        tests.append((f"integration expectation file {integration_file.name}", ["__INTEGRATION_CHECK__", str(integration_file)], 0))
    for legacy_file in sorted(LEGACY_DERIVED.glob("*.json")):
        tests.append((f"legacy anti-pattern file {legacy_file.name}", ["__LEGACY_CHECK__", str(legacy_file)], 0))


def static_check(kind: str, path: str) -> dict[str, object]:
    p = Path(path)
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
        if kind == "__SCHEMA_CHECK__":
            import jsonschema  # type: ignore
            jsonschema.Draft202012Validator.check_schema(payload)
        elif kind == "__BEHAVIORAL_CHECK__":
            if not isinstance(payload, list) or not payload:
                raise AssertionError("behavioral guardrail prompts must be a non-empty list")
            for idx, item in enumerate(payload):
                if not item.get("prompt") or not item.get("must_not") or not item.get("expected"):
                    raise AssertionError(f"behavioral prompt {idx} lacks prompt/must_not/expected")
        elif kind == "__INTEGRATION_CHECK__":
            required = {"initial", "standard", "full"}
            if set(payload) != required:
                raise AssertionError(f"integration expectations must define {sorted(required)}")
            for mode, sheets in payload.items():
                if not isinstance(sheets, list) or not sheets:
                    raise AssertionError(f"{mode} sheet expectation must be non-empty")
        elif kind == "__LEGACY_CHECK__":
            if not isinstance(payload, list) or not payload:
                raise AssertionError("legacy anti-patterns must be a non-empty list")
            for idx, item in enumerate(payload):
                if "anti_pattern" not in item or "expected_use" not in item:
                    raise AssertionError(f"legacy anti-pattern {idx} lacks anti_pattern/expected_use")
        return {"cmd": [kind, path], "returncode": 0, "expected": 0, "ok": True, "output": "ok"}
    except Exception as exc:
        return {"cmd": [kind, path], "returncode": 1, "expected": 0, "ok": False, "output": str(exc)}


def main() -> int:
    py = sys.executable
    tests: list[tuple[str, list[str], int]] = [
        ("preflight runs", [py, str(SCRIPTS / "preflight_capabilities.py"), "--format", "json"], 0),
        ("advanced delivery gate regressions", [py, str(ROOT / "evals" / "advanced_gate_tests.py")], 0),
    ]
    add_case_tests(py, tests)
    add_static_suite_tests(py, tests)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tests.append(("normalize runs", [py, str(SCRIPTS / "normalize_entities.py"), str(FIXTURES / "pass_minimal_graph.json"), "--output", str(tmp_path / "normalized.json")], 0))
        for index, (name, cmd, expect) in enumerate(tests):
            if cmd and cmd[0] == "__EXPORT_STANDARD__":
                fixture_path = cmd[1]
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "standard", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_ASSERT__":
                result = run_export_assertions(py, cmd[1], tmp_path, index, json.loads(cmd[2]))
            elif cmd and cmd[0] == "__AUDIT_STATUS__":
                result = run_audit_status(py, cmd[1], cmd[2])
            elif cmd and cmd[0].startswith("__") and cmd[0].endswith("_CHECK__"):
                result = static_check(cmd[0], cmd[1])
            else:
                result = run(cmd, expect)
            result["name"] = name
            results.append(result)
    passed = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]
    summary = {"passed": passed, "failed": len(failed), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
