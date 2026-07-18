#!/usr/bin/env python3
"""Validate Superleads research graph invariants."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from _superleads_common import (
    CLAIM_SUPPORT_ALLOWED_CAPABILITIES,
    CONTACT_NOTE_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_CAPABILITIES,
    CONTACT_SOURCE_ALLOWED_TYPES,
    ID_FIELDS,
    ARTIFACT_MEDIA,
    AUDIT_REVIEW_PROVENANCE_LEVELS,
    MATERIAL_ROLES,
    RULE_ALLOWED_CLAIM_TYPES,
    REVIEW_ATTESTATION_CONCLUSIONS,
    REVIEW_PROVENANCE_LEVELS,
    SCOPE_CLAIM_CLASSIFICATIONS,
    SCOPE_DECISION_STATUSES,
    SCOPE_RULE_OUTCOMES,
    SEARCH_LOG_RESULT_USES,
    all_id_maps,
    as_list,
    canonical_contact_user_status,
    claim_value_is_anchored_in_excerpt,
    customer_selection_contract,
    current_brief,
    current_run,
    entity_domain_matches_identity_literal,
    entity_matches_identity_literal,
    entity_name_matches_identity_literal,
    formal_exception_entity_ids,
    formal_exception_mode,
    formal_targeting_contract_required,
    contains_local_path,
    contact_literal_is_present,
    ensure_list,
    graph_hash,
    has_text,
    is_safe_anonymous_id,
    identity_reference_match,
    normalized_identity_domain,
    CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES,
    CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES,
    adapter_reports_from_run,
    codex_adapter_allows_observation,
    contains_shell_http_forbidden_data,
    is_canonical_platform_id,
    is_safe_public_http_url,
    resolve_capability_adapter_reports,
    source_has_safe_public_http_urls,
    source_evidence_scope,
    targeting_contract_required,
    targeting_rule_maps,
    issue,
    load_json,
    normalized_contact_derives_from_literal,
    normalize_region_values,
    review_subject_hash,
    review_provenance_snapshot,
    validate_current_review_attestation,
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
        if not isinstance(source, dict) or source.get("medium") == "search_result":
            return False
        if current.get("capability") not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES:
            return False
        status = current.get("translation_status")
        if status in {"original", "not_translated"}:
            return source_evidence_scope(source, current, "translation_origin")[0]
        if not has_text(current.get("derived_from_observation_id")):
            return False
        origin = ids["observations"].get(current.get("derived_from_observation_id"))
        if not isinstance(origin, dict):
            return False
        current = origin


def _claim_has_usable_assessment_support(claim_id: Any, ids: dict[str, dict[str, dict[str, Any]]], evidence_by_claim: dict[str, list[dict[str, Any]]]) -> bool:
    """Check that a scope rule cites a same-entity Claim with formal supports."""
    claim = ids["claims"].get(claim_id)
    if not isinstance(claim, dict):
        return False
    for evidence in evidence_by_claim.get(str(claim_id), []):
        if evidence.get("relation") != "supports":
            continue
        observation = ids["observations"].get(evidence.get("observation_id"))
        source = ids["sources"].get(observation.get("source_id")) if isinstance(observation, dict) else None
        if not isinstance(observation, dict) or observation.get("entity_id") != claim.get("entity_id"):
            continue
        if observation.get("access_status") in BLOCKED_ACCESS:
            continue
        if source_evidence_scope(source, observation, "assessment_basis")[0]:
            return True
    return False


def _claim_supporting_observations(claim_id: Any, ids: dict[str, dict[str, dict[str, Any]]], evidence_by_claim: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Return only formal, same-Entity Observations that support this Claim."""
    claim = ids["claims"].get(claim_id)
    if not isinstance(claim, dict):
        return []
    result: list[dict[str, Any]] = []
    for evidence in evidence_by_claim.get(str(claim_id), []):
        if evidence.get("relation") != "supports":
            continue
        observation = ids["observations"].get(evidence.get("observation_id"))
        source = ids["sources"].get(observation.get("source_id")) if isinstance(observation, dict) else None
        if not isinstance(observation, dict) or observation.get("entity_id") != claim.get("entity_id"):
            continue
        if source_evidence_scope(source, observation, "assessment_basis")[0]:
            result.append(observation)
    return result


def _formal_claim_ids_supported_by_observation(observation_id: Any, entity_id: Any, ids: dict[str, dict[str, dict[str, Any]]], evidence_by_claim: dict[str, list[dict[str, Any]]]) -> set[str]:
    result: set[str] = set()
    for claim_id, evidence_items in evidence_by_claim.items():
        claim = ids["claims"].get(claim_id)
        if not isinstance(claim, dict) or claim.get("entity_id") != entity_id:
            continue
        if any(item.get("relation") == "supports" and item.get("observation_id") == observation_id for item in evidence_items):
            if _claim_has_usable_assessment_support(claim_id, ids, evidence_by_claim):
                result.add(str(claim_id))
    return result


def _run_allows_delivery_status(run: dict[str, Any], brief: dict[str, Any] | None, status: Any) -> bool:
    if status == "initial_lead_list":
        return True
    if status not in FORMAL_STATUSES or run.get("status") != "checked":
        return False
    mode = run.get("review_mode")
    if status == "standard_development_list":
        return mode in {"independent", "self_review_fallback"}
    return False


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


def _formal_exception_binding_issues(
    brief: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
    observations: list[Any],
    path: str,
) -> list[dict[str, str]]:
    """Validate the user-input binding required by formal exception modes."""
    issues: list[dict[str, str]] = []
    mode = formal_exception_mode(brief)
    if mode == "single_company_analysis":
        target = brief.get("single_company_target")
        target_path = f"{path}.single_company_target"
        if not isinstance(target, dict):
            return [issue("critical", "single_company_target_missing", "Formal single-company analysis requires an explicit current-Brief target binding", target_path)]
        if not has_text(target.get("user_statement")):
            issues.append(issue("critical", "single_company_target_missing", "Single-company target requires the user's explicit target statement", f"{target_path}.user_statement"))
        identifiers = (target.get("company_name"), target.get("website_or_domain"), target.get("source_id"))
        if not any(has_text(value) for value in identifiers):
            issues.append(issue("critical", "single_company_target_missing", "Single-company target requires a company identifier, URL, or user-material reference", target_path))
        entity_id = target.get("resolved_entity_id")
        entity = ids["entities"].get(entity_id)
        if not has_text(entity_id) or not isinstance(entity, dict):
            issues.append(issue("critical", "single_company_target_entity_missing", "Single-company target must resolve to an existing Entity", f"{target_path}.resolved_entity_id"))
            return issues
        if has_text(target.get("company_name")):
            if not entity_name_matches_identity_literal(entity, target.get("company_name")):
                issues.append(issue("critical", "single_company_target_identifier_conflict", "Single-company company_name must exactly identify the resolved Entity", f"{target_path}.company_name"))
        if has_text(target.get("website_or_domain")):
            if not entity_domain_matches_identity_literal(entity, target.get("website_or_domain")):
                issues.append(issue("critical", "single_company_target_identifier_conflict", "Single-company website_or_domain must exactly identify the resolved Entity", f"{target_path}.website_or_domain"))
        if has_text(target.get("source_id")):
            source = ids["sources"].get(target.get("source_id"))
            if not isinstance(source, dict) or source.get("provenance") not in {"user_provided", "manual_input"}:
                issues.append(issue("critical", "single_company_target_source_unbound", "Single-company user-material reference must contain an Observation resolved to the target Entity", f"{target_path}.source_id"))
            literal = target.get("entity_literal")
            if not has_text(literal):
                issues.append(issue("critical", "single_company_target_entity_literal_missing", "Single-company user-material reference requires a visible Entity literal", f"{target_path}.entity_literal"))
            elif not entity_matches_identity_literal(entity, literal):
                issues.append(issue("critical", "single_company_target_literal_entity_mismatch", "Single-company user-material Entity literal must exactly identify the resolved Entity", f"{target_path}.entity_literal"))
            matching_observations = [
                observation for observation in observations
                if isinstance(observation, dict)
                and observation.get("source_id") == target.get("source_id")
                and observation.get("entity_id") == entity_id
            ]
            if not matching_observations:
                issues.append(issue("critical", "single_company_target_source_unbound", "Single-company user-material reference must contain an Observation resolved to the target Entity", f"{target_path}.source_id"))
            elif has_text(literal) and not any(text_contains_exact_phrase(observation.get("raw_excerpt"), literal) for observation in matching_observations):
                issues.append(issue("critical", "single_company_target_entity_literal_not_in_observation", "Single-company Entity literal must appear verbatim in a same-Entity user-material Observation", f"{target_path}.entity_literal"))
    elif mode == "existing_table_enrichment":
        binding = brief.get("existing_table_binding")
        binding_path = f"{path}.existing_table_binding"
        if not isinstance(binding, dict):
            return [issue("critical", "existing_table_binding_missing", "Formal existing-table enrichment requires a bound user-provided table and row/cell mappings", binding_path)]
        source_id = binding.get("source_id")
        source = ids["sources"].get(source_id)
        if not isinstance(source, dict) or source.get("provenance") != "user_provided" or source.get("medium") != "spreadsheet":
            issues.append(issue("critical", "existing_table_binding_source_invalid", "Existing-table enrichment must bind a user-provided spreadsheet Source", f"{binding_path}.source_id"))
        bindings = as_list(binding.get("entity_bindings"))
        if not bindings:
            issues.append(issue("critical", "existing_table_binding_missing", "Existing-table enrichment requires at least one Entity row/cell binding", f"{binding_path}.entity_bindings"))
        seen_entities: set[str] = set()
        for binding_idx, item in enumerate(bindings):
            item_path = f"{binding_path}.entity_bindings[{binding_idx}]"
            if not isinstance(item, dict):
                issues.append(issue("critical", "existing_table_binding_invalid", "Existing-table Entity binding must be an object", item_path))
                continue
            entity_id = item.get("entity_id")
            observation = ids["observations"].get(item.get("observation_id"))
            if not has_text(entity_id) or entity_id not in ids["entities"]:
                issues.append(issue("critical", "existing_table_binding_entity_missing", "Existing-table binding references a missing Entity", f"{item_path}.entity_id"))
            elif entity_id in seen_entities:
                issues.append(issue("critical", "existing_table_binding_duplicate_entity", "Existing-table binding repeats an Entity", f"{item_path}.entity_id"))
            else:
                seen_entities.add(str(entity_id))
            if not isinstance(observation, dict) or observation.get("source_id") != source_id or observation.get("entity_id") != entity_id:
                issues.append(issue("critical", "existing_table_binding_observation_mismatch", "Existing-table binding must use a same-Entity Observation from the bound Source", f"{item_path}.observation_id"))
            elif observation.get("page_or_dom_locator") != item.get("row_or_cell_locator"):
                issues.append(issue("critical", "existing_table_binding_locator_mismatch", "Existing-table row/cell locator must equal its Observation locator", f"{item_path}.row_or_cell_locator"))
            literal = item.get("entity_literal")
            if not has_text(literal):
                issues.append(issue("critical", "existing_table_binding_entity_literal_missing", "Existing-table binding requires a visible Entity literal from the bound row/cell", f"{item_path}.entity_literal"))
            elif isinstance(observation, dict) and not text_contains_exact_phrase(observation.get("raw_excerpt"), literal):
                issues.append(issue("critical", "existing_table_binding_literal_not_in_observation", "Existing-table Entity literal must appear verbatim in its bound row/cell Observation", f"{item_path}.entity_literal"))
            entity = ids["entities"].get(entity_id)
            if has_text(literal) and not entity_matches_identity_literal(entity, literal):
                issues.append(issue("critical", "existing_table_binding_literal_entity_mismatch", "Existing-table Entity literal must exactly identify the bound Entity", f"{item_path}.entity_literal"))
    return issues


def _query_group_ids(plan: dict[str, Any] | None) -> set[str]:
    result: set[str] = set()
    if not isinstance(plan, dict):
        return result
    for group in as_list(plan.get("query_groups")):
        if not isinstance(group, dict):
            continue
        for field in ("group_id", "query_group_id", "query_purpose", "purpose"):
            if has_text(group.get(field)):
                result.add(str(group.get(field)))
                break
    return result


def _valid_timestamp(value: Any) -> bool:
    if not has_text(value):
        return False
    try:
        datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _geography_support_is_formal(
    claim: dict[str, Any],
    entity_id: Any,
    target_literals: list[str],
    geography_contract: dict[str, Any],
    rule: dict[str, Any] | None,
    ids: dict[str, dict[str, dict[str, Any]]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> bool:
    """Require a same-Entity public source literal for a geography decision."""
    allowed_types = set(as_list(geography_contract.get("allowed_claim_types")))
    rule_allowed_types = set(as_list(rule.get("allowed_claim_types"))) if isinstance(rule, dict) else set()
    if (
        not target_literals
        or claim.get("entity_id") != entity_id
        or claim.get("claim_type") not in allowed_types
        or claim.get("claim_type") not in rule_allowed_types
    ):
        return False
    typed_value = json.dumps(claim.get("typed_value"), ensure_ascii=False)
    if not any(text_contains_exact_phrase(typed_value, literal) for literal in target_literals):
        return False
    for evidence in evidence_by_claim.get(str(claim.get("claim_id")), []):
        if evidence.get("relation") != "supports":
            continue
        observation = ids["observations"].get(evidence.get("observation_id"))
        source = ids["sources"].get(observation.get("source_id")) if isinstance(observation, dict) else None
        if not isinstance(observation, dict) or not isinstance(source, dict):
            continue
        if (
            observation.get("entity_id") != entity_id
            or observation.get("access_status") in BLOCKED_ACCESS
            or observation.get("capability") not in CLAIM_SUPPORT_ALLOWED_CAPABILITIES
            or source.get("provenance") != "discovered_public"
            or not source_evidence_scope(source, observation, "assessment_basis")[0]
        ):
            continue
        if geography_contract.get("source_relation_requirement") == "first_party_only" and source.get("publisher_relation") != "first_party":
            continue
        if any(text_contains_exact_phrase(observation.get("raw_excerpt"), literal) for literal in target_literals):
            return True
    return False


def _search_log_issues(
    graph: dict[str, Any],
    ids: dict[str, dict[str, dict[str, Any]]],
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    current = current_run(graph)
    logs_by_id = ids["search_logs"]
    candidate_refs: dict[str, set[str]] = {}
    for idx, log in enumerate(ensure_list(graph, "search_logs")):
        if not isinstance(log, dict):
            continue
        path = f"search_logs[{idx}]"
        for field, collection in (("run_id", "runs"), ("brief_id", "briefs"), ("plan_id", "plans")):
            raw = log.get(field)
            if not has_text(raw) or raw not in ids[collection]:
                issues.append(issue("critical", "search_log_reference_missing", f"SearchLog references missing {field}", f"{path}.{field}"))
        run = ids["runs"].get(log.get("run_id"))
        brief = ids["briefs"].get(log.get("brief_id"))
        plan = ids["plans"].get(log.get("plan_id"))
        if isinstance(run, dict):
            if log.get("brief_id") != run.get("brief_id") or log.get("plan_id") != run.get("plan_id"):
                issues.append(issue("critical", "search_log_run_binding_mismatch", "SearchLog Brief/Plan must match its Run", path))
            reports = adapter_reports_from_run(run)
            if not reports:
                issues.append(issue("critical", "search_log_adapter_missing", "SearchLog requires a verified Run capability adapter for its concrete search tool", f"{path}.concrete_tool"))
            else:
                adapter_result = resolve_capability_adapter_reports(reports)
                if not codex_adapter_allows_observation(adapter_result, "search.web", log.get("concrete_tool")):
                    issues.append(issue("critical", "search_log_tool_not_allowed_by_adapter", "SearchLog concrete_tool is not authorized by this Run's verified search provider", f"{path}.concrete_tool"))
            capabilities = run.get("capabilities")
            if not isinstance(capabilities, dict) or capabilities.get("search.web") != "available":
                issues.append(issue("critical", "search_log_capability_not_available", "SearchLog requires an explicit search.web=available Run capability", f"{path}.capability"))
        contract = customer_selection_contract(brief)
        if isinstance(plan, dict):
            allowed_group_ids = _query_group_ids(plan)
            if allowed_group_ids and log.get("query_group_id") not in allowed_group_ids:
                issues.append(issue("critical", "search_log_query_group_missing", "SearchLog query_group_id must match a query group in its Plan", f"{path}.query_group_id"))
        if not isinstance(contract, dict):
            issues.append(issue("critical", "search_log_contract_missing", "SearchLog requires the Brief customer selection contract", path))
        else:
            selection_rules, _ = targeting_rule_maps(contract)
            if log.get("customer_selection_contract_id") != contract.get("targeting_contract_id"):
                issues.append(issue("critical", "search_log_contract_mismatch", "SearchLog customer_selection_contract_id must match its Brief", f"{path}.customer_selection_contract_id"))
            if log.get("selection_rule_id") not in selection_rules:
                issues.append(issue("critical", "search_log_selection_rule_missing", "SearchLog selection_rule_id must be a current Brief selection rule", f"{path}.selection_rule_id"))
        if log.get("capability") != "search.web":
            issues.append(issue("critical", "search_log_capability_invalid", "SearchLog capability must be search.web", f"{path}.capability"))
        if not has_text(log.get("concrete_tool")) or str(log.get("concrete_tool")) in {"curl", "wget", "python_requests"}:
            issues.append(issue("critical", "search_log_concrete_tool_invalid", "SearchLog concrete_tool must identify the search provider, not a source-opening reader", f"{path}.concrete_tool"))
        if not _valid_timestamp(log.get("queried_at")):
            issues.append(issue("critical", "search_log_queried_at_missing", "SearchLog requires queried_at", f"{path}.queried_at"))
        if not has_text(log.get("query_text")):
            issues.append(issue("critical", "search_log_query_missing", "SearchLog requires a non-empty query_text", f"{path}.query_text"))
        if contains_local_path(log.get("query_text")) or "file:" in str(log.get("query_text") or "").casefold():
            issues.append(issue("critical", "search_log_query_contains_local_path", "SearchLog query_text must not contain a local path or file URI", f"{path}.query_text"))
        if __import__("re").search(r"(?i)\b(?:cookie|authorization|bearer|api[_ -]?key|access[_ -]?token|password)\b", str(log.get("query_text") or "")):
            issues.append(issue("critical", "search_log_query_contains_sensitive_data", "SearchLog query_text must not contain secret or credential material", f"{path}.query_text"))
        if log.get("result_use") not in SEARCH_LOG_RESULT_USES:
            issues.append(issue("critical", "search_log_result_use_invalid", "SearchLog result_use is invalid", f"{path}.result_use"))
        geography = [item for item in as_list(log.get("targeted_geography_literals")) if has_text(item)]
        if not geography or len(geography) != len(as_list(log.get("targeted_geography_literals"))):
            issues.append(issue("critical", "search_log_geography_missing", "SearchLog requires explicit non-empty targeted_geography_literals", f"{path}.targeted_geography_literals"))
        if isinstance(contract, dict):
            geography_contract = contract.get("geography_contract")
            if not isinstance(geography_contract, dict):
                issues.append(issue("critical", "search_log_geography_contract_missing", "SearchLog requires a current Brief geography contract", path))
            else:
                allowed_geography = normalize_region_values(geography_contract.get("included_geography_literals"))
                if not normalize_region_values(geography).issubset(allowed_geography):
                    issues.append(issue("critical", "search_log_target_geography_mismatch", "SearchLog targeted geography must be drawn from current Brief literals", f"{path}.targeted_geography_literals"))
                if log.get("selection_rule_id") not in set(as_list(geography_contract.get("required_selection_rule_ids"))):
                    issues.append(issue("critical", "search_log_geography_rule_mismatch", "SearchLog selection_rule_id must be a Brief geography selection rule", f"{path}.selection_rule_id"))
        for ref_idx, ref in enumerate(as_list(log.get("result_refs"))):
            ref_path = f"{path}.result_refs[{ref_idx}]"
            if not isinstance(ref, dict):
                issues.append(issue("critical", "search_log_result_ref_invalid", "SearchLog result_refs must be structured candidate locators", ref_path))
                continue
            candidate_id = ref.get("candidate_id")
            if not is_safe_public_http_url(ref.get("result_url")):
                issues.append(issue("critical", "search_log_result_url_not_public", "SearchLog result_url must be a safe public HTTP(S) locator", f"{ref_path}.result_url"))
            for field in ("result_title", "result_locator"):
                value = ref.get(field)
                if contains_local_path(value) or "file:" in str(value or "").casefold():
                    issues.append(issue("critical", "search_log_result_ref_contains_local_path", "SearchLog result locator fields must not contain a local path or file URI", f"{ref_path}.{field}"))
                if __import__("re").search(r"(?i)\b(?:cookie|authorization|bearer|api[_ -]?key|access[_ -]?token|password)\b", str(value or "")):
                    issues.append(issue("critical", "search_log_result_ref_contains_sensitive_data", "SearchLog result locator fields must not contain secret or credential material", f"{ref_path}.{field}"))
            candidate = ids["candidates"].get(candidate_id)
            if not isinstance(candidate, dict):
                issues.append(issue("critical", "search_log_candidate_missing", "SearchLog result ref must point to an existing Candidate", f"{ref_path}.candidate_id"))
                continue
            candidate_refs.setdefault(str(candidate_id), set()).add(str(log.get("search_log_id")))
            if candidate.get("discovery_method") == "search_web" and candidate.get("search_log_id") != log.get("search_log_id"):
                issues.append(issue("critical", "search_log_candidate_reverse_link_missing", "SearchLog candidate ref must agree with Candidate.search_log_id", ref_path))
    for idx, candidate in enumerate(ensure_list(graph, "candidates")):
        if not isinstance(candidate, dict) or candidate.get("discovery_method") != "search_web":
            continue
        path = f"candidates[{idx}]"
        search_log_id = candidate.get("search_log_id")
        log = logs_by_id.get(search_log_id)
        if not isinstance(log, dict):
            issues.append(issue("critical", "search_web_candidate_without_search_log", "search_web Candidate requires a formal same-run SearchLog", f"{path}.search_log_id"))
            continue
        if any(candidate.get(field) != log.get(field) for field in ("run_id", "brief_id", "plan_id")):
            issues.append(issue("critical", "search_web_candidate_binding_mismatch", "search_web Candidate Run/Brief/Plan must match its SearchLog", path))
        if str(search_log_id) not in candidate_refs.get(str(candidate.get("candidate_id")), set()):
            issues.append(issue("critical", "search_log_candidate_result_ref_missing", "search_web Candidate must appear in its SearchLog result_refs", path))
    has_search_artifact = any(
        isinstance(item, dict) and item.get("capability") == "search.web"
        for item in ensure_list(graph, "observations")
    ) or any(
        isinstance(item, dict) and item.get("medium") == "search_result"
        for item in ensure_list(graph, "sources")
    )
    if has_search_artifact:
        issues.append(issue("critical", "search_result_must_not_be_source_or_observation", "SearchLog is the only formal search-result record; open sources separately before Observation", "sources/observations"))
    return issues


def validate_graph(graph: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    issues.extend(_schema_validation_issues(graph))
    ids = all_id_maps(graph)
    current_hash = graph_hash(graph)
    current_subject_hash = review_subject_hash(graph)
    expected_review_snapshot = review_provenance_snapshot(graph)
    issues.extend(validate_current_review_attestation(graph))
    issues.extend(_search_log_issues(graph, ids))
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
            for field in ("executor_actor_id", "execution_session_id"):
                if has_text(run.get(field)) and not is_safe_anonymous_id(run.get(field)):
                    issues.append(issue(
                        "critical",
                        "run_execution_identity_not_opaque",
                        "Run execution identity must be a short opaque host/session ID, not a name, email, token, cookie, or path",
                        f"runs[{idx}].{field}",
                    ))
            brief_id = run.get("brief_id")
            plan_id = run.get("plan_id")
            if brief_id and brief_id not in ids["briefs"]:
                issues.append(issue("major", "run_brief_missing", f"Run references missing Brief {brief_id}", f"runs[{idx}].brief_id"))
            if plan_id and plan_id not in ids["plans"]:
                issues.append(issue("major", "run_plan_missing", f"Run references missing Plan {plan_id}", f"runs[{idx}].plan_id"))
            reports = adapter_reports_from_run(run)
            capabilities = run.get("capabilities")
            platform = run.get("platform")
            if not is_canonical_platform_id(platform):
                issues.append(issue(
                    "critical",
                    "run_platform_not_canonical",
                    "Run platform must be a non-empty canonical host ID, not a concrete tool or variant spelling",
                    f"runs[{idx}].platform",
                ))
            native_capability_declared = (
                platform == "codex_cli"
                and isinstance(capabilities, dict)
                and any(capabilities.get(capability) == "available" for capability in (
                    *CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES,
                    *CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES,
                ))
            )
            if native_capability_declared and not reports:
                issues.append(issue(
                    "critical",
                    "codex_native_capability_adapter_required",
                    "Codex CLI search/source capability requires a valid, explicit capability adapter report",
                    f"runs[{idx}].capability_adapter_reports",
                ))
            if reports:
                adapter_result = resolve_capability_adapter_reports(reports)
                for report_index, report in enumerate(reports):
                    report_platform = report.get("platform") if isinstance(report, dict) else None
                    if not is_canonical_platform_id(report_platform):
                        issues.append(issue(
                            "critical",
                            "run_platform_not_canonical",
                            "Capability adapter report platform must be a canonical host ID",
                            f"runs[{idx}].capability_adapter_reports[{report_index}].platform",
                        ))
                    if report_platform != platform:
                        issues.append(issue(
                            "critical",
                            "capability_adapter_run_platform_mismatch",
                            "Capability adapter report platform must match its Run platform",
                            f"runs[{idx}].capability_adapter_reports[{report_index}].platform",
                        ))
                for adapter_issue in adapter_result["issues"]:
                    issues.append(issue(
                        "critical",
                        str(adapter_issue["code"]),
                        str(adapter_issue["message"]),
                        f"runs[{idx}].{adapter_issue['path']}",
                    ))
                if not isinstance(capabilities, dict):
                    issues.append(issue("critical", "capability_adapter_run_mapping_missing", "Run capability adapter reports require canonical Run capabilities", f"runs[{idx}].capabilities"))
                else:
                    for capability in adapter_result["owned_capabilities"]:
                        expected_status = adapter_result["mapped_capabilities"][capability]
                        if capabilities.get(capability) != expected_status:
                            issues.append(issue(
                                "critical",
                                "capability_adapter_run_mapping_mismatch",
                                f"Run {capability} must match the verified capability adapter mapping",
                                f"runs[{idx}].capabilities.{capability}",
                            ))

    run_items = ensure_list(graph, "runs")
    valid_runs = [run for run in run_items if isinstance(run, dict) and has_text(run.get("run_id"))]
    multi_run_graph = len(run_items) > 1
    sole_run = valid_runs[0] if len(valid_runs) == 1 else None
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
        observation_run_id = obs.get("run_id")
        observation_run: dict[str, Any] | None = None
        if multi_run_graph:
            if not has_text(observation_run_id):
                issues.append(issue("critical", "observation_run_id_missing", "A multi-Run graph requires every Observation to declare its Run", f"observations[{idx}].run_id"))
            elif observation_run_id not in ids["runs"]:
                issues.append(issue("critical", "observation_run_missing", "Observation references a missing Run", f"observations[{idx}].run_id"))
            else:
                observation_run = ids["runs"].get(observation_run_id)
        elif has_text(observation_run_id):
            if observation_run_id not in ids["runs"]:
                issues.append(issue("critical", "observation_run_missing", "Observation references a missing Run", f"observations[{idx}].run_id"))
            else:
                observation_run = ids["runs"].get(observation_run_id)
        else:
            observation_run = sole_run
        source = ids["sources"].get(sid)
        observation_reports = adapter_reports_from_run(observation_run)
        if isinstance(observation_run, dict) and observation_reports:
            capabilities = observation_run.get("capabilities")
            capability = obs.get("capability")
            # A Run with a native adapter report must explicitly account for
            # every capability used to collect an Observation. The adapter owns
            # only search/source, but an undeclared independent capability is
            # still unverified for this Run and cannot support formal evidence.
            if not isinstance(capabilities, dict) or capabilities.get(capability) != "available":
                issues.append(issue(
                    "critical",
                    "run_capability_not_available_for_observation",
                    f"Observation uses {capability}, but its Run host capability report did not verify it as available",
                    f"observations[{idx}].capability",
                ))
            if observation_run.get("platform") == "codex_cli" and str(obs.get("concrete_tool")) in {
                "curl", "wget", "python_requests"
            } and capability != "source.open":
                issues.append(issue(
                    "critical",
                    "codex_shell_http_tool_capability_mismatch",
                    "Codex shell HTTP concrete_tool may be used only for source.open Observations",
                    f"observations[{idx}].capability",
                ))
            if observation_run.get("platform") == "codex_cli" and capability in {
                "search.web", "source.open"
            }:
                adapter_result = resolve_capability_adapter_reports(observation_reports)
                if not codex_adapter_allows_observation(adapter_result, capability, obs.get("concrete_tool")):
                    issues.append(issue(
                        "critical",
                        "codex_observation_concrete_tool_not_allowed_by_adapter",
                        "Codex search/source Observation concrete_tool is not explicitly authorized by a verified provider",
                        f"observations[{idx}].concrete_tool",
                    ))
                if capability == "source.open" and str(obs.get("concrete_tool")) in {"curl", "wget", "python_requests"}:
                    if (
                        not isinstance(source, dict)
                        or not is_safe_public_http_url(source.get("canonical_url"))
                        or not is_safe_public_http_url(source.get("final_url"))
                    ):
                        issues.append(issue(
                            "critical",
                            "codex_shell_http_observation_url_not_public",
                            "Codex shell HTTP Observation requires public credential-free HTTP(S) Source URLs",
                            f"observations[{idx}].source_id",
                        ))
                    if contains_shell_http_forbidden_data({
                        "canonical_url": source.get("canonical_url") if isinstance(source, dict) else None,
                        "final_url": source.get("final_url") if isinstance(source, dict) else None,
                        "title": obs.get("title"), "raw_excerpt": obs.get("raw_excerpt"),
                        "page_or_dom_locator": obs.get("page_or_dom_locator"),
                        "extraction_method": obs.get("extraction_method"),
                    }):
                        issues.append(issue(
                            "critical",
                            "codex_shell_http_observation_forbidden_data",
                            "Codex shell HTTP Observation may not contain local paths or credential/request-secret data",
                            f"observations[{idx}]",
                        ))
        elif isinstance(observation_run, dict) and observation_run.get("platform") == "codex_cli" and obs.get("capability") in CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES:
            issues.append(issue(
                "critical",
                "codex_native_capability_adapter_required",
                "Codex CLI native search/source Observation requires a valid capability adapter report on its Run",
                f"observations[{idx}].capability",
            ))
        if isinstance(source, dict) and source.get("provenance") in {"user_provided", "manual_input", "connected_account"}:
            for field in ("title", "raw_excerpt", "page_or_dom_locator", "extraction_method", "snapshot_ref"):
                if contains_local_path(obs.get(field)):
                    issues.append(issue("critical", "local_path_in_material_metadata", f"User material Observation contains a local path in {field}", f"observations[{idx}].{field}"))

    for idx, source in enumerate(ensure_list(graph, "sources")):
        if not isinstance(source, dict): continue
        for field in ("publisher_relation", "provenance", "medium", "access_boundary"):
            if not has_text(source.get(field)):
                issues.append(issue("major", "source_missing_required_context", f"Source {source.get('source_id')} lacks {field}", f"sources[{idx}].{field}"))
        if source.get("provenance") == "discovered_public" and not source_has_safe_public_http_urls(source):
            issues.append(issue(
                "critical",
                "public_source_url_not_safe",
                "A discovered_public Source requires only strict public credential-free HTTP(S) URLs",
                f"sources[{idx}]",
            ))
        if source.get("provenance") in {"user_provided", "manual_input", "connected_account"}:
            role = source.get("material_role")
            if not has_text(role):
                issues.append(issue("critical", "material_role_missing", f"User material Source {source.get('source_id')} lacks material_role", f"sources[{idx}].material_role"))
            elif role not in MATERIAL_ROLES:
                issues.append(issue("critical", "material_role_invalid", f"User material Source {source.get('source_id')} has invalid material_role {role}", f"sources[{idx}].material_role"))
            for field in ("canonical_url", "final_url", "access_boundary", "owner_hint", "artifact_name", "artifact_media_type", "sender_literal", "subject_literal", "mailbox_ref"):
                if contains_local_path(source.get(field)):
                    issues.append(issue("critical", "local_path_in_material_metadata", f"User material Source contains a local path in {field}", f"sources[{idx}].{field}"))
        if source.get("provenance") == "user_provided" and source.get("medium") in ARTIFACT_MEDIA:
            if not has_text(source.get("artifact_sha256")):
                issues.append(issue("critical", "user_provided_artifact_hash_missing", f"User-provided Source {source.get('source_id')} lacks artifact_sha256", f"sources[{idx}].artifact_sha256"))
            elif not __import__("re").fullmatch(r"[a-f0-9]{64}", str(source.get("artifact_sha256"))):
                issues.append(issue("critical", "user_provided_artifact_hash_invalid", f"User-provided Source {source.get('source_id')} has invalid artifact_sha256", f"sources[{idx}].artifact_sha256"))
            if not has_text(source.get("artifact_name")) or any(token in str(source.get("artifact_name") or "") for token in ("/", "\\", ":", "..")):
                issues.append(issue("critical", "user_provided_artifact_name_invalid", f"User-provided Source {source.get('source_id')} has unsafe artifact_name", f"sources[{idx}].artifact_name"))
        if source.get("provenance") == "connected_account" and source.get("medium") in {"document", "spreadsheet", "image"}:
            if not has_text(source.get("artifact_sha256")):
                issues.append(issue("critical", "user_provided_artifact_hash_missing", f"Connected attachment Source {source.get('source_id')} lacks artifact_sha256", f"sources[{idx}].artifact_sha256"))
            elif not __import__("re").fullmatch(r"[a-f0-9]{64}", str(source.get("artifact_sha256"))):
                issues.append(issue("critical", "user_provided_artifact_hash_invalid", f"Connected attachment Source {source.get('source_id')} has invalid artifact_sha256", f"sources[{idx}].artifact_sha256"))
            if not has_text(source.get("artifact_name")) or any(token in str(source.get("artifact_name") or "") for token in ("/", "\\", ":", "..")):
                issues.append(issue("critical", "user_provided_artifact_name_invalid", f"Connected attachment Source {source.get('source_id')} has unsafe artifact_name", f"sources[{idx}].artifact_name"))
        if source.get("provenance") == "connected_account":
            if source.get("medium") == "correspondence":
                required = ("message_id", "received_at", "sender_literal", "subject_literal", "message_content_sha256", "mailbox_ref")
                if any(not has_text(source.get(field)) for field in required):
                    issues.append(issue("critical", "connected_mail_metadata_missing", f"Connected mail Source {source.get('source_id')} lacks required metadata", f"sources[{idx}]"))
                if source.get("material_role") != "connected_inbound_correspondence":
                    issues.append(issue("critical", "connected_mail_material_role_invalid", "Connected mail Source must use connected_inbound_correspondence", f"sources[{idx}].material_role"))
                if source.get("direction") != "inbound":
                    issues.append(issue("critical", "connected_mail_direction_not_inbound", "Connected mail Source must be inbound", f"sources[{idx}].direction"))
                if source.get("access_boundary") != "read_only_connected_account":
                    issues.append(issue("critical", "connected_mail_access_boundary_invalid", "Connected mail Source must have read_only_connected_account boundary", f"sources[{idx}].access_boundary"))
            elif source.get("medium") in {"document", "spreadsheet", "image"}:
                parent_id = source.get("parent_source_id")
                parent = ids["sources"].get(parent_id)
                if not has_text(parent_id) or not isinstance(parent, dict):
                    issues.append(issue("critical", "connected_attachment_parent_source_missing", "Connected mail attachment must reference its parent mail Source", f"sources[{idx}].parent_source_id"))
                elif parent.get("provenance") != "connected_account" or parent.get("medium") != "correspondence":
                    issues.append(issue("critical", "connected_attachment_parent_source_invalid", "Connected attachment parent must be a connected correspondence Source", f"sources[{idx}].parent_source_id"))

    for idx, obs in enumerate(ensure_list(graph, "observations")):
        if not isinstance(obs, dict):
            continue
        source = ids["sources"].get(obs.get("source_id"))
        if isinstance(source, dict) and source.get("provenance") == "connected_account" and source.get("medium") == "correspondence":
            eligible, reason_code = source_evidence_scope(source, obs, "candidate_clue")
            if not eligible:
                issues.append(issue("critical", reason_code, "Connected mail Observation does not meet the read-only mail evidence contract", f"observations[{idx}]"))

    inquiry_statuses = {"new", "triaged", "needs_entity_resolution", "ready_for_follow_up", "closed"}
    for idx, inquiry in enumerate(ensure_list(graph, "inquiries")):
        if not isinstance(inquiry, dict):
            continue
        for field, collection in (("run_id", "runs"), ("source_id", "sources"), ("observation_id", "observations")):
            value = inquiry.get(field)
            if not has_text(value) or value not in ids[collection]:
                issues.append(issue("critical", "inquiry_reference_missing", f"Inquiry {inquiry.get('inquiry_id')} references missing {field}", f"inquiries[{idx}].{field}"))
        if inquiry.get("entity_id") and inquiry.get("entity_id") not in ids["entities"]:
            issues.append(issue("major", "inquiry_entity_missing", "Inquiry references missing Entity", f"inquiries[{idx}].entity_id"))
        if inquiry.get("contact_id") and inquiry.get("contact_id") not in ids["contact_points"]:
            issues.append(issue("major", "inquiry_contact_missing", "Inquiry references missing ContactPoint", f"inquiries[{idx}].contact_id"))
        if inquiry.get("direction") != "inbound":
            issues.append(issue("critical", "inquiry_direction_not_inbound", "Inquiry direction must be inbound", f"inquiries[{idx}].direction"))
        if inquiry.get("inquiry_status") not in inquiry_statuses:
            issues.append(issue("critical", "inquiry_status_invalid", "Inquiry uses an unsupported status", f"inquiries[{idx}].inquiry_status"))
        if not has_text(inquiry.get("received_at")):
            issues.append(issue("critical", "inquiry_received_at_missing", "Inquiry requires received_at", f"inquiries[{idx}].received_at"))
        if not has_text(inquiry.get("request_excerpt")) or len(str(inquiry.get("request_excerpt") or "")) > 1000:
            issues.append(issue("critical", "inquiry_request_excerpt_invalid", "Inquiry request_excerpt must be a non-empty bounded excerpt", f"inquiries[{idx}].request_excerpt"))
        observation = ids["observations"].get(inquiry.get("observation_id"))
        source = ids["sources"].get(inquiry.get("source_id"))
        if isinstance(observation, dict) and source is not None:
            if observation.get("source_id") != inquiry.get("source_id"):
                issues.append(issue("critical", "inquiry_source_observation_mismatch", "Inquiry Source and Observation must be linked", f"inquiries[{idx}].observation_id"))
            eligible, reason_code = source_evidence_scope(source, observation, "inquiry_event")
            if not eligible:
                issues.append(issue("critical", reason_code, "Inquiry requires a qualified inbound correspondence Observation", f"inquiries[{idx}].observation_id"))
            if has_text(inquiry.get("request_excerpt")) and not text_contains(observation.get("raw_excerpt"), inquiry.get("request_excerpt")):
                issues.append(issue("critical", "inquiry_excerpt_not_in_observation", "Inquiry request_excerpt must be present in its Observation excerpt", f"inquiries[{idx}].request_excerpt"))

    allowed_mail_actions = {"create_inquiry", "create_candidate", "create_contact_with_source_note", "create_entity_resolution_task"}
    for idx, rule in enumerate(ensure_list(graph, "mail_intake_rules")):
        if not isinstance(rule, dict):
            continue
        if not as_list(rule.get("folders_or_labels")):
            issues.append(issue("critical", "mail_rule_scope_missing", "MailIntakeRule requires at least one folder or label", f"mail_intake_rules[{idx}].folders_or_labels"))
        if rule.get("mode") == "one_shot" and (not has_text(rule.get("received_after")) or not has_text(rule.get("received_before"))):
            issues.append(issue("critical", "mail_rule_scope_missing", "one_shot MailIntakeRule requires received_after and received_before", f"mail_intake_rules[{idx}]"))
        if rule.get("mode") == "continuous" and (rule.get("enabled") is not True or not has_text(rule.get("user_approved_at"))):
            issues.append(issue("critical", "mail_rule_continuous_approval_missing", "continuous MailIntakeRule must be enabled and explicitly approved", f"mail_intake_rules[{idx}]"))
        if rule.get("direction") != "inbound" or rule.get("read_only") is not True:
            issues.append(issue("critical", "mail_rule_not_read_only_inbound", "MailIntakeRule must be read-only and inbound-only", f"mail_intake_rules[{idx}]"))
        actions = as_list(rule.get("actions"))
        if not actions or any(action not in allowed_mail_actions for action in actions):
            issues.append(issue("critical", "mail_rule_mutating_action", "MailIntakeRule contains a non-permitted or mutating action", f"mail_intake_rules[{idx}].actions"))

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
        if formal_exception_mode(brief):
            issues.extend(_formal_exception_binding_issues(brief, ids, ensure_list(graph, "observations"), f"briefs[{idx}]"))
        contract = customer_selection_contract(brief)
        target_literals = [str(value) for value in as_list(brief.get("target_country_or_region")) if has_text(value)]
        if (
            targeting_contract_required(brief)
            and target_literals
            and (not isinstance(contract, dict) or not isinstance(contract.get("geography_contract"), dict))
        ):
            issues.append(issue(
                "critical",
                "geography_contract_required_for_target",
                "A non-empty target_country_or_region requires a geography_contract for new customer development",
                f"briefs[{idx}].customer_selection_contract.geography_contract",
            ))
        if isinstance(contract, dict):
            selection_rules, exclusion_rules = targeting_rule_maps(contract)
            if not has_text(contract.get("targeting_contract_id")):
                issues.append(issue("critical", "targeting_contract_id_missing", "Customer selection contract lacks targeting_contract_id", f"briefs[{idx}].customer_selection_contract.targeting_contract_id"))
            if len(selection_rules) != len(as_list(contract.get("selection_requirements"))) or len(exclusion_rules) != len(as_list(contract.get("exclusion_rules"))):
                issues.append(issue("critical", "targeting_rule_missing", "Customer selection contract contains missing or duplicate rule IDs", f"briefs[{idx}].customer_selection_contract"))
            if contract.get("scope_state") not in {"explicit", "inferred_low_risk", "provisional"}:
                issues.append(issue("critical", "targeting_scope_state_invalid", "Customer selection contract has invalid scope_state", f"briefs[{idx}].customer_selection_contract.scope_state"))
            if any(not isinstance(rule.get("allowed_claim_types"), list) or not rule.get("allowed_claim_types") or any(claim_type not in RULE_ALLOWED_CLAIM_TYPES for claim_type in rule.get("allowed_claim_types", [])) for rule in [*selection_rules.values(), *exclusion_rules.values()]):
                issues.append(issue("critical", "targeting_rule_allowed_claim_types_invalid", "Every current-direction rule requires non-empty allowed_claim_types from the generic Claim taxonomy", f"briefs[{idx}].customer_selection_contract"))
            if any(not isinstance(rule.get("evidence_markers"), list) or not rule.get("evidence_markers") for rule in selection_rules.values()):
                issues.append(issue("critical", "targeting_rule_evidence_markers_missing", "Every selection rule requires current-Brief evidence_markers", f"briefs[{idx}].customer_selection_contract.selection_requirements"))
            if any(not isinstance(rule.get("conflict_markers"), list) or not rule.get("conflict_markers") for rule in exclusion_rules.values()):
                issues.append(issue("critical", "targeting_rule_conflict_markers_missing", "Every exclusion rule requires current-Brief conflict_markers", f"briefs[{idx}].customer_selection_contract.exclusion_rules"))
            geography_contract = contract.get("geography_contract")
            if geography_contract is not None:
                if not isinstance(geography_contract, dict):
                    issues.append(issue("critical", "geography_contract_invalid", "Brief geography contract must be a strict object", f"briefs[{idx}].customer_selection_contract.geography_contract"))
                else:
                    included = normalize_region_values(geography_contract.get("included_geography_literals"))
                    normalized_target_literals = normalize_region_values(brief.get("target_country_or_region"))
                    required_selection = {str(item) for item in as_list(geography_contract.get("required_selection_rule_ids")) if has_text(item)}
                    required_exclusion = {str(item) for item in as_list(geography_contract.get("required_exclusion_rule_ids")) if has_text(item)}
                    allowed_types = {str(item) for item in as_list(geography_contract.get("allowed_claim_types")) if has_text(item)}
                    if not included:
                        issues.append(issue("critical", "geography_contract_included_literals_missing", "Brief geography contract requires included geography literals", f"briefs[{idx}].customer_selection_contract.geography_contract.included_geography_literals"))
                    if normalized_target_literals and included != normalized_target_literals:
                        issues.append(issue("critical", "geography_contract_brief_literal_mismatch", "Brief geography contract must preserve the user's target geography literals", f"briefs[{idx}].customer_selection_contract.geography_contract.included_geography_literals"))
                    if not has_text(geography_contract.get("admission_definition")):
                        issues.append(issue("critical", "geography_contract_admission_definition_missing", "Brief geography contract requires a natural-language admission definition", f"briefs[{idx}].customer_selection_contract.geography_contract.admission_definition"))
                    if not required_selection or not required_selection.issubset(selection_rules):
                        issues.append(issue("critical", "geography_contract_selection_rule_missing", "Brief geography contract must cite current selection rules", f"briefs[{idx}].customer_selection_contract.geography_contract.required_selection_rule_ids"))
                    if not required_exclusion.issubset(exclusion_rules):
                        issues.append(issue("critical", "geography_contract_exclusion_rule_missing", "Brief geography contract cites a missing exclusion rule", f"briefs[{idx}].customer_selection_contract.geography_contract.required_exclusion_rule_ids"))
                    if not allowed_types or not allowed_types.issubset(RULE_ALLOWED_CLAIM_TYPES):
                        issues.append(issue("critical", "geography_contract_claim_types_invalid", "Brief geography contract requires permitted generic Claim types", f"briefs[{idx}].customer_selection_contract.geography_contract.allowed_claim_types"))
                    if not isinstance(geography_contract.get("source_relation_requirement"), str):
                        issues.append(issue("critical", "geography_contract_source_requirement_missing", "Brief geography contract requires its source relation requirement", f"briefs[{idx}].customer_selection_contract.geography_contract.source_relation_requirement"))

    for idx, plan in enumerate(ensure_list(graph, "plans")):
        if not isinstance(plan, dict): continue
        for field in PLAN_REQUIRED_FIELDS:
            value = plan.get(field)
            if not has_text(value) and not as_list(value) and not isinstance(value, dict):
                issues.append(issue("major", "plan_missing_required_field", f"Plan {plan.get('plan_id')} lacks {field}", f"plans[{idx}].{field}"))
        if plan.get("brief_id") not in ids["briefs"]:
            issues.append(issue("major", "plan_brief_missing", f"Plan {plan.get('plan_id')} references missing Brief {plan.get('brief_id')}", f"plans[{idx}].brief_id"))
            continue
        brief = ids["briefs"].get(plan.get("brief_id"))
        contract = customer_selection_contract(brief)
        if isinstance(contract, dict):
            selection_rules, exclusion_rules = targeting_rule_maps(contract)
            if plan.get("selection_contract_brief_id") != plan.get("brief_id"):
                issues.append(issue("critical", "targeting_contract_brief_mismatch", "Plan must bind the customer selection contract to its Brief", f"plans[{idx}].selection_contract_brief_id"))
            if set(as_list(plan.get("selection_requirement_ids"))) != set(selection_rules):
                issues.append(issue("critical", "plan_selection_requirement_ids_mismatch", "Plan must list every current Brief selection rule", f"plans[{idx}].selection_requirement_ids"))
            if set(as_list(plan.get("exclusion_rule_ids"))) != set(exclusion_rules):
                issues.append(issue("critical", "plan_exclusion_rule_ids_mismatch", "Plan must list every current Brief exclusion rule", f"plans[{idx}].exclusion_rule_ids"))
            query_groups = [group for group in as_list(plan.get("query_groups")) if isinstance(group, dict)]
            covered_ids = {rule_id for group in query_groups for rule_id in as_list(group.get("targeting_rule_ids"))}
            expected_ids = set(selection_rules) | set(exclusion_rules)
            if not expected_ids.issubset(covered_ids):
                issues.append(issue("critical", "plan_query_group_missing_targeting_rule", "Every customer-selection rule needs a linked query or check step", f"plans[{idx}].query_groups"))
            group_names = {str(group.get("group_id") or group.get("query_purpose") or group.get("purpose") or "") for group in query_groups}
            if not set(as_list(plan.get("positive_query_groups"))).issubset(group_names) or not set(as_list(plan.get("exclusion_check_query_groups"))).issubset(group_names):
                issues.append(issue("major", "plan_targeting_query_group_missing", "Plan targeting query references must name actual query groups", f"plans[{idx}]"))
            if contract.get("scope_state") == "provisional" and plan.get("sample_first_limit") not in {1, 2, 3, 4, 5}:
                issues.append(issue("critical", "provisional_scope_sample_limit_missing", "Provisional customer direction requires a 1-5 sample-first limit", f"plans[{idx}].sample_first_limit"))
            if contract.get("sample_first_required") is True and plan.get("sample_first_limit") not in {1, 2, 3, 4, 5}:
                issues.append(issue("critical", "sample_first_limit_missing", "sample_first_required requires a 1-5 sample-first limit", f"plans[{idx}].sample_first_limit"))
            geography_contract = contract.get("geography_contract")
            if isinstance(geography_contract, dict):
                group_names = {str(group.get("group_id") or group.get("query_purpose") or group.get("purpose") or "") for group in query_groups}
                geography_groups = {str(item) for item in as_list(plan.get("geography_query_group_ids")) if has_text(item)}
                if not geography_groups or not geography_groups.issubset(group_names):
                    issues.append(issue("critical", "plan_geography_query_group_missing", "Plan must record valid geography query groups for the Brief geography contract", f"plans[{idx}].geography_query_group_ids"))
                geography_rules = {str(item) for item in as_list(geography_contract.get("required_selection_rule_ids")) if has_text(item)}
                covered_geography_rules = {
                    str(rule_id) for group in query_groups
                    if str(group.get("group_id") or group.get("query_purpose") or group.get("purpose") or "") in geography_groups
                    for rule_id in as_list(group.get("targeting_rule_ids"))
                }
                if not geography_rules.issubset(covered_geography_rules):
                    issues.append(issue("critical", "plan_geography_rule_not_covered", "Plan geography query groups must link every required geography selection rule", f"plans[{idx}].geography_query_group_ids"))

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
            eligible, reason_code = source_evidence_scope(source, obs, "formal_claim")
            if not eligible:
                issues.append(issue("critical", reason_code, "ClaimEvidence support does not meet the formal source eligibility contract", f"claim_evidence[{idx}].observation_id"))
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

    # Search result records are discovery-only.  They cannot be promoted into
    # any formal conclusion even through an indirect scope classification.
    search_log_ids = set(ids["search_logs"])
    for idx, assessment in enumerate(ensure_list(graph, "assessments")):
        if isinstance(assessment, dict) and any(key in assessment for key in ("search_log_id", "search_log_ids", "query_text", "result_refs")):
            issues.append(issue("critical", "search_log_directly_in_assessment", "Assessment must cite Claims, never SearchLog data", f"assessments[{idx}]"))
    for idx, decision in enumerate(ensure_list(graph, "scope_decisions")):
        if isinstance(decision, dict) and any(key in decision for key in ("search_log_id", "search_log_ids", "query_text", "result_refs")):
            issues.append(issue("critical", "search_log_directly_in_scope_decision", "ScopeDecision must rely on formal Claims, never SearchLog data", f"scope_decisions[{idx}]"))

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
                allowed_capabilities = CONTACT_NOTE_ALLOWED_CAPABILITIES if export_status == "export_with_source_note" else CONTACT_SOURCE_ALLOWED_CAPABILITIES
                if not isinstance(contact_obs, dict) or contact_obs.get("capability") not in allowed_capabilities:
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
            contact_purpose = "contact_ready" if export_status == "ready" else "contact_with_source_note"
            for contact_obs, label in ((source_obs, "source"), (assoc_obs, "association")):
                contact_source = ids["sources"].get(contact_obs.get("source_id")) if isinstance(contact_obs, dict) else None
                eligible, reason_code = source_evidence_scope(contact_source, contact_obs, contact_purpose)
                if not eligible:
                    issues.append(issue("critical", reason_code, f"Exportable ContactClaim {label} Observation does not meet the formal source eligibility contract", f"contact_claims[{idx}].{label}_observation"))
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

    scope_decisions_by_id: dict[str, dict[str, Any]] = {}
    for idx, decision in enumerate(ensure_list(graph, "scope_decisions")):
        if not isinstance(decision, dict):
            continue
        decision_id = decision.get("scope_decision_id")
        if has_text(decision_id):
            scope_decisions_by_id[str(decision_id)] = decision
        brief = ids["briefs"].get(decision.get("brief_id"))
        run = ids["runs"].get(decision.get("run_id"))
        entity_id = decision.get("entity_id")
        candidate_id = decision.get("candidate_id")
        if not isinstance(brief, dict):
            issues.append(issue("critical", "scope_decision_brief_missing", "ScopeDecision references a missing Brief", f"scope_decisions[{idx}].brief_id"))
            continue
        contract = customer_selection_contract(brief)
        if not isinstance(contract, dict):
            issues.append(issue("critical", "brief_targeting_contract_missing", "ScopeDecision Brief lacks a customer selection contract", f"scope_decisions[{idx}].brief_id"))
            continue
        if not isinstance(run, dict):
            issues.append(issue("critical", "scope_decision_run_missing", "ScopeDecision references a missing Run", f"scope_decisions[{idx}].run_id"))
        elif run.get("brief_id") != decision.get("brief_id"):
            issues.append(issue("critical", "scope_decision_run_mismatch", "ScopeDecision Run must belong to the same Brief", f"scope_decisions[{idx}].run_id"))
        if decision.get("targeting_contract_id") != contract.get("targeting_contract_id"):
            issues.append(issue("critical", "targeting_contract_brief_mismatch", "ScopeDecision targeting contract must match its Brief", f"scope_decisions[{idx}].targeting_contract_id"))
        if entity_id is not None and entity_id not in ids["entities"]:
            issues.append(issue("critical", "scope_decision_entity_missing", "ScopeDecision references a missing Entity", f"scope_decisions[{idx}].entity_id"))
        if candidate_id is not None and candidate_id not in ids["candidates"]:
            issues.append(issue("major", "scope_decision_candidate_missing", "ScopeDecision references a missing Candidate", f"scope_decisions[{idx}].candidate_id"))
        if not has_text(entity_id) and not has_text(candidate_id):
            issues.append(issue("critical", "scope_decision_subject_missing", "ScopeDecision needs an Entity or Candidate", f"scope_decisions[{idx}]"))
        if decision.get("overall_status") not in SCOPE_DECISION_STATUSES:
            issues.append(issue("critical", "scope_decision_status_invalid", "ScopeDecision uses an invalid workflow status", f"scope_decisions[{idx}].overall_status"))
        if not has_text(entity_id) and decision.get("overall_status") == "in_scope":
            issues.append(issue("critical", "scope_decision_entity_required_for_in_scope", "An in-scope decision must resolve to an Entity before formal delivery", f"scope_decisions[{idx}].entity_id"))
        if not has_text(entity_id) and decision.get("overall_status") not in {"needs_confirmation", "reference_only"}:
            issues.append(issue("critical", "scope_decision_entity_required_for_status", "Candidate-only ScopeDecision may only remain needs_confirmation or reference_only", f"scope_decisions[{idx}].overall_status"))
        selection_rules, exclusion_rules = targeting_rule_maps(contract)
        geography_contract = contract.get("geography_contract") if isinstance(contract, dict) else None
        evaluations = [item for item in as_list(decision.get("rule_evaluations")) if isinstance(item, dict)]
        evaluation_by_key: dict[tuple[str, str], dict[str, Any]] = {}
        for eval_idx, evaluation in enumerate(evaluations):
            rule_id = evaluation.get("rule_id")
            rule_kind = evaluation.get("rule_kind")
            key = (str(rule_kind), str(rule_id))
            if key in evaluation_by_key:
                issues.append(issue("critical", "scope_decision_rule_duplicate", "ScopeDecision evaluates the same rule more than once", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}]"))
            evaluation_by_key[key] = evaluation
            expected_rules = selection_rules if rule_kind == "selection" else exclusion_rules if rule_kind == "exclusion" else {}
            if rule_kind not in {"selection", "exclusion"} or rule_id not in expected_rules:
                issues.append(issue("critical", "scope_decision_rule_missing", "ScopeDecision references a rule not present in its Brief contract", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].rule_id"))
            if evaluation.get("outcome") not in SCOPE_RULE_OUTCOMES:
                issues.append(issue("critical", "scope_decision_rule_outcome_invalid", "ScopeDecision rule has invalid outcome", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].outcome"))
            if evaluation.get("outcome") == "not_observed" and not as_list(evaluation.get("reviewed_observation_ids")):
                issues.append(issue("critical", "scope_decision_not_observed_without_review", "not_observed requires at least one reviewed Observation and does not prove absence", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].reviewed_observation_ids"))
            rule = expected_rules.get(rule_id) if isinstance(expected_rules, dict) else None
            classifications = [item for item in as_list(evaluation.get("claim_classifications")) if isinstance(item, dict)]
            classification_by_claim: dict[str, dict[str, Any]] = {}
            for class_idx, classification in enumerate(classifications):
                claim_id = classification.get("claim_id")
                classification_kind = classification.get("classification")
                class_path = f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].claim_classifications[{class_idx}]"
                if not has_text(claim_id) or claim_id in classification_by_claim:
                    issues.append(issue("critical", "scope_rule_evidence_classification_missing", "Each reviewed Claim requires one unique evidence classification", class_path))
                    continue
                classification_by_claim[str(claim_id)] = classification
                if classification_kind not in SCOPE_CLAIM_CLASSIFICATIONS:
                    issues.append(issue("critical", "scope_rule_evidence_classification_missing", "Scope rule Claim classification is invalid", class_path))
                    continue
                claim = ids["claims"].get(claim_id)
                if not isinstance(claim, dict):
                    issues.append(issue("critical", "scope_decision_rule_claim_missing", "ScopeDecision references a missing Claim", class_path))
                    continue
                if has_text(entity_id) and claim.get("entity_id") != entity_id:
                    issues.append(issue("critical", "scope_decision_rule_claim_entity_mismatch", "ScopeDecision rule Claim must belong to the same Entity", class_path))
                    continue
                if classification_kind != "irrelevant" and not _claim_has_usable_assessment_support(claim_id, ids, evidence_by_claim):
                    issues.append(issue("critical", "scope_decision_rule_evidence_missing", "ScopeDecision rule Claim lacks usable formal supports evidence", class_path))
                    continue
                if (
                    isinstance(geography_contract, dict)
                    and rule_kind == "selection"
                    and rule_id in set(as_list(geography_contract.get("required_selection_rule_ids")))
                    and classification_kind == "supports"
                    and not _geography_support_is_formal(
                        claim,
                        entity_id,
                        [str(value) for value in as_list(brief.get("target_country_or_region")) if has_text(value)],
                        geography_contract,
                        rule,
                        ids,
                        evidence_by_claim,
                    )
                ):
                    issues.append(issue("critical", "geography_rule_support_not_formal_location", "Geography ScopeDecision support must be a same-Entity public Claim whose literal appears in the source excerpt", class_path))
                if classification_kind == "irrelevant":
                    continue
                allowed_types = as_list(rule.get("allowed_claim_types")) if isinstance(rule, dict) else []
                if claim.get("claim_type") not in allowed_types:
                    issues.append(issue("critical", "scope_rule_claim_type_not_allowed", "Scope rule Claim type is not permitted by this current Brief rule", class_path))
                marker_field = "evidence_markers" if classification_kind == "supports" else "conflict_markers"
                allowed_markers = [marker for marker in as_list(rule.get(marker_field)) if has_text(marker)] if isinstance(rule, dict) else []
                matched_marker = classification.get("matched_marker")
                if not has_text(matched_marker) or matched_marker not in allowed_markers:
                    issues.append(issue("critical", "scope_rule_support_not_relevant", "Scope rule classification must use a marker declared by this current Brief rule", class_path))
                elif not any(text_contains_exact_phrase(observation.get("raw_excerpt"), matched_marker) for observation in _claim_supporting_observations(claim_id, ids, evidence_by_claim)):
                    issues.append(issue("critical", "scope_rule_marker_missing_from_observation", "Scope rule matched_marker is not present in the Claim's supporting public excerpt", class_path))
            supports_ids = {str(item.get("claim_id")) for item in classifications if item.get("classification") == "supports" and has_text(item.get("claim_id"))}
            conflicts_ids = {str(item.get("claim_id")) for item in classifications if item.get("classification") == "conflicts" and has_text(item.get("claim_id"))}
            if set(as_list(evaluation.get("supporting_claim_ids"))) != supports_ids or set(as_list(evaluation.get("conflicting_claim_ids"))) != conflicts_ids:
                issues.append(issue("critical", "scope_rule_evidence_classification_missing", "Scope rule legacy Claim lists must exactly match explicit classifications", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}]"))
            if evaluation.get("outcome") == "supported_match" and not supports_ids:
                issues.append(issue("critical", "scope_decision_rule_evidence_missing", "supported_match requires a supports classification", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}]"))
            if evaluation.get("outcome") == "supported_conflict" and not conflicts_ids:
                issues.append(issue("critical", "scope_decision_rule_evidence_missing", "supported_conflict requires a conflicts classification", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}]"))
            reviewed_claim_ids: set[str] = set()
            for observation_id in as_list(evaluation.get("reviewed_observation_ids")):
                observation = ids["observations"].get(observation_id)
                if not isinstance(observation, dict):
                    issues.append(issue("major", "scope_decision_observation_missing", "ScopeDecision references a missing reviewed Observation", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].reviewed_observation_ids"))
                elif has_text(entity_id) and observation.get("entity_id") not in {None, entity_id}:
                    issues.append(issue("critical", "scope_decision_observation_entity_mismatch", "ScopeDecision reviewed Observation belongs to another Entity", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].reviewed_observation_ids"))
                elif has_text(entity_id):
                    reviewed_claim_ids.update(_formal_claim_ids_supported_by_observation(observation_id, entity_id, ids, evidence_by_claim))
            unclassified_claims = reviewed_claim_ids - set(classification_by_claim)
            if unclassified_claims:
                issues.append(issue("critical", "scope_rule_evidence_classification_missing", "Every formal Claim supported by a reviewed Observation must be classified", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}].claim_classifications"))
            if isinstance(rule, dict):
                conflict_markers = [marker for marker in as_list(rule.get("conflict_markers")) if has_text(marker)]
                conflict_claims = {
                    claim_id for claim_id in reviewed_claim_ids
                    if any(text_contains_exact_phrase(observation.get("raw_excerpt"), marker) for claim_id in [claim_id] for observation in _claim_supporting_observations(claim_id, ids, evidence_by_claim) for marker in conflict_markers)
                }
                if conflict_claims and (not conflict_claims.issubset(conflicts_ids) or evaluation.get("outcome") != "supported_conflict"):
                    issues.append(issue("critical", "scope_rule_conflict_hidden_as_not_observed", "A reviewed public conflict marker cannot be recorded as not_observed, irrelevant, or a match", f"scope_decisions[{idx}].rule_evaluations[{eval_idx}]"))
        subject_names: set[str] = set()
        if has_text(entity_id):
            entity = ids["entities"].get(entity_id)
            subject_names.update(str(entity.get(field)).casefold() for field in ("name", "legal_name") if isinstance(entity, dict) and has_text(entity.get(field)))
        if has_text(candidate_id):
            candidate = ids["candidates"].get(candidate_id)
            if isinstance(candidate, dict):
                subject_names.update(str(candidate.get(field)).casefold() for field in ("name", "company_name") if has_text(candidate.get(field)))
        subject_domains: set[str] = set()
        if has_text(entity_id):
            entity = ids["entities"].get(entity_id)
            if isinstance(entity, dict):
                subject_domains.update(filter(None, (normalized_identity_domain(entity.get(field)) for field in ("website", "domain"))))
        competitor_references = [reference for reference in as_list(brief.get("competitors_or_brands")) if has_text(reference)]
        reference_matches = [identity_reference_match(subject_names, subject_domains, reference) for reference in competitor_references]
        relationship_exact = False
        relationship_distinct = False
        if has_text(entity_id) and competitor_references:
            for relation in ensure_list(graph, "entity_relationships"):
                if not isinstance(relation, dict):
                    continue
                endpoint_ids = {relation.get(field) for field in ("source_entity_id", "from_entity_id", "parent_entity_id", "target_entity_id", "to_entity_id", "child_entity_id") if has_text(relation.get(field))}
                if entity_id not in endpoint_ids:
                    continue
                for other_entity_id in endpoint_ids - {entity_id}:
                    other = ids["entities"].get(other_entity_id)
                    if not isinstance(other, dict):
                        continue
                    other_names = {str(other.get(field)) for field in ("name", "legal_name") if has_text(other.get(field))}
                    other_domains = set(filter(None, (normalized_identity_domain(other.get(field)) for field in ("website", "domain"))))
                    if not any(identity_reference_match(other_names, other_domains, reference) == "exact" for reference in competitor_references):
                        continue
                    if relation.get("relationship_type") == "unrelated_same_name" and relation.get("resolution_status") == "split":
                        relationship_distinct = True
                    elif relation.get("resolution_status") not in {"rejected", "manual_check"}:
                        relationship_exact = True
        if competitor_references and contract.get("competitor_as_prospect_allowed") is True:
            if decision.get("competitor_handling_status") != "explicitly_allowed":
                issues.append(issue("critical", "competitor_seed_identity_unresolved", "A competitor/brand reference needs an explicit handling result even when the user allows prospects", f"scope_decisions[{idx}].competitor_handling_status"))
        elif competitor_references and ("exact" in reference_matches or relationship_exact):
            if decision.get("overall_status") != "reference_only" or decision.get("competitor_handling_status") != "reference_exact":
                issues.append(issue("critical", "competitor_seed_auto_promoted_to_customer", "A current Brief competitor/brand identity match must remain reference_only", f"scope_decisions[{idx}].overall_status"))
        elif competitor_references and "unresolved" in reference_matches and not relationship_distinct:
            if decision.get("overall_status") != "needs_confirmation" or decision.get("competitor_handling_status") != "identity_unresolved" or decision.get("identity_review_required") is not True:
                issues.append(issue("critical", "competitor_alias_requires_identity_review", "A competitor/brand alias hint requires identity review and cannot be an in-scope formal customer", f"scope_decisions[{idx}]"))
        elif competitor_references and relationship_distinct:
            if decision.get("competitor_handling_status") != "resolved_distinct":
                issues.append(issue("critical", "competitor_seed_identity_unresolved", "A documented distinct-identity result must be recorded before formal prospect use", f"scope_decisions[{idx}].competitor_handling_status"))
        elif competitor_references and decision.get("competitor_handling_status") != "not_applicable":
            issues.append(issue("critical", "competitor_seed_identity_unresolved", "A competitor/brand reference requires a recorded current-task handling result", f"scope_decisions[{idx}].competitor_handling_status"))
        for rule_id in selection_rules:
            if ("selection", rule_id) not in evaluation_by_key:
                issues.append(issue("critical", "scope_decision_rule_missing", "ScopeDecision lacks a current Brief selection-rule evaluation", f"scope_decisions[{idx}].rule_evaluations"))
        for rule_id in exclusion_rules:
            if ("exclusion", rule_id) not in evaluation_by_key:
                issues.append(issue("critical", "scope_decision_rule_missing", "ScopeDecision lacks a current Brief exclusion-rule evaluation", f"scope_decisions[{idx}].rule_evaluations"))

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
        brief = ids["briefs"].get(assessment.get("brief_id"))
        contract = customer_selection_contract(brief)
        exception_entities = formal_exception_entity_ids(brief)
        basis_claim_ids = as_list(assessment.get("basis_claim_ids"))
        rationale = assessment.get("rationale_structured")
        if not isinstance(rationale, dict) or as_list(rationale.get("basis_claim_ids")) != basis_claim_ids:
            issues.append(issue("critical", "assessment_rationale_basis_mismatch", "Assessment rationale_structured must contain only the same basis_claim_ids", f"assessments[{idx}].rationale_structured"))
        if assessment.get("disposition") in POSITIVE_DISPOSITIONS and not basis_claim_ids:
            issues.append(issue("critical", "positive_assessment_without_basis_claims", f"Assessment {assessment.get('assessment_id')} has positive disposition without basis_claim_ids", f"assessments[{idx}].basis_claim_ids"))
        if assessment.get("disposition") in POSITIVE_DISPOSITIONS and formal_exception_mode(brief):
            if assessment.get("entity_id") not in exception_entities:
                code = "single_company_assessment_outside_target" if formal_exception_mode(brief) == "single_company_analysis" else "existing_table_assessment_outside_bound_input"
                issues.append(issue("critical", code, "Positive formal exception Assessment must stay within the current Brief's explicit input binding", f"assessments[{idx}].entity_id"))
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
            else:
                usable_assessment_support = False
                for support in supports:
                    observation = ids["observations"].get(support.get("observation_id"))
                    source = ids["sources"].get(observation.get("source_id")) if isinstance(observation, dict) else None
                    if source_evidence_scope(source, observation, "assessment_basis")[0]:
                        usable_assessment_support = True
                        break
                if not usable_assessment_support:
                    issues.append(issue("critical", "assessment_basis_claim_source_not_eligible", f"Assessment basis Claim {cid} has no source eligible for assessment_basis", f"assessments[{idx}].basis_claim_ids"))
        if assessment.get("disposition") in POSITIVE_DISPOSITIONS and formal_targeting_contract_required(brief):
            if isinstance(brief, dict) and brief.get("task_mode") == "unknown":
                issues.append(issue("critical", "unknown_task_mode_blocks_formal_delivery", "task_mode=unknown cannot create a positive formal customer Assessment", f"assessments[{idx}].brief_id"))
            if not isinstance(contract, dict):
                issues.append(issue("critical", "brief_targeting_contract_missing", "Positive new-customer Assessment requires a Brief customer selection contract", f"assessments[{idx}].brief_id"))
                continue
            selection_rules, exclusion_rules = targeting_rule_maps(contract)
            if not selection_rules and not exclusion_rules:
                issues.append(issue("critical", "targeting_contract_empty_for_formal_delivery", "Positive formal Assessment requires a substantive customer selection contract", f"assessments[{idx}].brief_id"))
            if not any(rule.get("required_for_positive") is True for rule in selection_rules.values()):
                issues.append(issue("critical", "targeting_contract_missing_required_selection_rule", "Positive formal Assessment requires at least one required selection rule", f"assessments[{idx}].brief_id"))
            if contract.get("scope_state") == "provisional":
                issues.append(issue("critical", "provisional_scope_blocks_formal_delivery", "Provisional customer direction cannot produce a positive formal Assessment", f"assessments[{idx}].brief_id"))
            if contract.get("sample_first_required") is True:
                issues.append(issue("critical", "sample_first_required_blocks_formal_delivery", "sample_first_required permits direction samples only until the Brief is explicitly updated and re-reviewed", f"assessments[{idx}].brief_id"))
            decision = scope_decisions_by_id.get(assessment.get("scope_decision_id"))
            if not isinstance(decision, dict):
                issues.append(issue("critical", "scope_decision_missing", "Positive Assessment requires a ScopeDecision", f"assessments[{idx}].scope_decision_id"))
                continue
            if decision.get("run_id") != assessment.get("run_id"):
                issues.append(issue("critical", "scope_decision_run_mismatch", "Positive Assessment ScopeDecision must belong to the current Run", f"assessments[{idx}].scope_decision_id"))
            if decision.get("brief_id") != assessment.get("brief_id") or decision.get("targeting_contract_id") != contract.get("targeting_contract_id"):
                issues.append(issue("critical", "scope_decision_brief_mismatch", "Positive Assessment ScopeDecision must belong to the current Brief contract", f"assessments[{idx}].scope_decision_id"))
            if decision.get("entity_id") != assessment.get("entity_id"):
                issues.append(issue("critical", "scope_decision_entity_mismatch", "Positive Assessment ScopeDecision must belong to the same Entity", f"assessments[{idx}].scope_decision_id"))
            if decision.get("overall_status") != "in_scope":
                issues.append(issue("critical", "positive_assessment_without_eligible_scope_decision", "Positive Assessment requires an in_scope ScopeDecision", f"assessments[{idx}].scope_decision_id"))
            evaluations = {(item.get("rule_kind"), item.get("rule_id")): item for item in as_list(decision.get("rule_evaluations")) if isinstance(item, dict)}
            for rule_id, rule in selection_rules.items():
                evaluation = evaluations.get(("selection", rule_id))
                outcome = evaluation.get("outcome") if isinstance(evaluation, dict) else None
                if rule.get("required_for_positive") and outcome != "supported_match":
                    issues.append(issue("critical", "required_targeting_rule_not_satisfied", "Positive Assessment is missing required current-direction support", f"assessments[{idx}].scope_decision_id"))
                if rule.get("unknown_blocks_positive") and outcome == "unknown":
                    issues.append(issue("critical", "targeting_critical_rule_unknown", "A current-direction unknown blocks positive Assessment", f"assessments[{idx}].scope_decision_id"))
                if rule.get("required_for_positive"):
                    classifications = as_list(evaluation.get("claim_classifications")) if isinstance(evaluation, dict) else []
                    supports = {str(item.get("claim_id")) for item in classifications if isinstance(item, dict) and item.get("classification") == "supports"}
                    if not supports & {str(claim_id) for claim_id in basis_claim_ids}:
                        issues.append(issue("critical", "assessment_basis_missing_scope_rule_support", "Positive Assessment basis must include a supports Claim for every required current-direction rule", f"assessments[{idx}].basis_claim_ids"))
            for rule_id, rule in exclusion_rules.items():
                evaluation = evaluations.get(("exclusion", rule_id))
                outcome = evaluation.get("outcome") if isinstance(evaluation, dict) else None
                if rule.get("block_when_supported") and outcome == "supported_conflict":
                    issues.append(issue("critical", "targeting_exclusion_rule_conflicts", "A supported current exclusion rule blocks positive Assessment", f"assessments[{idx}].scope_decision_id"))
                if rule.get("unknown_blocks_positive") and outcome == "unknown":
                    issues.append(issue("critical", "targeting_critical_rule_unknown", "An unknown critical exclusion rule blocks positive Assessment", f"assessments[{idx}].scope_decision_id"))
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
        for field in ("audited_at", "research_graph_hash", "audit_graph_hash", "review_cycle_id", "review_attestation_id", "reviewed_subject_hash", "review_provenance_level", "audit_status", "delivery_status", "allowed_delivery_statuses", "ok", "issue_count", "issues"):
            if field not in audit:
                issues.append(issue("major", "audit_missing_required_field", f"Audit {audit.get('audit_id')} lacks {field}", f"audits[{idx}].{field}"))
        if audit.get("audit_status") not in {None, "passed", "failed"}:
            issues.append(issue("major", "invalid_audit_status", f"Invalid Audit audit_status: {audit.get('audit_status')}", f"audits[{idx}].audit_status"))
        if audit.get("delivery_status") not in {None, "needs_correction", "initial_lead_list", "standard_development_list", "full_review_package", "inquiry_followup_queue"}:
            issues.append(issue("major", "invalid_audit_delivery_status", f"Invalid Audit delivery_status: {audit.get('delivery_status')}", f"audits[{idx}].delivery_status"))
        if audit.get("delivery_status") == "full_review_package":
            issues.append(issue("critical", "stored_audit_full_review_unavailable", "This local deployment does not provide full_review_package", f"audits[{idx}].delivery_status"))
        if audit.get("delivery_status") == "standard_development_list" and audit.get("review_provenance_level") in {"declared_separate_session", "self_review_fallback"} and audit.get("disclosure_required") is not True:
            issues.append(issue("critical", "audit_disclosure_required_missing", "Standard delivery with review disclosure provenance must set disclosure_required=true", f"audits[{idx}].disclosure_required"))
        if audit.get("research_graph_hash") and audit.get("research_graph_hash") != current_hash:
            issues.append(issue("major", "stale_audit_research_graph_hash", "Audit research_graph_hash does not match current graph hash", f"audits[{idx}].research_graph_hash"))
        if audit.get("audit_graph_hash") and audit.get("audit_graph_hash") != current_hash:
            issues.append(issue("major", "stale_audit_graph_hash", "Audit audit_graph_hash does not match current graph hash", f"audits[{idx}].audit_graph_hash"))
        if audit.get("review_attestation_id") != expected_review_snapshot.get("review_attestation_id"):
            issues.append(issue("critical", "audit_review_attestation_mismatch", "Audit must cite the current ReviewAttestation", f"audits[{idx}].review_attestation_id"))
        if audit.get("reviewed_subject_hash") != expected_review_snapshot.get("reviewed_subject_hash"):
            issues.append(issue("critical", "audit_reviewed_subject_hash_mismatch", "Audit must cite the current canonical review subject hash", f"audits[{idx}].reviewed_subject_hash"))
        if audit.get("review_provenance_level") != expected_review_snapshot.get("review_provenance_level"):
            issues.append(issue("critical", "audit_review_provenance_level_mismatch", "Audit must cite the current review provenance level", f"audits[{idx}].review_provenance_level"))
        active_run = current_run(graph)
        if isinstance(active_run, dict) and audit.get("review_cycle_id") != active_run.get("review_cycle_id"):
            issues.append(issue("critical", "audit_review_cycle_mismatch", "Audit review_cycle_id must match the current Run", f"audits[{idx}].review_cycle_id"))

    for idx, manifest in enumerate(ensure_list(graph, "delivery_manifests")):
        if not isinstance(manifest, dict): continue
        if manifest.get("delivery_status") == "full_review_package":
            issues.append(issue("critical", "stored_manifest_full_review_unavailable", "This local deployment does not provide full_review_package", f"delivery_manifests[{idx}].delivery_status"))
        inquiry_manifest = manifest.get("delivery_status") == "inquiry_followup_queue"
        manifest_refs = (("run_id", "runs"), ("audit_id", "audits")) if inquiry_manifest else (("run_id", "runs"), ("brief_id", "briefs"), ("plan_id", "plans"), ("audit_id", "audits"))
        for field, collection in manifest_refs:
            raw = manifest.get(field)
            if not has_text(raw):
                issues.append(issue("major", "manifest_missing_reference", f"DeliveryManifest lacks non-empty {field}", f"delivery_manifests[{idx}].{field}"))
            elif raw not in ids[collection]:
                issues.append(issue("major", "manifest_reference_missing", f"DeliveryManifest references missing {collection[:-1]} {raw}", f"delivery_manifests[{idx}].{field}"))
        if not inquiry_manifest and not has_text(manifest.get("review_cycle_id")):
            issues.append(issue("major", "manifest_missing_review_cycle_id", "DeliveryManifest lacks non-empty review_cycle_id", f"delivery_manifests[{idx}].review_cycle_id"))
        for field in ("review_attestation_id", "reviewed_subject_hash", "review_provenance_level"):
            if field not in manifest:
                issues.append(issue("major", "manifest_review_provenance_missing", f"DeliveryManifest lacks {field}", f"delivery_manifests[{idx}].{field}"))
        if manifest.get("delivery_status") == "standard_development_list" and manifest.get("review_provenance_level") == "declared_separate_session":
            disclosure = "本次复核由独立会话声明完成，未获得平台身份验证。"
            if disclosure not in as_list(manifest.get("disclosures")):
                issues.append(issue("critical", "manifest_declared_review_disclosure_missing", "Standard declared review manifest must include the required disclosure", f"delivery_manifests[{idx}].disclosures"))
        for field in ("audit_graph_hash", "research_graph_hash"):
            if not has_text(manifest.get(field)):
                issues.append(issue("major", "manifest_missing_hash", f"DeliveryManifest lacks {field}", f"delivery_manifests[{idx}].{field}"))
        snapshot = manifest.get("audit_snapshot")
        if isinstance(snapshot, dict):
            for field in ("review_cycle_id", "review_attestation_id", "reviewed_subject_hash", "review_provenance_level"):
                if snapshot.get(field) != manifest.get(field):
                    issues.append(issue("critical", "manifest_audit_snapshot_review_provenance_mismatch", f"DeliveryManifest audit_snapshot {field} must match its top-level value", f"delivery_manifests[{idx}].audit_snapshot.{field}"))
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
            for field in ("review_attestation_id", "reviewed_subject_hash", "review_provenance_level"):
                if manifest.get(field) != audit.get(field):
                    issues.append(issue("critical", "manifest_audit_review_provenance_mismatch", f"DeliveryManifest {field} must match its referenced Audit", f"delivery_manifests[{idx}].{field}"))
            if manifest.get("review_cycle_id") != audit.get("review_cycle_id"):
                issues.append(issue("critical", "manifest_audit_review_cycle_mismatch", "DeliveryManifest review_cycle_id must match its referenced Audit", f"delivery_manifests[{idx}].review_cycle_id"))
        run = ids["runs"].get(manifest.get("run_id"))
        if isinstance(run, dict):
            if not inquiry_manifest and (manifest.get("brief_id") != run.get("brief_id") or manifest.get("plan_id") != run.get("plan_id")):
                issues.append(issue("major", "manifest_run_binding_mismatch", "DeliveryManifest Brief/Plan must match its Run", f"delivery_manifests[{idx}]"))
            if not inquiry_manifest and manifest.get("review_cycle_id") != run.get("review_cycle_id"):
                issues.append(issue("major", "manifest_review_cycle_mismatch", "DeliveryManifest review_cycle_id must match its Run", f"delivery_manifests[{idx}].review_cycle_id"))
            if not inquiry_manifest:
                for field in ("review_attestation_id", "reviewed_subject_hash", "review_provenance_level"):
                    if manifest.get(field) != expected_review_snapshot.get(field):
                        issues.append(issue("critical", "manifest_review_provenance_mismatch", f"DeliveryManifest {field} must match current review provenance", f"delivery_manifests[{idx}].{field}"))
            brief = ids["briefs"].get(run.get("brief_id"))
            if not inquiry_manifest and not _run_allows_delivery_status(run, brief, manifest.get("delivery_status")):
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
