#!/usr/bin/env python3
"""Fast structural precheck for real-business Superleads UAT inputs.

This is deliberately narrower than the formal validators. It does not search,
open sources, mutate a graph, make a business conclusion, or approve delivery.
It catches the input mistakes that repeatedly caused UAT repair loops before a
full validator or product-market compiler is invoked.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _superleads_common import (
    as_list,
    claim_value_is_anchored_in_excerpt,
    contact_literal_is_present,
    has_text,
    normalized_contact_derives_from_literal,
    text_contains,
    text_contains_exact_phrase,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "shared" / "schemas"
RESEARCH_ROUTES = {"bulk_customer_development", "customer_background_research"}
ROUTES = (*sorted(RESEARCH_ROUTES), "product_outbound_market_analysis")
OPENED_ACCESS_STATUSES = {"opened", "captured", "extracted", "rendered"}
MARKET_STATUSES = {
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
MARKET_REVIEW_STATUSES = {"not_reviewed", "passed", "returned", "blocked", "downgraded"}
MARKET_SHEET_NAMES = {
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
MARKET_ROW_TYPES = {
    "overview",
    "product_attribute",
    "trend_signal",
    "market_info",
    "price_reference",
    "seasonality",
    "compliance_requirement",
    "origin_proof_requirement",
    "certification_requirement",
    "destination_requirement",
    "import_tax",
    "export_requirement",
    "logistics_node",
    "external_factor",
    "source_or_gap",
    "other",
}
PREDICATE_ANCHOR_LITERALS = {
    "offers": {"offers", "sells", "provides"},
    "sells": {"sells"},
    "manufactures": {"manufactures"},
    "distributes": {"distributes"},
    "provides": {"provides"},
    "is": {"is"},
    "operates_as": {"operates as"},
    "trades_as": {"trades as"},
    "lists": {"lists"},
    "publishes": {"publishes"},
    "is_located_in": {"located in"},
    "has_address": {"address"},
    "is_registered_as": {"registered as"},
    "is_registered_in": {"registered in"},
    "owns": {"owns"},
    "uses": {"uses"},
    "has_registered": {"registered"},
    "serves_as": {"serves as"},
    "is_owned_by": {"owned by"},
    "is_part_of": {"part of"},
    "holds": {"holds"},
    "is_certified_for": {"certified"},
}


def _issue(code: str, message: str, path: str, *, severity: str = "critical", focus: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "message": message, "path": path, "focus": focus}


def _items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    return [item for item in as_list(payload.get(key)) if isinstance(item, dict)]


def _index(payload: dict[str, Any], key: str, id_field: str) -> dict[str, dict[str, Any]]:
    return {
        str(item[id_field]): item
        for item in _items(payload, key)
        if has_text(item.get(id_field))
    }


def _append(issues: list[dict[str, str]], seen: set[tuple[str, str]], item: dict[str, str]) -> None:
    identity = (item["code"], item["path"])
    if identity not in seen:
        seen.add(identity)
        issues.append(item)


def _contains_enum_error(error: Any) -> bool:
    if getattr(error, "validator", None) in {"enum", "const"}:
        return True
    return any(_contains_enum_error(child) for child in getattr(error, "context", []))


def _schema_precheck(graph: dict[str, Any], schema_name: str) -> list[dict[str, str]]:
    try:
        import jsonschema  # type: ignore
        from jsonschema import RefResolver  # type: ignore
    except Exception as exc:
        return [_issue(
            "uat_precheck_schema_profile_unavailable",
            f"jsonschema is unavailable: {exc}",
            "shared/schemas",
            severity="major",
            focus="enum_values",
        )]
    try:
        schema_path = SCHEMA_DIR / schema_name
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        store: dict[str, Any] = {}
        for path in SCHEMA_DIR.glob("*.schema.json"):
            loaded = json.loads(path.read_text(encoding="utf-8"))
            store[path.as_uri()] = loaded
            if isinstance(loaded.get("$id"), str):
                store[loaded["$id"]] = loaded
        resolver = RefResolver(base_uri=SCHEMA_DIR.as_uri() + "/", referrer=schema, store=store)
        validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    except Exception as exc:
        return [_issue(
            "uat_precheck_schema_profile_unavailable",
            f"schema profile cannot be loaded: {exc}",
            "shared/schemas",
            severity="major",
            focus="enum_values",
        )]
    issues: list[dict[str, str]] = []
    for error in sorted(validator.iter_errors(graph), key=lambda item: list(item.absolute_path)):
        path = "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path).lstrip(".") or "$"
        if _contains_enum_error(error):
            issues.append(_issue(
                "uat_precheck_enum_invalid",
                f"invalid enum value: {error.message}",
                path,
                focus="enum_values",
            ))
        else:
            issues.append(_issue(
                "uat_precheck_schema_shape_invalid",
                f"input shape does not satisfy the graph schema: {error.message}",
                path,
                severity="major",
                focus="schema_shape",
            ))
    return issues


def _research_anchor_issues(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    observations = _index(graph, "observations", "observation_id")
    entities = _index(graph, "entities", "entity_id")
    claims = _index(graph, "claims", "claim_id")
    contact_points = _index(graph, "contact_points", "contact_id")

    for index, evidence in enumerate(_items(graph, "claim_evidence")):
        path = f"claim_evidence[{index}]"
        if evidence.get("relation") != "supports":
            continue
        observation = observations.get(str(evidence.get("observation_id") or ""))
        claim = claims.get(str(evidence.get("claim_id") or ""))
        if observation is None:
            _append(issues, seen, _issue(
                "uat_precheck_claim_observation_missing",
                "supporting ClaimEvidence must reference an existing Observation",
                f"{path}.observation_id",
                focus="source_literal_anchors",
            ))
            continue
        excerpt = observation.get("raw_excerpt")
        if not has_text(excerpt):
            _append(issues, seen, _issue(
                "uat_precheck_claim_observation_excerpt_missing",
                "supporting ClaimEvidence requires a non-empty Observation raw_excerpt",
                f"{path}.observation_id",
                focus="source_literal_anchors",
            ))
            continue
        if claim is not None and not claim_value_is_anchored_in_excerpt(claim, excerpt):
            _append(issues, seen, _issue(
                "uat_precheck_claim_value_not_in_observation",
                "Claim typed_value is not visible in the supporting Observation raw_excerpt",
                f"{path}.observation_id",
                focus="source_literal_anchors",
            ))
        anchors = evidence.get("claim_field_anchors")
        if not isinstance(anchors, dict):
            _append(issues, seen, _issue(
                "uat_precheck_claim_field_anchors_missing",
                "supporting ClaimEvidence must provide field-level source anchors",
                f"{path}.claim_field_anchors",
                focus="source_literal_anchors",
            ))
            continue
        for field in ("subject", "predicate", "claim_type", "typed_value"):
            if not has_text(anchors.get(field)) or not text_contains_exact_phrase(excerpt, anchors.get(field)):
                _append(issues, seen, _issue(
                    "uat_precheck_claim_field_anchor_not_in_observation",
                    f"{field} anchor is not visible in the supporting Observation raw_excerpt",
                    f"{path}.claim_field_anchors.{field}",
                    focus="source_literal_anchors",
                ))
        if claim is not None and str(anchors.get("subject") or "").casefold() != str(claim.get("subject") or "").casefold():
            _append(issues, seen, _issue(
                "uat_precheck_claim_subject_anchor_mismatch",
                "ClaimEvidence subject anchor must equal the Claim subject",
                f"{path}.claim_field_anchors.subject",
                focus="source_literal_anchors",
            ))
        if claim is not None:
            allowed = PREDICATE_ANCHOR_LITERALS.get(str(claim.get("predicate") or ""), set())
            if str(anchors.get("predicate") or "").casefold() not in allowed:
                _append(issues, seen, _issue(
                    "uat_precheck_claim_predicate_anchor_invalid",
                    "ClaimEvidence predicate anchor must use the allowed literal for the Claim predicate",
                    f"{path}.claim_field_anchors.predicate",
                    focus="source_literal_anchors",
                ))

    for index, contact in enumerate(_items(graph, "contact_points")):
        path = f"contact_points[{index}]"
        observation = observations.get(str(contact.get("source_observation_id") or ""))
        if observation is None:
            _append(issues, seen, _issue(
                "uat_precheck_contact_observation_missing",
                "ContactPoint must reference an existing source Observation",
                f"{path}.source_observation_id",
                focus="contact_association",
            ))
            continue
        if not contact_literal_is_present(contact.get("contact_type"), contact.get("source_literal"), observation.get("raw_excerpt")):
            _append(issues, seen, _issue(
                "uat_precheck_contact_literal_not_in_observation",
                "ContactPoint source_literal is not present in the cited Observation raw_excerpt",
                f"{path}.source_literal",
                focus="source_literal_anchors",
            ))
        if not normalized_contact_derives_from_literal(contact.get("contact_type"), contact.get("normalized_value"), contact.get("source_literal")):
            _append(issues, seen, _issue(
                "uat_precheck_contact_normalized_not_derived",
                "ContactPoint normalized_value cannot be derived from source_literal",
                f"{path}.normalized_value",
                focus="source_literal_anchors",
            ))

    for index, claim in enumerate(_items(graph, "contact_claims")):
        path = f"contact_claims[{index}]"
        contact = contact_points.get(str(claim.get("contact_id") or ""))
        source_observation = observations.get(str(contact.get("source_observation_id") or "")) if contact else None
        association = observations.get(str(claim.get("association_observation_id") or ""))
        entity_id = claim.get("entity_id")
        if contact is None:
            _append(issues, seen, _issue(
                "uat_precheck_contact_claim_contact_missing",
                "ContactClaim must reference an existing ContactPoint",
                f"{path}.contact_id",
                focus="contact_association",
            ))
        if association is None:
            _append(issues, seen, _issue(
                "uat_precheck_contact_association_observation_missing",
                "ContactClaim must reference an existing association Observation",
                f"{path}.association_observation_id",
                focus="contact_association",
            ))
            continue
        export_status = claim.get("export_status")
        evidence_text = claim.get("association_evidence_text")
        if export_status in {"ready", "export_with_source_note", "needs_manual_association_review"} and not text_contains(association.get("raw_excerpt"), evidence_text):
            _append(issues, seen, _issue(
                "uat_precheck_contact_association_not_in_observation",
                "ContactClaim association_evidence_text is not present in its association Observation",
                f"{path}.association_evidence_text",
                focus="contact_association",
            ))
        if has_text(entity_id) and str(entity_id) not in entities:
            _append(issues, seen, _issue(
                "uat_precheck_contact_claim_entity_missing",
                "ContactClaim entity_id must resolve to an existing Entity",
                f"{path}.entity_id",
                severity="major",
                focus="contact_association",
            ))
        entity = entities.get(str(entity_id)) if has_text(entity_id) else None
        entity_name = str(entity.get("name") or "").strip() if isinstance(entity, dict) else ""
        if (
            export_status in {"ready", "export_with_source_note"}
            and entity_name
            and not text_contains(evidence_text, entity_name)
        ):
            _append(issues, seen, _issue(
                "uat_precheck_contact_association_entity_name_missing",
                "Exportable ContactClaim association_evidence_text must name its resolved Entity",
                f"{path}.association_evidence_text",
                focus="contact_association",
            ))
        if has_text(entity_id):
            for observation, label in ((source_observation, "source"), (association, "association")):
                if isinstance(observation, dict) and has_text(observation.get("entity_id")) and observation.get("entity_id") != entity_id:
                    _append(issues, seen, _issue(
                        "uat_precheck_contact_entity_mismatch",
                        f"ContactClaim entity_id does not match its {label} Observation entity",
                        f"{path}.entity_id",
                        focus="contact_association",
                    ))
        for field in ("person_name", "job_title", "department"):
            if has_text(claim.get(field)) and not (text_contains(evidence_text, claim.get(field)) or text_contains(association.get("raw_excerpt"), claim.get(field))):
                _append(issues, seen, _issue(
                    "uat_precheck_contact_role_not_in_association",
                    f"ContactClaim {field} is not visible in association evidence",
                    f"{path}.{field}",
                    focus="contact_association",
                ))
    return issues


def _displayed_attribute_value(attribute: dict[str, Any]) -> str:
    value = str(attribute.get("value") if attribute.get("value") is not None else "").strip()
    unit = str(attribute.get("unit") or "").strip()
    if value and unit and value.casefold().endswith(unit.casefold()):
        return value
    return " ".join(part for part in (value, unit) if part)


def _market_projection_issues(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    products = _index(graph, "products", "product_subject_id")
    evidence_cards = _index(graph, "evidence_cards", "evidence_card_id")
    sources = _index(graph, "sources", "source_id")
    observations = _index(graph, "observations", "observation_id")
    product_rows = [
        row for row in _items(graph, "matrix_rows")
        if row.get("sheet_name") == "产品档案与触发项"
    ]

    for index, attribute in enumerate(_items(graph, "attributes")):
        path = f"attributes[{index}]"
        product_id = str(attribute.get("product_subject_id") or "")
        if product_id not in products:
            _append(issues, seen, _issue(
                "uat_precheck_product_attribute_subject_missing",
                "ProductAttribute must reference an existing ProductSubject",
                f"{path}.product_subject_id",
                focus="product_attribute_projection",
            ))
        for card_id in as_list(attribute.get("evidence_card_ids")):
            if str(card_id) not in evidence_cards:
                _append(issues, seen, _issue(
                    "uat_precheck_product_attribute_evidence_missing",
                    "ProductAttribute references a missing EvidenceCard",
                    f"{path}.evidence_card_ids",
                    focus="product_attribute_projection",
                ))
        # The compiler marks user-supplied attributes with this family. Those
        # are the values a UAT must prove are visible in the product-profile
        # sheet. Older source-derived attributes may legitimately support a
        # derived row or a gap without being a standalone visible row.
        if attribute.get("attribute_family") != "用户提供产品资料":
            continue
        name = str(attribute.get("attribute_name") or "").strip()
        expected_value = _displayed_attribute_value(attribute)
        projected = False
        for row in product_rows:
            cells = row.get("user_visible_cells")
            if not isinstance(cells, dict) or str(cells.get("属性") or "").strip() != name:
                continue
            displayed = str(cells.get("当前值") or "").strip()
            if expected_value and expected_value in displayed:
                projected = True
                break
        if name and not projected:
            _append(issues, seen, _issue(
                "uat_precheck_product_attribute_not_projected",
                "ProductAttribute has no matching 产品档案与触发项 MatrixRow with its displayed value",
                path,
                focus="product_attribute_projection",
            ))

    for index, card in enumerate(_items(graph, "evidence_cards")):
        path = f"evidence_cards[{index}]"
        for ref_index, raw_ref in enumerate(as_list(card.get("source_refs"))):
            if not isinstance(raw_ref, dict):
                continue
            ref_path = f"{path}.source_refs[{ref_index}]"
            source_id = raw_ref.get("source_id")
            observation_id = raw_ref.get("observation_id")
            observation = observations.get(str(observation_id or ""))
            if has_text(source_id) and str(source_id) not in sources:
                _append(issues, seen, _issue(
                    "uat_precheck_market_source_missing",
                    "EvidenceCard source_ref references a missing Source",
                    f"{ref_path}.source_id",
                    focus="source_literal_anchors",
                ))
            if has_text(observation_id) and observation is None:
                _append(issues, seen, _issue(
                    "uat_precheck_market_observation_missing",
                    "EvidenceCard source_ref references a missing Observation",
                    f"{ref_path}.observation_id",
                    focus="source_literal_anchors",
                ))
                continue
            if observation is not None and has_text(source_id) and observation.get("source_id") != source_id:
                _append(issues, seen, _issue(
                    "uat_precheck_market_source_observation_mismatch",
                    "EvidenceCard source_ref source_id does not match the cited Observation source_id",
                    ref_path,
                    focus="source_literal_anchors",
                ))
            quote = raw_ref.get("note")
            if observation is not None and has_text(quote) and not text_contains_exact_phrase(observation.get("raw_excerpt"), quote):
                _append(issues, seen, _issue(
                    "uat_precheck_market_card_quote_not_in_observation",
                    "EvidenceCard source_ref note is not visible in the cited Observation raw_excerpt",
                    f"{ref_path}.note",
                    focus="source_literal_anchors",
                ))
    return issues


def _market_notes_issues(graph: dict[str, Any], notes: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    observations = _index(graph, "observations", "observation_id")
    products = _index(graph, "products", "product_subject_id")
    briefs = _items(graph, "briefs")
    default_product_id = str(briefs[0].get("product_subject_id") or "") if briefs else ""

    for index, attribute in enumerate(_items(notes, "product_attributes")):
        path = f"product_attributes[{index}]"
        product_id = str(attribute.get("product_subject_id") or default_product_id)
        if product_id not in products:
            _append(issues, seen, _issue(
                "uat_precheck_note_product_attribute_subject_missing",
                "compact product attribute must target an existing ProductSubject",
                f"{path}.product_subject_id",
                focus="product_attribute_projection",
            ))
        if not has_text(attribute.get("attribute_name")) or attribute.get("value") is None:
            _append(issues, seen, _issue(
                "uat_precheck_note_product_attribute_incomplete",
                "compact product attribute requires attribute_name and value",
                path,
                severity="major",
                focus="product_attribute_projection",
            ))
        status = attribute.get("status")
        if has_text(status) and status not in MARKET_STATUSES:
            _append(issues, seen, _issue(
                "uat_precheck_enum_invalid",
                f"compact product attribute status is not allowed: {status}",
                f"{path}.status",
                focus="enum_values",
            ))

    for collection in ("evidence_notes", "authority_notes"):
        for index, note in enumerate(_items(notes, collection)):
            path = f"{collection}[{index}]"
            observation = observations.get(str(note.get("observation_id") or ""))
            if observation is None:
                _append(issues, seen, _issue(
                    "uat_precheck_market_note_observation_missing",
                    "compact note must reference an existing Observation",
                    f"{path}.observation_id",
                    focus="source_literal_anchors",
                ))
                continue
            if observation.get("access_status") not in OPENED_ACCESS_STATUSES or not has_text(observation.get("raw_excerpt")):
                _append(issues, seen, _issue(
                    "uat_precheck_market_note_observation_not_opened",
                    "compact note requires an opened Observation with a non-empty verbatim excerpt",
                    f"{path}.observation_id",
                    focus="source_literal_anchors",
                ))
            quote = note.get("source_excerpt_quote")
            if not has_text(quote) or not text_contains_exact_phrase(observation.get("raw_excerpt"), quote):
                _append(issues, seen, _issue(
                    "uat_precheck_market_note_quote_not_in_observation",
                    "compact note source_excerpt_quote is not visible in the cited Observation raw_excerpt",
                    f"{path}.source_excerpt_quote",
                    focus="source_literal_anchors",
                ))
            status = note.get("status")
            if has_text(status) and status not in MARKET_STATUSES:
                _append(issues, seen, _issue(
                    "uat_precheck_enum_invalid",
                    f"compact note status is not allowed: {status}",
                    f"{path}.status",
                    focus="enum_values",
                ))
            review_status = note.get("review_status")
            if has_text(review_status) and review_status not in MARKET_REVIEW_STATUSES:
                _append(issues, seen, _issue(
                    "uat_precheck_enum_invalid",
                    f"compact note review_status is not allowed: {review_status}",
                    f"{path}.review_status",
                    focus="enum_values",
                ))
    for index, template in enumerate(_items(notes, "matrix_row_templates")):
        path = f"matrix_row_templates[{index}]"
        sheet_name = template.get("sheet_name")
        if has_text(sheet_name) and sheet_name not in MARKET_SHEET_NAMES:
            _append(issues, seen, _issue(
                "uat_precheck_enum_invalid",
                f"matrix row template sheet_name is not allowed: {sheet_name}",
                f"{path}.sheet_name",
                focus="enum_values",
            ))
        row_type = template.get("row_type")
        if has_text(row_type) and row_type not in MARKET_ROW_TYPES:
            _append(issues, seen, _issue(
                "uat_precheck_enum_invalid",
                f"matrix row template row_type is not allowed: {row_type}",
                f"{path}.row_type",
                focus="enum_values",
            ))
    return issues


def precheck(graph: dict[str, Any], route: str, notes: dict[str, Any] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if route in RESEARCH_ROUTES:
        issues.extend(_schema_precheck(graph, "research-graph.schema.json"))
        issues.extend(_research_anchor_issues(graph))
    else:
        issues.extend(_schema_precheck(graph, "product-market-analysis.schema.json"))
        issues.extend(_market_projection_issues(graph))
        if notes is not None:
            issues.extend(_market_notes_issues(graph, notes))
    seen: set[tuple[str, str]] = set()
    deduplicated: list[dict[str, str]] = []
    for item in issues:
        _append(deduplicated, seen, item)
    return deduplicated


def _load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {label} JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} JSON must be an object")
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", choices=ROUTES, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--notes", type=Path, help="Optional compact evidence notes; valid only for product market analysis.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        graph = _load_object(args.graph, "graph")
        if args.notes and args.route != "product_outbound_market_analysis":
            raise ValueError("--notes is only valid for product_outbound_market_analysis")
        notes = _load_object(args.notes, "compact notes") if args.notes else None
        issues = precheck(graph, args.route, notes)
        result: dict[str, Any] = {
            "ok": not issues,
            "route": args.route,
            "precheck_only": True,
            "does_not_run_formal_validator": True,
            "does_not_search_web": True,
            "does_not_open_sources": True,
            "does_not_mutate_graph": True,
            "focuses": ["source_literal_anchors", "contact_association", "enum_values", "product_attribute_projection"],
            "issue_count": len(issues),
            "issues": issues,
        }
        status = 0 if not issues else 1
    except ValueError as exc:
        result = {"ok": False, "issue_count": 1, "issues": [_issue("uat_precheck_input_invalid", str(exc), "$", focus="schema_shape")]}
        status = 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print(f"UAT input precheck passed for {args.route}")
    else:
        for item in result["issues"]:
            print(f"[{item['code']}] {item['message']} ({item['path']})")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
