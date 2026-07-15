#!/usr/bin/env python3
"""Validate Superleads research graph invariants."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _superleads_common import (
    CLAIM_SUPPORT_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_TYPES,
    ID_FIELDS,
    all_id_maps,
    as_list,
    canonical_contact_user_status,
    claim_value_is_anchored_in_excerpt,
    contact_literal_is_present,
    ensure_list,
    graph_hash,
    has_text,
    is_public_http_url,
    issue,
    load_json,
    normalized_contact_derives_from_literal,
    text_contains,
    text_contains_exact_phrase,
)

STATE_ENUM = {"scoped", "planned", "collecting", "assessed", "under_review", "remediation_required", "remediation_submitted", "re_reviewed", "checked"}
REVIEW_STATUS_ENUM = {"open", "remediation_submitted", "re_reviewed", "verified_fixed", "accepted_with_disclosure", "rejected_with_reviewer_reason"}
DISPOSITION_ENUM = {"重点开发", "推荐跟进", "需人工核查", "暂不建议", "排除"}
CLAIM_EVIDENCE_RELATIONS = {"supports", "contradicts", "contextual"}
EXPORT_STATUS_ENUM = {"ready", "export_with_source_note", "needs_manual_association_review", "hold_no_source", "hold_inferred"}
POSITIVE_DISPOSITIONS = {"重点开发", "推荐跟进"}
BLOCKED_ACCESS = {"blocked", "login_wall", "login-wall", "login_required", "forbidden", "inaccessible", "not_accessed"}
PLAN_REQUIRED_FIELDS = [
    "plan_id",
    "brief_id",
    "query_groups",
    "source_categories",
    "contact_collection_targets",
    "lead_tiering_criteria",
    "claim_evidence_requirements",
    "stop_conditions",
    "downgrade_strategy",
]
CLAIM_TYPE_PREDICATES = {
    "product_match": {"offers", "sells", "manufactures", "distributes", "provides"},
    "company_identity": {"is", "operates_as", "trades_as"},
    "contact_route": {"lists", "publishes", "provides"},
    "location": {"is_located_in", "has_address"},
    "registration": {"is_registered_as", "is_registered_in"},
    "brand_trademark": {"owns", "uses", "has_registered"},
    "channel_role": {"is", "operates_as", "serves_as"},
    "ownership": {"owns", "is_owned_by", "is_part_of"},
    "certification": {"holds", "is_certified_for"},
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
FORMAL_STATUSES = {"standard_development_list", "full_review_package"}


def translated_support_has_original_root(
    obs: dict[str, Any], claim: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]
) -> bool:
    """Trace a translated support to a same-entity, non-translated source root."""
    entity_id = claim.get("entity_id")
    current = obs
    seen: set[str] = set()
    while True:
        observation_id = current.get("observation_id")
        if not has_text(observation_id) or observation_id in seen:
            return False
        seen.add(str(observation_id))
        if current.get("entity_id") != entity_id:
            return False
        if not has_text(current.get("raw_excerpt")) or current.get("access_status") in BLOCKED_ACCESS:
            return False
        source = ids["sources"].get(current.get("source_id"))
        if not isinstance(source, dict) or source.get("medium") == "search_result" or not (is_public_http_url(source.get("canonical_url")) or is_public_http_url(source.get("final_url"))):
            return False
        if current.get("capability") not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES:
            return False
        status = current.get("translation_status")
        if status in {"original", "not_translated"}:
            return True
        if not has_text(current.get("derived_from_observation_id")):
            return False
        origin = ids["observations"].get(current.get("derived_from_observation_id"))
        if not isinstance(origin, dict):
            return False
        current = origin


def _run_allows_delivery_status(run: dict[str, Any], brief: dict[str, Any] | None, status: Any) -> bool:
    if status == "initial_lead_list":
        return True
    if status not in FORMAL_STATUSES or run.get("status") != "checked":
        return False
    mode = run.get("review_mode")
    if status == "standard_development_list":
        return mode in {"independent", "self_review_fallback"}
    return mode == "independent" and isinstance(brief, dict) and brief.get("evidence_depth") == "full_review"


def _require_id(item: dict[str, Any], field: str, key: str, index: int, issues: list[dict[str, str]]) -> None:
    if not has_text(item.get(field)):
        issues.append(issue("critical", "missing_id", f"{key}[{index}] lacks {field}", f"{key}[{index}].{field}"))


def _schema_validation_issues(graph: dict[str, Any]) -> list[dict[str, str]]:
    """Run the repository JSON Schema profile when jsonschema is available.

    The deterministic checks below remain the source of truth for business
    invariants.  This schema pass catches malformed object shapes such as a
    Plan missing required fields before they can pass through audit/export.
    """
    try:
        import jsonschema  # type: ignore
        from jsonschema import RefResolver  # type: ignore
    except Exception:
        return [issue("major", "schema_profile_unavailable", "jsonschema is unavailable; schema profile cannot be verified", "shared/schemas")]
    schema_dir = Path(__file__).resolve().parents[1] / "shared" / "schemas"
    schema_path = schema_dir / "research-graph.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        store: dict[str, Any] = {}
        for item in schema_dir.glob("*.schema.json"):
            loaded = json.loads(item.read_text(encoding="utf-8"))
            store[item.as_uri()] = loaded
            store[(schema_dir / item.name).as_uri()] = loaded
            if has_text(loaded.get("$id")):
                store[str(loaded["$id"])] = loaded
        resolver = RefResolver(base_uri=schema_dir.as_uri() + "/", referrer=schema, store=store)
        validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    except Exception as exc:
        return [issue("major", "schema_profile_unavailable", f"Research graph schema profile could not be loaded: {exc}", "shared/schemas")]
    try:
        issues: list[dict[str, str]] = []
        for err in sorted(validator.iter_errors(graph), key=lambda e: list(e.absolute_path)):
            path = "".join(f"[{p}]" if isinstance(p, int) else f".{p}" for p in err.absolute_path).lstrip(".")
            issues.append(issue("major", "schema_validation_failed", err.message, path or "$"))
        return issues
    except Exception as exc:
        return [issue("major", "schema_validation_error", f"Research graph schema validation failed to execute: {exc}", "$")]


def validate_graph(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_schema_validation_issues(graph))
    ids = all_id_maps(graph)
    current_hash = graph_hash(graph)
    required_ids = ID_FIELDS
    seen_ids: dict[str, str] = {}
    for key, field in required_ids.items():
        for idx, item in enumerate(ensure_list(graph, key)):
            if not isinstance(item, dict):
                issues.append(issue("critical", "invalid_item", f"{key}[{idx}] is not an object", f"{key}[{idx}]")); continue
            _require_id(item, field, key, idx, issues)
            raw_id = item.get(field)
            if has_text(raw_id):
                if raw_id in seen_ids:
                    issues.append(issue("critical", "duplicate_global_id", f"ID {raw_id} appears in both {seen_ids[raw_id]} and {key}[{idx}]", f"{key}[{idx}].{field}"))
                else:
                    seen_ids[str(raw_id)] = f"{key}[{idx}]"

    for idx, run in enumerate(ensure_list(graph, "runs")):
        status = run.get("status") if isinstance(run, dict) else None
        if status is not None and status not in STATE_ENUM:
            issues.append(issue("major", "invalid_run_status", f"Run status is invalid: {status}", f"runs[{idx}].status"))
        if isinstance(run, dict):
            if status in {"initial_lead_list", "standard_development_list", "full_review_package"}:
                issues.append(issue("major", "run_status_is_delivery_status", f"Run status must not be a delivery status: {status}", f"runs[{idx}].status"))
            if "delivery_status" in run:
                issues.append(issue("major", "run_contains_delivery_status", "Run must not carry delivery_status; use Audit or DeliveryManifest", f"runs[{idx}].delivery_status"))
            brief_id = run.get("brief_id")
            plan_id = run.get("plan_id")
            if brief_id and brief_id not in ids["briefs"]:
                issues.append(issue("major", "run_brief_missing", f"Run references missing Brief {brief_id}", f"runs[{idx}].brief_id"))
            if plan_id and plan_id not in ids["plans"]:
                issues.append(issue("major", "run_plan_missing", f"Run references missing Plan {plan_id}", f"runs[{idx}].plan_id"))

    for idx, obs in enumerate(ensure_list(graph, "observations")):
        if not isinstance(obs, dict): continue
        sid = obs.get("source_id")
        if sid not in ids["sources"]:
            issues.append(issue("critical", "observation_source_missing", f"Observation {obs.get('observation_id')} references missing Source {sid}", f"observations[{idx}].source_id"))
        cand = obs.get("candidate_id")
        if cand and cand not in ids["candidates"]:
            issues.append(issue("major", "observation_candidate_missing", f"Observation references missing Candidate {cand}", f"observations[{idx}].candidate_id"))
        ent = obs.get("entity_id")
        if ent and ent not in ids["entities"]:
            issues.append(issue("major", "observation_entity_missing", f"Observation references missing Entity {ent}", f"observations[{idx}].entity_id"))

    for idx, source in enumerate(ensure_list(graph, "sources")):
        if not isinstance(source, dict): continue
        for field in ("publisher_relation", "provenance", "medium", "access_boundary"):
            if not has_text(source.get(field)):
                issues.append(issue("major", "source_missing_required_context", f"Source {source.get('source_id')} lacks {field}", f"sources[{idx}].{field}"))

    # New customer development requires product/service plus at least one scope axis.
    # Single-company analysis, existing-table enrichment, and material/list extraction
    # are allowed to proceed without that pair because the material itself is the target.
    no_product_required_modes = {"single_company_analysis", "existing_table_enrichment", "material_list_extraction"}
    for idx, brief in enumerate(ensure_list(graph, "briefs")):
        if not isinstance(brief, dict): continue
        mode = brief.get("task_mode")
        if mode not in no_product_required_modes and mode != "unknown":
            if not has_text(brief.get("product_or_service")):
                issues.append(issue("major", "brief_missing_product_or_service", "New customer development Brief lacks product_or_service", f"briefs[{idx}].product_or_service"))
            if not as_list(brief.get("scope_axis")):
                issues.append(issue("major", "brief_missing_scope_axis", "New customer development Brief lacks scope_axis", f"briefs[{idx}].scope_axis"))

    for idx, plan in enumerate(ensure_list(graph, "plans")):
        if not isinstance(plan, dict): continue
        for field in PLAN_REQUIRED_FIELDS:
            value = plan.get(field)
            if not has_text(value) and not as_list(value) and not isinstance(value, dict):
                issues.append(issue("major", "plan_missing_required_field", f"Plan {plan.get('plan_id')} lacks {field}", f"plans[{idx}].{field}"))
        if plan.get("brief_id") not in ids["briefs"]:
            issues.append(issue("major", "plan_brief_missing", f"Plan {plan.get('plan_id')} references missing Brief {plan.get('brief_id')}", f"plans[{idx}].brief_id"))

    evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
    supporting_evidence_by_claim: dict[str, list[dict[str, Any]]] = {}
    for idx, ce in enumerate(ensure_list(graph, "claim_evidence")):
        if not isinstance(ce, dict): continue
        claim_id, obs_id, relation = ce.get("claim_id"), ce.get("observation_id"), ce.get("relation")
        if claim_id not in ids["claims"]:
            issues.append(issue("critical", "claim_evidence_claim_missing", f"ClaimEvidence {ce.get('claim_evidence_id')} references missing Claim {claim_id}", f"claim_evidence[{idx}].claim_id"))
        else:
            evidence_by_claim.setdefault(claim_id, []).append(ce)
            if relation == "supports":
                supporting_evidence_by_claim.setdefault(claim_id, []).append(ce)
        if obs_id not in ids["observations"]:
            issues.append(issue("critical", "claim_evidence_observation_missing", f"ClaimEvidence {ce.get('claim_evidence_id')} references missing Observation {obs_id}", f"claim_evidence[{idx}].observation_id"))
        if relation not in CLAIM_EVIDENCE_RELATIONS:
            issues.append(issue("major", "invalid_claim_evidence_relation", f"Invalid ClaimEvidence relation: {relation}", f"claim_evidence[{idx}].relation"))
        for field in ("directness", "source_authority", "independence_group", "freshness", "excerpt_pointer"):
            if not has_text(ce.get(field)):
                issues.append(issue("major", "claim_evidence_missing_required_context", f"ClaimEvidence {ce.get('claim_evidence_id')} lacks {field}", f"claim_evidence[{idx}].{field}"))
        obs = ids["observations"].get(obs_id)
        if relation == "supports" and isinstance(obs, dict):
            claim = ids["claims"].get(claim_id)
            if isinstance(claim, dict) and obs.get("entity_id") != claim.get("entity_id"):
                issues.append(issue("critical", "claim_evidence_entity_mismatch", f"ClaimEvidence {ce.get('claim_evidence_id')} must use an Observation resolved to Claim Entity {claim.get('entity_id')}", f"claim_evidence[{idx}].observation_id"))
            if not has_text(obs.get("raw_excerpt")):
                issues.append(issue("critical", "supporting_observation_without_raw_excerpt", f"ClaimEvidence {ce.get('claim_evidence_id')} supports Claim without a non-empty Observation raw_excerpt", f"claim_evidence[{idx}].observation_id"))
            source = ids["sources"].get(obs.get("source_id"))
            medium = source.get("medium") if isinstance(source, dict) else None
            capability = obs.get("capability")
            if capability not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES or medium == "search_result":
                issues.append(issue("critical", "capability_not_allowed_to_support_claim", f"{capability or medium} cannot support a formal Claim", f"claim_evidence[{idx}]"))
            if not isinstance(source, dict) or not (is_public_http_url(source.get("canonical_url")) or is_public_http_url(source.get("final_url"))):
                issues.append(issue("critical", "claim_support_source_url_invalid", "ClaimEvidence support requires a public http/https Source URL", f"claim_evidence[{idx}].observation_id"))
            if obs.get("access_status") in BLOCKED_ACCESS:
                issues.append(issue("critical", "blocked_observation_supports_claim", "Blocked/login-wall/inaccessible Observation supports Claim", f"claim_evidence[{idx}]"))
            ts = obs.get("translation_status")
            if isinstance(claim, dict) and not claim_value_is_anchored_in_excerpt(claim, obs.get("raw_excerpt")):
                issues.append(issue("critical", "claim_value_not_anchored_in_observation", f"ClaimEvidence {ce.get('claim_evidence_id')} does not anchor Claim typed_value in its Observation raw_excerpt", f"claim_evidence[{idx}].observation_id"))
            if isinstance(claim, dict):
                anchors = ce.get("claim_field_anchors")
                if not isinstance(anchors, dict):
                    issues.append(issue("critical", "claim_field_anchors_missing", "ClaimEvidence supports a Claim without field-level anchors", f"claim_evidence[{idx}].claim_field_anchors"))
                else:
                    for field in ("subject", "predicate", "claim_type", "typed_value"):
                        if not has_text(anchors.get(field)) or not text_contains_exact_phrase(obs.get("raw_excerpt"), anchors.get(field)):
                            issues.append(issue("critical", "claim_field_anchor_not_in_observation", f"ClaimEvidence {ce.get('claim_evidence_id')} lacks a valid {field} anchor in Observation raw_excerpt", f"claim_evidence[{idx}].claim_field_anchors.{field}"))
                    if str(anchors.get("subject") or "").casefold() != str(claim.get("subject") or "").casefold():
                        issues.append(issue("critical", "claim_subject_anchor_mismatch", "ClaimEvidence subject anchor must equal Claim subject", f"claim_evidence[{idx}].claim_field_anchors.subject"))
                    predicate_literals = PREDICATE_ANCHOR_LITERALS.get(str(claim.get("predicate") or ""), set())
                    if str(anchors.get("predicate") or "").casefold() not in predicate_literals:
                        issues.append(issue("critical", "claim_predicate_anchor_mismatch", "ClaimEvidence predicate anchor must be a permitted literal for the Claim predicate", f"claim_evidence[{idx}].claim_field_anchors.predicate"))
                if ts not in {"original", "not_translated"} and not translated_support_has_original_root(obs, claim, ids):
                    issues.append(issue("critical", "translated_support_without_original_root", "Translated Observation supports Claim without a same-entity original source root", f"claim_evidence[{idx}].observation_id"))

    for idx, claim in enumerate(ensure_list(graph, "claims")):
        if not isinstance(claim, dict): continue
        claim_id, ent = claim.get("claim_id"), claim.get("entity_id")
        if str(claim.get("claim_type") or "").casefold() in {"hypothesis", "business_hypothesis", "outreach_angle"}:
            issues.append(issue("critical", "hypothesis_written_as_claim", f"Claim {claim_id} appears to encode a Hypothesis as a Claim", f"claims[{idx}].claim_type"))
        if str(claim.get("predicate") or "").casefold() in {"may_buy", "likely_buyer", "probably_needs", "recommended_outreach"}:
            issues.append(issue("critical", "hypothesis_predicate_written_as_claim", f"Claim {claim_id} uses a hypothesis-style predicate", f"claims[{idx}].predicate"))
        if ent not in ids["entities"]:
            issues.append(issue("critical", "claim_entity_missing", f"Claim {claim_id} references missing Entity {ent}", f"claims[{idx}].entity_id"))
        else:
            entity = ids["entities"][ent]
            entity_names = {str(entity.get(field)).casefold() for field in ("name", "legal_name") if has_text(entity.get(field))}
            if not entity_names or str(claim.get("subject") or "").casefold() not in entity_names:
                issues.append(issue("critical", "claim_subject_not_resolved_entity", f"Claim {claim_id} subject must match its resolved Entity name", f"claims[{idx}].subject"))
        allowed_predicates = CLAIM_TYPE_PREDICATES.get(str(claim.get("claim_type") or ""))
        if not allowed_predicates:
            issues.append(issue("critical", "claim_type_not_allowed", f"Claim {claim_id} uses unsupported claim_type {claim.get('claim_type')}", f"claims[{idx}].claim_type"))
        elif str(claim.get("predicate") or "") not in allowed_predicates:
            issues.append(issue("critical", "claim_predicate_not_allowed_for_type", f"Claim {claim_id} predicate is not allowed for its claim_type", f"claims[{idx}].predicate"))
        if claim_id not in evidence_by_claim:
            issues.append(issue("critical", "claim_without_evidence", f"Claim {claim_id} has no ClaimEvidence", f"claims[{idx}]"))
        if claim_id not in supporting_evidence_by_claim:
            issues.append(issue("critical", "claim_without_supporting_evidence", f"Claim {claim_id} has no supporting ClaimEvidence", f"claims[{idx}]"))

    for idx, cp in enumerate(ensure_list(graph, "contact_points")):
        if not isinstance(cp, dict): continue
        obs_id = cp.get("source_observation_id")
        if obs_id and obs_id not in ids["observations"]:
            issues.append(issue("critical", "contact_point_observation_missing", f"ContactPoint {cp.get('contact_id')} references missing Observation {obs_id}", f"contact_points[{idx}].source_observation_id"))
        obs = ids["observations"].get(obs_id)
        if isinstance(obs, dict):
            if not contact_literal_is_present(cp.get("contact_type"), cp.get("source_literal"), obs.get("raw_excerpt")):
                issues.append(issue("critical", "contact_literal_not_in_observation", f"ContactPoint {cp.get('contact_id')} source_literal is not present in cited Observation raw_excerpt", f"contact_points[{idx}].source_literal"))
            if not normalized_contact_derives_from_literal(cp.get("contact_type"), cp.get("normalized_value"), cp.get("source_literal")):
                issues.append(issue("critical", "contact_normalized_not_derived", f"ContactPoint {cp.get('contact_id')} normalized_value is not derivable from source_literal", f"contact_points[{idx}].normalized_value"))
        if has_text(cp.get("source_type")) and str(cp.get("source_type")).casefold() not in CONTACT_SOURCE_ALLOWED_TYPES:
            issues.append(issue("critical", "contact_source_type_not_allowed", f"ContactPoint source_type is not permitted: {cp.get('source_type')}", f"contact_points[{idx}].source_type"))

    for idx, cc in enumerate(ensure_list(graph, "contact_claims")):
        if not isinstance(cc, dict): continue
        if cc.get("contact_id") not in ids["contact_points"]:
            issues.append(issue("critical", "contact_claim_contact_missing", f"ContactClaim {cc.get('contact_claim_id')} references missing ContactPoint {cc.get('contact_id')}", f"contact_claims[{idx}].contact_id"))
        if cc.get("association_observation_id") not in ids["observations"]:
            issues.append(issue("critical", "contact_claim_observation_missing", f"ContactClaim {cc.get('contact_claim_id')} references missing association Observation {cc.get('association_observation_id')}", f"contact_claims[{idx}].association_observation_id"))
        ent = cc.get("entity_id")
        if ent and ent not in ids["entities"]:
            issues.append(issue("major", "contact_claim_entity_missing", f"ContactClaim references missing Entity {ent}", f"contact_claims[{idx}].entity_id"))
        for ceid in as_list(cc.get("association_claim_evidence_ids")):
            if ceid not in ids["claim_evidence"]:
                issues.append(issue("major", "contact_claim_evidence_missing", f"ContactClaim references missing ClaimEvidence {ceid}", f"contact_claims[{idx}].association_claim_evidence_ids"))
        export_status = cc.get("export_status")
        if export_status not in EXPORT_STATUS_ENUM:
            issues.append(issue("major", "invalid_contact_export_status", f"Invalid ContactClaim export_status: {export_status}", f"contact_claims[{idx}].export_status"))
        if "user_status" in cc and cc.get("user_status") != canonical_contact_user_status(export_status):
            issues.append(issue("critical", "contact_user_status_mismatch", f"ContactClaim user_status must be derived from export_status {export_status}", f"contact_claims[{idx}].user_status"))
        if export_status == "ready" and not has_text(cc.get("association_evidence_text")):
            issues.append(issue("critical", "ready_contact_without_association_text", "ready ContactClaim lacks association_evidence_text", f"contact_claims[{idx}].association_evidence_text"))
        cp = ids["contact_points"].get(cc.get("contact_id"))
        assoc_obs = ids["observations"].get(cc.get("association_observation_id"))
        source_obs = ids["observations"].get(cp.get("source_observation_id")) if isinstance(cp, dict) else None
        formal_contact_export = export_status in {"ready", "export_with_source_note"}
        if formal_contact_export and not has_text(cc.get("entity_id")):
            issues.append(issue("critical", "exportable_contact_without_resolved_entity", "Exportable ContactClaim must resolve to an Entity; person_id alone is insufficient", f"contact_claims[{idx}].entity_id"))
        if export_status in {"ready", "export_with_source_note", "needs_manual_association_review"}:
            for contact_obs, label in ((source_obs, "source"), (assoc_obs, "association")):
                if not isinstance(contact_obs, dict) or contact_obs.get("capability") not in CONTACT_SOURCE_ALLOWED_CAPABILITIES:
                    issues.append(issue("critical", "contact_capability_not_allowed", f"ContactClaim {cc.get('contact_claim_id')} uses non-permitted {label} capability", f"contact_claims[{idx}]"))
            if isinstance(assoc_obs, dict) and not text_contains(assoc_obs.get("raw_excerpt"), cc.get("association_evidence_text")):
                issues.append(issue("critical", "association_evidence_not_in_observation", f"ContactClaim {cc.get('contact_claim_id')} association_evidence_text is not present in cited Observation", f"contact_claims[{idx}].association_evidence_text"))
        if formal_contact_export:
            entity = ids["entities"].get(ent)
            entity_names = {str(entity.get(field)) for field in ("name", "legal_name") if isinstance(entity, dict) and has_text(entity.get(field))}
            if not isinstance(source_obs, dict) or source_obs.get("entity_id") != ent:
                issues.append(issue("critical", "exportable_contact_source_entity_mismatch", "Exportable ContactPoint source Observation must resolve to the ContactClaim Entity", f"contact_claims[{idx}].entity_id"))
            if not isinstance(assoc_obs, dict) or assoc_obs.get("entity_id") != ent:
                issues.append(issue("critical", "exportable_contact_association_entity_mismatch", "Exportable ContactClaim association Observation must resolve to the ContactClaim Entity", f"contact_claims[{idx}].entity_id"))
            if not any(text_contains_exact_phrase(cc.get("association_evidence_text"), name) for name in entity_names):
                issues.append(issue("critical", "exportable_contact_association_missing_entity_name", "Exportable ContactClaim association evidence must name its resolved Entity", f"contact_claims[{idx}].association_evidence_text"))
            for other_id, other_entity in ids["entities"].items():
                if other_id == ent or not isinstance(other_entity, dict):
                    continue
                for field in ("name", "legal_name"):
                    other_name = other_entity.get(field)
                    if has_text(other_name) and text_contains_exact_phrase(cc.get("association_evidence_text"), other_name):
                        issues.append(issue("critical", "exportable_contact_association_mentions_other_entity", "Exportable ContactClaim association evidence names another Entity", f"contact_claims[{idx}].association_evidence_text"))
        # Entity mismatch is unsafe even for non-ready contacts.  Keep such
        # records unassigned instead of binding them to the customer row.
        if ent and isinstance(source_obs, dict) and source_obs.get("entity_id") and source_obs.get("entity_id") != ent:
            issues.append(issue("critical", "contact_source_entity_mismatch", f"ContactPoint source Observation entity {source_obs.get('entity_id')} does not match ContactClaim entity {ent}", f"contact_claims[{idx}].entity_id"))
        if ent and isinstance(assoc_obs, dict) and assoc_obs.get("entity_id") and assoc_obs.get("entity_id") != ent:
            issues.append(issue("critical", "contact_association_entity_mismatch", f"ContactClaim association Observation entity {assoc_obs.get('entity_id')} does not match ContactClaim entity {ent}", f"contact_claims[{idx}].entity_id"))
        evidence_text = cc.get("association_evidence_text")
        for field, code in (("person_name", "person_name_not_in_evidence"), ("job_title", "job_title_not_in_evidence"), ("department", "department_not_in_evidence")):
            value = cc.get(field)
            if has_text(value) and not (text_contains(evidence_text, value) or (isinstance(assoc_obs, dict) and text_contains(assoc_obs.get("raw_excerpt"), value))):
                issues.append(issue("critical", code, f"ContactClaim {field} is not present in association evidence", f"contact_claims[{idx}].{field}"))

    for idx, lead in enumerate(ensure_list(graph, "unassigned_contact_leads")):
        if not isinstance(lead, dict): continue
        contact_id = lead.get("contact_id")
        if contact_id not in ids["contact_points"]:
            issues.append(issue("major", "unassigned_contact_missing_contact_point", f"UnassignedContactLead references missing ContactPoint {contact_id}", f"unassigned_contact_leads[{idx}].contact_id"))

    for idx, rel in enumerate(ensure_list(graph, "entity_relationships")):
        if not isinstance(rel, dict): continue
        endpoints = [rel.get(field) for field in ("source_entity_id", "from_entity_id", "parent_entity_id", "target_entity_id", "to_entity_id", "child_entity_id") if has_text(rel.get(field))]
        if len(endpoints) < 2:
            issues.append(issue("major", "entity_relationship_missing_endpoints", "EntityRelationship requires two resolved Entity endpoints", f"entity_relationships[{idx}]"))
        if not as_list(rel.get("evidence_claim_ids")) and not as_list(rel.get("evidence_observation_ids")):
            issues.append(issue("major", "entity_relationship_without_evidence", "EntityRelationship requires Claim or Observation evidence", f"entity_relationships[{idx}]"))
        for field in ("source_entity_id", "from_entity_id", "parent_entity_id", "target_entity_id", "to_entity_id", "child_entity_id"):
            if rel.get(field) and rel.get(field) not in ids["entities"]:
                issues.append(issue("major", "entity_relationship_endpoint_missing", f"EntityRelationship references missing Entity {rel.get(field)}", f"entity_relationships[{idx}].{field}"))
        endpoint_ids = set(endpoints)
        for claim_id in as_list(rel.get("evidence_claim_ids")):
            claim = ids["claims"].get(claim_id)
            if not isinstance(claim, dict):
                issues.append(issue("critical", "entity_relationship_claim_evidence_missing", f"EntityRelationship references missing Claim {claim_id}", f"entity_relationships[{idx}].evidence_claim_ids"))
            elif claim.get("entity_id") not in endpoint_ids:
                issues.append(issue("critical", "entity_relationship_claim_evidence_not_endpoint", "EntityRelationship Claim evidence must belong to an endpoint Entity", f"entity_relationships[{idx}].evidence_claim_ids"))
        for observation_id in as_list(rel.get("evidence_observation_ids")):
            observation = ids["observations"].get(observation_id)
            if not isinstance(observation, dict):
                issues.append(issue("critical", "entity_relationship_observation_evidence_missing", f"EntityRelationship references missing Observation {observation_id}", f"entity_relationships[{idx}].evidence_observation_ids"))
            elif observation.get("entity_id") not in endpoint_ids:
                issues.append(issue("critical", "entity_relationship_observation_evidence_not_endpoint", "EntityRelationship Observation evidence must belong to an endpoint Entity", f"entity_relationships[{idx}].evidence_observation_ids"))

    for idx, hyp in enumerate(ensure_list(graph, "hypotheses")):
        if not isinstance(hyp, dict): continue
        basis = as_list(hyp.get("basis_claim_ids"))
        if not basis:
            issues.append(issue("major", "hypothesis_without_basis_claims", f"Hypothesis {hyp.get('hypothesis_id')} lacks basis_claim_ids", f"hypotheses[{idx}].basis_claim_ids"))
        for cid in basis:
            if cid not in ids["claims"]:
                issues.append(issue("critical", "hypothesis_basis_claim_missing", f"Hypothesis references missing Claim {cid}", f"hypotheses[{idx}].basis_claim_ids"))
        for ccid in as_list(hyp.get("basis_contact_claim_ids")):
            if ccid not in ids["contact_claims"]:
                issues.append(issue("major", "hypothesis_contact_claim_missing", f"Hypothesis references missing ContactClaim {ccid}", f"hypotheses[{idx}].basis_contact_claim_ids"))

    for idx, assessment in enumerate(ensure_list(graph, "assessments")):
        if not isinstance(assessment, dict): continue
        for forbidden in ("candidate_id", "candidate_ids", "basis_candidate_ids"):
            if forbidden in assessment:
                issues.append(issue("critical", "candidate_directly_in_assessment", f"Assessment must not reference Candidate via {forbidden}", f"assessments[{idx}].{forbidden}"))
        if assessment.get("disposition") not in DISPOSITION_ENUM:
            issues.append(issue("major", "invalid_assessment_disposition", f"Invalid Assessment disposition: {assessment.get('disposition')}", f"assessments[{idx}].disposition"))
        if assessment.get("entity_id") not in ids["entities"]:
            issues.append(issue("critical", "assessment_entity_missing", f"Assessment references missing Entity {assessment.get('entity_id')}", f"assessments[{idx}].entity_id"))
        if assessment.get("brief_id") not in ids["briefs"]:
            issues.append(issue("major", "assessment_brief_missing", f"Assessment references missing Brief {assessment.get('brief_id')}", f"assessments[{idx}].brief_id"))
        run = ids["runs"].get(assessment.get("run_id"))
        if not isinstance(run, dict):
            issues.append(issue("critical", "assessment_run_missing", f"Assessment references missing Run {assessment.get('run_id')}", f"assessments[{idx}].run_id"))
        elif run.get("brief_id") != assessment.get("brief_id"):
            issues.append(issue("major", "assessment_run_brief_mismatch", "Assessment Brief must match its Run Brief", f"assessments[{idx}].run_id"))
        basis_claim_ids = as_list(assessment.get("basis_claim_ids"))
        rationale = assessment.get("rationale_structured")
        if not isinstance(rationale, dict) or as_list(rationale.get("basis_claim_ids")) != basis_claim_ids:
            issues.append(issue("critical", "assessment_rationale_basis_mismatch", "Assessment rationale_structured must contain only the same basis_claim_ids", f"assessments[{idx}].rationale_structured"))
        if assessment.get("disposition") in POSITIVE_DISPOSITIONS and not basis_claim_ids:
            issues.append(issue("critical", "positive_assessment_without_basis_claims", f"Assessment {assessment.get('assessment_id')} has positive disposition without basis_claim_ids", f"assessments[{idx}].basis_claim_ids"))
        for cid in as_list(assessment.get("basis_claim_ids")):
            if cid not in ids["claims"]:
                code = "assessment_uses_hypothesis_as_basis" if cid in ids["hypotheses"] else "assessment_basis_claim_missing"
                issues.append(issue("critical", code, f"Assessment basis_claim_ids references non-Claim {cid}", f"assessments[{idx}].basis_claim_ids"))
                continue
            claim = ids["claims"].get(cid)
            if isinstance(claim, dict) and claim.get("entity_id") != assessment.get("entity_id"):
                issues.append(issue("critical", "assessment_basis_claim_entity_mismatch", f"Assessment {assessment.get('assessment_id')} uses Claim {cid} from another Entity", f"assessments[{idx}].basis_claim_ids"))
            supports = supporting_evidence_by_claim.get(cid, [])
            if not supports:
                issues.append(issue("critical", "assessment_basis_claim_without_support", f"Assessment basis Claim {cid} has no supporting evidence", f"assessments[{idx}].basis_claim_ids"))
        for hid in as_list(assessment.get("related_hypothesis_ids_for_outreach")):
            if hid not in ids["hypotheses"]:
                issues.append(issue("minor", "assessment_related_hypothesis_missing", f"Assessment outreach hypothesis is missing: {hid}", f"assessments[{idx}].related_hypothesis_ids_for_outreach"))

    for idx, finding in enumerate(ensure_list(graph, "review_findings")):
        if not isinstance(finding, dict): continue
        if finding.get("status") not in REVIEW_STATUS_ENUM:
            issues.append(issue("major", "invalid_review_finding_status", f"Invalid ReviewFinding status: {finding.get('status')}", f"review_findings[{idx}].status"))
        if finding.get("severity") not in {"critical", "major", "minor"}:
            issues.append(issue("major", "invalid_review_finding_severity", f"Invalid ReviewFinding severity: {finding.get('severity')}", f"review_findings[{idx}].severity"))

    for idx, audit in enumerate(ensure_list(graph, "audits")):
        if not isinstance(audit, dict): continue
        for field in ("audited_at", "research_graph_hash", "audit_graph_hash", "audit_status", "delivery_status", "allowed_delivery_statuses", "ok", "issue_count", "issues"):
            if field not in audit:
                issues.append(issue("major", "audit_missing_required_field", f"Audit {audit.get('audit_id')} lacks {field}", f"audits[{idx}].{field}"))
        if audit.get("audit_status") not in {None, "passed", "failed"}:
            issues.append(issue("major", "invalid_audit_status", f"Invalid Audit audit_status: {audit.get('audit_status')}", f"audits[{idx}].audit_status"))
        if audit.get("delivery_status") not in {None, "needs_correction", "initial_lead_list", "standard_development_list", "full_review_package"}:
            issues.append(issue("major", "invalid_audit_delivery_status", f"Invalid Audit delivery_status: {audit.get('delivery_status')}", f"audits[{idx}].delivery_status"))
        if audit.get("research_graph_hash") and audit.get("research_graph_hash") != current_hash:
            issues.append(issue("major", "stale_audit_research_graph_hash", "Audit research_graph_hash does not match current graph hash", f"audits[{idx}].research_graph_hash"))
        if audit.get("audit_graph_hash") and audit.get("audit_graph_hash") != current_hash:
            issues.append(issue("major", "stale_audit_graph_hash", "Audit audit_graph_hash does not match current graph hash", f"audits[{idx}].audit_graph_hash"))

    for idx, manifest in enumerate(ensure_list(graph, "delivery_manifests")):
        if not isinstance(manifest, dict): continue
        for field, collection in (("run_id", "runs"), ("brief_id", "briefs"), ("plan_id", "plans"), ("audit_id", "audits")):
            raw = manifest.get(field)
            if not has_text(raw):
                issues.append(issue("major", "manifest_missing_reference", f"DeliveryManifest lacks non-empty {field}", f"delivery_manifests[{idx}].{field}"))
            elif raw not in ids[collection]:
                issues.append(issue("major", "manifest_reference_missing", f"DeliveryManifest references missing {collection[:-1]} {raw}", f"delivery_manifests[{idx}].{field}"))
        if not has_text(manifest.get("review_cycle_id")):
            issues.append(issue("major", "manifest_missing_review_cycle_id", "DeliveryManifest lacks non-empty review_cycle_id", f"delivery_manifests[{idx}].review_cycle_id"))
        for field in ("audit_graph_hash", "research_graph_hash"):
            if not has_text(manifest.get(field)):
                issues.append(issue("major", "manifest_missing_hash", f"DeliveryManifest lacks {field}", f"delivery_manifests[{idx}].{field}"))
        if manifest.get("audit_graph_hash") and manifest.get("audit_graph_hash") != current_hash:
            issues.append(issue("major", "stale_manifest_audit_graph_hash", "DeliveryManifest audit_graph_hash does not match current graph hash", f"delivery_manifests[{idx}].audit_graph_hash"))
        if manifest.get("research_graph_hash") and manifest.get("research_graph_hash") != current_hash:
            issues.append(issue("major", "stale_manifest_research_graph_hash", "DeliveryManifest research_graph_hash does not match current graph hash", f"delivery_manifests[{idx}].research_graph_hash"))
        audit = ids["audits"].get(manifest.get("audit_id"))
        if isinstance(audit, dict):
            if manifest.get("audit_graph_hash") and audit.get("audit_graph_hash") and manifest.get("audit_graph_hash") != audit.get("audit_graph_hash"):
                issues.append(issue("major", "manifest_audit_hash_mismatch", "DeliveryManifest audit_graph_hash does not match referenced Audit", f"delivery_manifests[{idx}].audit_graph_hash"))
            if manifest.get("research_graph_hash") and audit.get("research_graph_hash") and manifest.get("research_graph_hash") != audit.get("research_graph_hash"):
                issues.append(issue("major", "manifest_research_hash_mismatch", "DeliveryManifest research_graph_hash does not match referenced Audit", f"delivery_manifests[{idx}].research_graph_hash"))
            if audit.get("audit_status") != "passed":
                issues.append(issue("major", "manifest_audit_not_passed", "DeliveryManifest references an Audit that is not passed", f"delivery_manifests[{idx}].audit_id"))
            if manifest.get("delivery_status") != audit.get("delivery_status") or manifest.get("delivery_status") not in as_list(audit.get("allowed_delivery_statuses")):
                issues.append(issue("critical", "manifest_audit_delivery_status_mismatch", "DeliveryManifest delivery_status must be allowed by its referenced passed Audit", f"delivery_manifests[{idx}].delivery_status"))
        run = ids["runs"].get(manifest.get("run_id"))
        if isinstance(run, dict):
            if manifest.get("brief_id") != run.get("brief_id") or manifest.get("plan_id") != run.get("plan_id"):
                issues.append(issue("major", "manifest_run_binding_mismatch", "DeliveryManifest Brief/Plan must match its Run", f"delivery_manifests[{idx}]"))
            if manifest.get("review_cycle_id") != run.get("review_cycle_id"):
                issues.append(issue("major", "manifest_review_cycle_mismatch", "DeliveryManifest review_cycle_id must match its Run", f"delivery_manifests[{idx}].review_cycle_id"))
            brief = ids["briefs"].get(run.get("brief_id"))
            if not _run_allows_delivery_status(run, brief, manifest.get("delivery_status")):
                issues.append(issue("critical", "stored_manifest_delivery_status_not_allowed", "Stored DeliveryManifest status is not allowed by its Run review mode/state", f"delivery_manifests[{idx}].delivery_status"))
        for field, collection in (("exported_entity_ids", "entities"), ("exported_contact_ids", "contact_points"), ("exported_contact_claim_ids", "contact_claims"), ("exported_assessment_ids", "assessments")):
            for raw in as_list(manifest.get(field)):
                if raw and raw not in ids[collection]:
                    issues.append(issue("major", "manifest_export_reference_missing", f"DeliveryManifest exports missing {collection[:-1]} {raw}", f"delivery_manifests[{idx}].{field}"))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    graph = load_json(args.graph)
    issues = validate_graph(graph) if isinstance(graph, dict) else [issue("critical", "graph_not_object", "Research graph must be a JSON object")]
    ok = not any(item.get("severity") in {"critical", "major"} for item in issues)
    result = {"ok": ok, "issue_count": len(issues), "issues": issues}
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Superleads research graph validation passed" if ok else "Superleads research graph validation failed")
        for item in issues:
            print(f"[{item['severity']}] {item['code']}: {item['message']}" + (f" ({item['path']})" if item.get('path') else ""))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
