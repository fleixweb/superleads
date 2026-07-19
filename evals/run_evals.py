#!/usr/bin/env python3
"""Run Superleads default-discovery, deep-research, or complete eval suites."""
from __future__ import annotations

import argparse
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
MINIMAL_DISCOVERY_SKELETON = ROOT / "shared" / "references" / "default-discovery-minimal-skeleton.example.json"
REFERENCE_SAMPLE = ROOT / "shared" / "references" / "default-discovery-reference.example.json"
CAPABILITY_CASES = ROOT / "evals" / "cases" / "capability_adapter_cases.json"
MODE_TO_STATUS = {
    "initial": "initial_lead_list",
    "standard": "standard_development_list",
    "full": "full_review_package",
    "inquiry": "inquiry_followup_queue",
}
SUITES = ("default", "deep", "all")

MINIMUM_GATE_CASES = CASES / "minimum_gate_cases.json"
DEFAULT_CONTACT_SAFETY_FIXTURES = {
    "fail_guessed_contact_ready.json",
    "fail_contact_literal_not_in_observation.json",
    "fail_email_verify_as_contact_source.json",
    "fail_same_page_contact_misattribution.json",
    "fail_contact_user_status_bypass.json",
    "fail_fabricated_person_title.json",
    "fail_multi_email_normalized.json",
    "fail_phone_suffix_truncation.json",
    "fail_nonready_entity_mismatch.json",
}
PURE_DEEP_FIXTURES = {
    "fail_independent_without_attestation.json",
    "fail_attestation_subject_hash_stale.json",
    "fail_manifest_review_provenance_mismatch.json",
    "fail_positive_assessment_no_evidence.json",
}


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
    sheet_text: dict[str, str] = {}
    for item in sorted(out_dir.glob("*.csv")):
        content = item.read_text(encoding="utf-8-sig")
        haystack += item.name + "\n" + content + "\n"
        sheet_text[item.stem] = content
    if manifest_path.exists():
        haystack += manifest_path.read_text(encoding="utf-8")
    missing = [needle for needle in case.get("export_absent", []) if str(needle) in haystack]
    present_missing = [needle for needle in case.get("export_present", []) if str(needle) not in haystack]
    sheet_present_failures: list[str] = []
    for sheet, needles in case.get("export_sheet_present", {}).items() if isinstance(case.get("export_sheet_present"), dict) else []:
        content = sheet_text.get(str(sheet), "")
        for needle in needles if isinstance(needles, list) else []:
            if str(needle) not in content:
                sheet_present_failures.append(f"{sheet}:{needle}")
    sheet_absent_failures: list[str] = []
    for sheet, needles in case.get("export_sheet_absent", {}).items() if isinstance(case.get("export_sheet_absent"), dict) else []:
        content = sheet_text.get(str(sheet), "")
        for needle in needles if isinstance(needles, list) else []:
            if str(needle) in content:
                sheet_absent_failures.append(f"{sheet}:{needle}")
    ok = not missing and not present_missing and not sheet_present_failures and not sheet_absent_failures
    result["ok"] = ok
    result["export_absent_failures"] = missing
    result["export_present_failures"] = present_missing
    result["export_sheet_present_failures"] = sheet_present_failures
    result["export_sheet_absent_failures"] = sheet_absent_failures
    if not ok:
        result["returncode"] = 1
        result["output"] += f"\nexport assertion failed absent={missing} present_missing={present_missing} sheet_present={sheet_present_failures} sheet_absent={sheet_absent_failures}"
    return result


def run_audit_status(py: str, fixture_path: str, expected_status: str, expected_returncode: int, tmp_path: Path, index: int, requested_status: str | None = None) -> dict[str, object]:
    fixture_path = materialize_fixture(fixture_path, tmp_path, index)
    cmd = [py, str(SCRIPTS / "audit_delivery.py"), fixture_path, "--format", "json"]
    if requested_status:
        cmd.extend(["--delivery-status", requested_status])
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
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


def run_preflight_assertion(py: str, input_path: str, case: dict[str, object]) -> dict[str, object]:
    proc = subprocess.run(
        [py, str(SCRIPTS / "preflight_capabilities.py"), "--input", input_path, "--format", "json"],
        cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    expected_returncode = int(case.get("returncode", 0))
    actual: dict[str, object] | None = None
    try:
        parsed = json.loads(proc.stdout)
        actual = parsed if isinstance(parsed, dict) else None
    except Exception:
        actual = None
    expected_capabilities = case.get("expected_capabilities", {})
    missing: list[str] = []
    for capability, expected_status in expected_capabilities.items() if isinstance(expected_capabilities, dict) else []:
        current = actual.get("capabilities", {}).get(capability, {}).get("status") if isinstance(actual, dict) and isinstance(actual.get("capabilities"), dict) else None
        if current != expected_status:
            missing.append(f"{capability}={expected_status} (got {current})")
    expected_max = case.get("expected_max_output")
    if expected_max and (not isinstance(actual, dict) or actual.get("max_output_without_manual_sources") != expected_max):
        missing.append(f"max_output_without_manual_sources={expected_max}")
    for code in case.get("expected_adapter_codes", []) if isinstance(case.get("expected_adapter_codes"), list) else []:
        adapter_issues = actual.get("adapter_report", {}).get("issues", []) if isinstance(actual, dict) and isinstance(actual.get("adapter_report"), dict) else []
        if not any(isinstance(item, dict) and item.get("code") == code for item in adapter_issues):
            missing.append(f"adapter code {code}")
    if "expected_adapter_valid" in case:
        actual_valid = actual.get("adapter_report", {}).get("valid") if isinstance(actual, dict) and isinstance(actual.get("adapter_report"), dict) else None
        if actual_valid is not case.get("expected_adapter_valid"):
            missing.append(f"adapter valid={case.get('expected_adapter_valid')} (got {actual_valid})")
    ok = proc.returncode == expected_returncode and actual is not None and not missing
    return {
        "cmd": [py, str(SCRIPTS / "preflight_capabilities.py"), "--input", input_path, "--format", "json"],
        "returncode": proc.returncode if ok else 1,
        "expected": expected_returncode,
        "ok": ok,
        "output": proc.stdout if not missing else proc.stdout + "\nmissing preflight assertions: " + ", ".join(missing),
    }


def add_capability_adapter_tests(tests: list[tuple[str, list[str], int, list[str]]]) -> None:
    if not CAPABILITY_CASES.exists():
        return
    payload = json.loads(CAPABILITY_CASES.read_text(encoding="utf-8"))
    for case in payload.get("cases", []):
        if not isinstance(case, dict) or not isinstance(case.get("input"), str):
            continue
        tests.append((
            f"capability adapter {case.get('name', case['input'])}",
            ["__PREFLIGHT_ASSERT__", str(ROOT / case["input"]), json.dumps(case, ensure_ascii=False)],
            int(case.get("returncode", 0)),
            [],
        ))


def _minimum_gate_suite_membership(payload: dict[str, object]) -> dict[str, set[str]]:
    """Load and fail closed on the explicit suite map for minimum-gate cases."""
    raw_membership = payload.get("suite_membership")
    cases = payload.get("cases")
    if not isinstance(raw_membership, dict) or not isinstance(cases, list):
        raise ValueError("minimum_gate_cases.json requires suite_membership and cases")
    membership: dict[str, set[str]] = {}
    for suite in ("default", "deep"):
        fixtures = raw_membership.get(suite)
        if not isinstance(fixtures, list) or not all(isinstance(item, str) for item in fixtures):
            raise ValueError(f"minimum_gate_cases.json suite_membership.{suite} must be a fixture list")
        for fixture in fixtures:
            membership.setdefault(fixture, set()).add(suite)
    case_fixtures = {case.get("fixture") for case in cases if isinstance(case, dict) and isinstance(case.get("fixture"), str)}
    missing = sorted(case_fixtures - set(membership))
    unknown = sorted(set(membership) - case_fixtures)
    if missing or unknown:
        raise ValueError(f"minimum_gate_cases.json suite_membership mismatch: missing={missing}, unknown={unknown}")
    return membership


def _case_suites(case: dict[str, object], membership: dict[str, set[str]] | None) -> set[str]:
    """Use explicit case labels/map; unlabeled non-minimum legacy cases stay deep."""
    raw_suites = case.get("suites")
    if isinstance(raw_suites, list) and all(isinstance(item, str) for item in raw_suites):
        suites = set(raw_suites)
    else:
        fixture = case.get("fixture")
        suites = membership.get(fixture, set()) if isinstance(fixture, str) and membership is not None else set()
    if not suites:
        # Compatibility is deliberately conservative: new non-minimum cases
        # are deep until their owner assigns a default label. Minimum-gate
        # cases cannot use this fallback because their map is exhaustively
        # checked above.
        return {"deep"}
    if not suites.issubset({"default", "deep"}):
        raise ValueError(f"unsupported case suite labels: {sorted(suites)}")
    return suites


def _case_belongs_to_suite(case: dict[str, object], suite: str, membership: dict[str, set[str]] | None) -> bool:
    if suite == "all":
        return True
    return suite in _case_suites(case, membership)


def _planned_fixture_names(tests: list[tuple[str, list[str], int, list[str]]]) -> set[str]:
    """Read fixture identities from structured command arguments, not display text."""
    fixture_names: set[str] = set()
    for _, command, _, _ in tests:
        for argument in command:
            if isinstance(argument, str):
                path = Path(argument)
                if path.parent == FIXTURES and path.suffix == ".json":
                    fixture_names.add(path.name)
    return fixture_names


def _suite_membership_check(suite: str, selected_fixture_names: set[str]) -> dict[str, object]:
    """Programmatically prove the explicit map matches the selected test plan."""
    payload = json.loads(MINIMUM_GATE_CASES.read_text(encoding="utf-8"))
    membership = _minimum_gate_suite_membership(payload)
    selected_default = {fixture for fixture, suites in membership.items() if "default" in suites}
    missing_contacts = sorted(DEFAULT_CONTACT_SAFETY_FIXTURES - selected_default)
    pure_deep_selected = sorted(PURE_DEEP_FIXTURES & selected_default)
    missing_contact_tests = sorted(
        fixture for fixture in DEFAULT_CONTACT_SAFETY_FIXTURES
        if fixture not in selected_fixture_names
    ) if suite == "default" else []
    selected_pure_deep_tests = sorted(
        fixture for fixture in PURE_DEEP_FIXTURES
        if fixture in selected_fixture_names
    ) if suite == "default" else []
    problems = []
    if missing_contacts:
        problems.append(f"default contact fixtures missing: {missing_contacts}")
    if pure_deep_selected:
        problems.append(f"pure deep fixtures selected by default: {pure_deep_selected}")
    if missing_contact_tests:
        problems.append(f"default test plan missing contact fixtures: {missing_contact_tests}")
    if selected_pure_deep_tests:
        problems.append(f"default test plan includes pure deep fixtures: {selected_pure_deep_tests}")
    return {
        "cmd": ["__SUITE_MEMBERSHIP_CHECK__", suite],
        "returncode": 0 if not problems else 1,
        "expected": 0,
        "ok": not problems,
        "output": "suite membership passed" if not problems else "; ".join(problems),
        "default_contact_fixture_count": len(DEFAULT_CONTACT_SAFETY_FIXTURES & selected_default),
        "default_pure_deep_fixture_count": len(PURE_DEEP_FIXTURES & selected_default),
        "selected_default_contact_fixture_count": len(DEFAULT_CONTACT_SAFETY_FIXTURES) - len(missing_contact_tests),
        "selected_default_pure_deep_fixture_count": len(selected_pure_deep_tests),
    }


def add_case_tests(py: str, tests: list[tuple[str, list[str], int, list[str]]], suite: str) -> None:
    for case_file in sorted(CASES.glob("*.json")):
        payload = json.loads(case_file.read_text(encoding="utf-8"))
        membership = _minimum_gate_suite_membership(payload) if case_file == MINIMUM_GATE_CASES else None
        for case in payload.get("cases", []):
            if not isinstance(case, dict):
                continue
            fixture = case.get("fixture")
            if not isinstance(fixture, str) or not _case_belongs_to_suite(case, suite, membership):
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
            if suite != "default" and case.get("audit_standard"):
                codes = list(case.get("standard_error_codes", case.get("expected_error_codes", [])))
                tests.append((f"case {fixture} audit_standard {case['audit_standard']}", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", "standard_development_list"], 0 if case["audit_standard"] == "pass" else 1, codes))
            if suite != "default" and case.get("export_standard"):
                expect = 0 if case["export_standard"] == "pass" else 1
                codes = list(case.get("standard_error_codes", case.get("expected_error_codes", [])))
                tests.append((f"case {fixture} export_standard {case['export_standard']}", ["__EXPORT_STANDARD__", path], expect, codes))
            if case.get("export_initial"):
                expect = 0 if case["export_initial"] == "pass" else 1
                tests.append((f"case {fixture} export_initial {case['export_initial']}", ["__EXPORT_INITIAL__", path], expect, list(case.get("expected_error_codes", []))))
            if suite != "default" and case.get("audit_inquiry"):
                expect = 0 if case["audit_inquiry"] == "pass" else 1
                tests.append((f"case {fixture} audit_inquiry {case['audit_inquiry']}", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", "inquiry_followup_queue"], expect, list(case.get("expected_error_codes", []))))
            if suite != "default" and case.get("export_inquiry"):
                expect = 0 if case["export_inquiry"] == "pass" else 1
                tests.append((f"case {fixture} export_inquiry {case['export_inquiry']}", ["__EXPORT_INQUIRY__", path], expect, list(case.get("expected_error_codes", []))))
            if case.get("export_absent") or case.get("export_present") or case.get("export_sheet_present") or case.get("export_sheet_absent"):
                tests.append((f"case {fixture} export assertions", ["__EXPORT_ASSERT__", path, json.dumps(case, ensure_ascii=False)], 0, []))


def add_phase2_tests(py: str, tests: list[tuple[str, list[str], int, list[str]]]) -> None:
    """Exercise each Phase 2 fixture through validate, standard audit, and export."""
    cases = [
        ("fail_independent_without_attestation.json", ["independent_review_attestation_missing"], "standard"),
        ("fail_attestation_subject_hash_stale.json", ["review_attestation_subject_hash_mismatch"], "standard"),
        ("fail_attestation_same_actor_session.json", ["review_attestation_reviewer_actor_not_independent"], "standard"),
        ("fail_attestation_binding_mismatch.json", ["independent_review_attestation_missing"], "standard"),
        ("fail_attestation_assessment_coverage.json", ["review_attestation_assessment_coverage_missing"], "standard"),
        ("fail_manifest_review_provenance_mismatch.json", ["audit_review_attestation_mismatch"], "standard"),
        ("fail_searchlog_missing_required.json", ["search_log_query_missing"], "standard"),
        ("fail_searchlog_duplicate_id.json", ["duplicate_global_id"], "standard"),
        ("fail_searchlog_wrong_run.json", ["search_log_reference_missing"], "standard"),
        ("fail_searchlog_unauthorized_tool.json", ["search_log_concrete_tool_invalid"], "standard"),
        ("fail_searchweb_candidate_without_log.json", ["search_web_candidate_without_search_log"], "standard"),
        ("fail_geography_nonlocation_claim.json", ["geography_rule_support_not_formal_location"], "standard"),
        ("fail_geography_rule_nonlocation_support.json", ["geography_rule_support_not_formal_location"], "standard"),
        ("fail_target_country_without_geography_contract.json", ["geography_contract_required_for_target"], "standard"),
        ("fail_target_country_array_without_geography_contract.json", ["geography_contract_required_for_target"], "standard"),
    ]
    for fixture, codes, mode in cases:
        path = str(FIXTURES / fixture)
        tests.extend([
            (f"phase2 {fixture} validate fail", [py, str(SCRIPTS / "validate_research_graph.py"), path], 1, codes),
            (f"phase2 {fixture} audit {mode} fail", [py, str(SCRIPTS / "audit_delivery.py"), path, "--delivery-status", MODE_TO_STATUS[mode]], 1, codes),
            (f"phase2 {fixture} export {mode} fail", ["__EXPORT_FULL__" if mode == "full" else "__EXPORT_STANDARD__", path], 1, codes),
        ])
    declared_path = str(FIXTURES / "fail_declared_separate_session_full.json")
    tests.extend([
        ("phase2 fail_declared_separate_session_full.json validate pass", [py, str(SCRIPTS / "validate_research_graph.py"), declared_path], 0, []),
        ("phase2 fail_declared_separate_session_full.json audit full fail", [py, str(SCRIPTS / "audit_delivery.py"), declared_path, "--delivery-status", "full_review_package"], 1, ["full_review_unavailable_in_local_deployment"]),
        ("phase2 fail_declared_separate_session_full.json export full fail", ["__EXPORT_FULL__", declared_path], 1, ["full_review_unavailable_in_local_deployment"]),
    ])
    for fixture, mode, audit_status, export_present, export_absent in (
        ("pass_geography_searchlog_standard.json", "standard", "standard_development_list", ["本次复核由独立会话声明完成，未获得平台身份验证。"], ["Region Q official address", "fixture_search", "executor_run_001", "review_session_run_001"]),
        ("pass_global_target_without_geography_contract.json", "standard", "standard_development_list", ["本次复核由独立会话声明完成，未获得平台身份验证。"], []),
    ):
        path = str(FIXTURES / fixture)
        tests.extend([
            (f"phase2 {fixture} validate pass", [py, str(SCRIPTS / "validate_research_graph.py"), path], 0, []),
            (f"phase2 {fixture} audit {mode} pass", ["__AUDIT_STATUS__", path, audit_status, "0", audit_status], 0, []),
            (f"phase2 {fixture} export assertions", ["__EXPORT_ASSERT__", path, json.dumps({"export_assert_mode": mode, "export_present": export_present, "export_absent": export_absent}, ensure_ascii=False)], 0, []),
        ])


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


def _add_default_reference_tests(py: str, tests: list[tuple[str, list[str], int, list[str]]]) -> None:
    # Both shared runtime references are tested from their real locations:
    # the minimal skeleton for bulk default discovery and the complete
    # reference for status/contact/conflict boundaries.
    tests.extend([
        ("minimal discovery skeleton validate pass", [py, str(SCRIPTS / "validate_research_graph.py"), str(MINIMAL_DISCOVERY_SKELETON)], 0, []),
        ("minimal discovery skeleton audit initial pass", [py, str(SCRIPTS / "audit_delivery.py"), str(MINIMAL_DISCOVERY_SKELETON), "--delivery-status", "initial_lead_list"], 0, []),
        ("minimal discovery skeleton export initial pass", ["__EXPORT_INITIAL__", str(MINIMAL_DISCOVERY_SKELETON)], 0, []),
        ("complete discovery reference validate pass", [py, str(SCRIPTS / "validate_research_graph.py"), str(REFERENCE_SAMPLE)], 0, []),
        ("complete discovery reference audit initial pass", [py, str(SCRIPTS / "audit_delivery.py"), str(REFERENCE_SAMPLE), "--delivery-status", "initial_lead_list"], 0, []),
        ("complete discovery reference export initial pass", ["__EXPORT_INITIAL__", str(REFERENCE_SAMPLE)], 0, []),
    ])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        choices=SUITES,
        default="all",
        help="default: discovery-only checks; deep: strict research checks; all: complete compatible suite (default).",
    )
    return parser.parse_args()


def main() -> int:
    suite = parse_args().suite
    py = sys.executable
    tests: list[tuple[str, list[str], int, list[str]]] = [
        ("preflight runs", [py, str(SCRIPTS / "preflight_capabilities.py"), "--format", "json"], 0, []),
        (f"advanced {suite} gate regressions", [py, str(ROOT / "evals" / "advanced_gate_tests.py"), "--suite", suite], 0, []),
    ]
    if suite in {"default", "all"}:
        _add_default_reference_tests(py, tests)
    add_case_tests(py, tests, suite)
    if suite in {"deep", "all"}:
        add_phase2_tests(py, tests)
        add_capability_adapter_tests(tests)
    add_static_suite_tests(py, tests)
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if suite in {"deep", "all"}:
            tests.append(("normalize validate audit export chain", ["__NORMALIZE_CHAIN__", str(FIXTURES / "pass_minimal_graph.json")], 0, []))
        planned_fixture_names = sorted(_planned_fixture_names(tests))
        tests.insert(1, (
            f"{suite} suite membership metadata",
            ["__SUITE_MEMBERSHIP_CHECK__", suite, json.dumps(planned_fixture_names, ensure_ascii=False)],
            0,
            [],
        ))
        for index, (name, cmd, expect, expected_codes) in enumerate(tests):
            if cmd and cmd[0] == "__EXPORT_STANDARD__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "standard", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_INITIAL__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "initial", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
                result = run(cmd, expect)
            elif cmd and cmd[0] == "__EXPORT_FULL__":
                fixture_path = materialize_fixture(cmd[1], tmp_path, index)
                cmd = [py, str(SCRIPTS / "export_workbook.py"), fixture_path, "--output-dir", str(tmp_path / f"export_{index}"), "--mode", "full", "--format", "csv", "--manifest", str(tmp_path / f"manifest_{index}.json")]
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
            elif cmd and cmd[0] == "__PREFLIGHT_ASSERT__":
                result = run_preflight_assertion(py, cmd[1], json.loads(cmd[2]))
            elif cmd and cmd[0] == "__SUITE_MEMBERSHIP_CHECK__":
                result = _suite_membership_check(cmd[1], set(json.loads(cmd[2])))
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
    summary = {"suite": suite, "total": len(results), "passed": passed, "failed": len(failed), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
