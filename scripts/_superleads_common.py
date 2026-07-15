#!/usr/bin/env python3
"""Shared helpers for Superleads scripts. Uses only Python standard library."""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

GRAPH_ARRAY_KEYS = [
    "runs", "briefs", "plans", "candidates", "sources", "observations", "entities",
    "entity_relationships", "claims", "claim_evidence", "contact_points", "contact_claims",
    "unassigned_contact_leads", "hypotheses", "assessments", "review_findings", "audits",
    "delivery_manifests", "search_logs",
]

ID_FIELDS = {
    "runs": "run_id", "briefs": "brief_id", "plans": "plan_id", "candidates": "candidate_id",
    "sources": "source_id", "observations": "observation_id", "entities": "entity_id",
    "entity_relationships": "entity_relationship_id", "claims": "claim_id", "claim_evidence": "claim_evidence_id",
    "contact_points": "contact_id", "contact_claims": "contact_claim_id",
    "unassigned_contact_leads": "unassigned_contact_lead_id", "hypotheses": "hypothesis_id",
    "assessments": "assessment_id", "review_findings": "finding_id", "audits": "audit_id",
    "delivery_manifests": "delivery_manifest_id", "search_logs": "search_log_id",
}

FIXED_FINDING_STATUS = "verified_fixed"
NON_BLOCKING_DISCLOSURE_STATUSES = {"accepted_with_disclosure", "rejected_with_reviewer_reason"}

EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
URL_RE = re.compile(r"(?i)https?://[^\s<>\"']+")

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
CONTACT_SOURCE_ALLOWED_TYPES = {
    "website",
    "social",
    "registry",
    "directory",
    "map",
    "document",
    "spreadsheet",
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
