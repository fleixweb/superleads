#!/usr/bin/env python3
"""Shared helpers for Superleads scripts. Uses only Python standard library."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

GRAPH_ARRAY_KEYS = [
    "runs", "briefs", "plans", "candidates", "sources", "observations", "entities",
    "entity_relationships", "claims", "claim_evidence", "contact_points", "contact_claims",
    "unassigned_contact_leads", "hypotheses", "assessments", "review_findings", "audits",
    "delivery_manifests", "search_logs", "inquiries", "mail_intake_rules", "scope_decisions",
]

ID_FIELDS = {
    "runs": "run_id", "briefs": "brief_id", "plans": "plan_id", "candidates": "candidate_id",
    "sources": "source_id", "observations": "observation_id", "entities": "entity_id",
    "entity_relationships": "entity_relationship_id", "claims": "claim_id", "claim_evidence": "claim_evidence_id",
    "contact_points": "contact_id", "contact_claims": "contact_claim_id",
    "unassigned_contact_leads": "unassigned_contact_lead_id", "hypotheses": "hypothesis_id",
    "assessments": "assessment_id", "review_findings": "finding_id", "audits": "audit_id",
    "delivery_manifests": "delivery_manifest_id", "search_logs": "search_log_id",
    "inquiries": "inquiry_id", "mail_intake_rules": "mail_intake_rule_id", "scope_decisions": "scope_decision_id",
}

FIXED_FINDING_STATUS = "verified_fixed"
NON_BLOCKING_DISCLOSURE_STATUSES = {"accepted_with_disclosure", "rejected_with_reviewer_reason"}

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)https?://[^\s<>\"']+")
LOCAL_PATH_RE = re.compile(
    r"(?i)(?:file://|(?:^|[\s\"'])+[a-z]:[\\/]|(?:^|[\s\"'])+/(?:home|users|tmp|var|etc|mnt|private|volumes)(?:/|\b))"
)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
ARTIFACT_SNAPSHOT_RE = re.compile(r"^artifact:sha256:([a-f0-9]{64})#(.+)$")
SPREADSHEET_CELL_OR_RANGE_RE = re.compile(
    r"^\$?[A-Z]{1,3}\$?[1-9][0-9]*(?::\$?[A-Z]{1,3}\$?[1-9][0-9]*)?$",
    re.IGNORECASE,
)
ARTIFACT_MEDIA = {"document", "spreadsheet", "image", "correspondence"}
MATERIAL_ROLES = {
    "published_source_copy",
    "user_business_dataset",
    "correspondence_export",
    "user_authored_note",
    "visual_reference",
    "connected_inbound_correspondence",
    "unknown",
}
SOURCE_EVIDENCE_PURPOSES = {
    "formal_claim",
    "assessment_basis",
    "contact_ready",
    "contact_with_source_note",
    "candidate_clue",
    "translation_origin",
    "inquiry_event",
}
NEW_CUSTOMER_DEVELOPMENT_TASK_MODES = {
    "product_scope_research",
    "keyword_research",
    "industry_application_research",
    "market_customer_type_research",
    "competitor_seed_research",
}
FORMAL_TARGETING_EXEMPT_TASK_MODES = {
    "single_company_analysis",
    "existing_table_enrichment",
}
SCOPE_DECISION_STATUSES = {"in_scope", "out_of_scope", "needs_confirmation", "reference_only"}
SCOPE_RULE_OUTCOMES = {"supported_match", "supported_conflict", "not_observed", "unknown"}
SCOPE_CLAIM_CLASSIFICATIONS = {"supports", "conflicts", "irrelevant"}
RULE_ALLOWED_CLAIM_TYPES = {
    "product_match",
    "company_identity",
    "contact_route",
    "location",
    "registration",
    "brand_trademark",
    "channel_role",
    "ownership",
    "certification",
}
IDENTITY_LEGAL_SUFFIX_RE = re.compile(
    r"\b(inc|inc\.|ltd|ltd\.|limited|llc|gmbh|sarl|sas|spa|bv|ag|ab|as|oy|plc|co\.|company|corp\.|corporation)\b",
    re.IGNORECASE,
)

# Only capabilities that can inspect source material may support a formal
# Claim or an exported contact. New capability names must be added here with
# an explicit policy decision instead of silently inheriting formal access.
CLAIM_SUPPORT_ALLOWED_CAPABILITIES = {
    "source.open",
    "browser.render",
    "document.extract",
    "source.capture",
    "social.visible.read",
    "registry.lookup",
    "trademark.lookup",
    "maps.lookup",
    "translate.text",
}
CONTACT_SOURCE_ALLOWED_CAPABILITIES = CLAIM_SUPPORT_ALLOWED_CAPABILITIES
CONTACT_NOTE_ALLOWED_CAPABILITIES = CONTACT_SOURCE_ALLOWED_CAPABILITIES | {"mail.read"}
CONTACT_SOURCE_ALLOWED_TYPES = {
    "website",
    "social",
    "registry",
    "directory",
    "map",
    "document",
    "spreadsheet",
    "image",
    "correspondence",
    "user_provided",
}

CONTACT_USER_STATUS_BY_EXPORT_STATUS = {
    "ready": "可直接使用",
    "export_with_source_note": "建议核查后使用",
    "needs_manual_association_review": "待确认归属",
    "hold_no_source": "不可导出",
    "hold_inferred": "不可导出",
}


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def ensure_list(graph: dict[str, Any], key: str) -> list[Any]:
    value = graph.get(key, [])
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def customer_selection_contract(brief: Any) -> dict[str, Any] | None:
    """Return the current Brief's free-text targeting contract when present."""
    if not isinstance(brief, dict):
        return None
    contract = brief.get("customer_selection_contract")
    return contract if isinstance(contract, dict) else None


def targeting_contract_required(brief: Any) -> bool:
    """Only new-customer-development modes need a formal direction contract."""
    return isinstance(brief, dict) and brief.get("task_mode") in NEW_CUSTOMER_DEVELOPMENT_TASK_MODES


def formal_targeting_contract_required(brief: Any) -> bool:
    """Fail closed for a formal positive list except defined analysis/enrichment work."""
    return isinstance(brief, dict) and brief.get("task_mode") not in FORMAL_TARGETING_EXEMPT_TASK_MODES


def formal_exception_mode(brief: Any) -> str | None:
    """Return a constrained formal-analysis mode, never a targeting bypass."""
    if not isinstance(brief, dict):
        return None
    mode = brief.get("task_mode")
    return str(mode) if mode in FORMAL_TARGETING_EXEMPT_TASK_MODES else None


def formal_exception_entity_ids(brief: Any) -> set[str]:
    """Return explicitly bound Entity IDs for a constrained formal exception.

    Validation proves that these identifiers are current, user-specified input
    bindings before audit/export can use them. This helper intentionally does
    not infer an Entity from a company name, URL, or table row.
    """
    mode = formal_exception_mode(brief)
    if mode == "single_company_analysis":
        target = brief.get("single_company_target") if isinstance(brief, dict) else None
        entity_id = target.get("resolved_entity_id") if isinstance(target, dict) else None
        return {str(entity_id)} if has_text(entity_id) else set()
    if mode == "existing_table_enrichment":
        binding = brief.get("existing_table_binding") if isinstance(brief, dict) else None
        return {
            str(item.get("entity_id"))
            for item in as_list(binding.get("entity_bindings") if isinstance(binding, dict) else None)
            if isinstance(item, dict) and has_text(item.get("entity_id"))
        }
    return set()


def formal_exception_result_label(brief: Any) -> str | None:
    """Return a user-facing label that does not claim current-direction fit."""
    return {
        "single_company_analysis": "单公司分析结果",
        "existing_table_enrichment": "原表补全结果",
    }.get(formal_exception_mode(brief))


def normalized_identity_name(value: Any) -> str:
    """Conservative normal form for identity-review routing, never identity proof."""
    if not has_text(value):
        return ""
    without_suffix = IDENTITY_LEGAL_SUFFIX_RE.sub("", str(value).casefold().strip())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", without_suffix)).strip()


def identity_tokens(value: Any) -> set[str]:
    return {token for token in normalized_identity_name(value).split() if token}


def identity_names_need_review(left: Any, right: Any) -> bool:
    """Detect a strong alias hint without treating it as an identity match."""
    left_tokens, right_tokens = identity_tokens(left), identity_tokens(right)
    return bool(left_tokens and right_tokens and (left_tokens <= right_tokens or right_tokens <= left_tokens))


def normalized_identity_domain(value: Any) -> str:
    """Extract a hostname-like identity hint; it is never identity proof."""
    if not has_text(value):
        return ""
    raw = str(value).strip()
    parsed = urlsplit(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").casefold()
    return host[4:] if host.startswith("www.") else host


def entity_name_matches_identity_literal(entity: Any, literal: Any) -> bool:
    """Match only an exact conservative normalized Entity name/legal name."""
    if not isinstance(entity, dict) or not has_text(literal):
        return False
    literal_name = normalized_identity_name(literal)
    return bool(literal_name and literal_name in {
        normalized_identity_name(entity.get("name")),
        normalized_identity_name(entity.get("legal_name")),
    })


def entity_domain_matches_identity_literal(entity: Any, literal: Any) -> bool:
    """Match only an exact conservative normalized Entity website/domain."""
    if not isinstance(entity, dict) or not has_text(literal):
        return False
    literal_domain = normalized_identity_domain(literal)
    entity_domains = {
        normalized_identity_domain(entity.get(field))
        for field in ("website", "domain")
        if has_text(entity.get(field))
    }
    return bool(literal_domain and literal_domain in entity_domains)


def entity_matches_identity_literal(entity: Any, literal: Any) -> bool:
    """Allow a visible identity literal only when it exactly names or domains an Entity."""
    return entity_name_matches_identity_literal(entity, literal) or entity_domain_matches_identity_literal(entity, literal)


def identity_reference_match(names: set[str], domains: set[str], reference: Any) -> str:
    """Return exact/unresolved/none without merging entities by name similarity."""
    reference_name = normalized_identity_name(reference)
    reference_domain = normalized_identity_domain(reference)
    if reference_domain and reference_domain in domains:
        return "exact"
    normalized_names = {normalized_identity_name(name) for name in names if has_text(name)}
    if reference_name and reference_name in normalized_names:
        return "exact"
    if reference_name and any(identity_names_need_review(name, reference_name) for name in normalized_names):
        return "unresolved"
    return "none"


def targeting_rule_maps(contract: Any) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Index contract rules without interpreting their free-text business meaning."""
    if not isinstance(contract, dict):
        return {}, {}
    selection = {
        str(item.get("rule_id")): item for item in as_list(contract.get("selection_requirements"))
        if isinstance(item, dict) and has_text(item.get("rule_id"))
    }
    exclusion = {
        str(item.get("rule_id")): item for item in as_list(contract.get("exclusion_rules"))
        if isinstance(item, dict) and has_text(item.get("rule_id"))
    }
    return selection, exclusion


def scope_status_user_label(status: Any) -> str:
    return {
        "in_scope": "符合本次方向",
        "out_of_scope": "不符合本次方向",
        "needs_confirmation": "需确认",
        "reference_only": "仅作参考",
    }.get(str(status or ""), "需确认")


def compact_text(value: Any) -> str:
    """Case-fold and collapse whitespace for conservative source containment checks."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def text_contains(haystack: Any, needle: Any) -> bool:
    """Return True when a visible source excerpt contains a claimed literal."""
    compact_haystack = compact_text(haystack)
    compact_needle = compact_text(needle)
    return bool(compact_haystack and compact_needle and compact_needle in compact_haystack)


def text_contains_exact_phrase(haystack: Any, needle: Any) -> bool:
    """Match a visible phrase without allowing word-prefix/suffix bypasses."""
    compact_haystack = compact_text(haystack)
    compact_needle = compact_text(needle)
    if not compact_haystack or not compact_needle:
        return False
    pattern = rf"(?<!\w){re.escape(compact_needle)}(?!\w)"
    return re.search(pattern, compact_haystack) is not None


def is_public_http_url(value: Any) -> bool:
    """Return whether a source link is an inspectable public web URL."""
    if not has_text(value):
        return False
    parsed = urlsplit(str(value).strip())
    return parsed.scheme.casefold() in {"http", "https"} and bool(parsed.hostname)


def is_safe_artifact_name(value: Any) -> bool:
    """Accept only a display filename, never a path or a drive-qualified name."""
    if not has_text(value):
        return False
    name = str(value).strip()
    return not (
        ".." in name
        or any(char in name for char in ("/", "\\", ":"))
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
    )


def contains_local_path(value: Any) -> bool:
    """Reject local-path disclosure in graph metadata and delivery text."""
    if not isinstance(value, str):
        return False
    return LOCAL_PATH_RE.search(value) is not None


def _safe_snapshot_locator(value: Any) -> bool:
    if not has_text(value):
        return False
    locator = str(value).strip()
    lowered = locator.casefold()
    return not (
        ".." in locator
        or "file:" in lowered
        or "\\" in locator
        or "/" in locator
        or any(ord(char) < 32 or ord(char) == 127 for char in locator)
    )


def parse_artifact_snapshot_ref(value: Any) -> tuple[str, str, dict[str, str]] | None:
    """Parse the closed artifact snapshot format without accepting path syntax."""
    if not isinstance(value, str):
        return None
    match = ARTIFACT_SNAPSHOT_RE.fullmatch(value.strip())
    if not match:
        return None
    artifact_hash, locator = match.groups()
    if not _safe_snapshot_locator(locator):
        return None
    try:
        pairs = parse_qsl(locator, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return None
    if not pairs or len({key for key, _ in pairs}) != len(pairs):
        return None
    fields = {key: item for key, item in pairs}
    if any(
        not has_text(key)
        or not has_text(item)
        or not _safe_snapshot_locator(key)
        or not _safe_snapshot_locator(item)
        for key, item in fields.items()
    ):
        return None
    return artifact_hash, locator, fields


def _document_locator_is_valid(fields: dict[str, str]) -> bool:
    if set(fields) - {"page", "section", "chapter"}:
        return False
    if "page" in fields and fields["page"].isdigit() and int(fields["page"]) >= 1:
        return True
    return any(has_text(fields.get(key)) for key in ("section", "chapter"))


def _spreadsheet_locator_is_valid(fields: dict[str, str]) -> bool:
    if set(fields) - {"sheet", "range", "cell"} or not has_text(fields.get("sheet")):
        return False
    location = fields.get("range") or fields.get("cell")
    return bool(has_text(location) and SPREADSHEET_CELL_OR_RANGE_RE.fullmatch(str(location)))


def _image_locator_is_valid(fields: dict[str, str]) -> bool:
    if set(fields) - {"image", "region", "ocr_region"}:
        return False
    if fields.get("image", "").isdigit() and int(fields["image"]) >= 1:
        return True
    return has_text(fields.get("region")) or has_text(fields.get("ocr_region"))


MAIL_SNAPSHOT_RE = re.compile(r"^mail:sha256:([a-f0-9]{64})#(.+)$")
MAIL_HEADER_FIELDS = {"from", "subject", "date", "reply_to"}


def is_safe_opaque_ref(value: Any) -> bool:
    """Accept a short host-owned opaque handle, not a credential or path."""
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,128}", value) is not None


def parse_mail_snapshot_ref(value: Any) -> tuple[str, str, dict[str, str]] | None:
    """Parse a bounded mail excerpt pointer without accepting path syntax."""
    if not isinstance(value, str):
        return None
    match = MAIL_SNAPSHOT_RE.fullmatch(value.strip())
    if not match:
        return None
    message_hash, locator = match.groups()
    if not _safe_snapshot_locator(locator):
        return None
    try:
        pairs = parse_qsl(locator, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return None
    if not pairs or len({key for key, _ in pairs}) != len(pairs):
        return None
    fields = {key: item for key, item in pairs}
    if any(not has_text(key) or not has_text(item) or not _safe_snapshot_locator(key) or not _safe_snapshot_locator(item) for key, item in fields.items()):
        return None
    part = fields.get("part")
    if part == "header":
        if set(fields) != {"part", "field"} or fields.get("field") not in MAIL_HEADER_FIELDS:
            return None
    elif part == "body":
        if set(fields) != {"part", "offset", "length"}:
            return None
        if not fields["offset"].isdigit() or not fields["length"].isdigit():
            return None
        if int(fields["length"]) < 1 or int(fields["length"]) > 1000:
            return None
    else:
        return None
    return message_hash, locator, fields


def _mail_source_scope(source: dict[str, Any], observation: dict[str, Any]) -> tuple[bool, str]:
    if source.get("provenance") != "connected_account" or source.get("medium") != "correspondence":
        return False, "connected_mail_source_invalid"
    if source.get("material_role") != "connected_inbound_correspondence":
        return False, "connected_mail_material_role_invalid"
    required = ("message_id", "received_at", "sender_literal", "subject_literal", "message_content_sha256", "mailbox_ref")
    if any(not has_text(source.get(field)) for field in required):
        return False, "connected_mail_metadata_missing"
    if source.get("direction") != "inbound":
        return False, "connected_mail_direction_not_inbound"
    if source.get("access_boundary") != "read_only_connected_account":
        return False, "connected_mail_access_boundary_invalid"
    if not SHA256_RE.fullmatch(str(source.get("message_content_sha256"))):
        return False, "connected_mail_content_hash_invalid"
    if not is_safe_opaque_ref(source.get("mailbox_ref")):
        return False, "connected_mailbox_ref_invalid"
    if observation.get("capability") != "mail.read":
        return False, "connected_mail_capability_not_mail_read"
    if not has_text(observation.get("raw_excerpt")) or len(str(observation.get("raw_excerpt") or "")) > 1000 or not has_text(observation.get("content_hash")):
        return False, "connected_mail_observation_missing_excerpt"
    parsed = parse_mail_snapshot_ref(observation.get("snapshot_ref"))
    if parsed is None:
        return False, "connected_mail_snapshot_ref_invalid"
    if parsed[0] != source.get("message_content_sha256"):
        return False, "connected_mail_snapshot_ref_hash_mismatch"
    return True, "ok"


def _user_provided_artifact_scope(source: dict[str, Any], observation: dict[str, Any]) -> tuple[bool, str]:
    """Validate a user-uploaded binary reference without assigning its trust role."""
    medium = source.get("medium")
    if medium not in ARTIFACT_MEDIA:
        return False, "user_provided_medium_not_allowed"
    artifact_hash = source.get("artifact_sha256")
    if not has_text(artifact_hash):
        return False, "user_provided_artifact_hash_missing"
    if not SHA256_RE.fullmatch(str(artifact_hash)):
        return False, "user_provided_artifact_hash_invalid"
    if not is_safe_artifact_name(source.get("artifact_name")):
        return False, "user_provided_artifact_name_invalid"
    expected_capability = "image.inspect" if medium == "image" else "document.extract"
    if observation.get("capability") != expected_capability:
        return False, "visual_reference_capability_not_image_inspect" if medium == "image" else "user_provided_capability_not_document_extract"
    if medium == "image" and observation.get("observation_content_kind") not in {"ocr_text", "visual_description"}:
        return False, "visual_reference_content_kind_invalid"
    if not has_text(observation.get("raw_excerpt")):
        return False, "user_provided_raw_excerpt_missing"
    if not has_text(observation.get("content_hash")):
        return False, "user_provided_content_hash_missing"
    snapshot_ref = observation.get("snapshot_ref")
    if not has_text(snapshot_ref):
        return False, "user_provided_snapshot_ref_missing"
    parsed = parse_artifact_snapshot_ref(snapshot_ref)
    if parsed is None:
        return False, "user_provided_snapshot_ref_invalid"
    snapshot_hash, _locator, fields = parsed
    if snapshot_hash != artifact_hash:
        return False, "user_provided_snapshot_ref_hash_mismatch"
    if medium in {"document", "correspondence"} and not _document_locator_is_valid(fields):
        return False, "user_provided_snapshot_ref_invalid"
    if medium == "spreadsheet" and not _spreadsheet_locator_is_valid(fields):
        return False, "user_provided_snapshot_ref_invalid"
    if medium == "image" and not _image_locator_is_valid(fields):
        return False, "user_provided_snapshot_ref_invalid"
    return True, "ok"


def source_evidence_scope(source: Any, observation: Any, purpose: str) -> tuple[bool, str]:
    """Decide whether an Observation may serve one explicit evidence purpose.

    The function validates graph metadata and reference consistency only. It
    does not establish that a user-provided artifact is official, current, or
    re-hash the original bytes when those bytes are not retained.
    """
    if purpose not in SOURCE_EVIDENCE_PURPOSES:
        return False, "source_evidence_purpose_invalid"
    if not isinstance(source, dict) or not isinstance(observation, dict):
        return False, "formal_source_not_eligible"
    if observation.get("capability") == "image.inspect" and purpose != "candidate_clue":
        return False, f"image_inspect_not_allowed_for_{purpose}"
    provenance = source.get("provenance")
    role = source.get("material_role")
    if provenance in {"user_provided", "manual_input", "connected_account"}:
        if not has_text(role):
            return False, "material_role_missing"
        if role not in MATERIAL_ROLES:
            return False, "material_role_invalid"
    if provenance == "manual_input":
        if purpose == "candidate_clue" and has_text(observation.get("raw_excerpt")):
            return True, "ok"
        return False, f"manual_input_not_allowed_for_{purpose}"
    if provenance == "connected_account":
        if source.get("medium") == "correspondence":
            mail_ok, reason = _mail_source_scope(source, observation)
            if not mail_ok:
                return False, reason
            if purpose in {"contact_with_source_note", "inquiry_event", "candidate_clue"}:
                return True, "ok"
            return False, f"connected_inbound_correspondence_not_allowed_for_{purpose}"
        if source.get("medium") in ARTIFACT_MEDIA:
            artifact_ok, reason = _user_provided_artifact_scope(source, observation)
            if not artifact_ok:
                return False, reason
            return _artifact_role_scope(str(source.get("material_role")), str(source.get("medium")), purpose)
        return False, "connected_account_medium_not_allowed"
    if provenance == "user_provided":
        artifact_ok, reason = _user_provided_artifact_scope(source, observation)
        if not artifact_ok:
            return False, reason
        if source.get("medium") == "image" and purpose != "candidate_clue":
            return False, f"image_inspect_not_allowed_for_{purpose}"
        if purpose == "inquiry_event":
            if role != "correspondence_export" or source.get("direction") != "inbound" or not has_text(source.get("received_at")):
                return False, "correspondence_export_not_allowed_for_inquiry_event"
        return _artifact_role_scope(str(role), str(source.get("medium")), purpose)
    if not has_text(observation.get("raw_excerpt")):
        return False, "formal_source_not_eligible"
    if purpose == "inquiry_event":
        return False, "formal_source_not_eligible"
    if is_public_http_url(source.get("canonical_url")) or is_public_http_url(source.get("final_url")):
        return True, "ok"
    return False, "formal_source_not_eligible"


def _artifact_role_scope(role: str, medium: str, purpose: str) -> tuple[bool, str]:
    """Apply the material-role matrix after binary-reference validation."""
    if role == "published_source_copy" and medium in {"document", "spreadsheet"} and purpose != "inquiry_event":
        return True, "ok"
    if role == "user_business_dataset" and purpose in {"contact_with_source_note", "candidate_clue"}:
        return True, "ok"
    if role == "correspondence_export" and purpose in {"contact_with_source_note", "candidate_clue", "inquiry_event"}:
        return True, "ok"
    if role in {"user_authored_note", "visual_reference", "unknown"} and purpose == "candidate_clue":
        return True, "ok"
    return False, f"{role}_not_allowed_for_{purpose}"


def is_eligible_formal_source(source: Any, observation: Any) -> tuple[bool, str]:
    """Compatibility wrapper for legacy formal-Claim callers."""
    return source_evidence_scope(source, observation, "formal_claim")


def safe_public_source_url(source: Any) -> str:
    """Return the public link suitable for a workbook, never a local URI."""
    if not isinstance(source, dict):
        return ""
    for field in ("final_url", "canonical_url"):
        value = source.get(field)
        if is_public_http_url(value):
            return str(value).strip()
    return ""


def user_provided_source_display(source: Any, observation: Any) -> str:
    """Render a safe business-facing source label without a hash or path."""
    if not isinstance(source, dict) or source.get("provenance") != "user_provided":
        return ""
    name = str(source.get("artifact_name")).strip() if is_safe_artifact_name(source.get("artifact_name")) else "用户提供文件"
    parsed = parse_artifact_snapshot_ref(observation.get("snapshot_ref")) if isinstance(observation, dict) else None
    fields = parsed[2] if parsed else {}
    prefix = "用户提供沟通记录" if source.get("material_role") == "correspondence_export" else "用户提供文件"
    if source.get("medium") in {"document", "correspondence"}:
        if fields.get("page", "").isdigit() and int(fields["page"]) >= 1:
            return f"{prefix}：{name}（第 {fields['page']} 页）"
        if has_text(fields.get("section")):
            return f"{prefix}：{name}（章节 {fields['section']}）"
        if has_text(fields.get("chapter")):
            return f"{prefix}：{name}（章节 {fields['chapter']}）"
    if source.get("medium") == "spreadsheet" and has_text(fields.get("sheet")):
        location = fields.get("range") or fields.get("cell")
        if has_text(location) and SPREADSHEET_CELL_OR_RANGE_RE.fullmatch(str(location)):
            return f"{prefix}：{name}（工作表 {fields['sheet']}，{location}）"
    if source.get("medium") == "image":
        location = fields.get("region") or fields.get("ocr_region") or fields.get("image")
        if has_text(location):
            return f"用户提供图片线索：{name}（图像 {location}）"
        return f"用户提供图片线索：{name}"
    return f"{prefix}：{name}"


def connected_source_display(source: Any, observation: Any) -> str:
    """Render a read-only connected-mail or attachment label without IDs or content."""
    if not isinstance(source, dict) or source.get("provenance") != "connected_account":
        return ""
    if source.get("medium") == "correspondence":
        received = str(source.get("received_at") or "").strip()
        return f"邮件来信（{received[:10]}）" if received else "邮件来信"
    name = str(source.get("artifact_name") or "").strip()
    if is_safe_artifact_name(name):
        parsed = parse_artifact_snapshot_ref(observation.get("snapshot_ref")) if isinstance(observation, dict) else None
        fields = parsed[2] if parsed else {}
        if source.get("medium") == "spreadsheet" and has_text(fields.get("sheet")):
            location = fields.get("range") or fields.get("cell")
            if has_text(location) and SPREADSHEET_CELL_OR_RANGE_RE.fullmatch(str(location)):
                return f"邮件附件：{name}（工作表 {fields['sheet']}，{location}）"
        if fields.get("page", "").isdigit():
            return f"邮件附件：{name}（第 {fields['page']} 页）"
        return f"邮件附件：{name}"
    return "邮件附件"


def _normalized_url_tokens(value: Any) -> set[str]:
    tokens: set[str] = set()
    for match in URL_RE.findall(str(value or "")):
        token = match.rstrip(".,;:!?)]}\"").casefold().rstrip("/")
        if token:
            tokens.add(token)
    return tokens


def contact_literal_is_present(contact_type: Any, source_literal: Any, raw_excerpt: Any) -> bool:
    """Verify the full typed contact token exists in the cited source text."""
    literal = str(source_literal or "").strip()
    ctype = str(contact_type or "").casefold()
    if not literal:
        return False
    literal_emails = {item.casefold() for item in EMAIL_RE.findall(literal)}
    if literal_emails:
        if ctype not in {"email", "department_email", "person_email"}:
            return False
        raw_emails = {item.casefold() for item in EMAIL_RE.findall(str(raw_excerpt or ""))}
        return literal_emails == raw_emails.intersection(literal_emails)
    literal_urls = _normalized_url_tokens(literal)
    if literal_urls:
        if ctype not in {"contact_form", "supplier_portal", "inquiry_entry", "linkedin_company", "linkedin_person"}:
            return False
        return literal_urls.issubset(_normalized_url_tokens(raw_excerpt))
    return text_contains_exact_phrase(raw_excerpt, literal)


def digits_only(value: Any) -> str:
    return re.sub(r"\D+", "", str(value or ""))


def normalize_contact_value(contact_type: Any, value: Any) -> str:
    """Normalize a contact value enough to verify it can derive from source_literal."""
    raw = str(value or "").strip()
    ctype = str(contact_type or "").casefold()
    if "email" in ctype:
        emails = EMAIL_RE.findall(raw)
        return emails[0].casefold() if emails else raw.casefold()
    if ctype in {"phone", "mobile", "whatsapp", "fax"}:
        return digits_only(raw)
    if ctype in {"contact_form", "supplier_portal", "inquiry_entry", "linkedin_company", "linkedin_person"}:
        return raw.rstrip("/").casefold()
    return compact_text(raw)


def canonical_contact_user_status(export_status: Any) -> str:
    """Return the only user-facing contact status allowed for an export_status."""
    return CONTACT_USER_STATUS_BY_EXPORT_STATUS.get(str(export_status or ""), "待确认归属")


def normalized_contact_derives_from_literal(contact_type: Any, normalized_value: Any, source_literal: Any) -> bool:
    """Check that normalized_value is derivable from the cited source_literal."""
    ctype = str(contact_type or "").casefold()
    normalized = normalize_contact_value(ctype, normalized_value)
    literal_norm = normalize_contact_value(ctype, source_literal)
    if not normalized or not literal_norm:
        return False
    if "email" in ctype:
        normalized_raw = str(normalized_value or "").strip()
        normalized_emails = [email.casefold() for email in EMAIL_RE.findall(normalized_raw)]
        # The exported normalized value must be exactly one canonical email,
        # not a semicolon/comma bundle where only the first address matches.
        if len(normalized_emails) != 1 or normalized_raw.casefold() != normalized_emails[0]:
            return False
        literal_emails = {email.casefold() for email in EMAIL_RE.findall(str(source_literal or ""))}
        return normalized_emails[0] in literal_emails
    if ctype in {"phone", "mobile", "whatsapp", "fax"}:
        # Phone normalization may strip punctuation/spacing only.  Arbitrary
        # prefix/suffix truncation (for example "9" from a full number) is not
        # a valid derivation.
        return normalized == literal_norm
    # URL, form, portal, social, address, and other non-phone values may only
    # receive the normalization defined above. Substring matching would turn
    # `/contact-form` into a different `/contact` route.
    return normalized == literal_norm


def structured_value_fragments(value: Any) -> tuple[list[str], bool]:
    """Return verifiable scalar content from a Claim typed_value."""
    if isinstance(value, str):
        return ([value] if has_text(value) else []), not has_text(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return [str(value)], False
    if value is None or isinstance(value, bool):
        return [], True
    if isinstance(value, list):
        fragments: list[str] = []
        unanchorable = not value
        for item in value:
            item_fragments, item_unanchorable = structured_value_fragments(item)
            fragments.extend(item_fragments)
            unanchorable = unanchorable or item_unanchorable
        return fragments, unanchorable
    if isinstance(value, dict):
        fragments = []
        unanchorable = not value
        for item in value.values():
            item_fragments, item_unanchorable = structured_value_fragments(item)
            fragments.extend(item_fragments)
            unanchorable = unanchorable or item_unanchorable
        return fragments, unanchorable
    return [], True


def claim_value_is_anchored_in_excerpt(claim: dict[str, Any], raw_excerpt: Any) -> bool:
    """Require every structured Claim value fragment to be visible in its evidence."""
    fragments, unanchorable = structured_value_fragments(claim.get("typed_value"))
    return not unanchorable and bool(fragments) and all(text_contains_exact_phrase(raw_excerpt, fragment) for fragment in fragments)


def review_finding_blocks_delivery(finding: dict[str, Any]) -> bool:
    """Critical/major findings close only when verified fixed."""
    severity = finding.get("severity")
    status = finding.get("status")
    if severity in {"critical", "major"}:
        return status != FIXED_FINDING_STATUS
    if severity == "minor":
        return status not in ({FIXED_FINDING_STATUS} | NON_BLOCKING_DISCLOSURE_STATUSES)
    return True


def issue(severity: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"severity": severity, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def id_map(graph: dict[str, Any], key: str, id_field: str | None = None) -> dict[str, dict[str, Any]]:
    id_field = id_field or ID_FIELDS.get(key)
    result: dict[str, dict[str, Any]] = {}
    if id_field is None:
        return result
    for item in ensure_list(graph, key):
        if isinstance(item, dict):
            raw = item.get(id_field)
            if isinstance(raw, str) and raw:
                result[raw] = item
    return result


def all_id_maps(graph: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {key: id_map(graph, key) for key in GRAPH_ARRAY_KEYS}


def canonical_graph_for_hash(graph: dict[str, Any]) -> dict[str, Any]:
    copy_graph = copy.deepcopy(graph)
    copy_graph.pop("audits", None)
    copy_graph.pop("delivery_manifests", None)
    return copy_graph


def graph_hash(graph: dict[str, Any]) -> str:
    canonical = canonical_graph_for_hash(graph)
    data = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
