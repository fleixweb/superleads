#!/usr/bin/env python3
"""Compile concise opened-source notes into existing product-market graph objects.

This is deliberately a graph compiler, not a research agent. It never searches,
opens URLs, classifies an authority, or upgrades a note's status. Callers supply
only facts from existing opened Observations; the compiler fills the repetitive
EvidenceCard, MatrixRowRecord, and ProductAttributeRecord linkage.
"""
from __future__ import annotations

import argparse
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from _superleads_common import has_text, issue, load_json, write_json
from validate_product_market_analysis import validate_graph


OPENED_ACCESS_STATUSES = {"opened", "captured", "extracted", "rendered"}
STATUSES = {
    "verified",
    "derived_calculation",
    "candidate",
    "preliminary_reference",
    "business_confirmation_required",
    "technical_docs_required",
    "physical_verification_required",
    "professional_confirmation_required",
    "source_restricted",
    "not_executed",
    "not_applicable",
    "not_provided",
    "conflict_pending_review",
}
SHEET_NAMES = {
    "市场事实总览",
    "产品档案与触发项",
    "长期需求与搜索趋势",
    "公开市场资料与行业信息",
    "线上市场与价格参考",
    "季节、节日与销售窗口",
    "产品准入与合规要求",
    "进口税费",
    "出口国要求",
    "运输方式、路线、港口与申报节点",
    "近期外部因素",
    "信息来源与待确认事项",
}
NOTE_ROOT_KEYS = {"product_attributes", "evidence_notes"}
ATTRIBUTE_KEYS = {"attribute_id", "product_subject_id", "attribute_name", "value", "unit", "status", "trigger_paths"}
EVIDENCE_NOTE_KEYS = {
    "evidence_note_id",
    "observation_id",
    "field_domain",
    "field_name",
    "current_value",
    "status",
    "source_excerpt_quote",
    "source_date",
    "applicability_scope",
    "supports",
    "does_not_support",
    "boundary_rule_ids",
    "review_status",
    "authority_verification_record_ids",
    "freshness_record_ids",
    "gap",
    "row",
    "rows",
}
ROW_KEYS = {
    "sheet_name",
    "row_topic",
    "user_visible_cells",
    "module_key",
    "row_type",
    "certification_requirement",
    "origin_proof_requirement",
    "authority_verification_record_ids",
    "freshness_record_ids",
}
GAP_KEYS = {"gap_id", "field_domain", "field_name", "status", "missing_item", "requested_from", "user_visible_note"}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [] if value is None else [value]


def _text(value: Any) -> str:
    return str(value).strip() if has_text(value) else ""


def _safe_id(value: Any, fallback: str) -> str:
    normalized = re.sub(r"[^a-z0-9._-]+", "-", str(value or "").casefold()).strip("-._")
    return normalized[:72] or fallback


def _error(code: str, message: str, path: str) -> dict[str, str]:
    return issue("critical", code, message, path)


def _index(items: Any, field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in _as_list(items):
        if isinstance(item, dict) and has_text(item.get(field)):
            result[str(item[field])] = item
    return result


def _require_string(note: dict[str, Any], field: str, path: str, issues: list[dict[str, str]]) -> str:
    value = _text(note.get(field))
    if not value:
        issues.append(_error("market_evidence_compiler_required_missing", f"evidence note requires {field}", f"{path}.{field}"))
    return value


def _validate_keys(item: Any, allowed: set[str], path: str, issues: list[dict[str, str]]) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        issues.append(_error("market_evidence_compiler_note_invalid", "compiler input item must be an object", path))
        return None
    for key in sorted(set(item) - allowed):
        issues.append(_error("market_evidence_compiler_unknown_field", f"compiler input does not accept {key}", f"{path}.{key}"))
    return item


def _unique_id(existing: set[str], prefix: str, source: Any) -> str:
    base = f"{prefix}-{_safe_id(source, prefix)}"
    candidate = base
    index = 2
    while candidate in existing:
        candidate = f"{base}-{index}"
        index += 1
    existing.add(candidate)
    return candidate


def _split_attribute_parts(value: Any) -> list[str]:
    return [part.strip() for part in re.split(r"[/、,，;；|]+", str(value or "")) if part.strip()]


def _attribute_part_matches(provided_name: str, unknown_part: str) -> bool:
    provided = re.sub(r"\s+", "", provided_name)
    unknown = re.sub(r"\s+", "", unknown_part)
    if not provided or not unknown:
        return False
    return provided == unknown or provided in unknown or unknown in provided


def _remaining_unknown_attributes(unknowns: list[Any], provided_name: str) -> list[str]:
    remaining: list[str] = []
    for raw_unknown in unknowns:
        unknown = str(raw_unknown).strip()
        parts = _split_attribute_parts(unknown)
        if not parts:
            continue
        unresolved = [part for part in parts if not _attribute_part_matches(provided_name, part)]
        if unresolved:
            remaining.append("/".join(unresolved) if len(parts) > 1 else unknown)
    return remaining


def _row_identity(row: dict[str, Any]) -> str:
    fields = {
        key: row.get(key)
        for key in ("sheet_name", "row_topic", "user_visible_cells", "module_key", "row_type", "certification_requirement", "origin_proof_requirement")
        if key in row
    }
    return json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _append_refs(row: dict[str, Any], field: str, values: list[str]) -> None:
    if not values:
        return
    existing = [str(value) for value in _as_list(row.get(field)) if has_text(value)]
    for value in values:
        if value not in existing:
            existing.append(value)
    row[field] = existing


def _target_rows(note: dict[str, Any], path: str, issues: list[dict[str, str]]) -> list[dict[str, Any]]:
    has_row = "row" in note
    has_rows = "rows" in note
    if has_row and has_rows:
        issues.append(_error("market_evidence_compiler_row_input_ambiguous", "evidence note must use row or rows, not both", path))
        return []
    raw_rows = [note.get("row")] if has_row else note.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        issues.append(_error("market_evidence_compiler_row_missing", "evidence note requires a row or non-empty rows array", f"{path}.row"))
        return []
    result: list[dict[str, Any]] = []
    for row_index, raw_row in enumerate(raw_rows):
        row_path = f"{path}.row" if has_row else f"{path}.rows[{row_index}]"
        row = _validate_keys(raw_row, ROW_KEYS, row_path, issues)
        if row is None:
            continue
        sheet_name = _require_string(row, "sheet_name", row_path, issues)
        _require_string(row, "row_topic", row_path, issues)
        if sheet_name and sheet_name not in SHEET_NAMES:
            issues.append(_error("market_evidence_compiler_sheet_invalid", "row sheet_name must be an existing product-market sheet", f"{row_path}.sheet_name"))
        if not isinstance(row.get("user_visible_cells"), dict):
            issues.append(_error("market_evidence_compiler_visible_cells_invalid", "row requires a user_visible_cells object", f"{row_path}.user_visible_cells"))
        for field in ("authority_verification_record_ids", "freshness_record_ids"):
            if field in row:
                _string_list(row, field, row_path, issues)
        result.append(row)
    return result


def _status(value: Any, path: str, issues: list[dict[str, str]], default: str = "preliminary_reference") -> str:
    value = _text(value) or default
    if value not in STATUSES:
        issues.append(_error("market_evidence_compiler_status_invalid", f"status must be an existing product-market status, got {value}", path))
    return value


def _string_list(note: dict[str, Any], field: str, path: str, issues: list[dict[str, str]]) -> list[str]:
    raw = note.get(field, [])
    if not isinstance(raw, list) or any(not has_text(value) for value in raw):
        issues.append(_error("market_evidence_compiler_string_list_invalid", f"{field} must be an array of non-empty strings", f"{path}.{field}"))
        return []
    return [str(value).strip() for value in raw]


def _compile_attribute(
    graph: dict[str, Any],
    raw: Any,
    index: int,
    attribute_ids: set[str],
    product_ids: set[str],
    default_product_id: str,
    issues: list[dict[str, str]],
) -> None:
    path = f"product_attributes[{index}]"
    note = _validate_keys(raw, ATTRIBUTE_KEYS, path, issues)
    if note is None:
        return
    name = _require_string(note, "attribute_name", path, issues)
    if "value" not in note or note.get("value") is None:
        issues.append(_error("market_evidence_compiler_required_missing", "product attribute requires value", f"{path}.value"))
    status = _status(note.get("status"), f"{path}.status", issues)
    trigger_paths = _string_list(note, "trigger_paths", path, issues)
    product_id = _text(note.get("product_subject_id")) or default_product_id
    if product_id not in product_ids:
        issues.append(_error("market_evidence_compiler_product_missing", "product attribute must target an existing ProductSubject", f"{path}.product_subject_id"))
    attribute_id = _text(note.get("attribute_id")) or _unique_id(attribute_ids, "attr-compiler", name)
    if attribute_id in attribute_ids and has_text(note.get("attribute_id")):
        issues.append(_error("market_evidence_compiler_duplicate_id", "product attribute ID already exists", f"{path}.attribute_id"))
    else:
        attribute_ids.add(attribute_id)
    if issues:
        return
    graph.setdefault("attributes", []).append(
        {
            "attribute_id": attribute_id,
            "product_subject_id": product_id,
            "component_scope": "产品整体",
            "attribute_family": "用户提供产品资料",
            "attribute_name": name,
            "value": note.get("value"),
            "unit": note.get("unit") if has_text(note.get("unit")) else None,
            "status": status,
            "trigger_paths": trigger_paths,
            "evidence_card_ids": [],
        }
    )
    for product in _as_list(graph.get("products")):
        if isinstance(product, dict) and product.get("product_subject_id") == product_id:
            unknowns = _remaining_unknown_attributes(_as_list(product.get("unknown_key_attributes")), name)
            product["unknown_key_attributes"] = unknowns


def _compile_evidence_note(
    graph: dict[str, Any],
    raw: Any,
    index: int,
    sources: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    evidence_ids: set[str],
    row_ids: set[str],
    gap_ids: set[str],
    run: dict[str, Any],
    brief: dict[str, Any],
    issues: list[dict[str, str]],
) -> None:
    path = f"evidence_notes[{index}]"
    note = _validate_keys(raw, EVIDENCE_NOTE_KEYS, path, issues)
    if note is None:
        return
    note_id = _require_string(note, "evidence_note_id", path, issues)
    observation_id = _require_string(note, "observation_id", path, issues)
    field_domain = _require_string(note, "field_domain", path, issues)
    field_name = _require_string(note, "field_name", path, issues)
    _require_string(note, "source_excerpt_quote", path, issues)
    _require_string(note, "applicability_scope", path, issues)
    supports = _string_list(note, "supports", path, issues)
    does_not_support = _string_list(note, "does_not_support", path, issues)
    boundary_rule_ids = _string_list(note, "boundary_rule_ids", path, issues)
    status = _status(note.get("status"), f"{path}.status", issues)
    rows = _target_rows(note, path, issues)
    observation = observations.get(observation_id)
    if observation is None:
        issues.append(_error("market_evidence_compiler_observation_missing", "evidence note must cite an existing Observation", f"{path}.observation_id"))
    elif observation.get("access_status") not in OPENED_ACCESS_STATUSES or not has_text(observation.get("raw_excerpt")):
        issues.append(_error("market_evidence_compiler_observation_not_opened", "evidence note requires an opened Observation with a non-empty verbatim excerpt", f"{path}.observation_id"))
    else:
        quote = _text(note.get("source_excerpt_quote"))
        if quote and quote not in str(observation.get("raw_excerpt")):
            issues.append(_error("market_evidence_compiler_quote_not_in_observation", "source_excerpt_quote must occur verbatim in the cited Observation", f"{path}.source_excerpt_quote"))
    source = sources.get(str(observation.get("source_id"))) if observation else None
    if observation is not None and source is None:
        issues.append(_error("market_evidence_compiler_source_missing", "cited Observation must reference an existing Source", f"{path}.observation_id"))
    if issues:
        return

    evidence_id = _unique_id(evidence_ids, "card", note_id)
    gap_id = None
    gap = note.get("gap")
    if gap is not None:
        gap_note = _validate_keys(gap, GAP_KEYS, f"{path}.gap", issues)
        if gap_note is None:
            return
        missing_item = _require_string(gap_note, "missing_item", f"{path}.gap", issues)
        user_visible_note = _require_string(gap_note, "user_visible_note", f"{path}.gap", issues)
        gap_status = _status(gap_note.get("status"), f"{path}.gap.status", issues, "technical_docs_required")
        if issues:
            return
        gap_id = _text(gap_note.get("gap_id")) or _unique_id(gap_ids, "gap", note_id)
        if gap_id in gap_ids and has_text(gap_note.get("gap_id")):
            issues.append(_error("market_evidence_compiler_duplicate_id", "gap ID already exists", f"{path}.gap.gap_id"))
            return
        gap_ids.add(gap_id)
        graph.setdefault("gaps", []).append(
            {
                "gap_id": gap_id,
                "run_id": run["run_id"],
                "field_domain": _text(gap_note.get("field_domain")) or field_domain,
                "field_name": _text(gap_note.get("field_name")) or field_name,
                "status": gap_status,
                "missing_item": missing_item,
                "requested_from": gap_note.get("requested_from") if has_text(gap_note.get("requested_from")) else None,
                "user_visible_note": user_visible_note,
                "evidence_card_ids": [evidence_id],
            }
        )

    source_date = _text(note.get("source_date")) or "日期未见"
    card = {
        "evidence_card_id": evidence_id,
        "run_id": run["run_id"],
        "brief_version_id": brief["brief_version_id"],
        "producer_skill": "产品市场证据编译器",
        "reviewer_skill": None,
        "field_domain": field_domain,
        "field_name": field_name,
        "current_value": note.get("current_value"),
        "status": status,
        "source_refs": [{"source_id": source["source_id"], "observation_id": observation_id, "relation": "supports", "note": _text(note.get("source_excerpt_quote"))}],
        "source_type": _text(source.get("medium")) or "website",
        "source_locator": _text(observation.get("page_or_dom_locator")) or _text(observation.get("title")) or source["source_id"],
        "source_date": source_date,
        "observed_at": observation["observed_at"],
        "applicability_scope": _text(note.get("applicability_scope")),
        "supports": supports,
        "does_not_support": does_not_support,
        "boundary_rule_ids": boundary_rule_ids,
        "review_status": _text(note.get("review_status")) or "not_reviewed",
    }
    if gap_id:
        card["gap_ids"] = [gap_id]
    if isinstance(note.get("authority_verification_record_ids"), list):
        card["authority_verification_record_ids"] = [str(value) for value in note["authority_verification_record_ids"]]
    if isinstance(note.get("freshness_record_ids"), list):
        card["freshness_record_ids"] = [str(value) for value in note["freshness_record_ids"]]
    graph.setdefault("evidence_cards", []).append(card)

    for row in rows:
        row_id = _unique_id(row_ids, "row", f"{note_id}-{row.get('row_topic')}" if len(rows) > 1 else note_id)
        matrix_row = {
            "matrix_row_id": row_id,
            "sheet_name": row["sheet_name"],
            "row_topic": row["row_topic"],
            "user_visible_cells": row["user_visible_cells"],
            "status": status,
            "evidence_card_ids": [evidence_id],
            "boundary_rule_ids": boundary_rule_ids,
            "internal_refs_hidden": True,
        }
        if gap_id:
            matrix_row["gap_ids"] = [gap_id]
        for key in ("module_key", "row_type", "certification_requirement", "origin_proof_requirement"):
            if key in row:
                matrix_row[key] = row[key]
        for field in ("authority_verification_record_ids", "freshness_record_ids"):
            values = row.get(field) if field in row else note.get(field)
            if isinstance(values, list):
                matrix_row[field] = [str(value) for value in values]
        row_identity = _row_identity(matrix_row)
        existing_row = next(
            (candidate for candidate in _as_list(graph.get("matrix_rows")) if isinstance(candidate, dict) and _row_identity(candidate) == row_identity),
            None,
        )
        if existing_row is None:
            graph.setdefault("matrix_rows", []).append(matrix_row)
        else:
            _append_refs(existing_row, "evidence_card_ids", [evidence_id])
            _append_refs(existing_row, "gap_ids", [gap_id] if gap_id else [])
            _append_refs(existing_row, "boundary_rule_ids", boundary_rule_ids)
            _append_refs(existing_row, "authority_verification_record_ids", [str(value) for value in row.get("authority_verification_record_ids", note.get("authority_verification_record_ids", []))])
            _append_refs(existing_row, "freshness_record_ids", [str(value) for value in row.get("freshness_record_ids", note.get("freshness_record_ids", []))])


def compile_notes(graph: dict[str, Any], notes: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    if graph.get("graph_type") != "ProductMarketAnalysisGraph":
        return None, [_error("market_evidence_compiler_graph_type_invalid", "compiler requires ProductMarketAnalysisGraph", "graph_type")]
    if not isinstance(notes, dict):
        return None, [_error("market_evidence_compiler_notes_invalid", "notes input must be an object", "notes")]
    for key in sorted(set(notes) - NOTE_ROOT_KEYS):
        issues.append(_error("market_evidence_compiler_unknown_field", f"compiler input does not accept {key}", key))
    for field in ("product_attributes", "evidence_notes"):
        if field in notes and not isinstance(notes[field], list):
            issues.append(_error("market_evidence_compiler_list_invalid", f"{field} must be an array", field))
    if issues:
        return None, issues

    compiled = deepcopy(graph)
    runs = [item for item in _as_list(compiled.get("runs")) if isinstance(item, dict)]
    briefs = [item for item in _as_list(compiled.get("briefs")) if isinstance(item, dict)]
    if len(runs) != 1 or len(briefs) != 1:
        return None, [_error("market_evidence_compiler_graph_scope_ambiguous", "compiler currently requires exactly one Run and one MarketAnalysisBrief", "runs/briefs")]
    run, brief = runs[0], briefs[0]
    product_ids = set(_index(compiled.get("products"), "product_subject_id"))
    default_product_id = _text(brief.get("product_subject_id"))
    if default_product_id not in product_ids:
        return None, [_error("market_evidence_compiler_product_missing", "Brief must reference an existing ProductSubject", "briefs[0].product_subject_id")]

    sources = _index(compiled.get("sources"), "source_id")
    observations = _index(compiled.get("observations"), "observation_id")
    attribute_ids = set(_index(compiled.get("attributes"), "attribute_id"))
    evidence_ids = set(_index(compiled.get("evidence_cards"), "evidence_card_id"))
    row_ids = set(_index(compiled.get("matrix_rows"), "matrix_row_id"))
    gap_ids = set(_index(compiled.get("gaps"), "gap_id"))

    for index, raw in enumerate(notes.get("product_attributes", [])):
        _compile_attribute(compiled, raw, index, attribute_ids, product_ids, default_product_id, issues)
    for index, raw in enumerate(notes.get("evidence_notes", [])):
        _compile_evidence_note(compiled, raw, index, sources, observations, evidence_ids, row_ids, gap_ids, run, brief, issues)
    if issues:
        return None, issues

    validation_issues = validate_graph(compiled)
    if validation_issues:
        return None, [
            _error("market_evidence_compiler_output_invalid", item.get("message", "compiled graph failed validation"), item.get("path", "graph"))
            for item in validation_issues
        ]
    return compiled, []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", required=True, help="Existing ProductMarketAnalysisGraph JSON")
    parser.add_argument("--notes", required=True, help="Compact evidence-note JSON")
    parser.add_argument("--output", required=True, help="Compiled ProductMarketAnalysisGraph JSON")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    graph = load_json(args.graph)
    notes = load_json(args.notes)
    compiled, issues = compile_notes(graph, notes)
    result = {
        "ok": not issues,
        "route": "product_outbound_market_analysis_evidence_compile",
        "input_is_not_evidence": True,
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "does_not_promote_status": True,
        "issue_count": len(issues),
        "issues": issues,
    }
    if compiled is not None:
        write_json(args.output, compiled)
        result["output"] = str(args.output)
        result["evidence_card_count"] = len(_as_list(compiled.get("evidence_cards")))
        result["matrix_row_count"] = len(_as_list(compiled.get("matrix_rows")))
        result["attribute_count"] = len(_as_list(compiled.get("attributes")))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif issues:
        for item in issues:
            print(f"[{item.get('code')}] {item.get('message')} ({item.get('path')})")
    else:
        print("Product market evidence compilation passed")
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
