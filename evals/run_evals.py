#!/usr/bin/env python3
"""Run minimal Superleads eval suite."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from copy import deepcopy
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


def _decode_pointer_token(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _patch_parent(document: object, pointer: str) -> tuple[object, str]:
    if not pointer.startswith("/"):
        raise ValueError(f"patch path must be a JSON Pointer: {pointer}")
    tokens = [_decode_pointer_token(token) for token in pointer[1:].split("/")]
    if not tokens:
        raise ValueError("patch path must target a value")
    current = document
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]  # type: ignore[index]
    return current, tokens[-1]


def _apply_fixture_patches(graph: dict[str, object], patches: object) -> dict[str, object]:
    if not isinstance(patches, list):
        raise ValueError("fixture patches must be a list")
    result = deepcopy(graph)
    for patch in patches:
        if not isinstance(patch, dict):
            raise ValueError("fixture patch must be an object")
        parent, token = _patch_parent(result, str(patch.get("path", "")))
        operation = patch.get("op")
        if operation == "remove":
            if isinstance(parent, list):
                del parent[int(token)]
            elif isinstance(parent, dict):
                del parent[token]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "replace":
            if "value" not in patch:
                raise ValueError("replace patch lacks value")
            if isinstance(parent, list):
                parent[int(token)] = patch["value"]
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "add":
            if "value" not in patch:
                raise ValueError("add patch lacks value")
            if isinstance(parent, list):
                parent.insert(int(token), patch["value"])
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "append":
            if not isinstance(parent, list) or token != "-" or "value" not in patch:
                raise ValueError("append patch must target /-")
            parent.append(patch["value"])
        else:
            raise ValueError(f"unsupported fixture patch operation: {operation}")
    return result


def _load_fixture_graph(path: Path, seen: set[Path] | None = None) -> dict[str, object]:
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        raise ValueError(f"fixture inheritance cycle: {path.name}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "extends" not in payload:
        if not isinstance(payload, dict):
            raise ValueError(f"fixture must be a JSON object: {path.name}")
        return payload
    base_name = payload.get("extends")
    if not isinstance(base_name, str) or Path(base_name).name != base_name:
        raise ValueError(f"fixture base must be a local filename: {path.name}")
    base = _load_fixture_graph(path.parent / base_name, seen | {path})
    return _apply_fixture_patches(base, payload.get("patches"))


def materialize_fixture(path: str, tmp_path: Path, index: int) -> str:
    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception:
        return path
    if not isinstance(payload, dict) or "extends" not in payload:
        return path
    graph = _load_fixture_graph(fixture_path)
    target = tmp_path / f"fixture_{index}_{fixture_path.name}"
    target.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(target)


def assert_expected_error_codes(result: dict[str, object], expected_codes: list[str]) -> dict[str, object]:
    if not expected_codes:
        return result
    output = str(result.get("output", ""))
    missing = [code for code in expected_codes if code not in output]
    result["expected_error_codes"] = expected_codes
    result["missing_error_codes"] = missing
    if missing:
        result["ok"] = False
        result["returncode"] = 1
        result["output"] = output + f"\nmissing expected error codes: {', '.join(missing)}"
    return result


def run_export_assertions(py: str, fixture_path: str, tmp_path: Path, index: int, case: dict[str, object]) -> dict[str, object]:
    fixture_path = materialize_fixture(fixture_path, tmp_path, index)
    out_dir = tmp_path / f"export_assert_{index}"
    manifest_path = out_dir / "manifest.json"
    mode = str(case.get("export_assert_mode", "standard"))
    cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(out_dir), "--mode", mode, "--format", "csv", "--manifest", str(manifest_path)]
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


def run_audit_status(py: str, fixture_path: str, expected_status: str, expected_returncode: int, tmp_path: Path, index: int, requested_status: str | None = None) -> dict[str, object]:
    fixture_path = materialize_fixture(fixture_path, tmp_path, index)
    cmd = [py, str(SCRIPTS / "audit_delivery.py"), fixture_path, "--format", "json"]
    if requested_status:
        cmd.extend(["--delivery-status", requested_status])
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    ok = False
    actual_status = None
    try:
        payload = json.loads(proc.stdout)
        actual_status = payload.get("delivery_status")
        ok = proc.returncode == expected_returncode and actual_status == expected_status
    except Exception:
        ok = False
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "expected": expected_returncode,
        "expected_delivery_status": expected_status,
        "actual_delivery_status": actual_status,
        "ok": ok,
        "output": proc.stdout,
    }


def run_normalize_chain(py: str, fixture_path: str, tmp_path: Path, index: int) -> dict[str, object]:
    graph_path = materialize_fixture(fixture_path, tmp_path, index)
    output = tmp_path / f"normalized_{index}.json"
    report = tmp_path / f"identity_report_{index}.json"
    normalize = run([py, str(SCRIPTS / "normalize_entities.py"), graph_path, "--output", str(output), "--identity-report", str(report)], 0)
    outputs = [normalize["output"]]
    if not normalize["ok"] or not output.exists() or not report.exists():
        return {"cmd": normalize["cmd"], "returncode": 1, "expected": 0, "ok": False, "output": "\n".join(str(item) for item in outputs)}
    validate = run([py, str(SCRIPTS / "validate_research_graph.py"), str(output)], 0)
    audit = run([py, str(SCRIPTS / "audit_delivery.py"), str(output), "--delivery-status", "standard_development_list"], 0)
    export = run([py, str(SCRIPTS / "export_workbook.py"), str(output), "--output-dir", str(tmp_path / f"normalized_export_{index}"), "--mode", "standard", "--format", "csv"], 0)
    outputs.extend([validate["output"], audit["output"], export["output"]])
    ok = all(result["ok"] for result in (normalize, validate, audit, export))
    return {
        "cmd": ["normalize -> validate -> audit -> export", graph_path],
        "returncode": 0 if ok else 1,
        "expected": 0,
        "ok": ok,
        "output": "\n".join(str(item) for item in outputs),
    }


def add_case_tests(py: str, tests: list[tuple[str, list[str], int, list[str]]]) -> None:
    for case_file in sorted(CASES.glob("*.json")):
        payload = json.loads(case_file.read_text(encoding="utf-8"))
        for case in payload.get("cases", []):
            fixture = case.get("fixture")
            if not fixture:
                continue
            path = str(FIXTURES / fixture)
            if case.get("validate"):
                tests.append((f"case {fixture} validate {case['validate']}", [py, str(SCRIPTS / "validate_research_graph.py"), path], 0 if case["validate"] == "pass" else 1, list(case.get("expected_error_codes", []))))
            if case.get("audit"):
                tests.append((f"case {fixture} audit {case['audit']}", [py, str(SCRIPTS / "audit_delivery.py"), path], 0 if case["audit"] == "pass" else 1, list(case.get("expected_error_codes", []))))
            if case.get("audit_delivery_status"):
                expected_returncode = int(case.get("audit_delivery_returncode", 0))
                requested = str(case.get("audit_requested_status", ""))
                tests.append((f"case {fixture} audit_delivery_status {case['audit_delivery_status']}", ["__AUDIT_STATUS__", path, case["audit_delivery_status"], str(expected_returncode), requested], expected_returncode, list(case.get("expected_error_codes", []))))
            if case.get("audit_standard"):
                codes = list(case.get("standard_error_codes", case.get("expected_error_codes", [])))
                tests.append((f"case {fixture} audit_standard {case['audit_standard']}", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", "standard_development_list"], 0 if case["audit_standard"] == "pass" else 1, codes))
            if case.get("export_standard"):
                expect = 0 if case["export_standard"] == "pass" else 1
                codes = list(case.get("standard_error_codes", case.get("expected_error_codes", [])))
                tests.append((f"case {fixture} export_standard {case['export_standard']}", ["__EXPORT_STANDARD__", path], expect, codes))
            if case.get("export_initial"):
                expect = 0 if case["export_initial"] == "pass" else 1
                tests.append((f"case {fixture} export_initial {case['export_initial']}", ["__EXPORT_INITIAL__", path], expect, list(case.get("expected_error_codes", []))))
            if case.get("audit_inquiry"):
                expect = 0 if case["audit_inquiry"] == "pass" else 1
                tests.append((f"case {fixture} audit_inquiry {case['audit_inquiry']}", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", "inquiry_followup_queue"], expect, list(case.get("expected_error_codes", []))))
            if case.get("export_inquiry"):
                expect = 0 if case["export_inquiry"] == "pass" else 1
                tests.append((f"case {fixture} export_inquiry {case['export_inquiry']}", ["__EXPORT_INQUIRY__", path], expect, list(case.get("expected_error_codes", []))))
            if case.get("export_absent") or case.get("export_present"):
                tests.append((f"case {fixture} export assertions", ["__EXPORT_ASSERT__", path, json.dumps(case, ensure_ascii=False)], 0, []))


def add_static_suite_tests(py: str, tests: list[tuple[str, list[str], int, list[str]]]) -> None:
    for schema_file in sorted(SCHEMAS.glob("*.schema.json")):
        tests.append((f"schema self-check {schema_file.name}", ["__SCHEMA_CHECK__", str(schema_file)], 0, []))
    for prompt_file in sorted(BEHAVIORAL.glob("*.json")):
        tests.append((f"behavioral guardrail file {prompt_file.name}", ["__BEHAVIORAL_CHECK__", str(prompt_file)], 0, []))
    for integration_file in sorted(INTEGRATION.glob("*.json")):
        tests.append((f"integration expectation file {integration_file.name}", ["__INTEGRATION_CHECK__", str(integration_file)], 0, []))
    for legacy_file in sorted(LEGACY_DERIVED.glob("*.json")):
        tests.append((f"legacy anti-pattern file {legacy_file.name}", ["__LEGACY_CHECK__", str(legacy_file)], 0, []))


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
            required = {"initial", "standard", "full", "inquiry"}
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
    tests: list[tuple[str, list[str], int, list[str]]] = [
        ("preflight runs", [py, str(SCRIPTS / "preflight_capabilities.py"), "--format", "json"], 0, []),
        ("advanced delivery gate regressions", [py, str(ROOT / "evals" / "advanced_gate_tests.py")], 0, []),
    ]
    add_case_tests(py, tests)
    add_static_suite_tests(py, tests)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        tests.append(("normalize validate audit export chain", ["__NORMALIZE_CHAIN__", str(FIXTURES / "pass_minimal_graph.json")], 0, []))
        for index, (name, cmd, expect, expected_codes) in enumerate(tests):
            if cmd and cmd[0] == "__EXPORT_STANDARD__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "standard", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_INITIAL__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "initial", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_INQUIRY__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "inquiry", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_ASSERT__":
                result = run_export_assertions(py, cmd[1], tmp_path, index, json.loads(cmd[2]))
            elif cmd and cmd[0] == "__AUDIT_STATUS__":
                result = run_audit_status(py, cmd[1], cmd[2], int(cmd[3]), tmp_path, index, cmd[4] or None)
            elif cmd and cmd[0] == "__NORMALIZE_CHAIN__":
                result = run_normalize_chain(py, cmd[1], tmp_path, index)
            elif cmd and cmd[0].startswith("__") and cmd[0].endswith("_CHECK__"):
                result = static_check(cmd[0], cmd[1])
            else:
                cmd = [materialize_fixture(part, tmp_path, index) if part.endswith(".json") and Path(part).parent == FIXTURES else part for part in cmd]
                result = run(cmd, expect)
            result = assert_expected_error_codes(result, expected_codes)
            result["name"] = name
            results.append(result)
    passed = sum(1 for r in results if r["ok"])
    failed = [r for r in results if not r["ok"]]
    summary = {"passed": passed, "failed": len(failed), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
