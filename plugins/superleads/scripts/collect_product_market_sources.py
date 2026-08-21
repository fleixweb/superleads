#!/usr/bin/env python3
"""Build Product Market Source/Observation records from manual public URLs.

This Slice K bridge is intentionally narrow:

* it does not search the web;
* it does not fetch, crawl, download, or open URLs by itself;
* it does not create EvidenceCards or MatrixRows;
* it only turns user-supplied public URL/source status input into auditable
  Source and Observation records that a later evidence-card step may review.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from _superleads_common import contains_local_path, has_text, is_safe_public_http_url, issue

ROUTE = "product_outbound_market_analysis_source_collection"
SOURCE_PLAN_ROUTE = "product_outbound_market_analysis_source_plan"
ALLOWED_OUTPUT = "source_and_observation_records_only"

OPENED_ACCESS_STATUSES = {"opened", "captured", "extracted", "rendered"}
RESTRICTED_ACCESS_STATUSES = {
    "blocked",
    "login_wall",
    "login_required",
    "forbidden",
    "inaccessible",
    "not_accessed",
    "restricted",
}
ALLOWED_ACCESS_STATUSES = OPENED_ACCESS_STATUSES | RESTRICTED_ACCESS_STATUSES

SOURCE_MEDIA = {
    "website",
    "social",
    "registry",
    "directory",
    "map",
    "document",
    "spreadsheet",
    "image",
    "correspondence",
}
PUBLISHER_RELATIONS = {"first_party", "third_party", "unknown"}
SOURCE_OPEN_CAPABILITIES = {"source.open", "browser.render", "document.extract", "source.capture", "registry.lookup"}

SECRET_TEXT_RE = re.compile(
    r"(?i)(?:\b(?:cookie|authorization|bearer|api[_ -]?key|access[_ -]?token|password|secret)\b)"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _safe_id_component(value: Any, fallback: str) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"[^a-z0-9._-]+", "-", text).strip("-._")
    return text[:72] or fallback


def _source_url(item: dict[str, Any]) -> Any:
    for field in ("url", "final_url", "canonical_url"):
        if has_text(item.get(field)):
            return item.get(field)
    return None


def _infer_medium(url: str, explicit: Any) -> str:
    if has_text(explicit):
        return str(explicit).strip()
    path = urlsplit(url).path.casefold()
    if path.endswith(".pdf"):
        return "document"
    if path.endswith((".csv", ".xls", ".xlsx")):
        return "spreadsheet"
    if path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "image"
    return "website"


def _access_status(item: dict[str, Any]) -> str:
    raw = item.get("access_status")
    opened = item.get("opened")
    if has_text(raw):
        return str(raw).strip()
    return "opened" if opened is True else "not_accessed"


def _opened_flag(item: dict[str, Any], status: str) -> bool:
    if isinstance(item.get("opened"), bool):
        return bool(item.get("opened"))
    return status in OPENED_ACCESS_STATUSES


def _validate_root(payload: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for field in ("run_id", "brief_id", "brief_version_id", "query_plan_id", "query_group_id"):
        if not has_text(payload.get(field)):
            issues.append(issue("critical", "market_source_collection_required_missing", f"manual source collection input requires {field}", field))
        elif contains_local_path(payload.get(field)) or SECRET_TEXT_RE.search(str(payload.get(field))):
            issues.append(issue("critical", "market_source_collection_locator_unsafe", f"manual source collection identifier must not contain local paths or credential-shaped text: {field}", field))
    if has_text(payload.get("collection_run_id")) and (contains_local_path(payload.get("collection_run_id")) or SECRET_TEXT_RE.search(str(payload.get("collection_run_id")))):
        issues.append(issue("critical", "market_source_collection_locator_unsafe", "collection_run_id must not contain local paths or credential-shaped text", "collection_run_id"))
    if payload.get("source_plan_route") != SOURCE_PLAN_ROUTE:
        issues.append(issue("critical", "market_source_collection_source_plan_route_invalid", "manual source collection must stay tied to the Product Market Source Plan route", "source_plan_route"))
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        issues.append(issue("critical", "market_source_collection_sources_missing", "manual source collection requires a non-empty sources list", "sources"))
    return issues


def _validate_source(item: Any, index: int) -> list[dict[str, str]]:
    path = f"sources[{index}]"
    issues: list[dict[str, str]] = []
    if not isinstance(item, dict):
        return [issue("critical", "market_source_collection_source_invalid", "source entry must be an object", path)]

    url = _source_url(item)
    declared_urls = [item.get(field) for field in ("url", "canonical_url", "final_url") if has_text(item.get(field))]
    if not declared_urls:
        issues.append(issue("critical", "market_source_collection_url_not_public", "source URL must be a safe public HTTP(S) URL without local paths, credentials, or token-like query parameters", f"{path}.url"))
    for field in ("url", "canonical_url", "final_url"):
        if has_text(item.get(field)) and (contains_local_path(item.get(field)) or not is_safe_public_http_url(item.get(field))):
            issues.append(issue("critical", "market_source_collection_url_not_public", "source URL must be a safe public HTTP(S) URL without local paths, credentials, or token-like query parameters", f"{path}.{field}"))

    medium = _infer_medium(str(url or ""), item.get("medium"))
    if medium not in SOURCE_MEDIA:
        issues.append(issue("critical", "market_source_collection_medium_invalid", "source medium must be a normal source type, not a search result or arbitrary value", f"{path}.medium"))
    if medium == "search_result":
        issues.append(issue("critical", "market_source_collection_search_result_medium", "search results belong in SearchLog, not manual Source records", f"{path}.medium"))

    publisher_relation = str(item.get("publisher_relation") or "unknown").strip()
    if publisher_relation not in PUBLISHER_RELATIONS:
        issues.append(issue("critical", "market_source_collection_publisher_relation_invalid", "publisher_relation must be first_party, third_party, or unknown", f"{path}.publisher_relation"))

    status = _access_status(item)
    opened = _opened_flag(item, status)
    if status not in ALLOWED_ACCESS_STATUSES:
        issues.append(issue("critical", "market_source_collection_access_status_invalid", "access_status must be opened/captured/extracted/rendered or a restricted/not_accessed status", f"{path}.access_status"))
    if opened and status not in OPENED_ACCESS_STATUSES:
        issues.append(issue("critical", "market_source_collection_open_status_mismatch", "opened=true requires an opened/captured/extracted/rendered access_status", f"{path}.opened"))
    if not opened and status in OPENED_ACCESS_STATUSES:
        issues.append(issue("critical", "market_source_collection_open_status_mismatch", "opened=false cannot use opened/captured/extracted/rendered access_status", f"{path}.access_status"))
    if not opened and has_text(item.get("raw_excerpt")):
        issues.append(issue("critical", "market_source_collection_unopened_excerpt", "not-opened or restricted sources must not carry factual raw_excerpt", f"{path}.raw_excerpt"))
    if has_text(item.get("raw_excerpt")) and (contains_local_path(item.get("raw_excerpt")) or SECRET_TEXT_RE.search(str(item.get("raw_excerpt")))):
        issues.append(issue("critical", "market_source_collection_excerpt_unsafe", "manual raw_excerpt must not contain local paths or credential-shaped text", f"{path}.raw_excerpt"))

    capability = str(item.get("capability") or "source.open").strip()
    if capability not in SOURCE_OPEN_CAPABILITIES:
        issues.append(issue("critical", "market_source_collection_capability_invalid", "manual collection can only emit source-opening/access capabilities, never search.web or extraction claims without a separate extractor", f"{path}.capability"))
    if capability == "document.extract" and (not opened or not has_text(item.get("raw_excerpt")) or not has_text(item.get("content_hash"))):
        issues.append(issue("critical", "market_source_collection_document_extract_incomplete", "document.extract requires an opened/extracted source, raw_excerpt, and content_hash", f"{path}.capability"))

    locator_text = " ".join(
        str(item.get(field) or "")
        for field in ("title", "page_or_dom_locator", "source_entry_id", "source_id", "observation_id")
    )
    if contains_local_path(locator_text) or SECRET_TEXT_RE.search(locator_text):
        issues.append(issue("critical", "market_source_collection_locator_unsafe", "manual source metadata must not contain local paths or credential-shaped text", path))
    return issues


def _source_record(payload: dict[str, Any], item: dict[str, Any], index: int) -> dict[str, Any]:
    url = str(_source_url(item)).strip()
    source_entry_id = item.get("source_entry_id") or item.get("source_id") or f"manual_source_{index + 1:03d}"
    source_id = str(item.get("source_id") or f"source-{_safe_id_component(source_entry_id, f'manual-{index + 1:03d}')}-{index + 1:03d}")
    medium = _infer_medium(url, item.get("medium"))
    return {
        "source_id": source_id,
        "canonical_url": url,
        "final_url": str(item.get("final_url") or url).strip(),
        "publisher_relation": str(item.get("publisher_relation") or "unknown").strip(),
        "provenance": "manual_input",
        "medium": medium,
        "access_boundary": str(item.get("access_boundary") or "manual_public_url_no_auto_fetch"),
        "owner_hint": str(item.get("owner_hint") or item.get("source_entry_id") or payload.get("query_group_id") or "manual_public_source"),
        "material_role": "published_source_copy",
    }


def _observation_record(payload: dict[str, Any], item: dict[str, Any], source: dict[str, Any], index: int) -> dict[str, Any]:
    source_entry_id = item.get("source_entry_id") or source.get("source_id") or f"manual_source_{index + 1:03d}"
    status = _access_status(item)
    opened = _opened_flag(item, status)
    raw_excerpt = str(item.get("raw_excerpt")).strip() if has_text(item.get("raw_excerpt")) else None
    capability = str(item.get("capability") or "source.open").strip()
    extraction_method = item.get("extraction_method")
    if not has_text(extraction_method):
        extraction_method = "manual_user_supplied_excerpt" if raw_excerpt else "manual_url_access_status_only"
    observation = {
        "observation_id": str(item.get("observation_id") or f"observation-{_safe_id_component(source_entry_id, f'manual-{index + 1:03d}')}-{index + 1:03d}"),
        "run_id": str(payload.get("run_id")),
        "source_id": source["source_id"],
        "capability": capability,
        "concrete_tool": str(item.get("concrete_tool") or "manual_user_supplied_source_record"),
        "observed_at": str(item.get("observed_at") or payload.get("collected_at") or _now_iso()),
        "access_status": status,
        "http_status": item.get("http_status"),
        "title": item.get("title"),
        "raw_excerpt": raw_excerpt if opened else None,
        "page_or_dom_locator": item.get("page_or_dom_locator") if has_text(item.get("page_or_dom_locator")) else "manual-visible-excerpt" if raw_excerpt else "manual-url-only",
        "extraction_method": extraction_method,
        "language": item.get("language") if has_text(item.get("language")) else "unknown",
        "translation_status": item.get("translation_status") if has_text(item.get("translation_status")) else "not_translated",
    }
    if has_text(item.get("content_hash")):
        observation["content_hash"] = str(item.get("content_hash")).strip()
    return observation


def build_collection(payload: dict[str, Any]) -> dict[str, Any]:
    issues = _validate_root(payload)
    for idx, item in enumerate(_as_list(payload.get("sources"))):
        issues.extend(_validate_source(item, idx))

    base = {
        "ok": not issues,
        "route": ROUTE,
        "source_plan_route": payload.get("source_plan_route"),
        "execution_level": "manual_source_collection_records_only",
        "not_evidence": True,
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "uses_user_supplied_urls": True,
        "uses_user_declared_open_status": True,
        "does_not_create_evidence_cards": True,
        "does_not_create_matrix_rows": True,
        "allowed_output": ALLOWED_OUTPUT,
        "issues": issues,
        "guardrails": [
            "不自动搜索，只接收用户给定 URL / 已知来源。",
            "不自动打开、抓取或下载来源；opened/access_status 只记录用户或上游工具已经完成的打开状态。",
            "Source / Observation 只是 EvidenceCard 的输入，不是事实卡。",
            "不创建 EvidenceCard，不创建 MatrixRow，不输出税率、认证、物流、趋势、价格或市场进入判断。",
            "未打开、未访问或来源受限时，不能携带事实 raw_excerpt。",
            "Source Pack / Query Plan / SearchLog 不能当事实来源。",
        ],
        "sources": [],
        "observations": [],
        "collection_manifest": {
            "collection_run_id": payload.get("collection_run_id") or "collection-run-manual-source-collection",
            "run_id": payload.get("run_id"),
            "brief_id": payload.get("brief_id"),
            "brief_version_id": payload.get("brief_version_id"),
            "query_plan_id": payload.get("query_plan_id"),
            "query_group_id": payload.get("query_group_id"),
            "source_plan_route": payload.get("source_plan_route"),
            "created_at": payload.get("collected_at") or _now_iso(),
            "source_count": 0,
            "observation_count": 0,
            "opened_observation_count": 0,
            "restricted_or_not_accessed_count": 0,
            "records_are_not_evidence": True,
        },
    }
    if issues:
        return base

    sources: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    manifest_entries: list[dict[str, Any]] = []
    for idx, item in enumerate(payload.get("sources", [])):
        source = _source_record(payload, item, idx)
        observation = _observation_record(payload, item, source, idx)
        sources.append(source)
        observations.append(observation)
        status = str(observation.get("access_status") or "")
        manifest_entries.append({
            "source_id": source["source_id"],
            "observation_id": observation["observation_id"],
            "source_entry_id": item.get("source_entry_id"),
            "medium": source["medium"],
            "access_status": status,
            "has_factual_excerpt": bool(has_text(observation.get("raw_excerpt")) and status in OPENED_ACCESS_STATUSES),
            "not_evidence": True,
        })

    opened_count = sum(1 for obs in observations if str(obs.get("access_status") or "") in OPENED_ACCESS_STATUSES)
    restricted_count = sum(1 for obs in observations if str(obs.get("access_status") or "") not in OPENED_ACCESS_STATUSES)
    base["sources"] = sources
    base["observations"] = observations
    base["collection_manifest"] = {
        **base["collection_manifest"],
        "source_count": len(sources),
        "observation_count": len(observations),
        "opened_observation_count": opened_count,
        "restricted_or_not_accessed_count": restricted_count,
        "manual_entries": manifest_entries,
    }
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Manual source collection JSON input")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    try:
        payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input root must be an object")
    except Exception as exc:
        result = {
            "ok": False,
            "route": ROUTE,
            "not_evidence": True,
            "does_not_search_web": True,
            "does_not_open_sources": True,
            "does_not_create_evidence_cards": True,
            "does_not_create_matrix_rows": True,
            "allowed_output": ALLOWED_OUTPUT,
            "issues": [issue("critical", "market_source_collection_input_load_failed", f"could not load collection input: {exc}", "input")],
            "sources": [],
            "observations": [],
            "collection_manifest": {"records_are_not_evidence": True},
            "guardrails": ["不自动搜索", "不自动打开来源", "不创建 EvidenceCard 或 MatrixRow"],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result = build_collection(payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
