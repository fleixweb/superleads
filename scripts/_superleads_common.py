#!/usr/bin/env python3
"""Shared helpers for Superleads scripts. Uses only Python standard library."""
from __future__ import annotations

import copy
import hashlib
import ipaddress
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlsplit

GRAPH_ARRAY_KEYS = [
    "runs", "briefs", "plans", "candidates", "sources", "observations", "entities",
    "entity_relationships", "claims", "claim_evidence", "contact_points", "contact_claims",
    "unassigned_contact_leads", "hypotheses", "assessments", "review_findings", "audits",
    "delivery_manifests", "search_logs", "review_attestations", "inquiries", "mail_intake_rules",
    "scope_decisions",
]

ID_FIELDS = {
    "runs": "run_id", "briefs": "brief_id", "plans": "plan_id", "candidates": "candidate_id",
    "sources": "source_id", "observations": "observation_id", "entities": "entity_id",
    "entity_relationships": "entity_relationship_id", "claims": "claim_id", "claim_evidence": "claim_evidence_id",
    "contact_points": "contact_id", "contact_claims": "contact_claim_id",
    "unassigned_contact_leads": "unassigned_contact_lead_id", "hypotheses": "hypothesis_id",
    "assessments": "assessment_id", "review_findings": "finding_id", "audits": "audit_id",
    "delivery_manifests": "delivery_manifest_id", "search_logs": "search_log_id",
    "review_attestations": "attestation_id",
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
SAFE_ANONYMOUS_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
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
REVIEW_ATTESTATION_CONCLUSIONS = {"passed", "failed"}
REVIEW_PROVENANCE_LEVELS = {"declared_separate_session"}
AUDIT_REVIEW_PROVENANCE_LEVELS = REVIEW_PROVENANCE_LEVELS | {
    "self_review_fallback",
    "not_run",
    "not_applicable",
}
REVIEW_SUBJECT_EXCLUDED_KEYS = {"review_attestations", "audits", "delivery_manifests"}
SEARCH_LOG_RESULT_USES = {"candidate_seed_only"}
OPAQUE_ID_FORBIDDEN_TERMS = {"token", "cookie", "password", "passwd", "secret", "bearer", "authorization"}
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

BUSINESS_RELEVANCE_STATUS_LABELS = {
    "directly_related": "直接相关",
    "possibly_related": "可能相关",
    "explicitly_excluded_or_unrelated": "明确排除/不相关",
    "identity_pending": "主体待确认",
    "insufficient_information": "信息不足",
}

PUBLIC_SIGNAL_STATUS_LABELS = {
    "observed": "已观察",
    "not_observed": "已查未见",
    "not_searched": "未检索",
    "identity_pending": "主体待确认",
    "source_restricted": "来源受限",
}

# Capability reports are supplied by the Agent/host, never discovered by the
# local scripts.  These are workflow values, not a platform or business ICP.
CANONICAL_CAPABILITY_STATUSES = {"available", "missing", "unknown"}
HOST_TOOL_STATUSES = {"available", "missing", "unknown", "failed"}
HOST_OPERATION_STATUSES = {"verified", "missing", "unknown", "failed", "not_verified"}
CODEX_NATIVE_WEB_SEARCH_ADAPTER_ID = "codex_cli_native_web_search"
CODEX_NATIVE_WEB_SEARCH_ADAPTER_VERSION = "1"
CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES = ("search.web", "source.open")
CODEX_NATIVE_WEB_SEARCH_ALLOWED_CONCRETE_TOOLS = ("web_search",)
CODEX_SHELL_HTTP_SOURCE_OPEN_ADAPTER_ID = "codex_cli_shell_http_source_open"
CODEX_SHELL_HTTP_SOURCE_OPEN_ADAPTER_VERSION = "1"
CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES = ("source.open",)
CODEX_SHELL_HTTP_ALLOWED_CONCRETE_TOOLS = ("curl", "wget", "python_requests")
TOOL_NAME_PLATFORM_VALUES = set(CODEX_SHELL_HTTP_ALLOWED_CONCRETE_TOOLS) | {"shell_curl", "native_fetch"}
CANONICAL_PLATFORM_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DNS_HOST_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
LEGACY_IPV4_PART_RE = re.compile(r"(?:0[xX][0-9A-Fa-f]+|0[0-7]*|[1-9][0-9]*|0)$")
NUMERIC_IPV4_PART_RE = re.compile(r"(?:0[xX][0-9A-Fa-f]*|[0-9]+)$")
SHELL_HTTP_SENSITIVE_VALUE_RE = re.compile(
    r"(?i)(?:\b(?:authorization|cookie|token|password)\s*[:=]|\b(?:bearer|basic)\s+[a-z0-9._~+/-]+)"
)


def _host_status(value: Any) -> str:
    return str(value).strip().lower() if isinstance(value, str) else "unknown"


def _operation_status(operation: Any) -> str:
    if not isinstance(operation, dict):
        return "unknown"
    return _host_status(operation.get("status"))


def is_canonical_platform_id(value: Any) -> bool:
    """Accept one unambiguous host ID, never a concrete tool name."""
    return (
        isinstance(value, str)
        and CANONICAL_PLATFORM_ID_RE.fullmatch(value) is not None
        and value not in TOOL_NAME_PLATFORM_VALUES
    )


def _legacy_ipv4_address(hostname: str) -> ipaddress.IPv4Address | None:
    """Parse historical numeric IPv4 spellings accepted by common HTTP stacks.

    This is intentionally local parsing only.  It catches known textual
    loopback/private bypasses without making a DNS request from graph tools.
    """
    parts = hostname.split(".")
    if not 1 <= len(parts) <= 4 or not all(LEGACY_IPV4_PART_RE.fullmatch(part) for part in parts):
        return None

    def parse_part(part: str) -> int:
        lowered = part.casefold()
        if lowered.startswith("0x"):
            return int(part[2:], 16)
        if len(part) > 1 and part.startswith("0"):
            return int(part, 8)
        return int(part, 10)

    values = [parse_part(part) for part in parts]
    if len(values) == 1:
        if values[0] > 0xFFFFFFFF:
            return None
        number = values[0]
    elif len(values) == 2:
        if values[0] > 0xFF or values[1] > 0xFFFFFF:
            return None
        number = (values[0] << 24) | values[1]
    elif len(values) == 3:
        if values[0] > 0xFF or values[1] > 0xFF or values[2] > 0xFFFF:
            return None
        number = (values[0] << 24) | (values[1] << 16) | values[2]
    else:
        if any(value > 0xFF for value in values):
            return None
        number = sum(value << (8 * (3 - index)) for index, value in enumerate(values))
    return ipaddress.IPv4Address(number)


def _looks_like_numeric_ipv4(hostname: str) -> bool:
    """Recognize invalid numeric IPv4-looking hosts so they fail closed."""
    parts = hostname.split(".")
    return bool(1 <= len(parts) <= 4 and all(NUMERIC_IPV4_PART_RE.fullmatch(part) for part in parts))


def _is_valid_public_dns_hostname(hostname: str) -> bool:
    """Validate a normal DNS name without claiming anything about its DNS answer."""
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii").casefold()
    except UnicodeError:
        return False
    if len(ascii_hostname) > 253 or "." not in ascii_hostname:
        return False
    labels = ascii_hostname.split(".")
    return all(DNS_HOST_LABEL_RE.fullmatch(label) for label in labels)


def is_safe_public_http_url(value: Any) -> bool:
    """Allow a credential-free public HTTP(S) URL without resolving DNS.

    The graph layer rejects literal global-address failures, including legacy
    IPv4 spellings such as ``127.1`` and ``0x7f000001``.  It deliberately does
    not resolve arbitrary DNS names; an HTTP executor must separately pin each
    connection and redirect target to a global address.
    """
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        return False
    try:
        parsed = urlsplit(value)
        hostname = (parsed.hostname or "").casefold().rstrip(".")
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme.casefold() not in {"http", "https"} or not hostname:
        return False
    if port is not None and not 1 <= port <= 65535:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
        return False
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        legacy_address = _legacy_ipv4_address(hostname)
        if legacy_address is not None:
            return False
        if _looks_like_numeric_ipv4(hostname):
            return False
        return _is_valid_public_dns_hostname(hostname)
    return address.is_global


def source_has_safe_public_http_urls(source: Any) -> bool:
    """Require a public Source to contain no unsafe declared HTTP endpoint."""
    if not isinstance(source, dict):
        return False
    values = [source.get(field) for field in ("canonical_url", "final_url")]
    declared = [value for value in values if has_text(value)]
    return bool(declared) and all(is_safe_public_http_url(value) for value in declared)


def contains_shell_http_forbidden_data(value: Any) -> bool:
    """Reject local paths and credential-shaped text from shell HTTP metadata."""
    if isinstance(value, dict):
        return any(contains_shell_http_forbidden_data(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_shell_http_forbidden_data(item) for item in value)
    if not isinstance(value, str):
        return False
    return contains_local_path(value) or bool(SHELL_HTTP_SENSITIVE_VALUE_RE.search(value))


def _adapter_result(adapter_id: str | None, owned: tuple[str, ...], raw_mapped: dict[str, str],
                    issues: list[dict[str, str]], recognized: bool,
                    allowed_tools: dict[str, list[str]] | None = None) -> dict[str, Any]:
    valid = recognized and not issues
    return {
        "adapter_id": adapter_id,
        "recognized": recognized,
        "valid": valid,
        "owned_capabilities": list(owned),
        "mapped_capabilities": dict(raw_mapped if valid else {capability: "unknown" for capability in owned}),
        "raw_mapped_capabilities": dict(raw_mapped),
        "allowed_concrete_tools": allowed_tools or {},
        "issues": issues,
    }


def _validate_adapter_mapping(report: dict[str, Any], owned: tuple[str, ...], raw_mapped: dict[str, str],
                              issues: list[dict[str, str]], adapter_label: str) -> None:
    declared = report.get("canonical_capabilities")
    if not isinstance(declared, dict):
        issues.append({"code": "capability_adapter_canonical_mapping_missing", "message": "Capability adapter report requires its canonical capability mapping", "path": "capability_adapter_report.canonical_capabilities"})
        return
    if set(declared) != set(owned):
        issues.append({"code": "capability_adapter_canonical_mapping_invalid", "message": f"{adapter_label} may declare only its owned canonical capabilities", "path": "capability_adapter_report.canonical_capabilities"})
    for capability in owned:
        actual = declared.get(capability)
        if actual not in CANONICAL_CAPABILITY_STATUSES:
            issues.append({"code": "capability_adapter_canonical_mapping_invalid", "message": f"Canonical mapping for {capability} is missing or invalid", "path": f"capability_adapter_report.canonical_capabilities.{capability}"})
        elif actual != raw_mapped[capability]:
            issues.append({"code": "capability_adapter_mapping_mismatch", "message": f"Canonical mapping for {capability} does not match the verified adapter operation", "path": f"capability_adapter_report.canonical_capabilities.{capability}"})


def _resolve_native_web_search_adapter(report: Any) -> dict[str, Any]:
    raw_mapped = {"search.web": "unknown", "source.open": "unknown"}
    issues: list[dict[str, str]] = []
    adapter_id = CODEX_NATIVE_WEB_SEARCH_ADAPTER_ID

    def add(code: str, message: str, path: str) -> None:
        issues.append({"code": code, "message": message, "path": path})

    if not isinstance(report, dict):
        add("capability_adapter_report_invalid", "Capability adapter report must be an object", "capability_adapter_report")
        return _adapter_result(adapter_id, CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES, raw_mapped, issues, False)
    if not is_canonical_platform_id(report.get("platform")):
        add("capability_adapter_platform_not_canonical", "Capability adapter report platform must be a canonical host ID", "capability_adapter_report.platform")
    if report.get("platform") != "codex_cli":
        add("capability_adapter_platform_unsupported", "Capability adapter report platform is not codex_cli", "capability_adapter_report.platform")
    adapter = report.get("adapter")
    if not isinstance(adapter, dict) or adapter.get("adapter_id") != adapter_id:
        add("capability_adapter_unsupported", "Capability adapter report does not identify the supported Codex CLI native web-search adapter", "capability_adapter_report.adapter")
    if not isinstance(adapter, dict) or not has_text(adapter.get("adapter_version")):
        add("capability_adapter_version_missing", "Capability adapter report requires an adapter version", "capability_adapter_report.adapter.adapter_version")
    elif adapter.get("adapter_version") != CODEX_NATIVE_WEB_SEARCH_ADAPTER_VERSION:
        add("capability_adapter_version_unsupported", "Capability adapter report uses an unsupported adapter version", "capability_adapter_report.adapter.adapter_version")
    for field in ("detected_at", "detection"):
        if not has_text(report.get(field)):
            add("capability_adapter_detection_missing", "Capability adapter report requires detection time and method", f"capability_adapter_report.{field}")
    tools = report.get("host_tools")
    if not isinstance(tools, dict) or set(tools) != {"web_search"}:
        add("capability_adapter_host_tool_unsupported", "Only the explicit native web_search host tool may map through this adapter", "capability_adapter_report.host_tools")
        tools = {}
    web_search = tools.get("web_search") if isinstance(tools, dict) else None
    if not isinstance(web_search, dict):
        add("capability_adapter_host_tool_invalid", "Native web_search tool report must be an object", "capability_adapter_report.host_tools.web_search")
        web_search = {}
    tool_status = _host_status(web_search.get("status"))
    if tool_status not in HOST_TOOL_STATUSES:
        add("capability_adapter_host_tool_status_invalid", "Native web_search status is invalid", "capability_adapter_report.host_tools.web_search.status")
        tool_status = "unknown"
    operations = web_search.get("operations")
    if not isinstance(operations, dict) or set(operations) != {"search", "open_source"}:
        add("capability_adapter_operations_invalid", "Native web_search report must distinguish search from open_source", "capability_adapter_report.host_tools.web_search.operations")
        operations = {}
    search_status, open_status = _operation_status(operations.get("search")), _operation_status(operations.get("open_source"))
    if search_status not in HOST_OPERATION_STATUSES:
        add("capability_adapter_operation_status_invalid", "search operation status is invalid", "capability_adapter_report.host_tools.web_search.operations.search.status")
        search_status = "unknown"
    if open_status not in HOST_OPERATION_STATUSES:
        add("capability_adapter_operation_status_invalid", "open_source operation status is invalid", "capability_adapter_report.host_tools.web_search.operations.open_source.status")
        open_status = "unknown"
    if tool_status == "available" and search_status == "verified": raw_mapped["search.web"] = "available"
    elif tool_status in {"missing", "failed"} or search_status in {"missing", "failed"}: raw_mapped["search.web"] = "missing"
    open_record = operations.get("open_source") if isinstance(operations.get("open_source"), dict) else {}
    open_complete = open_status == "verified" and is_safe_public_http_url(open_record.get("original_url")) and all(has_text(open_record.get(field)) for field in ("source_title", "raw_excerpt", "excerpt_locator"))
    if open_status == "verified" and not open_complete:
        add("capability_adapter_open_source_verification_incomplete", "open_source requires a public URL, source identifier, verbatim excerpt, and locator", "capability_adapter_report.host_tools.web_search.operations.open_source")
    if tool_status == "available" and open_complete: raw_mapped["source.open"] = "available"
    elif tool_status in {"missing", "failed"}: raw_mapped["source.open"] = "missing"
    _validate_adapter_mapping(report, CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES, raw_mapped, issues, "Native web-search adapter")
    for field in ("source_title", "raw_excerpt", "excerpt_locator"):
        if field in open_record and contains_local_path(open_record.get(field)):
            add("capability_adapter_local_path_forbidden", "Capability adapter report may not contain a local path", f"capability_adapter_report.host_tools.web_search.operations.open_source.{field}")
    return _adapter_result(adapter_id, CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES, raw_mapped, issues, True, {"source.open": list(CODEX_NATIVE_WEB_SEARCH_ALLOWED_CONCRETE_TOOLS), "search.web": ["web_search"]})


def _resolve_shell_http_source_open_adapter(report: Any) -> dict[str, Any]:
    raw_mapped = {"source.open": "unknown"}
    issues: list[dict[str, str]] = []
    adapter_id = CODEX_SHELL_HTTP_SOURCE_OPEN_ADAPTER_ID

    def add(code: str, message: str, path: str) -> None:
        issues.append({"code": code, "message": message, "path": path})

    if not isinstance(report, dict):
        add("capability_adapter_report_invalid", "Capability adapter report must be an object", "capability_adapter_report")
        return _adapter_result(adapter_id, CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES, raw_mapped, issues, False)
    if not is_canonical_platform_id(report.get("platform")):
        add("capability_adapter_platform_not_canonical", "Capability adapter report platform must be a canonical host ID", "capability_adapter_report.platform")
    if report.get("platform") != "codex_cli": add("capability_adapter_platform_unsupported", "Shell HTTP adapter requires platform codex_cli", "capability_adapter_report.platform")
    adapter = report.get("adapter")
    if not isinstance(adapter, dict) or adapter.get("adapter_id") != adapter_id: add("capability_adapter_unsupported", "Capability adapter report does not identify the supported Codex CLI shell HTTP adapter", "capability_adapter_report.adapter")
    if not isinstance(adapter, dict) or not has_text(adapter.get("adapter_version")):
        add("capability_adapter_version_missing", "Capability adapter report requires an adapter version", "capability_adapter_report.adapter.adapter_version")
    elif adapter.get("adapter_version") != CODEX_SHELL_HTTP_SOURCE_OPEN_ADAPTER_VERSION:
        add("capability_adapter_version_unsupported", "Capability adapter report uses an unsupported adapter version", "capability_adapter_report.adapter.adapter_version")
    for field in ("detected_at", "detection"):
        if not has_text(report.get(field)): add("capability_adapter_detection_missing", "Capability adapter report requires detection time and method", f"capability_adapter_report.{field}")
    tools = report.get("host_tools")
    if not isinstance(tools, dict) or set(tools) != {"shell_http"}:
        add("capability_adapter_host_tool_unsupported", "Shell HTTP adapter accepts only the explicit shell_http host tool", "capability_adapter_report.host_tools")
        tools = {}
    shell_http = tools.get("shell_http") if isinstance(tools, dict) else None
    if not isinstance(shell_http, dict):
        add("capability_adapter_host_tool_invalid", "shell_http tool report must be an object", "capability_adapter_report.host_tools.shell_http")
        shell_http = {}
    tool_status = _host_status(shell_http.get("status"))
    if tool_status not in HOST_TOOL_STATUSES:
        add("capability_adapter_host_tool_status_invalid", "shell_http status is invalid", "capability_adapter_report.host_tools.shell_http.status")
        tool_status = "unknown"
    allowed_tools = shell_http.get("allowed_concrete_tools")
    if not isinstance(allowed_tools, list) or not allowed_tools or len(set(allowed_tools)) != len(allowed_tools) or any(tool not in CODEX_SHELL_HTTP_ALLOWED_CONCRETE_TOOLS for tool in allowed_tools):
        add("codex_shell_http_allowed_tool_invalid", "Shell HTTP adapter requires a non-empty unique allowlist of supported concrete tools", "capability_adapter_report.host_tools.shell_http.allowed_concrete_tools")
        allowed_tools = []
    operations = shell_http.get("operations")
    if not isinstance(operations, dict) or set(operations) != {"open_source"}:
        add("capability_adapter_operations_invalid", "Shell HTTP adapter must record only open_source", "capability_adapter_report.host_tools.shell_http.operations")
        operations = {}
    open_record = operations.get("open_source") if isinstance(operations.get("open_source"), dict) else {}
    open_status = _operation_status(open_record)
    if open_status not in HOST_OPERATION_STATUSES:
        add("capability_adapter_operation_status_invalid", "open_source operation status is invalid", "capability_adapter_report.host_tools.shell_http.operations.open_source.status")
        open_status = "unknown"
    if open_status == "verified" and open_record.get("request_method") != "GET":
        add("codex_shell_http_request_method_not_allowed", "Shell HTTP source opening allows GET only", "capability_adapter_report.host_tools.shell_http.operations.open_source.request_method")
    if open_status == "verified" and (not is_safe_public_http_url(open_record.get("original_url")) or not is_safe_public_http_url(open_record.get("final_url"))):
        add("codex_shell_http_url_not_public", "Shell HTTP source opening requires public credential-free HTTP(S) original and final URLs", "capability_adapter_report.host_tools.shell_http.operations.open_source")
    if open_status == "verified" and (not isinstance(open_record.get("http_status"), int) or not 200 <= open_record["http_status"] < 300):
        add("codex_shell_http_http_status_not_success", "Shell HTTP source opening requires a successful HTTP status", "capability_adapter_report.host_tools.shell_http.operations.open_source.http_status")
    if open_status == "verified" and not all(has_text(open_record.get(field)) for field in ("source_title", "raw_excerpt", "excerpt_locator")):
        add("capability_adapter_open_source_verification_incomplete", "Shell HTTP source opening requires source identifier, verbatim excerpt, and locator", "capability_adapter_report.host_tools.shell_http.operations.open_source")
    if contains_shell_http_forbidden_data(report):
        add("codex_shell_http_forbidden_request_data", "Shell HTTP adapter report may not contain local paths or credential/request-secret data", "capability_adapter_report")
    open_complete = open_status == "verified" and open_record.get("request_method") == "GET" and is_safe_public_http_url(open_record.get("original_url")) and is_safe_public_http_url(open_record.get("final_url")) and isinstance(open_record.get("http_status"), int) and 200 <= open_record["http_status"] < 300 and all(has_text(open_record.get(field)) for field in ("source_title", "raw_excerpt", "excerpt_locator")) and bool(allowed_tools)
    if tool_status == "available" and open_complete: raw_mapped["source.open"] = "available"
    elif tool_status in {"missing", "failed"}: raw_mapped["source.open"] = "missing"
    _validate_adapter_mapping(report, CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES, raw_mapped, issues, "Shell HTTP adapter")
    return _adapter_result(adapter_id, CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES, raw_mapped, issues, True, {"source.open": list(allowed_tools)})


def resolve_capability_adapter_report(report: Any) -> dict[str, Any]:
    """Resolve one backwards-compatible adapter report without probing host tools."""
    adapter = report.get("adapter") if isinstance(report, dict) else None
    adapter_id = adapter.get("adapter_id") if isinstance(adapter, dict) else None
    if adapter_id == CODEX_NATIVE_WEB_SEARCH_ADAPTER_ID:
        return _resolve_native_web_search_adapter(report)
    if adapter_id == CODEX_SHELL_HTTP_SOURCE_OPEN_ADAPTER_ID:
        return _resolve_shell_http_source_open_adapter(report)
    return _adapter_result(
        str(adapter_id) if has_text(adapter_id) else None,
        (), {},
        [{"code": "capability_adapter_unsupported", "message": "Capability adapter report does not identify a supported adapter", "path": "capability_adapter_report.adapter"}],
        False,
    )


def resolve_capability_adapter_reports(reports: Any) -> dict[str, Any]:
    """Aggregate independently verified providers without allowing duplicate active owners."""
    report_items = reports if isinstance(reports, list) else []
    adapter_results = [resolve_capability_adapter_report(report) for report in report_items]
    issues: list[dict[str, str]] = []
    if not adapter_results:
        issues.append({
            "code": "capability_adapter_reports_empty",
            "message": "Capability adapter reports must contain at least one explicit provider report",
            "path": "capability_adapter_reports",
        })
    owned: set[str] = set()
    active_owners: dict[str, list[str]] = {}
    raw_statuses: dict[str, list[str]] = {}
    for index, result in enumerate(adapter_results):
        for item in result["issues"]:
            issues.append({**item, "path": f"capability_adapter_reports[{index}].{item['path']}"})
        for capability in result["owned_capabilities"]:
            owned.add(capability)
            raw_statuses.setdefault(capability, []).append(result["mapped_capabilities"].get(capability, "unknown"))
            if result["valid"] and result["mapped_capabilities"].get(capability) == "available":
                active_owners.setdefault(capability, []).append(str(result.get("adapter_id") or "unknown"))
    for capability, owners in active_owners.items():
        if len(owners) > 1:
            issues.append({"code": "capability_adapter_capability_owner_conflict", "message": f"Multiple verified adapters claim {capability}: {', '.join(owners)}", "path": "capability_adapter_reports"})
    mapped: dict[str, str] = {}
    for capability in owned:
        statuses = raw_statuses.get(capability, [])
        if len(active_owners.get(capability, [])) > 1: mapped[capability] = "unknown"
        elif active_owners.get(capability): mapped[capability] = "available"
        elif "missing" in statuses: mapped[capability] = "missing"
        else: mapped[capability] = "unknown"
    return {
        "recognized": bool(adapter_results) and all(result["recognized"] for result in adapter_results),
        "valid": bool(adapter_results) and not issues,
        "owned_capabilities": sorted(owned),
        "mapped_capabilities": mapped,
        "issues": issues,
        "adapter_results": adapter_results,
        "active_owners": active_owners,
    }


def adapter_reports_from_run(run: Any) -> list[Any]:
    """Read plural reports first while accepting the historical single report."""
    if not isinstance(run, dict):
        return []
    reports: list[Any] = []
    plural = run.get("capability_adapter_reports")
    if isinstance(plural, list): reports.extend(plural)
    if run.get("capability_adapter_report") is not None: reports.append(run["capability_adapter_report"])
    return reports


def codex_adapter_allows_observation(adapter_result: dict[str, Any], capability: Any, concrete_tool: Any) -> bool:
    """Require an active provider to explicitly authorize a Codex observation tool."""
    if not isinstance(capability, str) or not isinstance(concrete_tool, str):
        return False
    for result in adapter_result.get("adapter_results", []):
        if not isinstance(result, dict) or not result.get("valid"):
            continue
        if result.get("mapped_capabilities", {}).get(capability) != "available":
            continue
        allowed = result.get("allowed_concrete_tools", {}).get(capability, [])
        if concrete_tool in allowed:
            return True
    return False


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


def is_safe_anonymous_id(value: Any) -> bool:
    """Accept only short host/session opaque IDs, not names, emails, tokens, or paths."""
    lowered = str(value or "").casefold()
    return (
        isinstance(value, str)
        and SAFE_ANONYMOUS_ID_RE.fullmatch(value) is not None
        and not contains_local_path(value)
        and not EMAIL_RE.search(value)
        and not URL_RE.search(value)
        and not any(term in lowered for term in OPAQUE_ID_FORBIDDEN_TERMS)
    )


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


def current_run(graph: dict[str, Any]) -> dict[str, Any] | None:
    """Return the last Run, matching the existing delivery scripts' convention."""
    for run in reversed(ensure_list(graph, "runs")):
        if isinstance(run, dict):
            return run
    return None


def current_brief(graph: dict[str, Any], run: dict[str, Any] | None = None) -> dict[str, Any] | None:
    run = run or current_run(graph)
    brief_id = run.get("brief_id") if isinstance(run, dict) else None
    for brief in ensure_list(graph, "briefs"):
        if isinstance(brief, dict) and brief.get("brief_id") == brief_id:
            return brief
    return None


def formal_positive_assessments_for_run(graph: dict[str, Any], run: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return current-run positive Assessments that a formal export would review."""
    run = run or current_run(graph)
    if not isinstance(run, dict):
        return []
    run_id = run.get("run_id")
    brief_id = run.get("brief_id")
    brief = current_brief(graph, run)
    contract_required = formal_targeting_contract_required(brief)
    exception_entities = formal_exception_entity_ids(brief)
    exception_mode = formal_exception_mode(brief)
    in_scope_entities = {
        str(item.get("entity_id"))
        for item in ensure_list(graph, "scope_decisions")
        if isinstance(item, dict)
        and item.get("run_id") == run_id
        and item.get("brief_id") == brief_id
        and item.get("overall_status") == "in_scope"
        and has_text(item.get("entity_id"))
    }
    result: list[dict[str, Any]] = []
    for assessment in ensure_list(graph, "assessments"):
        if not isinstance(assessment, dict):
            continue
        entity_id = assessment.get("entity_id")
        if assessment.get("run_id") != run_id or assessment.get("brief_id") != brief_id:
            continue
        if assessment.get("disposition") not in {"重点开发", "推荐跟进"}:
            continue
        if exception_mode:
            if str(entity_id) not in exception_entities:
                continue
        elif contract_required:
            if str(entity_id) not in in_scope_entities:
                continue
        result.append(assessment)
    return result


def normalize_region_values(value: Any) -> set[str]:
    """Normalize a user-specified country/region value without inventing defaults."""
    if isinstance(value, str):
        return {compact_text(value).casefold()} if has_text(value) else set()
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            if has_text(item):
                result.add(compact_text(item).casefold())
        return result
    return set()


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
    if source_has_safe_public_http_urls(source):
        return True, "ok"
    return False, "public_source_url_not_safe"


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
    if not source_has_safe_public_http_urls(source):
        return ""
    for field in ("final_url", "canonical_url"):
        value = source.get(field)
        if is_safe_public_http_url(value):
            return str(value)
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


def business_relevance_user_label(status: Any) -> str:
    """Return the only business-facing label for candidate relevance."""
    return BUSINESS_RELEVANCE_STATUS_LABELS.get(str(status or ""), "信息不足")


def public_signal_status_user_label(status: Any) -> str:
    """Return the only business-facing label for public-signal observation status."""
    return PUBLIC_SIGNAL_STATUS_LABELS.get(str(status or ""), "未检索")


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
    """Return the stable semantic research projection used for freshness checks.

    The projection is intentionally not a raw JSON file-byte hash.  It keeps
    all research and review-input objects that can affect conclusions
    (Run/Brief/Plan, entities, sources, observations, Claims, ClaimEvidence,
    contacts, ScopeDecision, Assessment, ReviewFinding, SearchLog, inquiries,
    and similar graph records) while excluding self-referential delivery
    objects: ReviewAttestation, Audit, and DeliveryManifest.
    """
    copy_graph = copy.deepcopy(graph)
    for key in REVIEW_SUBJECT_EXCLUDED_KEYS:
        copy_graph.pop(key, None)
    # Array order is a storage detail, not a research conclusion.  The
    # documented semantic projection sorts every graph collection by its
    # formal ID before canonical JSON serialization.
    for key, id_field in ID_FIELDS.items():
        items = copy_graph.get(key)
        if isinstance(items, list) and all(isinstance(item, dict) for item in items):
            copy_graph[key] = sorted(items, key=lambda item: str(item.get(id_field) or ""))
    return copy_graph


def graph_hash(graph: dict[str, Any]) -> str:
    canonical = canonical_graph_for_hash(graph)
    data = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def review_subject_hash(graph: dict[str, Any]) -> str:
    """Hash the documented canonical projection reviewed by an attestation."""
    return graph_hash(graph)


def active_review_attestations(graph: dict[str, Any], run: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Return passed attestations for the current Run/Brief/Plan/review cycle."""
    run = run or current_run(graph)
    if not isinstance(run, dict):
        return []
    result: list[dict[str, Any]] = []
    for item in ensure_list(graph, "review_attestations"):
        if not isinstance(item, dict):
            continue
        if (
            item.get("run_id") == run.get("run_id")
            and item.get("brief_id") == run.get("brief_id")
            and item.get("plan_id") == run.get("plan_id")
            and item.get("review_cycle_id") == run.get("review_cycle_id")
            and item.get("conclusion") == "passed"
        ):
            result.append(item)
    return result


def current_review_attestation(graph: dict[str, Any], run: dict[str, Any] | None = None) -> dict[str, Any] | None:
    items = active_review_attestations(graph, run)
    return items[0] if len(items) == 1 else None


def review_provenance_snapshot(graph: dict[str, Any], run: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return audit/manifest review-provenance fields for the current subject.

    ``reviewed_subject_hash`` is the canonical semantic projection hash, not
    the input file-byte hash.  The projection excludes ReviewAttestation,
    Audit, and DeliveryManifest so that a stored attestation can be checked
    without a self-reference loop.
    """
    run = run or current_run(graph)
    subject_hash = review_subject_hash(graph)
    if not isinstance(run, dict):
        return {
            "review_attestation_id": None,
            "reviewed_subject_hash": subject_hash,
            "review_provenance_level": "not_applicable",
        }
    formal_subjects = formal_positive_assessments_for_run(graph, run)
    if not formal_subjects:
        return {
            "review_attestation_id": None,
            "reviewed_subject_hash": subject_hash,
            "review_provenance_level": "not_applicable",
        }
    if run.get("review_mode") == "independent":
        att = current_review_attestation(graph, run)
        return {
            "review_attestation_id": att.get("attestation_id") if isinstance(att, dict) else None,
            "reviewed_subject_hash": att.get("reviewed_subject_hash") if isinstance(att, dict) else subject_hash,
            "review_provenance_level": att.get("provenance_level") if isinstance(att, dict) else None,
        }
    if run.get("review_mode") == "self_review_fallback":
        return {
            "review_attestation_id": None,
            "reviewed_subject_hash": subject_hash,
            "review_provenance_level": "self_review_fallback",
        }
    if run.get("review_mode") == "not_run":
        return {
            "review_attestation_id": None,
            "reviewed_subject_hash": subject_hash,
            "review_provenance_level": "not_run",
        }
    return {
        "review_attestation_id": None,
        "reviewed_subject_hash": subject_hash,
        "review_provenance_level": "not_applicable",
    }


def review_provenance_disclosure(level: Any) -> str:
    """Return the required user-facing disclosure for local review provenance."""
    if level == "declared_separate_session":
        return "本次复核由独立会话声明完成，未获得平台身份验证。"
    if level == "self_review_fallback":
        return "本次为 self_review_fallback 复核，未运行独立复核；交付时需保留该说明。"
    if level == "not_run":
        return "本次未运行复核，仅可作为发现候选池或待核查输出。"
    return ""


def validate_current_review_attestation(graph: dict[str, Any]) -> list[dict[str, str]]:
    """Fail closed unless independent review has a current declared attestation."""
    issues: list[dict[str, str]] = []
    run = current_run(graph)
    if not isinstance(run, dict):
        return [issue("critical", "review_attestation_run_missing", "Review provenance requires a current Run", "runs")]
    mode = run.get("review_mode")
    if mode != "independent":
        return issues
    if not formal_positive_assessments_for_run(graph, run):
        return issues
    attestations = active_review_attestations(graph, run)
    if len(attestations) != 1:
        issues.append(issue(
            "critical",
            "independent_review_attestation_missing",
            "review_mode=independent requires exactly one current passed ReviewAttestation",
            "review_attestations",
        ))
        for idx, other in enumerate(ensure_list(graph, "review_attestations")):
            if not isinstance(other, dict) or other.get("conclusion") != "passed" or other.get("run_id") != run.get("run_id"):
                continue
            for field, code in (
                ("brief_id", "review_attestation_brief_mismatch"),
                ("plan_id", "review_attestation_plan_mismatch"),
                ("review_cycle_id", "review_attestation_cycle_mismatch"),
            ):
                if other.get(field) != run.get(field):
                    issues.append(issue("critical", code, f"ReviewAttestation {field} must match current Run", f"review_attestations[{idx}].{field}"))
        return issues
    att = attestations[0]
    for field in ("executor_actor_id", "execution_session_id"):
        if not has_text(run.get(field)):
            issues.append(issue(
                "critical",
                "run_execution_identity_missing",
                f"Independent review requires Run.{field}",
                f"runs.{field}",
            ))
    for field in (
        "attestation_id", "run_id", "brief_id", "plan_id", "review_cycle_id",
        "executor_actor_id", "execution_session_id", "reviewer_actor_id",
        "reviewer_session_id", "reviewed_at", "conclusion", "input_graph_hash",
        "reviewed_subject_hash", "provenance_level",
    ):
        if not has_text(att.get(field)):
            issues.append(issue("critical", "review_attestation_field_missing", f"ReviewAttestation lacks {field}", f"review_attestations.{field}"))
    try:
        datetime.fromisoformat(str(att.get("reviewed_at")).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        issues.append(issue("critical", "review_attestation_reviewed_at_invalid", "ReviewAttestation reviewed_at must be an ISO-8601 timestamp", "review_attestations.reviewed_at"))
    if att.get("conclusion") not in REVIEW_ATTESTATION_CONCLUSIONS:
        issues.append(issue("critical", "review_attestation_conclusion_invalid", "ReviewAttestation conclusion is invalid", "review_attestations.conclusion"))
    if att.get("provenance_level") not in REVIEW_PROVENANCE_LEVELS:
        issues.append(issue("critical", "review_attestation_provenance_level_invalid", "ReviewAttestation provenance_level is invalid", "review_attestations.provenance_level"))
    for field in ("reviewed_entity_ids", "reviewed_assessment_ids"):
        if not isinstance(att.get(field), list):
            issues.append(issue("critical", "review_attestation_field_missing", f"ReviewAttestation lacks list {field}", f"review_attestations.{field}"))
    for left, right, code, message in (
        (att.get("run_id"), run.get("run_id"), "review_attestation_run_mismatch", "ReviewAttestation run_id must match current Run"),
        (att.get("brief_id"), run.get("brief_id"), "review_attestation_brief_mismatch", "ReviewAttestation brief_id must match current Run"),
        (att.get("plan_id"), run.get("plan_id"), "review_attestation_plan_mismatch", "ReviewAttestation plan_id must match current Run"),
        (att.get("review_cycle_id"), run.get("review_cycle_id"), "review_attestation_cycle_mismatch", "ReviewAttestation review_cycle_id must match current Run"),
        (att.get("executor_actor_id"), run.get("executor_actor_id"), "review_attestation_executor_mismatch", "ReviewAttestation executor_actor_id must match current Run"),
        (att.get("execution_session_id"), run.get("execution_session_id"), "review_attestation_execution_session_mismatch", "ReviewAttestation execution_session_id must match current Run"),
    ):
        if left != right:
            issues.append(issue("critical", code, message, "review_attestations"))
    for idx, other in enumerate(ensure_list(graph, "review_attestations")):
        if not isinstance(other, dict):
            continue
        if (
            other is not att
            and other.get("run_id") == run.get("run_id")
            and other.get("brief_id") == run.get("brief_id")
            and other.get("plan_id") == run.get("plan_id")
            and other.get("review_cycle_id") == run.get("review_cycle_id")
            and other.get("conclusion") == "failed"
        ):
            issues.append(issue(
                "critical",
                "review_cycle_reused_after_failed_attestation",
                "A new independent review must use a new review_cycle_id after a failed attestation",
                f"review_attestations[{idx}].review_cycle_id",
            ))
    for field in ("executor_actor_id", "execution_session_id", "reviewer_actor_id", "reviewer_session_id"):
        if has_text(att.get(field)) and not is_safe_anonymous_id(att.get(field)):
            issues.append(issue(
                "critical",
                "review_attestation_identity_not_opaque",
                "ReviewAttestation identity fields must be short opaque actor/session IDs, not names, emails, paths, or secrets",
                f"review_attestations.{field}",
            ))
    for field in ("executor_actor_id", "execution_session_id"):
        if has_text(run.get(field)) and not is_safe_anonymous_id(run.get(field)):
            issues.append(issue(
                "critical",
                "run_execution_identity_not_opaque",
                "Run execution identity fields must be short opaque host/session IDs",
                f"runs.{field}",
            ))
    if att.get("reviewer_actor_id") == run.get("executor_actor_id"):
        issues.append(issue("critical", "review_attestation_reviewer_actor_not_independent", "Reviewer actor must differ from executor actor", "review_attestations.reviewer_actor_id"))
    if att.get("reviewer_session_id") == run.get("execution_session_id"):
        issues.append(issue("critical", "review_attestation_reviewer_session_not_independent", "Reviewer session must differ from execution session", "review_attestations.reviewer_session_id"))
    subject_hash = review_subject_hash(graph)
    if att.get("reviewed_subject_hash") != subject_hash:
        issues.append(issue(
            "critical",
            "review_attestation_subject_hash_mismatch",
            "ReviewAttestation reviewed_subject_hash must match the current canonical review subject",
            "review_attestations.reviewed_subject_hash",
        ))
    if has_text(att.get("input_graph_hash")) and att.get("input_graph_hash") != att.get("reviewed_subject_hash"):
        issues.append(issue(
            "critical",
            "review_attestation_input_hash_mismatch",
            "ReviewAttestation input_graph_hash must match the reviewed canonical subject for the delivered graph",
            "review_attestations.input_graph_hash",
        ))
    formal_assessments = formal_positive_assessments_for_run(graph, run)
    required_assessment_ids = {str(item.get("assessment_id")) for item in formal_assessments if has_text(item.get("assessment_id"))}
    required_entity_ids = {str(item.get("entity_id")) for item in formal_assessments if has_text(item.get("entity_id"))}
    reviewed_assessment_ids = {str(item) for item in as_list(att.get("reviewed_assessment_ids")) if has_text(item)}
    reviewed_entity_ids = {str(item) for item in as_list(att.get("reviewed_entity_ids")) if has_text(item)}
    ids = all_id_maps(graph)
    for raw in reviewed_assessment_ids:
        if raw not in ids["assessments"]:
            issues.append(issue("critical", "review_attestation_reviewed_assessment_missing", "ReviewAttestation reviewed_assessment_ids references a missing Assessment", "review_attestations.reviewed_assessment_ids"))
    for raw in reviewed_entity_ids:
        if raw not in ids["entities"]:
            issues.append(issue("critical", "review_attestation_reviewed_entity_missing", "ReviewAttestation reviewed_entity_ids references a missing Entity", "review_attestations.reviewed_entity_ids"))
    if not required_assessment_ids.issubset(reviewed_assessment_ids):
        issues.append(issue(
            "critical",
            "review_attestation_assessment_coverage_missing",
            "ReviewAttestation must cover all current formal positive Assessments",
            "review_attestations.reviewed_assessment_ids",
        ))
    if not required_entity_ids.issubset(reviewed_entity_ids):
        issues.append(issue(
            "critical",
            "review_attestation_entity_coverage_missing",
            "ReviewAttestation must cover all Entities for current formal positive Assessments",
            "review_attestations.reviewed_entity_ids",
        ))
    if not required_assessment_ids and run.get("status") == "checked":
        issues.append(issue(
            "critical",
            "review_attestation_no_formal_subject",
            "Independent review attestation cannot approve an empty formal subject",
            "review_attestations.reviewed_assessment_ids",
        ))
    return issues
