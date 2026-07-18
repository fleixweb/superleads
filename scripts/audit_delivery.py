#!/usr/bin/env python3
"""Audit Superleads delivery readiness."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from _superleads_common import (
    CLAIM_SUPPORT_ALLOWED_CAPABILITIES,
    CONTACT_NOTE_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_TYPES,
    all_id_maps,
    as_list,
    canonical_contact_user_status,
    claim_value_is_anchored_in_excerpt,
    customer_selection_contract,
    current_review_attestation,
    formal_exception_entity_ids,
    formal_exception_mode,
    formal_targeting_contract_required,
    ensure_list,
    graph_hash,
    has_text,
    source_evidence_scope,
    targeting_rule_maps,
    issue,
    load_json,
    normalized_contact_derives_from_literal,
    review_finding_blocks_delivery,
    review_provenance_disclosure,
    review_provenance_snapshot,
    review_subject_hash,
    text_contains,
    write_json,
)
from validate_research_graph import translated_support_has_original_root, validate_graph

BLOCKED_ACCESS = {"blocked", "login_wall", "login-wall", "login_required", "forbidden", "inaccessible", "not_accessed"}
FORMAL_STATUSES = {"standard_development_list", "full_review_package"}
POSITIVE_DISPOSITIONS = {"重点开发", "推荐跟进"}
FORMAL_RUN_STATUSES = {"checked"}
INQUIRY_STATUS = "inquiry_followup_queue"


def _review_modes(graph: dict[str, Any]) -> set[str]:
    run = _current_run(graph)
    if isinstance(run, dict) and has_text(run.get("review_mode")):
        return {str(run["review_mode"])}
    return set()


def _review_provenance(graph: dict[str, Any]) -> dict[str, Any]:
    return review_provenance_snapshot(graph, _current_run(graph))


def _has_minimum_formal_content(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not ensure_list(graph, "briefs"):
        issues.append(issue("critical", "formal_delivery_missing_brief", "Formal delivery requires at least one Brief", "briefs"))
    if not ensure_list(graph, "plans"):
        issues.append(issue("critical", "formal_delivery_missing_plan", "Formal delivery requires at least one Plan", "plans"))
    if not ensure_list(graph, "entities") and not ensure_list(graph, "candidates"):
        issues.append(issue("critical", "formal_delivery_missing_leads", "Formal delivery requires at least one Entity or Candidate", "entities"))
    if not ensure_list(graph, "assessments"):
        issues.append(issue("critical", "formal_delivery_missing_assessment", "Formal delivery requires at least one Assessment", "assessments"))
    return issues


def _formal_content_complete(graph: dict[str, Any]) -> bool:
    return not _has_minimum_formal_content(graph)


def _current_run(graph: dict[str, Any]) -> dict[str, Any] | None:
    for run in reversed(ensure_list(graph, "runs")):
        if isinstance(run, dict):
            return run
    return None


def _claim_has_usable_support(claim_id: str, graph: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> bool:
    for ce in ensure_list(graph, "claim_evidence"):
        if not isinstance(ce, dict) or ce.get("claim_id") != claim_id or ce.get("relation") != "supports":
            continue
        obs = ids["observations"].get(ce.get("observation_id"))
        if not isinstance(obs, dict):
            continue
        source = ids["sources"].get(obs.get("source_id"))
        medium = source.get("medium") if isinstance(source, dict) else None
        ts = obs.get("translation_status")
        if obs.get("access_status") in BLOCKED_ACCESS:
            continue
        if not has_text(obs.get("raw_excerpt")):
            continue
        claim = ids["claims"].get(claim_id)
        if isinstance(claim, dict) and obs.get("entity_id") and claim.get("entity_id") and obs.get("entity_id") != claim.get("entity_id"):
            continue
        if obs.get("capability") not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES or medium == "search_result":
            continue
        if not source_evidence_scope(source, obs, "assessment_basis")[0]:
            continue
        if not isinstance(claim, dict) or not claim_value_is_anchored_in_excerpt(claim, obs.get("raw_excerpt")):
            continue
        if ts not in {"original", "not_translated"} and not translated_support_has_original_root(obs, claim, ids):
            continue
        return True
    return False


def _formal_delivery_gate_issues(graph: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_has_minimum_formal_content(graph))
    run = _current_run(graph)
    if not run:
        issues.append(issue("critical", "formal_delivery_missing_run", "Formal delivery requires a current Run", "runs"))
        return issues
    if run.get("status") not in FORMAL_RUN_STATUSES:
        issues.append(issue("critical", "formal_delivery_run_not_checked", f"Formal delivery requires current Run status checked; got {run.get('status')}", "runs[-1].status"))
    if not has_text(run.get("review_cycle_id")):
        issues.append(issue("major", "formal_delivery_run_missing_review_cycle", "Formal delivery Run must have a non-empty review_cycle_id", "runs[-1].review_cycle_id"))
    run_brief_id = run.get("brief_id")
    run_plan_id = run.get("plan_id")
    if not has_text(run_brief_id):
        issues.append(issue("major", "formal_delivery_run_missing_brief_id", "Formal delivery Run must reference brief_id", "runs[-1].brief_id"))
    elif run_brief_id not in ids["briefs"]:
        issues.append(issue("major", "formal_delivery_run_brief_missing", f"Formal delivery Run references missing Brief {run_brief_id}", "runs[-1].brief_id"))
    if not has_text(run_plan_id):
        issues.append(issue("major", "formal_delivery_run_missing_plan_id", "Formal delivery Run must reference plan_id", "runs[-1].plan_id"))
    elif run_plan_id not in ids["plans"]:
        issues.append(issue("major", "formal_delivery_run_plan_missing", f"Formal delivery Run references missing Plan {run_plan_id}", "runs[-1].plan_id"))
    plan = ids["plans"].get(run_plan_id)
    if isinstance(plan, dict) and run_brief_id and plan.get("brief_id") != run_brief_id:
        issues.append(issue("major", "formal_delivery_plan_brief_mismatch", "Formal delivery Run Plan does not belong to Run Brief", "runs[-1].plan_id"))
    brief = ids["briefs"].get(run_brief_id)
    contract = customer_selection_contract(brief)
    exception_mode = formal_exception_mode(brief)
    if formal_targeting_contract_required(brief):
        if isinstance(brief, dict) and brief.get("task_mode") == "unknown":
            issues.append(issue("critical", "unknown_task_mode_blocks_formal_delivery", "task_mode=unknown can produce samples only, not formal delivery", "briefs"))
        if not isinstance(contract, dict):
            issues.append(issue("critical", "brief_targeting_contract_missing", "Formal new-customer delivery requires a current customer selection contract", "briefs"))
        else:
            selection_rules, exclusion_rules = targeting_rule_maps(contract)
            if not selection_rules and not exclusion_rules:
                issues.append(issue("critical", "targeting_contract_empty_for_formal_delivery", "Formal delivery requires a substantive customer selection contract", "briefs"))
            if not any(rule.get("required_for_positive") is True for rule in selection_rules.values()):
                issues.append(issue("critical", "targeting_contract_missing_required_selection_rule", "Formal delivery requires at least one required selection rule", "briefs"))
            if contract.get("scope_state") == "provisional":
                issues.append(issue("critical", "provisional_scope_blocks_formal_delivery", "Provisional customer direction can produce samples only, not formal delivery", "briefs"))
            if contract.get("sample_first_required") is True:
                issues.append(issue("critical", "sample_first_required_blocks_formal_delivery", "sample_first_required permits direction samples only until the Brief is explicitly updated and re-reviewed", "briefs"))

    exception_entities = formal_exception_entity_ids(brief)
    if exception_mode and not exception_entities:
        code = "single_company_target_missing" if exception_mode == "single_company_analysis" else "existing_table_binding_missing"
        issues.append(issue("critical", code, "Formal exception delivery requires an explicit current-Brief input binding", "briefs"))

    decisions_by_entity = {
        item.get("entity_id"): item for item in ensure_list(graph, "scope_decisions")
        if isinstance(item, dict) and item.get("run_id") == run.get("run_id") and item.get("brief_id") == run_brief_id and item.get("entity_id")
    }

    assessments_by_entity = {
        a.get("entity_id"): a
        for a in ensure_list(graph, "assessments")
        if isinstance(a, dict) and a.get("entity_id") and a.get("brief_id") == run_brief_id and a.get("run_id") == run.get("run_id")
    }
    if exception_mode:
        for entity_id, assessment in assessments_by_entity.items():
            if assessment.get("disposition") in POSITIVE_DISPOSITIONS and str(entity_id) not in exception_entities:
                code = "single_company_assessment_outside_target" if exception_mode == "single_company_analysis" else "existing_table_assessment_outside_bound_input"
                issues.append(issue("critical", code, "Formal exception delivery contains a positive Entity outside its explicit input binding", "assessments"))
    if formal_targeting_contract_required(brief):
        in_scope_positive_entities = {
            str(assessment.get("entity_id"))
            for assessment in assessments_by_entity.values()
            if assessment.get("disposition") in POSITIVE_DISPOSITIONS
            and isinstance(decisions_by_entity.get(assessment.get("entity_id")), dict)
            and decisions_by_entity[assessment.get("entity_id")].get("overall_status") == "in_scope"
        }
        if not in_scope_positive_entities:
            issues.append(issue("critical", "formal_delivery_no_in_scope_entity", "Formal new-customer delivery requires at least one current positive Entity confirmed in scope", "assessments"))
    for idx, entity in enumerate(ensure_list(graph, "entities")):
        if not isinstance(entity, dict):
            continue
        entity_id = entity.get("entity_id")
        decision = decisions_by_entity.get(entity_id)
        if exception_mode and str(entity_id) not in exception_entities:
            continue
        # A current graph may retain excluded, reference, or unresolved
        # entities for traceability. They are not formal-list rows and must
        # not force an Assessment merely by being present beside in-scope rows.
        if formal_targeting_contract_required(brief) and isinstance(decision, dict) and decision.get("overall_status") != "in_scope":
            continue
        assessment = assessments_by_entity.get(entity_id)
        if not isinstance(assessment, dict):
            issues.append(issue("critical", "formal_entity_without_current_run_assessment", f"Formal delivery Entity {entity_id} has no Assessment for current Run {run.get('run_id')}", f"entities[{idx}]"))
            continue
        if assessment.get("disposition") in POSITIVE_DISPOSITIONS:
            basis = as_list(assessment.get("basis_claim_ids"))
            if not basis:
                issues.append(issue("critical", "formal_positive_assessment_without_basis", f"Positive Assessment for Entity {entity_id} has no basis_claim_ids", "assessments.basis_claim_ids"))
            for cid in basis:
                claim = ids["claims"].get(cid)
                if not isinstance(claim, dict):
                    issues.append(issue("critical", "formal_assessment_basis_claim_missing", f"Assessment basis Claim {cid} is missing", "assessments.basis_claim_ids"))
                    continue
                if claim.get("entity_id") != entity_id:
                    issues.append(issue("critical", "formal_assessment_basis_claim_entity_mismatch", f"Assessment for Entity {entity_id} uses Claim {cid} from Entity {claim.get('entity_id')}", "assessments.basis_claim_ids"))
                if not _claim_has_usable_support(str(cid), graph, ids):
                    issues.append(issue("critical", "formal_assessment_basis_claim_without_usable_support", f"Assessment basis Claim {cid} has no usable supports evidence", "assessments.basis_claim_ids"))
            if formal_targeting_contract_required(brief):
                if not isinstance(decision, dict) or decision.get("overall_status") != "in_scope":
                    issues.append(issue("critical", "positive_assessment_without_eligible_scope_decision", f"Formal positive Entity {entity_id} is not confirmed in scope for this Brief", f"entities[{idx}]"))
                elif not isinstance(contract, dict) or decision.get("targeting_contract_id") != contract.get("targeting_contract_id"):
                    issues.append(issue("critical", "scope_decision_brief_mismatch", "Formal ScopeDecision does not match current Brief contract", f"entities[{idx}]"))
    return issues


def _inquiry_delivery_gate_issues(graph: dict[str, Any], ids: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, str]]:
    """Audit the read-only inquiry queue without applying formal-list gates."""
    issues: list[dict[str, str]] = []
    inquiries = [item for item in ensure_list(graph, "inquiries") if isinstance(item, dict)]
    if not inquiries:
        return [issue("critical", "inquiry_delivery_missing_inquiry", "Inquiry delivery requires at least one Inquiry", "inquiries")]
    for idx, inquiry in enumerate(inquiries):
        source = ids["sources"].get(inquiry.get("source_id"))
        observation = ids["observations"].get(inquiry.get("observation_id"))
        if not isinstance(source, dict) or not isinstance(observation, dict):
            issues.append(issue("critical", "inquiry_reference_missing", "Inquiry Source or Observation is missing", f"inquiries[{idx}]"))
            continue
        if inquiry.get("direction") != "inbound" or source.get("direction") != "inbound":
            issues.append(issue("critical", "inquiry_direction_not_inbound", "Inquiry delivery accepts inbound correspondence only", f"inquiries[{idx}].direction"))
        eligible, reason_code = source_evidence_scope(source, observation, "inquiry_event")
        if not eligible:
            issues.append(issue("critical", reason_code, "Inquiry source does not meet the inbound correspondence contract", f"inquiries[{idx}].observation_id"))
        if not has_text(inquiry.get("request_excerpt")) or len(str(inquiry.get("request_excerpt") or "")) > 1000:
            issues.append(issue("critical", "inquiry_request_excerpt_invalid", "Inquiry delivery requires a bounded request excerpt", f"inquiries[{idx}].request_excerpt"))
        if not has_text(inquiry.get("received_at")):
            issues.append(issue("critical", "inquiry_received_at_missing", "Inquiry delivery requires received_at", f"inquiries[{idx}].received_at"))
    return issues


def _allowed_statuses(
    graph: dict[str, Any],
    issues: list[dict[str, str]],
    formal_ready: bool,
    provenance_level: str | None,
) -> tuple[list[str], bool]:
    if any(i.get("severity") in {"critical", "major"} for i in issues):
        return [], False
    modes = _review_modes(graph)
    if "not_run" in modes:
        return ["initial_lead_list"], False
    disclosure_required = False
    allowed = ["initial_lead_list"]
    if "self_review_fallback" in modes:
        disclosure_required = True
        if formal_ready:
            allowed.append("standard_development_list")
        return allowed, disclosure_required
    if "independent" in modes:
        if formal_ready:
            allowed.append("standard_development_list")
        return allowed, True
    # Absence of review is treated as not reviewed for formal delivery.
    return ["initial_lead_list"], False


def audit_graph(graph: dict[str, Any], requested_delivery_status: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    ids = all_id_maps(graph)
    provenance = _review_provenance(graph)

    for validation_issue in validate_graph(graph):
        if validation_issue.get("severity") in {"critical", "major"}:
            issues.append(issue(validation_issue["severity"], "validation_" + validation_issue["code"], validation_issue["message"], validation_issue.get("path")))

    for idx, cp in enumerate(ensure_list(graph, "contact_points")):
        if not isinstance(cp, dict):
            continue
        for field in ("source_literal", "normalized_value", "source_observation_id"):
            if not has_text(cp.get(field)):
                issues.append(issue("critical", "contact_point_missing_source_field", f"ContactPoint {cp.get('contact_id')} lacks {field}", f"contact_points[{idx}].{field}"))
        obs_id = cp.get("source_observation_id")
        obs = ids["observations"].get(obs_id)
        if obs_id and obs_id not in ids["observations"]:
            issues.append(issue("critical", "contact_point_source_observation_missing", f"ContactPoint {cp.get('contact_id')} source observation missing", f"contact_points[{idx}].source_observation_id"))
        if isinstance(obs, dict):
            raw_excerpt = obs.get("raw_excerpt")
            if not text_contains(raw_excerpt, cp.get("source_literal")):
                issues.append(issue("critical", "contact_literal_not_in_observation", f"ContactPoint {cp.get('contact_id')} source_literal is not present in cited Observation raw_excerpt", f"contact_points[{idx}].source_literal"))
            if not normalized_contact_derives_from_literal(cp.get("contact_type"), cp.get("normalized_value"), cp.get("source_literal")):
                issues.append(issue("critical", "contact_normalized_not_derived", f"ContactPoint {cp.get('contact_id')} normalized_value is not derivable from source_literal", f"contact_points[{idx}].normalized_value"))
        if has_text(cp.get("source_type")) and str(cp.get("source_type")).casefold() not in CONTACT_SOURCE_ALLOWED_TYPES:
            issues.append(issue("critical", "contact_source_type_not_allowed", f"ContactPoint {cp.get('contact_id')} uses non-permitted source_type {cp.get('source_type')}", f"contact_points[{idx}].source_type"))

    for idx, cc in enumerate(ensure_list(graph, "contact_claims")):
        if not isinstance(cc, dict):
            continue
        cp = ids["contact_points"].get(cc.get("contact_id"))
        assoc_obs = ids["observations"].get(cc.get("association_observation_id"))
        source_obs = ids["observations"].get(cp.get("source_observation_id")) if isinstance(cp, dict) else None
        export_status = cc.get("export_status")
        delivery_visible_contact = export_status in {"ready", "export_with_source_note", "needs_manual_association_review"}
        if "user_status" in cc and cc.get("user_status") != canonical_contact_user_status(export_status):
            issues.append(issue("critical", "contact_user_status_mismatch", f"ContactClaim {cc.get('contact_claim_id')} user_status must be derived from export_status {export_status}", f"contact_claims[{idx}].user_status"))
        for field in ("source_context", "association_evidence_text"):
            if not has_text(cc.get(field)):
                sev = "critical" if delivery_visible_contact else "major"
                issues.append(issue(sev, "contact_claim_missing_association_field", f"ContactClaim {cc.get('contact_claim_id')} lacks {field}", f"contact_claims[{idx}].{field}"))
        if isinstance(source_obs, dict) and source_obs.get("entity_id") and cc.get("entity_id") and source_obs.get("entity_id") != cc.get("entity_id"):
            issues.append(issue("critical", "contact_source_entity_mismatch", f"ContactPoint source Observation entity {source_obs.get('entity_id')} does not match ContactClaim entity {cc.get('entity_id')}", f"contact_claims[{idx}].entity_id"))
        if isinstance(assoc_obs, dict) and assoc_obs.get("entity_id") and cc.get("entity_id") and assoc_obs.get("entity_id") != cc.get("entity_id"):
            issues.append(issue("critical", "contact_association_entity_mismatch", f"ContactClaim association Observation entity {assoc_obs.get('entity_id')} does not match ContactClaim entity {cc.get('entity_id')}", f"contact_claims[{idx}].entity_id"))
        for field, code in (("person_name", "person_name_not_in_observation"), ("job_title", "job_title_not_in_observation"), ("department", "department_not_in_observation")):
            value = cc.get(field)
            if has_text(value) and not (text_contains(cc.get("association_evidence_text"), value) or (isinstance(assoc_obs, dict) and text_contains(assoc_obs.get("raw_excerpt"), value))):
                issues.append(issue("critical", code, f"ContactClaim {cc.get('contact_claim_id')} {field} is not present in association Observation", f"contact_claims[{idx}].{field}"))
        if cc.get("export_status") == "ready":
            if not has_text(cc.get("entity_id")):
                issues.append(issue("critical", "ready_contact_without_resolved_entity", f"ready ContactClaim {cc.get('contact_claim_id')} lacks a resolved entity_id", f"contact_claims[{idx}]"))
            if not has_text(cc.get("association_evidence_text")):
                issues.append(issue("critical", "ready_contact_without_ownership_evidence", f"ready ContactClaim {cc.get('contact_claim_id')} lacks ownership evidence", f"contact_claims[{idx}]"))
        if delivery_visible_contact:
            if isinstance(assoc_obs, dict) and not text_contains(assoc_obs.get("raw_excerpt"), cc.get("association_evidence_text")):
                issues.append(issue("critical", "association_evidence_not_in_observation", f"ContactClaim {cc.get('contact_claim_id')} association_evidence_text is not present in cited Observation", f"contact_claims[{idx}].association_evidence_text"))
            for obs, obs_label in ((source_obs, "source"), (assoc_obs, "association")):
                if isinstance(obs, dict):
                    source = ids["sources"].get(obs.get("source_id"))
                    medium = source.get("medium") if isinstance(source, dict) else None
                    allowed_capabilities = CONTACT_NOTE_ALLOWED_CAPABILITIES if export_status == "export_with_source_note" else CONTACT_SOURCE_ALLOWED_CAPABILITIES
                    if obs.get("capability") not in allowed_capabilities or medium == "search_result":
                        issues.append(issue("critical", "contact_capability_not_allowed", f"ContactClaim {cc.get('contact_claim_id')} uses non-permitted {obs_label} capability {obs.get('capability') or medium}", f"contact_claims[{idx}]"))
                    if obs.get("access_status") in BLOCKED_ACCESS:
                        issues.append(issue("critical", "contact_from_blocked_observation", f"ContactClaim {cc.get('contact_claim_id')} uses blocked {obs_label} Observation", f"contact_claims[{idx}]"))
                    if export_status in {"ready", "export_with_source_note"}:
                        purpose = "contact_ready" if export_status == "ready" else "contact_with_source_note"
                        eligible, reason_code = source_evidence_scope(source, obs, purpose)
                        if not eligible:
                            issues.append(issue("critical", reason_code, f"Exportable ContactClaim {obs_label} Observation does not meet the formal source eligibility contract", f"contact_claims[{idx}]"))
            if isinstance(cp, dict) and str(cp.get("source_type") or "").casefold() not in CONTACT_SOURCE_ALLOWED_TYPES:
                issues.append(issue("critical", "contact_source_type_not_allowed", f"ContactClaim {cc.get('contact_claim_id')} uses non-permitted contact source_type {cp.get('source_type')}", f"contact_claims[{idx}]"))
            if isinstance(cp, dict) and isinstance(assoc_obs, dict) and cc.get("association_observation_id") != cp.get("source_observation_id"):
                evidence = cc.get("association_evidence_text")
                literal = cp.get("source_literal")
                normalized = cp.get("normalized_value")
                if not (text_contains(evidence, literal) or text_contains(evidence, normalized) or text_contains(assoc_obs.get("raw_excerpt"), literal) or text_contains(assoc_obs.get("raw_excerpt"), normalized)):
                    issues.append(issue("critical", "contact_association_not_tied_to_contact_literal", f"ContactClaim {cc.get('contact_claim_id')} association evidence does not include the contact value", f"contact_claims[{idx}].association_evidence_text"))
        if has_text(cc.get("person_name")) and not has_text(cc.get("association_evidence_text")):
            issues.append(issue("major", "person_name_without_source_text", "person_name is filled without evidence text", f"contact_claims[{idx}].person_name"))
        if has_text(cc.get("job_title")) and not has_text(cc.get("association_evidence_text")):
            issues.append(issue("major", "job_title_without_source_text", "job_title is filled without evidence text", f"contact_claims[{idx}].job_title"))

    for idx, ce in enumerate(ensure_list(graph, "claim_evidence")):
        if not isinstance(ce, dict):
            continue
        obs = ids["observations"].get(ce.get("observation_id"))
        if not isinstance(obs, dict):
            continue
        if ce.get("relation") == "supports" and obs.get("access_status") in BLOCKED_ACCESS:
            issues.append(issue("critical", "blocked_observation_supports_claim", "Blocked/login-wall/inaccessible Observation supports Claim", f"claim_evidence[{idx}]"))
        if ce.get("relation") == "supports":
            claim = ids["claims"].get(ce.get("claim_id"))
            if isinstance(claim, dict) and obs.get("entity_id") and claim.get("entity_id") and obs.get("entity_id") != claim.get("entity_id"):
                issues.append(issue("critical", "claim_evidence_entity_mismatch", f"ClaimEvidence {ce.get('claim_evidence_id')} uses Observation from Entity {obs.get('entity_id')} to support Claim for Entity {claim.get('entity_id')}", f"claim_evidence[{idx}].observation_id"))
            if not has_text(obs.get("raw_excerpt")):
                issues.append(issue("critical", "supporting_observation_without_raw_excerpt", f"ClaimEvidence {ce.get('claim_evidence_id')} supports Claim without a non-empty Observation raw_excerpt", f"claim_evidence[{idx}].observation_id"))
        if ce.get("relation") == "supports":
            claim = ids["claims"].get(ce.get("claim_id"))
            source = ids["sources"].get(obs.get("source_id"))
            medium = source.get("medium") if isinstance(source, dict) else None
            if obs.get("capability") not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES or medium == "search_result":
                issues.append(issue("critical", "capability_not_allowed_to_support_claim", f"{obs.get('capability') or medium} cannot support a formal Claim", f"claim_evidence[{idx}]"))
            eligible, reason_code = source_evidence_scope(source, obs, "formal_claim")
            if not eligible:
                issues.append(issue("critical", reason_code, "ClaimEvidence support does not meet the formal source eligibility contract", f"claim_evidence[{idx}].observation_id"))
            if isinstance(claim, dict) and not claim_value_is_anchored_in_excerpt(claim, obs.get("raw_excerpt")):
                issues.append(issue("critical", "claim_value_not_anchored_in_observation", f"ClaimEvidence {ce.get('claim_evidence_id')} does not anchor Claim typed_value in its Observation raw_excerpt", f"claim_evidence[{idx}]"))
            ts = obs.get("translation_status")
            if ts and ts not in {"original", "not_translated", "unknown"}:
                origin = ids["observations"].get(obs.get("derived_from_observation_id"))
                if not isinstance(origin, dict):
                    issues.append(issue("critical", "translated_support_origin_missing", "Translated Observation supports Claim but original Observation is missing", f"claim_evidence[{idx}].observation_id"))
                elif not has_text(origin.get("raw_excerpt")) or origin.get("access_status") in BLOCKED_ACCESS or (isinstance(claim, dict) and claim.get("entity_id") and origin.get("entity_id") and claim.get("entity_id") != origin.get("entity_id")):
                    issues.append(issue("critical", "translated_support_origin_not_usable", "Translated Observation lacks a usable same-entity original Observation", f"claim_evidence[{idx}].observation_id"))

    for idx, hyp in enumerate(ensure_list(graph, "hypotheses")):
        if not isinstance(hyp, dict):
            continue
        if not as_list(hyp.get("unknowns")):
            issues.append(issue("major", "hypothesis_without_unknowns", f"Hypothesis {hyp.get('hypothesis_id')} lacks unknowns", f"hypotheses[{idx}].unknowns"))
        if not has_text(hyp.get("next_verification_action")):
            issues.append(issue("major", "hypothesis_without_next_verification", f"Hypothesis {hyp.get('hypothesis_id')} lacks next_verification_action", f"hypotheses[{idx}].next_verification_action"))

    for idx, obs in enumerate(ensure_list(graph, "observations")):
        if not isinstance(obs, dict):
            continue
        ts = obs.get("translation_status")
        if ts and ts not in {"original", "not_translated", "unknown"} and not obs.get("derived_from_observation_id"):
            issues.append(issue("minor", "translated_observation_without_origin", "Translated Observation lacks derived_from_observation_id", f"observations[{idx}].derived_from_observation_id"))

    current_run = _current_run(graph) or {}
    current_review_cycle_id = current_run.get("review_cycle_id")
    for idx, finding in enumerate(ensure_list(graph, "review_findings")):
        if not isinstance(finding, dict):
            continue
        finding_cycle = finding.get("review_cycle_id")
        # Older review cycles are historical records. They cannot approve or
        # block the current delivery cycle without an explicit shared cycle.
        if current_review_cycle_id and finding_cycle and finding_cycle != current_review_cycle_id:
            continue
        if review_finding_blocks_delivery(finding):
            issues.append(issue("critical", "open_blocking_review_finding", f"Blocking ReviewFinding {finding.get('finding_id')} is not verified fixed", f"review_findings[{idx}].status"))

    formal_gate_issues = _formal_delivery_gate_issues(graph, ids)
    inquiry_gate_issues = _inquiry_delivery_gate_issues(graph, ids) if requested_delivery_status == INQUIRY_STATUS else []
    formal_ready = not any(i.get("severity") in {"critical", "major"} for i in formal_gate_issues)
    if requested_delivery_status in FORMAL_STATUSES:
        issues.extend(formal_gate_issues)
    if requested_delivery_status == INQUIRY_STATUS:
        issues.extend(inquiry_gate_issues)

    current_hash = graph_hash(graph)
    for idx, audit in enumerate(ensure_list(graph, "audits")):
        if not isinstance(audit, dict):
            continue
        if audit.get("research_graph_hash") and audit.get("research_graph_hash") != current_hash:
            issues.append(issue("critical", "stale_audit_research_graph_hash", "Audit research_graph_hash does not match current graph hash", f"audits[{idx}].research_graph_hash"))
        if audit.get("audit_graph_hash") and audit.get("audit_graph_hash") != current_hash:
            issues.append(issue("critical", "stale_audit_graph_hash", "Audit audit_graph_hash does not match current graph hash", f"audits[{idx}].audit_graph_hash"))
        if audit.get("audit_status") and audit.get("audit_status") != "passed":
            issues.append(issue("critical", "referenced_audit_not_passed", "Stored Audit is not passed", f"audits[{idx}].audit_status"))
        if audit.get("review_attestation_id") and audit.get("review_attestation_id") != provenance.get("review_attestation_id"):
            issues.append(issue("critical", "audit_review_attestation_mismatch", "Audit review_attestation_id does not match current review provenance", f"audits[{idx}].review_attestation_id"))
        if audit.get("reviewed_subject_hash") and audit.get("reviewed_subject_hash") != provenance.get("reviewed_subject_hash"):
            issues.append(issue("critical", "audit_reviewed_subject_hash_mismatch", "Audit reviewed_subject_hash does not match current review provenance", f"audits[{idx}].reviewed_subject_hash"))
        if audit.get("review_provenance_level") and audit.get("review_provenance_level") != provenance.get("review_provenance_level"):
            issues.append(issue("critical", "audit_review_provenance_level_mismatch", "Audit review_provenance_level does not match current review provenance", f"audits[{idx}].review_provenance_level"))
    for idx, manifest in enumerate(ensure_list(graph, "delivery_manifests")):
        if not isinstance(manifest, dict):
            continue
        if manifest.get("audit_graph_hash") and manifest.get("audit_graph_hash") != current_hash:
            issues.append(issue("critical", "stale_audit_graph_hash", "DeliveryManifest audit_graph_hash does not match current graph hash", f"delivery_manifests[{idx}].audit_graph_hash"))
        if manifest.get("research_graph_hash") and manifest.get("research_graph_hash") != current_hash:
            issues.append(issue("critical", "stale_manifest_research_graph_hash", "DeliveryManifest research_graph_hash does not match current graph hash", f"delivery_manifests[{idx}].research_graph_hash"))
        if manifest.get("review_attestation_id") and manifest.get("review_attestation_id") != provenance.get("review_attestation_id"):
            issues.append(issue("critical", "manifest_review_attestation_mismatch", "DeliveryManifest review_attestation_id does not match current review provenance", f"delivery_manifests[{idx}].review_attestation_id"))
        if manifest.get("reviewed_subject_hash") and manifest.get("reviewed_subject_hash") != provenance.get("reviewed_subject_hash"):
            issues.append(issue("critical", "manifest_reviewed_subject_hash_mismatch", "DeliveryManifest reviewed_subject_hash does not match current review provenance", f"delivery_manifests[{idx}].reviewed_subject_hash"))
        if manifest.get("review_provenance_level") and manifest.get("review_provenance_level") != provenance.get("review_provenance_level"):
            issues.append(issue("critical", "manifest_review_provenance_level_mismatch", "DeliveryManifest review_provenance_level does not match current review provenance", f"delivery_manifests[{idx}].review_provenance_level"))
        audit = ids["audits"].get(manifest.get("audit_id"))
        if isinstance(audit, dict) and audit.get("audit_status") != "passed":
            issues.append(issue("critical", "manifest_audit_not_passed", "DeliveryManifest references an Audit that is not passed", f"delivery_manifests[{idx}].audit_id"))
        if isinstance(audit, dict):
            if audit.get("review_attestation_id") and manifest.get("review_attestation_id") != audit.get("review_attestation_id"):
                issues.append(issue("critical", "manifest_audit_review_attestation_mismatch", "DeliveryManifest review_attestation_id must match its referenced Audit", f"delivery_manifests[{idx}].review_attestation_id"))
            if audit.get("reviewed_subject_hash") and manifest.get("reviewed_subject_hash") != audit.get("reviewed_subject_hash"):
                issues.append(issue("critical", "manifest_audit_reviewed_subject_hash_mismatch", "DeliveryManifest reviewed_subject_hash must match its referenced Audit", f"delivery_manifests[{idx}].reviewed_subject_hash"))
            if audit.get("review_provenance_level") and manifest.get("review_provenance_level") != audit.get("review_provenance_level"):
                issues.append(issue("critical", "manifest_audit_review_provenance_level_mismatch", "DeliveryManifest review_provenance_level must match its referenced Audit", f"delivery_manifests[{idx}].review_provenance_level"))
        if manifest.get("delivery_status") in FORMAL_STATUSES and any(i.get("severity") == "critical" for i in issues):
            issues.append(issue("critical", "formal_delivery_has_blockers", "Formal delivery status is present while critical blockers exist", f"delivery_manifests[{idx}].delivery_status"))

    allowed_statuses, disclosure_required = _allowed_statuses(graph, issues, formal_ready, provenance.get("review_provenance_level"))
    if provenance.get("review_provenance_level") in {"declared_separate_session", "self_review_fallback", "not_run"}:
        disclosure_required = True
    if requested_delivery_status == INQUIRY_STATUS and not any(i.get("severity") in {"critical", "major"} for i in issues):
        allowed_statuses = [INQUIRY_STATUS]
    if requested_delivery_status in FORMAL_STATUSES:
        if requested_delivery_status not in allowed_statuses:
            modes = sorted(_review_modes(graph)) or ["not_run"]
            issues.append(issue("critical", "requested_delivery_not_allowed_by_review", f"Requested {requested_delivery_status} is not allowed by review mode(s): {', '.join(modes)}", "runs.review_mode"))
    if requested_delivery_status == "full_review_package":
        issues.append(issue("critical", "full_review_unavailable_in_local_deployment", "This local deployment does not provide full_review_package", "delivery_status"))

    blocking = any(i.get("severity") in {"critical", "major"} for i in issues)
    if blocking:
        delivery_status = "needs_correction"
        allowed_statuses = []
    elif requested_delivery_status:
        delivery_status = requested_delivery_status
    elif "full_review_package" in allowed_statuses:
        delivery_status = "full_review_package"
    elif "standard_development_list" in allowed_statuses:
        delivery_status = "standard_development_list"
    else:
        delivery_status = "initial_lead_list"

    return {
        "audit_id": f"audit_{current_hash[:12]}",
        "audited_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "research_graph_hash": current_hash,
        "audit_graph_hash": current_hash,
        "review_cycle_id": (_current_run(graph) or {}).get("review_cycle_id"),
        "review_attestation_id": provenance.get("review_attestation_id"),
        "reviewed_subject_hash": provenance.get("reviewed_subject_hash"),
        "review_provenance_level": provenance.get("review_provenance_level"),
        "audit_status": "failed" if blocking else "passed",
        "delivery_status": delivery_status,
        "allowed_delivery_statuses": allowed_statuses,
        "disclosure_required": disclosure_required,
        "ok": not blocking,
        "issue_count": len(issues),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("graph")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--output")
    parser.add_argument("--delivery-status", choices=["initial_lead_list", "standard_development_list", "full_review_package", INQUIRY_STATUS], help="Optional target status to audit before export")
    args = parser.parse_args()
    graph = load_json(args.graph)
    audit = audit_graph(graph, requested_delivery_status=args.delivery_status) if isinstance(graph, dict) else {"ok": False, "audit_status": "failed", "delivery_status": "needs_correction", "issues": [issue("critical", "graph_not_object", "Research graph must be a JSON object")], "issue_count": 1}
    if args.output:
        write_json(args.output, audit)
    if args.format == "json":
        print(json.dumps(audit, ensure_ascii=False, indent=2))
    else:
        print("Superleads delivery audit passed" if audit.get("ok") else "Superleads delivery audit failed")
        print(f"graph_hash: {audit.get('research_graph_hash', 'unknown')}")
        print(f"delivery_status: {audit.get('delivery_status')}")
        for item in audit.get("issues", []):
            print(f"[{item['severity']}] {item['code']}: {item['message']}" + (f" ({item['path']})" if item.get('path') else ""))
    return 0 if audit.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
