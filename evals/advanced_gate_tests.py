#!/usr/bin/env python3
"""Regression tests for formal-delivery bypasses found in independent reviews."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
BASE_GRAPH = ROOT / "evals" / "fixtures" / "pass_minimal_graph.json"
USER_FILE_PDF = ROOT / "evals" / "fixtures" / "pass_user_provided_pdf_claim.json"
USER_FILE_SHEET = ROOT / "evals" / "fixtures" / "pass_user_provided_spreadsheet_contact.json"
DATASET_CONTACT = ROOT / "evals" / "fixtures" / "pass_user_business_dataset_contact_with_note.json"
CORRESPONDENCE_CONTACT = ROOT / "evals" / "fixtures" / "pass_correspondence_export_contact_with_note.json"
VISUAL_CANDIDATE = ROOT / "evals" / "fixtures" / "pass_visual_reference_candidate_only.json"
CONNECTED_INQUIRY = ROOT / "evals" / "fixtures" / "pass_connected_inbound_inquiry.json"
MAIL_ADAPTER_INPUT = ROOT / "evals" / "fixtures" / "mail_read_normalized_input.json"
sys.path.insert(0, str(SCRIPTS))
from _superleads_common import graph_hash, review_subject_hash  # noqa: E402
sys.path.insert(0, str(ROOT / "evals"))
from run_evals import _load_fixture_graph  # noqa: E402


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=environment)


def _write_graph(path: Path, graph: dict[str, Any]) -> None:
    path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")


def _formal_results(graph: dict[str, Any], directory: Path, name: str) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    graph_path = directory / f"{name}.json"
    export_dir = directory / name
    _write_graph(graph_path, graph)
    validate = _run([sys.executable, "-B", str(SCRIPTS / "validate_research_graph.py"), str(graph_path), "--format", "json"])
    audit = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(graph_path), "--delivery-status", "standard_development_list", "--format", "json"])
    export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(export_dir), "--mode", "standard", "--format", "csv", "--manifest", str(export_dir / "manifest.json")])
    return validate, audit, export


def _must_block(name: str, graph: dict[str, Any], directory: Path) -> list[str]:
    validate, audit, export = _formal_results(graph, directory, name)
    errors = []
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0:
            errors.append(f"{name}: {label} unexpectedly passed\n{result.stdout}")
    return errors


def _base() -> dict[str, Any]:
    return json.loads(BASE_GRAPH.read_text(encoding="utf-8"))


def _append_unassigned(graph: dict[str, Any]) -> None:
    graph["unassigned_contact_leads"].append({
        "unassigned_contact_lead_id": "unassigned_001",
        "contact_id": "contact_001",
        "reason": "requires manual sourcing",
        "suggested_manual_check": "Find a public source.",
    })


def _refresh_current_attestation(graph: dict[str, Any]) -> None:
    """Simulate a current independent review after a test-only data change."""
    attestations = graph.get("review_attestations")
    if not isinstance(attestations, list) or not attestations or not isinstance(attestations[0], dict):
        return
    subject_hash = review_subject_hash(graph)
    attestations[0]["input_graph_hash"] = subject_hash
    attestations[0]["reviewed_subject_hash"] = subject_hash


def _assert_self_review_disclosure(directory: Path) -> list[str]:
    graph = _base()
    graph["runs"][0]["review_mode"] = "self_review_fallback"
    validate, audit, export = _formal_results(graph, directory, "self_review_disclosure")
    errors = []
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"self_review_disclosure: expected formal export to pass\n{audit.stdout}\n{export.stdout}"]
    try:
        if not json.loads(audit.stdout).get("disclosure_required"):
            errors.append("self_review_disclosure: audit must require disclosure")
    except json.JSONDecodeError:
        errors.append("self_review_disclosure: audit did not return JSON")
    disclosure_sheet = (directory / "self_review_disclosure" / "风险与说明.csv").read_text(encoding="utf-8-sig")
    if "本次未运行独立复核，建议在使用前进行人工确认。" not in disclosure_sheet:
        errors.append("self_review_disclosure: workbook risk sheet lacks self_review_fallback disclosure")
    return errors


def _assert_phase2_provenance_and_searchlog(directory: Path) -> list[str]:
    """Directly pressure the new provenance and candidate-only search gates."""
    errors: list[str] = []
    geography = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
    validate, audit, export = _formal_results(geography, directory, "phase2_geography_control")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        errors.append(f"phase2_geography_control: expected validate/audit/export pass\n{validate.stdout}\n{audit.stdout}\n{export.stdout}")
    else:
        try:
            if not json.loads(audit.stdout).get("disclosure_required"):
                errors.append("phase2_geography_control: declared review must require audit disclosure")
        except json.JSONDecodeError:
            errors.append("phase2_geography_control: audit did not return JSON")
        payload = (directory / "phase2_geography_control" / "manifest.json").read_text(encoding="utf-8")
        csv_text = "\n".join(path.read_text(encoding="utf-8-sig") for path in (directory / "phase2_geography_control").glob("*.csv"))
        disclosure = "本次复核由独立会话声明完成，未获得平台身份验证。"
        if disclosure not in payload or disclosure not in csv_text:
            errors.append("phase2_geography_control: declared-review disclosure missing from manifest or risk sheet")
        for forbidden in ("Region Q official address", "fixture_search", "executor_run_001", "review_session_run_001"):
            if forbidden in payload or forbidden in csv_text:
                errors.append(f"phase2_geography_control: leaked internal search/session data {forbidden}")
        if "search_001" not in payload or "\"search_log_count\": 1" not in payload:
            errors.append("phase2_geography_control: manifest omitted internal SearchLog trace IDs/count")
        try:
            import openpyxl  # type: ignore
            xlsx_dir = directory / "phase2_geography_xlsx"
            xlsx = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(directory / "phase2_geography_control.json"), "--output-dir", str(xlsx_dir), "--mode", "standard", "--format", "xlsx"])
            if xlsx.returncode != 0:
                errors.append(f"phase2_geography_xlsx: export failed\n{xlsx.stdout}")
            else:
                workbook = openpyxl.load_workbook(xlsx_dir / "superleads_workbook.xlsx", read_only=True, data_only=True)
                cells = "\n".join(str(value) for sheet in workbook.worksheets for row in sheet.iter_rows(values_only=True) for value in row if value is not None)
                for forbidden in ("Region Q official address", "fixture_search", "executor_run_001", "review_session_run_001"):
                    if forbidden in cells:
                        errors.append(f"phase2_geography_xlsx: leaked internal search/session data {forbidden}")
        except ImportError:
            pass

    full = copy.deepcopy(geography)
    full["briefs"][0]["evidence_depth"] = "full_review"
    _refresh_current_attestation(full)
    graph_path = directory / "phase2_full_unavailable.json"
    _write_graph(graph_path, full)
    full_audit = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(graph_path), "--delivery-status", "full_review_package", "--format", "json"])
    full_export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(directory / "phase2_full_unavailable"), "--mode", "full", "--format", "csv"])
    full_code = "full_review_unavailable_in_local_deployment"
    if full_audit.returncode == 0 or full_export.returncode == 0 or full_code not in full_audit.stdout or full_code not in full_export.stdout:
        errors.append(f"phase2_full_unavailable: full delivery was not fail-closed\n{full_audit.stdout}\n{full_export.stdout}")

    declared = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
    declared["briefs"][0]["evidence_depth"] = "full_review"
    subject = review_subject_hash(declared)
    declared["review_attestations"][0]["input_graph_hash"] = subject
    declared["review_attestations"][0]["reviewed_subject_hash"] = subject
    graph_path = directory / "phase2_declared_full.json"
    _write_graph(graph_path, declared)
    declared_audit = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(graph_path), "--delivery-status", "full_review_package", "--format", "json"])
    declared_export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(directory / "phase2_declared_full"), "--mode", "full", "--format", "csv"])
    if declared_audit.returncode == 0 or declared_export.returncode == 0 or "full_review_unavailable_in_local_deployment" not in declared_audit.stdout:
        errors.append(f"phase2_declared_full: declared separate session bypassed full block\n{declared_audit.stdout}\n{declared_export.stdout}")

    proxy = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
    proxy["observations"][0]["raw_excerpt"] = "Example Buyer contact +61 2 5555 0101. English service page at example.au."
    proxy["claims"][0]["typed_value"] = {"text": "Region Q"}
    proxy["claim_evidence"][0]["claim_field_anchors"]["claim_type"] = "Example Buyer contact"
    proxy["claim_evidence"][0]["claim_field_anchors"]["typed_value"] = "Region Q"
    proxy["review_attestations"][0]["input_graph_hash"] = review_subject_hash(proxy)
    proxy["review_attestations"][0]["reviewed_subject_hash"] = review_subject_hash(proxy)
    proxy_path = directory / "phase2_geography_proxy.json"
    _write_graph(proxy_path, proxy)
    proxy_result = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(proxy_path), "--delivery-status", "standard_development_list", "--format", "json"])
    if proxy_result.returncode == 0 or "geography_rule_support_not_formal_location" not in proxy_result.stdout:
        errors.append(f"phase2_geography_proxy: proxy signal bypassed geography evidence\n{proxy_result.stdout}")
    return errors


def _assert_target_geography_contract_required(directory: Path) -> list[str]:
    """Independently recreate the missing-contract geography delivery bypass."""
    errors: list[str] = []
    attack = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
    brief = attack["briefs"][0]
    contract = brief["customer_selection_contract"]
    contract.pop("geography_contract")
    contract["selection_requirements"][0].update({
        "rule_id": "sel_product_001",
        "user_statement": "Include organizations whose public page says it sells sample product.",
        "evidence_needed": "A same-Entity public page states sample product.",
        "search_hints": ["sample product seller"],
        "allowed_claim_types": ["product_match"],
        "evidence_markers": ["sample product"],
    })
    plan = attack["plans"][0]
    plan["selection_requirement_ids"] = ["sel_product_001"]
    plan["positive_query_groups"] = ["product_fit"]
    plan.pop("geography_query_group_ids", None)
    plan["query_groups"][0].update({
        "group_id": "product_fit",
        "query_purpose": "Find public product evidence before formal assessment.",
        "targeting_rule_ids": ["sel_product_001"],
        "queries": ["sample product seller"],
    })
    attack["candidates"][0].update({"discovery_method": "other", "search_log_id": None})
    attack["search_logs"] = []
    attack["observations"][0]["raw_excerpt"] = "Example Buyer sells sample product. Example Buyer Contact: sales@example.com"
    attack["claims"][0].update({"claim_type": "product_match", "predicate": "sells", "typed_value": {"text": "sample product"}})
    attack["claim_evidence"][0]["claim_field_anchors"].update({
        "predicate": "sells",
        "claim_type": "Example Buyer sells sample product",
        "typed_value": "sample product",
    })
    evaluation = attack["scope_decisions"][0]["rule_evaluations"][0]
    evaluation["rule_id"] = "sel_product_001"
    evaluation["claim_classifications"][0].update({"matched_marker": "sample product", "reason": "The public source contains the product marker."})
    evaluation["reason"] = "The opened public source states sample product."
    attack["scope_decisions"][0]["decision_summary"] = "Opened public source supports the product rule."
    _refresh_current_attestation(attack)
    validate, audit, export = _formal_results(attack, directory, "target_geography_contract_missing")
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0 or "geography_contract_required_for_target" not in result.stdout:
            errors.append(f"target_geography_contract_missing: {label} did not fail closed\n{result.stdout}")

    global_graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_global_target_without_geography_contract.json")
    validate, audit, export = _formal_results(global_graph, directory, "global_target_without_geography_contract")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        errors.append(f"global_target_without_geography_contract: null target unexpectedly required geography contract\n{validate.stdout}\n{audit.stdout}\n{export.stdout}")
    return errors


def _assert_legacy_review_fields_rejected(directory: Path) -> list[str]:
    """Schema must reject retired review-field shapes without keeping fixtures."""
    errors: list[str] = []
    field_name = "host" + "_identity_attestation"
    provenance_value = "host" + "_verified"
    legacy_signature_field = "signature" + "_base64"
    for name, mutate in (
        ("legacy_run_field", lambda graph: graph["runs"][0].update({field_name: {legacy_signature_field: "x"}})),
        ("legacy_attestation_value", lambda graph: graph["review_attestations"][0].update({"provenance_level": provenance_value})),
    ):
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
        mutate(graph)
        validate, audit, export = _formal_results(graph, directory, name)
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or "schema_validation_failed" not in result.stdout:
                errors.append(f"{name}: {label} did not schema-block retired review data\n{result.stdout}")

    for name, collection in (("legacy_audit_value", "audits"), ("legacy_manifest_value", "delivery_manifests")):
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
        graph[collection].append({"review_provenance_level": provenance_value})
        validate, audit, export = _formal_results(graph, directory, name)
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or "schema_validation_failed" not in result.stdout:
                errors.append(f"{name}: {label} did not schema-block retired provenance\n{result.stdout}")
    return errors


def _assert_review_attestation_coverage_and_disclosures(directory: Path) -> list[str]:
    """Exercise independent-session, Entity coverage, and stored disclosure gates."""
    errors: list[str] = []
    base = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json")
    variants = (
        (
            "attestation_same_session_only",
            lambda graph: graph["review_attestations"][0].update({"reviewer_session_id": graph["runs"][0]["execution_session_id"]}),
            "review_attestation_reviewer_session_not_independent",
        ),
        (
            "attestation_entity_coverage_only",
            lambda graph: graph["review_attestations"][0].update({"reviewed_entity_ids": []}),
            "review_attestation_entity_coverage_missing",
        ),
    )
    for name, mutate, expected_code in variants:
        graph = copy.deepcopy(base)
        mutate(graph)
        _refresh_current_attestation(graph)
        validate, audit, export = _formal_results(graph, directory, name)
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or expected_code not in result.stdout:
                errors.append(f"{name}: {label} did not enforce {expected_code}\n{result.stdout}")

    graph = copy.deepcopy(base)
    current_hash = graph_hash(graph)
    graph["audits"].append({
        "audit_id": "audit_disclosure_001",
        "audited_at": "2026-07-17T00:00:00Z",
        "research_graph_hash": current_hash,
        "audit_graph_hash": current_hash,
        "review_cycle_id": "review_run_001",
        "review_attestation_id": "att_run_001",
        "reviewed_subject_hash": current_hash,
        "review_provenance_level": "declared_separate_session",
        "audit_status": "passed",
        "delivery_status": "standard_development_list",
        "allowed_delivery_statuses": ["initial_lead_list", "standard_development_list"],
        "disclosure_required": False,
        "ok": True,
        "issue_count": 0,
        "issues": [],
    })
    graph["delivery_manifests"].append({
        "delivery_manifest_id": "manifest_disclosure_001",
        "run_id": "run_001",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "audit_id": "audit_disclosure_001",
        "audit_graph_hash": current_hash,
        "research_graph_hash": current_hash,
        "review_cycle_id": "review_run_001",
        "review_attestation_id": "att_run_001",
        "reviewed_subject_hash": current_hash,
        "review_provenance_level": "declared_separate_session",
        "generated_at": "2026-07-17T00:00:00Z",
        "delivery_status": "standard_development_list",
        "output_mode": "standard",
        "exported_entity_ids": ["ent_001"],
        "exported_contact_ids": ["contact_001"],
        "exported_contact_claim_ids": ["cc_001"],
        "exported_assessment_ids": ["assess_001"],
        "output_files": [],
        "warnings": [],
        "disclosures": [],
    })
    validate, audit, export = _formal_results(graph, directory, "stored_declared_disclosure_missing")
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0 or "audit_disclosure_required_missing" not in result.stdout or "manifest_declared_review_disclosure_missing" not in result.stdout:
            errors.append(f"stored_declared_disclosure_missing: {label} did not enforce stored disclosure metadata\n{result.stdout}")
    return errors


def _assert_hold_value_is_not_exported(directory: Path) -> list[str]:
    graph = _base()
    graph["contact_claims"][0]["export_status"] = "hold_inferred"
    graph["contact_claims"][0]["user_status"] = "不可导出"
    _append_unassigned(graph)
    _refresh_current_attestation(graph)
    validate, audit, export = _formal_results(graph, directory, "hold_value_filtered")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"hold_value_filtered: expected export to pass\n{audit.stdout}\n{export.stdout}"]
    exported = "\n".join(path.read_text(encoding="utf-8-sig") for path in (directory / "hold_value_filtered").glob("*.csv"))
    return ["hold_value_filtered: hold contact value leaked into export"] if "sales@example.com" in exported else []


def _assert_historical_review_cannot_approve(directory: Path) -> list[str]:
    graph = _base()
    graph["observations"][0]["run_id"] = "run_001"
    graph["runs"].append({
        "run_id": "run_002",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "created_at": "2026-01-02T00:00:00Z",
        "review_cycle_id": "review_run_002",
        "status": "checked",
        "platform": "fixture",
    })
    validate, audit, export = _formal_results(graph, directory, "historical_review_scope")
    errors = []
    if validate.returncode != 0:
        errors.append(f"historical_review_scope: graph should remain structurally valid\n{validate.stdout}")
    if audit.returncode == 0 or export.returncode == 0:
        errors.append(f"historical_review_scope: historical independent review approved current Run\n{audit.stdout}\n{export.stdout}")
    return errors


def _assert_historical_assessment_cannot_be_reused(directory: Path) -> list[str]:
    graph = _base()
    graph["observations"][0]["run_id"] = "run_001"
    graph["runs"].append({
        "run_id": "run_002",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "created_at": "2026-01-02T00:00:00Z",
        "review_cycle_id": "review_run_002",
        "review_mode": "independent",
        "status": "checked",
        "platform": "fixture",
    })
    validate, audit, export = _formal_results(graph, directory, "historical_assessment_scope")
    errors = []
    if validate.returncode != 0:
        errors.append(f"historical_assessment_scope: graph should remain structurally valid\n{validate.stdout}")
    if audit.returncode == 0 or export.returncode == 0:
        errors.append(f"historical_assessment_scope: current Run reused an Assessment from another Run\n{audit.stdout}\n{export.stdout}")
    return errors


def _assert_formal_exception_bindings(directory: Path) -> list[str]:
    errors: list[str] = []
    for mode, expected_code in (
        ("single_company_analysis", "single_company_target_missing"),
        ("existing_table_enrichment", "existing_table_binding_missing"),
    ):
        graph = _base()
        graph["briefs"][0]["task_mode"] = mode
        graph["briefs"][0].pop("customer_selection_contract", None)
        graph["scope_decisions"] = []
        graph["assessments"][0].pop("scope_decision_id", None)
        validate, audit, export = _formal_results(graph, directory, f"{mode}_missing_binding")
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or expected_code not in result.stdout:
                errors.append(f"{mode}_missing_binding: {label} did not block the unbound exception\n{result.stdout}")
    for mode, expected_code in (
        ("single_company_analysis", "single_company_assessment_outside_target"),
        ("existing_table_enrichment", "existing_table_assessment_outside_bound_input"),
    ):
        graph = _base()
        graph["briefs"][0]["task_mode"] = mode
        graph["briefs"][0].pop("customer_selection_contract", None)
        graph["scope_decisions"] = []
        graph["assessments"][0].pop("scope_decision_id", None)
        if mode == "single_company_analysis":
            graph["briefs"][0]["single_company_target"] = {
                "user_statement": "Analyze Example Buyer.", "company_name": "Example Buyer",
                "website_or_domain": "https://example.com", "source_id": None, "entity_literal": None, "resolved_entity_id": "ent_001",
            }
        else:
            graph["sources"].append({
                "source_id": "src_table_001", "publisher_relation": "unknown", "provenance": "user_provided",
                "material_role": "user_business_dataset", "medium": "spreadsheet", "access_boundary": "user_supplied",
                "owner_hint": "existing table", "artifact_sha256": "f" * 64, "artifact_name": "existing.xlsx",
                "artifact_media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            })
            graph["observations"].append({
                "observation_id": "obs_table_001", "source_id": "src_table_001", "candidate_id": None, "entity_id": "ent_001",
                "capability": "document.extract", "concrete_tool": "fixture", "observed_at": "2026-01-01T00:00:00Z",
                "access_status": "ok", "http_status": None, "title": "existing table", "raw_excerpt": "Example Buyer",
                "page_or_dom_locator": "Rows!A2", "content_hash": "table_001", "extraction_method": "fixture",
                "tool_version": "fixture", "language": "en", "translation_status": "original",
                "derived_from_observation_id": None, "snapshot_ref": "artifact:sha256:" + "f" * 64 + "#sheet=Rows&range=A2",
            })
            graph["briefs"][0]["existing_table_binding"] = {
                "source_id": "src_table_001",
                "entity_bindings": [{"entity_id": "ent_001", "observation_id": "obs_table_001", "row_or_cell_locator": "Rows!A2", "entity_literal": "Example Buyer"}],
            }
        graph["entities"].append({"entity_id": "ent_002", "name": "Unbound Buyer", "website": "https://unbound.example"})
        graph["assessments"][0]["entity_id"] = "ent_002"
        validate, audit, export = _formal_results(graph, directory, f"{mode}_outside_binding")
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or expected_code not in result.stdout:
                errors.append(f"{mode}_outside_binding: {label} did not block the unbound Entity\n{result.stdout}")
    return errors


def _assert_identity_literal_bindings(directory: Path) -> list[str]:
    errors: list[str] = []
    graph = _base()
    graph["briefs"][0]["task_mode"] = "single_company_analysis"
    graph["briefs"][0].pop("customer_selection_contract", None)
    graph["scope_decisions"] = []
    graph["assessments"][0].pop("scope_decision_id", None)
    graph["briefs"][0]["single_company_target"] = {
        "user_statement": "Analyze the supplied company.", "company_name": "Unrelated Buyer",
        "website_or_domain": "https://example.com", "source_id": None, "entity_literal": None,
        "resolved_entity_id": "ent_001",
    }
    validate, audit, export = _formal_results(graph, directory, "single_company_conflicting_identifiers")
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0 or "single_company_target_identifier_conflict" not in result.stdout:
            errors.append(f"single_company_conflicting_identifiers: {label} did not block conflicting identifiers\n{result.stdout}")

    graph = _base()
    graph["briefs"][0]["task_mode"] = "existing_table_enrichment"
    graph["briefs"][0].pop("customer_selection_contract", None)
    graph["scope_decisions"] = []
    graph["assessments"][0].pop("scope_decision_id", None)
    graph["sources"].append({
        "source_id": "src_table_literal_001", "publisher_relation": "unknown", "provenance": "user_provided",
        "material_role": "user_business_dataset", "medium": "spreadsheet", "access_boundary": "user_supplied",
        "owner_hint": "existing table", "artifact_sha256": "e" * 64, "artifact_name": "existing.xlsx",
        "artifact_media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    })
    graph["observations"].append({
        "observation_id": "obs_table_literal_001", "source_id": "src_table_literal_001", "candidate_id": None, "entity_id": "ent_001",
        "capability": "document.extract", "concrete_tool": "fixture", "observed_at": "2026-01-01T00:00:00Z",
        "access_status": "ok", "http_status": None, "title": "existing table", "raw_excerpt": "Unrelated Buyer",
        "page_or_dom_locator": "Rows!A2", "content_hash": "table_literal_001", "extraction_method": "fixture",
        "tool_version": "fixture", "language": "en", "translation_status": "original",
        "derived_from_observation_id": None, "snapshot_ref": "artifact:sha256:" + "e" * 64 + "#sheet=Rows&range=A2",
    })
    graph["briefs"][0]["existing_table_binding"] = {
        "source_id": "src_table_literal_001",
        "entity_bindings": [{"entity_id": "ent_001", "observation_id": "obs_table_literal_001", "row_or_cell_locator": "Rows!A2", "entity_literal": "Unrelated Buyer"}],
    }
    validate, audit, export = _formal_results(graph, directory, "existing_table_wrong_row_identity")
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0 or "existing_table_binding_literal_entity_mismatch" not in result.stdout:
            errors.append(f"existing_table_wrong_row_identity: {label} did not block mismatched row identity\n{result.stdout}")
    return errors


def _assert_hold_free_text_is_redacted(directory: Path) -> list[str]:
    graph = _base()
    graph["contact_claims"][0]["export_status"] = "hold_inferred"
    graph["contact_claims"][0]["user_status"] = "不可导出"
    graph["assessments"][0]["missing_requirements"] = ["Do not expose sales@example.com"]
    _append_unassigned(graph)
    graph["unassigned_contact_leads"][0].update({
        "reason": "sales@example.com was inferred",
        "suggested_manual_check": "Verify sales@example.com only from a public page.",
    })
    _refresh_current_attestation(graph)
    validate, audit, export = _formal_results(graph, directory, "hold_free_text_redaction")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"hold_free_text_redaction: expected sanitized export to pass\n{audit.stdout}\n{export.stdout}"]
    output_dir = directory / "hold_free_text_redaction"
    exported = "\n".join(path.read_text(encoding="utf-8-sig") for path in output_dir.glob("*.csv"))
    exported += (output_dir / "manifest.json").read_text(encoding="utf-8")
    errors = ["hold_free_text_redaction: hold contact leaked through free text"] if "sales@example.com" in exported else []
    try:
        import openpyxl  # type: ignore
    except Exception:
        return errors
    graph_path = directory / "hold_free_text_redaction.json"
    xlsx_dir = directory / "hold_free_text_redaction_xlsx"
    xlsx = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(xlsx_dir), "--mode", "standard", "--format", "xlsx"])
    if xlsx.returncode != 0:
        errors.append(f"hold_free_text_redaction: XLSX export failed\n{xlsx.stdout}")
        return errors
    workbook = openpyxl.load_workbook(xlsx_dir / "superleads_workbook.xlsx", read_only=True, data_only=True)
    cells = "\n".join(str(cell) for sheet in workbook.worksheets for row in sheet.iter_rows(values_only=True) for cell in row if cell is not None)
    if "sales@example.com" in cells:
        errors.append("hold_free_text_redaction: hold contact leaked into XLSX")
    return errors


def _assert_manual_contact_is_not_exported(directory: Path) -> list[str]:
    graph = _base()
    graph["contact_claims"][0].update({
        "export_status": "needs_manual_association_review",
        "user_status": "待确认归属",
        "manual_check_note": "Manual owner check required.",
    })
    _refresh_current_attestation(graph)
    validate, audit, export = _formal_results(graph, directory, "manual_contact_filtered")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"manual_contact_filtered: expected formal export to pass\n{audit.stdout}\n{export.stdout}"]
    contacts = (directory / "manual_contact_filtered" / "联系方式汇总.csv").read_text(encoding="utf-8-sig")
    return ["manual_contact_filtered: manual-association contact leaked into contact summary"] if "sales@example.com" in contacts else []


def _assert_standard_docs_include_source_links() -> list[str]:
    paths = [
        ROOT / "skills" / "exporting-lead-workbooks" / "SKILL.md",
        ROOT / "shared" / "references" / "output-schema.md",
    ]
    return [f"{path}: standard export documentation omits 官网与来源链接" for path in paths if "官网与来源链接" not in path.read_text(encoding="utf-8")]


def _assert_user_file_direct_pressure_tests(directory: Path) -> list[str]:
    errors: list[str] = []
    validate = _run([sys.executable, "-B", str(SCRIPTS / "validate_research_graph.py"), str(USER_FILE_PDF)])
    if validate.returncode != 0:
        errors.append(f"user_file_pdf_validate: expected pass\n{validate.stdout}")
    audit = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(USER_FILE_PDF), "--delivery-status", "standard_development_list", "--format", "json"])
    if audit.returncode != 0 or '"delivery_status": "standard_development_list"' not in audit.stdout:
        errors.append(f"user_file_pdf_audit: expected standard delivery\n{audit.stdout}")
    output = directory / "superleads-user-file-test.xlsx"
    export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(USER_FILE_SHEET), str(output), "--mode", "standard"])
    if export.returncode != 0 or not output.exists():
        errors.append(f"user_file_sheet_export: expected XLSX output\n{export.stdout}")
        return errors
    try:
        import openpyxl  # type: ignore
        workbook = openpyxl.load_workbook(output, read_only=True, data_only=True)
        cells = "\n".join(str(value) for sheet in workbook.worksheets for row in sheet.iter_rows(values_only=True) for value in row if value is not None)
    except Exception as exc:
        return errors + [f"user_file_sheet_export: could not inspect XLSX: {exc}"]
    if "用户提供文件：客户名单.xlsx（工作表 Contacts，A2:F2）" not in cells:
        errors.append("user_file_sheet_export: workbook lacks safe spreadsheet source display")
    for forbidden in ("file://", "/home/", "C:\\", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"):
        if forbidden in cells:
            errors.append(f"user_file_sheet_export: forbidden local/internal value leaked: {forbidden}")
    return errors


def _assert_material_role_direct_pressure_tests(directory: Path) -> list[str]:
    errors: list[str] = []
    for name, fixture, expected_label in (
        ("dataset", DATASET_CONTACT, "用户提供文件：历史客户表.xlsx（工作表 Contacts，A2:F2）"),
        ("correspondence", CORRESPONDENCE_CONTACT, "用户提供沟通记录：客户沟通.eml（章节 message-1）"),
    ):
        out_dir = directory / f"{name}_export"
        graph_path = directory / f"{name}_source_note.json"
        _write_graph(graph_path, _load_fixture_graph(fixture))
        export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(out_dir), "--mode", "standard", "--format", "csv", "--manifest", str(out_dir / "manifest.json")])
        if export.returncode != 0:
            errors.append(f"{name}_source_note_export: expected standard export\n{export.stdout}")
            continue
        text = "\n".join(path.read_text(encoding="utf-8-sig") for path in out_dir.glob("*.csv"))
        text += (out_dir / "manifest.json").read_text(encoding="utf-8")
        if expected_label not in text or "建议核查后使用" not in text:
            errors.append(f"{name}_source_note_export: missing source-note display or status")
        for forbidden in ("可直接使用", "material_role", "file://", "/home/", "C:\\", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"):
            if forbidden in text:
                errors.append(f"{name}_source_note_export: forbidden value leaked: {forbidden}")
    visual_path = directory / "visual_candidate.json"
    visual_output = directory / "visual_export"
    _write_graph(visual_path, _load_fixture_graph(VISUAL_CANDIDATE))
    validate = _run([sys.executable, "-B", str(SCRIPTS / "validate_research_graph.py"), str(visual_path)])
    standard = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(visual_path), "--output-dir", str(visual_output), "--mode", "standard", "--format", "csv"])
    initial = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(visual_path), "--output-dir", str(visual_output), "--mode", "initial", "--format", "csv"])
    if validate.returncode != 0 or initial.returncode != 0 or standard.returncode == 0:
        errors.append(f"visual_candidate_delivery_levels: expected validate+initial pass and standard block\n{validate.stdout}\n{standard.stdout}\n{initial.stdout}")
    return errors


def _assert_inquiry_export_redaction(directory: Path) -> list[str]:
    graph_path = directory / "connected_inquiry.json"
    out_dir = directory / "connected_inquiry_export"
    _write_graph(graph_path, _load_fixture_graph(CONNECTED_INQUIRY))
    audit = _run([sys.executable, "-B", str(SCRIPTS / "audit_delivery.py"), str(graph_path), "--delivery-status", "inquiry_followup_queue", "--format", "json"])
    export = _run([sys.executable, "-B", str(SCRIPTS / "export_workbook.py"), str(graph_path), "--output-dir", str(out_dir), "--mode", "inquiry", "--format", "csv", "--manifest", str(out_dir / "manifest.json")])
    if audit.returncode != 0 or export.returncode != 0:
        return [f"inquiry_export: expected inquiry audit/export to pass\n{audit.stdout}\n{export.stdout}"]
    text = "\n".join(path.read_text(encoding="utf-8-sig") for path in out_dir.glob("*.csv"))
    text += (out_dir / "manifest.json").read_text(encoding="utf-8")
    errors = []
    if "邮件来信（2026-07-15）" not in text or "询盘待办" not in text:
        errors.append("inquiry_export: missing business-facing inquiry label")
    for forbidden in ("host-message-001", "host-thread-001", "mailbox_inbox_001", "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", "From: sales@example.com", "file://", "/home/", "C:\\"):
        if forbidden in text:
            errors.append(f"inquiry_export: leaked internal or full-mail value: {forbidden}")
    return errors


def _assert_mail_adapter_boundary(directory: Path) -> list[str]:
    output = directory / "mail_adapter_output.json"
    accepted = _run([sys.executable, "-B", str(SCRIPTS / "ingest_mail_read_result.py"), str(MAIL_ADAPTER_INPUT), "--output", str(output)])
    if accepted.returncode != 0 or not output.exists():
        return [f"mail_adapter_accept: expected bounded host result to normalize\n{accepted.stdout}"]
    payload = json.loads(output.read_text(encoding="utf-8"))
    text = json.dumps(payload, ensure_ascii=False)
    if "password" in text or "token" in text or "host-message-adapter-001" not in text:
        return ["mail_adapter_accept: unexpected normalized result boundary"]
    bad_input = dict(json.loads(MAIL_ADAPTER_INPUT.read_text(encoding="utf-8")))
    bad_input["access_token"] = "must-not-store"
    bad_path = directory / "mail_adapter_bad.json"
    _write_graph(bad_path, bad_input)
    rejected = _run([sys.executable, "-B", str(SCRIPTS / "ingest_mail_read_result.py"), str(bad_path), "--output", str(directory / "mail_adapter_bad_output.json")])
    return [] if rejected.returncode != 0 and "mail_input_forbidden_sensitive_field" in rejected.stdout else [f"mail_adapter_reject: sensitive host input was not blocked\n{rejected.stdout}"]


def _assert_platform_and_public_url_pressure_tests(directory: Path) -> list[str]:
    """Construct variants directly so coverage cannot depend on fixture names."""
    errors: list[str] = []
    platform_variants = ("curl ", "shell-curl", "codex_cli ", "CODEX_CLI")
    for index, platform in enumerate(platform_variants):
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_codex_shell_http_source_open_standard.json")
        graph["runs"][0]["platform"] = platform
        graph["runs"][0].pop("capability_adapter_report", None)
        validate, audit, export = _formal_results(graph, directory, f"platform_variant_{index}")
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or "run_platform_not_canonical" not in result.stdout:
                errors.append(f"platform_variant_{platform!r}: {label} did not block canonical-platform bypass\n{result.stdout}")

    for index, hostname in enumerate(("127.1", "2130706433", "0x7f000001")):
        graph = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_codex_shell_http_source_open_standard.json")
        url = f"http://{hostname}/private"
        graph["sources"][0].update({"canonical_url": url, "final_url": url})
        operation = graph["runs"][0]["capability_adapter_report"]["host_tools"]["shell_http"]["operations"]["open_source"]
        operation.update({"original_url": url, "final_url": url})
        validate, audit, export = _formal_results(graph, directory, f"shell_loopback_{index}")
        for label, result in (("validate", validate), ("audit", audit), ("export", export)):
            if result.returncode == 0 or "codex_shell_http_url_not_public" not in result.stdout:
                errors.append(f"shell_loopback_{hostname}: {label} did not block legacy IPv4 loopback\n{result.stdout}")

    generic = _base()
    generic["runs"][0]["platform"] = "hermes"
    generic["sources"][0].update({"canonical_url": "http://127.0.0.1/private", "final_url": "http://127.0.0.1/private"})
    validate, audit, export = _formal_results(generic, directory, "generic_loopback")
    for label, result in (("validate", validate), ("audit", audit), ("export", export)):
        if result.returncode == 0 or "public_source_url_not_safe" not in result.stdout:
            errors.append(f"generic_loopback: {label} did not block formal private URL\n{result.stdout}")

    public_shell = _load_fixture_graph(ROOT / "evals" / "fixtures" / "pass_codex_shell_http_source_open_standard.json")
    validate, audit, export = _formal_results(public_shell, directory, "public_shell_control")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        errors.append(f"public_shell_control: public HTTPS shell source no longer passes\n{validate.stdout}\n{audit.stdout}\n{export.stdout}")
    return errors


def _stored_unauthorized_manifest(graph: dict[str, Any]) -> None:
    graph["runs"][0]["review_mode"] = "not_run"
    current_hash = graph_hash(graph)
    graph["audits"].append({
        "audit_id": "audit_001",
        "audited_at": "2026-01-01T00:00:00Z",
        "research_graph_hash": current_hash,
        "audit_graph_hash": current_hash,
        "review_cycle_id": "review_run_001",
        "review_attestation_id": None,
        "reviewed_subject_hash": current_hash,
        "review_provenance_level": "not_run",
        "audit_status": "passed",
        "delivery_status": "standard_development_list",
        "allowed_delivery_statuses": ["initial_lead_list", "standard_development_list"],
        "disclosure_required": False,
        "ok": True,
        "issue_count": 0,
        "issues": [],
    })
    graph["delivery_manifests"].append({
        "delivery_manifest_id": "manifest_001",
        "run_id": "run_001",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "audit_id": "audit_001",
        "audit_graph_hash": current_hash,
        "research_graph_hash": current_hash,
        "review_cycle_id": "review_run_001",
        "review_attestation_id": None,
        "reviewed_subject_hash": current_hash,
        "review_provenance_level": "not_run",
        "generated_at": "2026-01-01T00:00:00Z",
        "delivery_status": "standard_development_list",
        "output_mode": "standard",
        "exported_entity_ids": ["ent_001"],
        "exported_contact_ids": ["contact_001"],
        "exported_contact_claim_ids": ["cc_001"],
        "exported_assessment_ids": ["assess_001"],
        "output_files": [],
        "warnings": [],
        "disclosures": [],
    })


def main() -> int:
    tests: list[tuple[str, Callable[[dict[str, Any]], None]]] = []

    def add(name: str, mutate: Callable[[dict[str, Any]], None]) -> None:
        tests.append((name, mutate))

    add("claim_value_not_in_observation", lambda g: g["claims"][0].update({"typed_value": {"text": "unrelated high-risk equipment"}}))
    add("claim_semantic_fields_unanchored", lambda g: g["claims"][0].update({"subject": "Other Buyer", "predicate": "is exclusive purchaser of", "claim_type": "exclusive_purchase_authority", "claim_scope": "global_2026", "typed_value": {"text": "sample product", "exclusive": True}}))
    add("assessment_rationale_unanchored_fact", lambda g: g["assessments"][0].update({"rationale_structured": {"summary": "confirmed exclusive purchaser"}}))
    def claim_value_substring(graph: dict[str, Any]) -> None:
        graph["observations"][0]["raw_excerpt"] = graph["observations"][0]["raw_excerpt"].replace("sample product", "sample products")
        graph["claims"][0]["typed_value"] = {"text": "product"}
        graph["claim_evidence"][0]["claim_field_anchors"]["claim_type"] = "Example Buyer sells sample products"
        graph["claim_evidence"][0]["claim_field_anchors"]["typed_value"] = "product"

    add("claim_value_substring", claim_value_substring)

    def translation_missing_origin(graph: dict[str, Any]) -> None:
        graph["observations"][0].update({"translation_status": "translated", "derived_from_observation_id": "obs_missing"})

    add("translation_missing_origin", translation_missing_origin)

    def translation_cross_entity(graph: dict[str, Any]) -> None:
        graph["entities"].append({"entity_id": "ent_002", "name": "Other Buyer", "website": "https://other.example"})
        origin = copy.deepcopy(graph["observations"][0])
        origin.update({"observation_id": "obs_002", "entity_id": "ent_002"})
        graph["observations"].append(origin)
        graph["observations"][0].update({"translation_status": "translated", "derived_from_observation_id": "obs_002"})

    add("translation_cross_entity_origin", translation_cross_entity)

    def translation_cycle(graph: dict[str, Any]) -> None:
        translated = copy.deepcopy(graph["observations"][0])
        translated.update({"observation_id": "obs_002", "translation_status": "translated", "derived_from_observation_id": "obs_001"})
        graph["observations"].append(translated)
        graph["observations"][0].update({"translation_status": "translated", "derived_from_observation_id": "obs_002"})

    add("translation_cycle_without_original_root", translation_cycle)
    add("unknown_capability_support", lambda g: g["observations"][0].update({"capability": "vendor.magic_lookup"}))
    add("search_result_contact_source", lambda g: g["contact_points"][0].update({"source_type": "search_result"}))

    def contact_form_truncation(graph: dict[str, Any]) -> None:
        graph["observations"][0]["raw_excerpt"] += " Form: https://example.com/contact-form"
        graph["contact_points"][0].update({
            "contact_type": "contact_form",
            "source_literal": "https://example.com/contact-form",
            "normalized_value": "https://example.com/contact",
        })
        graph["contact_claims"][0]["association_evidence_text"] = "Form: https://example.com/contact-form"

    add("contact_form_truncation", contact_form_truncation)

    def ready_without_entity(graph: dict[str, Any]) -> None:
        graph["contact_claims"][0].update({"entity_id": None, "person_id": "person_001"})

    add("ready_contact_without_resolved_entity", ready_without_entity)
    add("manual_contact_fabricated_association", lambda g: g["contact_claims"][0].update({"export_status": "needs_manual_association_review", "user_status": "待确认归属", "association_evidence_text": "Invented association text"}))
    add("exportable_contact_without_entity", lambda g: g["contact_claims"][0].update({"export_status": "export_with_source_note", "user_status": "建议核查后使用", "entity_id": None, "person_id": "person_001"}))

    def email_disguised_as_other(graph: dict[str, Any]) -> None:
        graph["observations"][0]["raw_excerpt"] = "Example Buyer sells sample product. Example Buyer Contact: not-sales@example.com"
        graph["contact_points"][0].update({"contact_type": "other", "source_literal": "sales@example.com", "normalized_value": "sales@example.com"})
        graph["contact_claims"][0]["association_evidence_text"] = "Example Buyer Contact: sales@example.com"

    add("email_disguised_as_other_substring", email_disguised_as_other)

    def cross_company_contact_section(graph: dict[str, Any]) -> None:
        graph["entities"].append({"entity_id": "ent_002", "name": "Other Buyer", "website": "https://other.example"})
        graph["observations"][0]["raw_excerpt"] = "Example Buyer sells sample product. Other Buyer Contact: sales@example.com"
        graph["contact_claims"][0]["association_evidence_text"] = "Other Buyer Contact: sales@example.com"

    add("cross_company_contact_section", cross_company_contact_section)
    add("invalid_claim_support_source_url", lambda g: g["sources"][0].update({"canonical_url": "data:text/html,not-a-source", "final_url": "javascript:alert(1)"}))

    def forged_relationship_evidence(graph: dict[str, Any]) -> None:
        graph["entities"].append({"entity_id": "ent_002", "name": "Other Buyer", "website": "https://other.example"})
        graph["entity_relationships"].append({
            "entity_relationship_id": "rel_001",
            "source_entity_id": "ent_001",
            "target_entity_id": "ent_002",
            "relationship_type": "dealer_of",
            "resolution_status": "contextual",
            "confidence": "high",
            "rationale": "fixture",
            "evidence_claim_ids": ["claim_missing"],
            "evidence_observation_ids": ["obs_missing"],
        })

    add("entity_relationship_forged_evidence", forged_relationship_evidence)
    add("stored_manifest_delivery_status_not_allowed", _stored_unauthorized_manifest)

    def manifest_empty_reference(graph: dict[str, Any]) -> None:
        graph["delivery_manifests"].append({
            "delivery_manifest_id": "manifest_001", "run_id": "", "brief_id": "", "plan_id": "", "audit_id": "",
            "audit_graph_hash": "", "research_graph_hash": "", "review_cycle_id": "review_run_001", "review_attestation_id": None, "reviewed_subject_hash": "a" * 64, "review_provenance_level": "not_applicable",
            "generated_at": "2026-01-01T00:00:00Z", "delivery_status": "standard_development_list", "output_mode": "standard",
            "exported_entity_ids": [], "exported_contact_ids": [], "exported_contact_claim_ids": [], "exported_assessment_ids": [],
            "output_files": [], "warnings": [], "disclosures": [],
        })

    add("manifest_empty_reference_chain", manifest_empty_reference)
    add("unknown_control_field", lambda g: g["runs"][0].update({"audit_bypass": True}))

    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="superleads_advanced_gates_") as temporary:
        directory = Path(temporary)
        for name, mutate in tests:
            graph = _base()
            mutate(graph)
            errors.extend(_must_block(name, graph, directory))
        errors.extend(_assert_hold_value_is_not_exported(directory))
        errors.extend(_assert_hold_free_text_is_redacted(directory))
        errors.extend(_assert_manual_contact_is_not_exported(directory))
        errors.extend(_assert_standard_docs_include_source_links())
        errors.extend(_assert_user_file_direct_pressure_tests(directory))
        errors.extend(_assert_material_role_direct_pressure_tests(directory))
        errors.extend(_assert_inquiry_export_redaction(directory))
        errors.extend(_assert_mail_adapter_boundary(directory))
        errors.extend(_assert_platform_and_public_url_pressure_tests(directory))
        errors.extend(_assert_self_review_disclosure(directory))
        errors.extend(_assert_historical_review_cannot_approve(directory))
        errors.extend(_assert_historical_assessment_cannot_be_reused(directory))
        errors.extend(_assert_formal_exception_bindings(directory))
        errors.extend(_assert_identity_literal_bindings(directory))
        errors.extend(_assert_phase2_provenance_and_searchlog(directory))
        errors.extend(_assert_target_geography_contract_required(directory))
        errors.extend(_assert_legacy_review_fields_rejected(directory))
        errors.extend(_assert_review_attestation_coverage_and_disclosures(directory))
        invalid_schema = _base()
        invalid_schema["observations"][0]["capability"] = "vendor.magic_lookup"
        schema_path = directory / "schema_fail_closed.json"
        _write_graph(schema_path, invalid_schema)
        fallback = _run([sys.executable, "-S", "-B", str(SCRIPTS / "audit_delivery.py"), str(schema_path), "--delivery-status", "standard_development_list"])
        if fallback.returncode == 0:
            errors.append(f"schema_fail_closed: audit passed without jsonschema\n{fallback.stdout}")

    if errors:
        print("Advanced gate regressions failed:")
        print("\n\n".join(errors))
        return 1
    print(f"advanced gate regressions passed: {len(tests) + 18}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
