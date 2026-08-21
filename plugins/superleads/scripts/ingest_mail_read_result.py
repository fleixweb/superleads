#!/usr/bin/env python3
"""Normalize a host-read inbound message into a bounded Superleads graph patch.

This adapter never connects to a mailbox. Its input is already read by the
host under a user-approved, read-only mail.read capability boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from _superleads_common import (
    contains_local_path,
    has_text,
    is_safe_opaque_ref,
    load_json,
    parse_mail_snapshot_ref,
    write_json,
)

FORBIDDEN_FIELDS = {
    "password", "token", "access_token", "refresh_token", "authorization",
    "oauth", "path", "file_path", "local_path", "raw_message", "full_body",
}
EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")


def _require_text(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not has_text(value):
        raise ValueError(f"mail_input_missing_{field}")
    return str(value).strip()


def normalize_mail_read_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a graph fragment after rejecting credentials, paths, and full mail data."""
    if not isinstance(payload, dict):
        raise ValueError("mail_input_not_object")
    lowered = {str(key).casefold() for key in payload}
    if lowered & FORBIDDEN_FIELDS:
        raise ValueError("mail_input_forbidden_sensitive_field")
    if payload.get("direction") != "inbound":
        raise ValueError("mail_input_direction_not_inbound")
    if payload.get("access_boundary") != "read_only_connected_account":
        raise ValueError("mail_input_not_read_only")
    message_id = _require_text(payload, "message_id")
    mailbox_ref = _require_text(payload, "mailbox_ref")
    if not is_safe_opaque_ref(mailbox_ref):
        raise ValueError("mail_input_mailbox_ref_invalid")
    received_at = _require_text(payload, "received_at")
    sender_literal = _require_text(payload, "sender_literal")
    subject_literal = _require_text(payload, "subject_literal")
    excerpt = _require_text(payload, "raw_excerpt")
    if len(excerpt) > 1000:
        raise ValueError("mail_input_excerpt_too_long")
    if any(contains_local_path(value) for value in (message_id, mailbox_ref, sender_literal, subject_literal, excerpt)):
        raise ValueError("mail_input_local_path_forbidden")
    message_hash = _require_text(payload, "message_content_sha256")
    snapshot_ref = _require_text(payload, "snapshot_ref")
    parsed = parse_mail_snapshot_ref(snapshot_ref)
    if parsed is None or parsed[0] != message_hash:
        raise ValueError("mail_input_snapshot_invalid")
    source_id = str(payload.get("source_id") or f"mail_{hashlib.sha256(message_id.encode()).hexdigest()[:16]}")
    observation_id = str(payload.get("observation_id") or f"obs_{hashlib.sha256((message_id + excerpt).encode()).hexdigest()[:16]}")
    run_id = str(payload.get("run_id") or "")
    source = {
        "source_id": source_id,
        "publisher_relation": "unknown",
        "provenance": "connected_account",
        "material_role": "connected_inbound_correspondence",
        "medium": "correspondence",
        "access_boundary": "read_only_connected_account",
        "owner_hint": None,
        "message_id": message_id,
        "thread_id": payload.get("thread_id") if has_text(payload.get("thread_id")) else None,
        "received_at": received_at,
        "direction": "inbound",
        "sender_literal": sender_literal,
        "subject_literal": subject_literal,
        "message_content_sha256": message_hash,
        "mailbox_ref": mailbox_ref,
        "mail_intake_rule_id": payload.get("mail_intake_rule_id") if has_text(payload.get("mail_intake_rule_id")) else None,
    }
    observation = {
        "observation_id": observation_id,
        "source_id": source_id,
        "candidate_id": None,
        "entity_id": payload.get("entity_id") if has_text(payload.get("entity_id")) else None,
        "capability": "mail.read",
        "concrete_tool": "host_mail_read_adapter",
        "observed_at": received_at,
        "access_status": "ok",
        "http_status": None,
        "title": "Inbound mail excerpt",
        "raw_excerpt": excerpt,
        "page_or_dom_locator": "bounded mail excerpt",
        "content_hash": str(payload.get("content_hash") or hashlib.sha256(excerpt.encode()).hexdigest()),
        "extraction_method": "host_read_only_excerpt",
        "tool_version": "host",
        "language": str(payload.get("language") or "unknown"),
        "translation_status": "original",
        "derived_from_observation_id": None,
        "snapshot_ref": snapshot_ref,
    }
    result: dict[str, Any] = {"sources": [source], "observations": [observation]}
    sender_emails = EMAIL_RE.findall(sender_literal)
    contact_id: str | None = None
    if len(sender_emails) == 1:
        email = sender_emails[0].casefold()
        contact_id = str(payload.get("contact_id") or f"contact_{hashlib.sha256((message_id + email).encode()).hexdigest()[:16]}")
        result["contact_points"] = [{
            "contact_id": contact_id, "contact_type": "email", "normalized_value": email,
            "source_literal": sender_emails[0], "source_observation_id": observation_id,
            "source_type": "correspondence", "visibility_status": "inbound_message",
            "last_seen_at": received_at, "verification_status": "not_verified",
        }]
        if observation["entity_id"] and has_text(payload.get("entity_name")) and str(payload["entity_name"]) in excerpt:
            association = f"{payload['entity_name']} <{sender_emails[0]}>"
            if association in excerpt:
                result["contact_claims"] = [{
                    "contact_claim_id": str(payload.get("contact_claim_id") or f"cc_{hashlib.sha256((message_id + contact_id).encode()).hexdigest()[:16]}"),
                    "contact_id": contact_id, "entity_id": observation["entity_id"], "person_id": None,
                    "person_name": None, "job_title": None, "department": None,
                    "relationship_type": "mail_sender", "association_observation_id": observation_id,
                    "association_claim_evidence_ids": [], "source_context": "邮件来信联系人/待核验",
                    "association_evidence_text": association, "association_locator": "mail excerpt",
                    "association_confidence": "medium", "is_role_based": False,
                    "is_personal_business": False, "export_status": "export_with_source_note",
                    "user_status": "建议核查后使用", "manual_check_note": "需独立核验联系人归属。",
                }]
        else:
            result["unassigned_contact_leads"] = [{
                "unassigned_contact_lead_id": str(payload.get("unassigned_contact_lead_id") or f"unassigned_{hashlib.sha256((message_id + contact_id).encode()).hexdigest()[:16]}"),
                "contact_id": contact_id, "reason": "来信地址尚无明确企业归属语境", "suggested_manual_check": "核实公司官网、域名或邮件签名中的主体信息。",
            }]
    if run_id:
        request_excerpt = str(payload.get("request_excerpt") or excerpt)
        if request_excerpt not in excerpt or len(request_excerpt) > 1000:
            raise ValueError("mail_input_request_excerpt_invalid")
        result["inquiries"] = [{
            "inquiry_id": str(payload.get("inquiry_id") or f"inq_{hashlib.sha256((message_id + run_id).encode()).hexdigest()[:16]}"),
            "run_id": run_id, "source_id": source_id, "observation_id": observation_id,
            "entity_id": observation["entity_id"], "contact_id": contact_id,
            "received_at": received_at, "direction": "inbound",
            "inquiry_status": str(payload.get("inquiry_status") or "new"),
            "priority": str(payload.get("priority") or "normal"),
            "requested_action": str(payload.get("requested_action") or "核实主体并处理来信需求"),
            "request_excerpt": request_excerpt,
            "mentioned_product_or_need": payload.get("mentioned_product_or_need"),
            "missing_information": payload.get("missing_information") if isinstance(payload.get("missing_information"), list) else [],
            "entity_resolution_status": str(payload.get("entity_resolution_status") or "pending"),
            "external_verification_status": str(payload.get("external_verification_status") or "not_started"),
            "created_at": received_at,
        }]
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        payload = load_json(args.input)
        result = normalize_mail_read_result(payload)
        write_json(args.output, result)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"mail ingest rejected: {exc}")
        return 1
    print(json.dumps({"ok": True, "output": args.output}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
