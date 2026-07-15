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
sys.path.insert(0, str(SCRIPTS))
from _superleads_common import graph_hash  # noqa: E402


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


def _assert_self_review_disclosure(directory: Path) -> list[str]:
    graph = _base()
    graph["runs"][0]["review_mode"] = "self_review_fallback"
    validate, audit, export = _formal_results(graph, directory, "self_review_disclosure")
    errors = []
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"self_review_disclosure: expected formal export to pass\n{audit.stdout}\n{export.stdout}"]
    disclosure_sheet = (directory / "self_review_disclosure" / "风险与说明.csv").read_text(encoding="utf-8-sig")
    if "self_review_fallback" not in disclosure_sheet:
        errors.append("self_review_disclosure: workbook risk sheet lacks self_review_fallback disclosure")
    return errors


def _assert_hold_value_is_not_exported(directory: Path) -> list[str]:
    graph = _base()
    graph["contact_claims"][0]["export_status"] = "hold_inferred"
    graph["contact_claims"][0]["user_status"] = "不可导出"
    _append_unassigned(graph)
    validate, audit, export = _formal_results(graph, directory, "hold_value_filtered")
    if any(result.returncode != 0 for result in (validate, audit, export)):
        return [f"hold_value_filtered: expected export to pass\n{audit.stdout}\n{export.stdout}"]
    exported = "\n".join(path.read_text(encoding="utf-8-sig") for path in (directory / "hold_value_filtered").glob("*.csv"))
    return ["hold_value_filtered: hold contact value leaked into export"] if "sales@example.com" in exported else []


def _assert_historical_review_cannot_approve(directory: Path) -> list[str]:
    graph = _base()
    graph["runs"].append({
        "run_id": "run_002",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "created_at": "2026-01-02T00:00:00Z",
        "review_cycle_id": "review_run_002",
        "status": "checked",
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
    graph["runs"].append({
        "run_id": "run_002",
        "brief_id": "brief_001",
        "plan_id": "plan_001",
        "created_at": "2026-01-02T00:00:00Z",
        "review_cycle_id": "review_run_002",
        "review_mode": "independent",
        "status": "checked",
    })
    validate, audit, export = _formal_results(graph, directory, "historical_assessment_scope")
    errors = []
    if validate.returncode != 0:
        errors.append(f"historical_assessment_scope: graph should remain structurally valid\n{validate.stdout}")
    if audit.returncode == 0 or export.returncode == 0:
        errors.append(f"historical_assessment_scope: current Run reused an Assessment from another Run\n{audit.stdout}\n{export.stdout}")
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


def _stored_unauthorized_manifest(graph: dict[str, Any]) -> None:
    graph["runs"][0]["review_mode"] = "not_run"
    current_hash = graph_hash(graph)
    graph["audits"].append({
        "audit_id": "audit_001",
        "audited_at": "2026-01-01T00:00:00Z",
        "research_graph_hash": current_hash,
        "audit_graph_hash": current_hash,
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
            "audit_graph_hash": "", "research_graph_hash": "", "review_cycle_id": "review_run_001",
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
        errors.extend(_assert_self_review_disclosure(directory))
        errors.extend(_assert_historical_review_cannot_approve(directory))
        errors.extend(_assert_historical_assessment_cannot_be_reused(directory))
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
    print(f"advanced gate regressions passed: {len(tests) + 7}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
