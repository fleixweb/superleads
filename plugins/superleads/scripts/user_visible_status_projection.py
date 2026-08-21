#!/usr/bin/env python3
"""Project internal Superleads states into small user-visible labels.

This module is intentionally pure: it does not inspect the web, create facts,
or decide whether a product/customer is good.  It only maps already-recorded
internal status records into the Slice AE user-facing status vocabulary.
"""
from __future__ import annotations

from typing import Any

USER_VISIBLE_STATUS_LABELS = (
    "已有明确依据",
    "按已知数据计算",
    "多来源方向一致",
    "可作为线索",
    "需补充资料",
    "需权威/专业复核",
    "资料过旧需复核",
    "来源受限",
    "说法冲突待复核",
    "本轮未执行",
    "暂不适用",
)

BASE_STATUS_TO_USER = {
    "verified": "已有明确依据",
    "derived_calculation": "按已知数据计算",
    "candidate": "可作为线索",
    "preliminary_reference": "可作为线索",
    "business_confirmation_required": "需补充资料",
    "technical_docs_required": "需补充资料",
    "physical_verification_required": "需补充资料",
    "professional_confirmation_required": "需权威/专业复核",
    "source_restricted": "来源受限",
    "not_executed": "本轮未执行",
    "not_applicable": "暂不适用",
    "not_provided": "需补充资料",
    "conflict_pending_review": "说法冲突待复核",
}

CORROBORATION_STATUS_TO_USER = {
    "multi_source_consistent": "多来源方向一致",
    "single_source_only": "可作为线索",
    "not_enough_independent_sources": "可作为线索",
    "conflict_present": "说法冲突待复核",
    "source_restricted": "来源受限",
    "not_executed": "本轮未执行",
}

FRESHNESS_STATUS_TO_USER = {
    "current_enough_for_scope": "已有明确依据",
    "date_unknown_recently_observed": "需权威/专业复核",
    "stale_needs_recheck": "资料过旧需复核",
    "date_unknown_needs_recheck": "资料过旧需复核",
    "not_time_sensitive": "已有明确依据",
    "not_executed": "本轮未执行",
}

AUTHORITY_STATUS_TO_USER = {
    "verified_for_fact_domain": "已有明确依据",
    "candidate_needs_check": "需权威/专业复核",
    "secondary_reference_only": "可作为线索",
    "unable_to_verify": "需权威/专业复核",
    "conflicting_identity": "说法冲突待复核",
    "not_executed": "需权威/专业复核",
}

ORIGIN_REQUIREMENT_TO_USER = {
    "required": "目标国规则显示通常需要",
    "conditionally_required": "满足条件时需要",
    "normally_not_required": "当前场景通常不要求",
    "not_applicable": "本场景暂不适用",
    "unable_to_verify": "本轮未能核实目标国规则",
}

ORIGIN_USER_MATERIAL_TO_USER = {
    "user_provided_valid_for_scope": "用户已提供，范围初步匹配",
    "user_provided_needs_review": "用户已提供，需核对范围",
    "user_not_provided_but_required": "当前未见用户材料，规则可能要求",
    "user_not_provided_and_not_required_for_current_scenario": "当前未见用户材料，且本场景暂未触发要求",
    "user_material_status_unknown": "用户材料状态未知",
}

DESTINATION_REQUIREMENT_TO_USER = {
    "required": "目标市场规则显示通常要求",
    "conditionally_required": "满足条件时要求",
    "normally_not_required": "当前场景通常不要求",
    "not_applicable": "本场景暂不适用",
    "unable_to_verify": "本轮未能核实目标市场规则",
    "not_executed": "本轮未核验此项",
}

CERTIFICATION_USER_MATERIAL_TO_USER = {
    "user_material_not_requested_yet": "尚未向用户索取",
    "user_material_status_unknown": "用户材料状态未知",
    "user_not_provided_but_required": "当前未见用户材料，规则可能要求",
    "user_not_provided_and_not_required_for_current_scenario": "当前未见用户材料，且本场景暂未触发要求",
    "user_provided_needs_review": "用户已提供，需核对范围",
    "user_provided_valid_for_scope": "用户已提供，范围初步匹配",
    "user_provided_not_valid_for_scope": "用户已提供，但与本场景不匹配",
}

REQUIREMENT_FAMILY_TO_USER = {
    "certification": "认证",
    "test_report": "测试报告",
    "registration": "注册",
    "labeling": "标签",
    "packaging": "包装",
    "import_permit": "进口许可",
    "transport_document": "运输文件",
    "channel_requirement": "渠道要求",
    "other": "其它要求",
}

# Exact enum replacement only.  Do not use this on arbitrary prose unless the
# caller has already decided the cell is an enum/status cell.
EXACT_ENUM_TO_USER = {
    **BASE_STATUS_TO_USER,
    **CORROBORATION_STATUS_TO_USER,
    **FRESHNESS_STATUS_TO_USER,
    **AUTHORITY_STATUS_TO_USER,
    **ORIGIN_REQUIREMENT_TO_USER,
    **ORIGIN_USER_MATERIAL_TO_USER,
    **DESTINATION_REQUIREMENT_TO_USER,
    **CERTIFICATION_USER_MATERIAL_TO_USER,
    **REQUIREMENT_FAMILY_TO_USER,
}

SUPPLEMENT_REQUIRED_STATUSES = {
    "business_confirmation_required",
    "technical_docs_required",
    "physical_verification_required",
    "not_provided",
}

FRESHNESS_STALE_STATUSES = {"stale_needs_recheck", "date_unknown_needs_recheck"}
FRESHNESS_NEEDS_REVIEW_STATUSES = {"date_unknown_recently_observed"}
CORROBORATION_CONFLICT_STATUSES = {"conflict_present"}
CORROBORATION_RESTRICTED_STATUSES = {"source_restricted"}
AUTHORITY_CONFLICT_STATUSES = {"conflicting_identity"}
AUTHORITY_NEEDS_REVIEW_STATUSES = {"candidate_needs_check", "unable_to_verify", "not_executed"}
AUTHORITY_SECONDARY_STATUSES = {"secondary_reference_only"}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def humanize_enum_value(value: Any) -> str:
    """Return a safe user-facing label for a single known enum value."""
    if isinstance(value, list):
        parts = [humanize_enum_value(item) for item in value if _text(item)]
        return "；".join(parts) if parts else "未提供"
    raw = _text(value)
    if not raw:
        return "未提供"
    return EXACT_ENUM_TO_USER.get(raw, raw)


def project_base_status(value: Any) -> str:
    return BASE_STATUS_TO_USER.get(_text(value), _text(value) or "需补充资料")


def project_freshness_status(value: Any) -> str:
    return FRESHNESS_STATUS_TO_USER.get(_text(value), _text(value) or "需权威/专业复核")


def project_authority_status(value: Any) -> str:
    return AUTHORITY_STATUS_TO_USER.get(_text(value), _text(value) or "需权威/专业复核")


def project_corroboration_status(value: Any) -> str:
    return CORROBORATION_STATUS_TO_USER.get(_text(value), _text(value) or "可作为线索")


def _records_for_ids(ids: list[Any], records: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw_id in ids:
        record = records.get(str(raw_id))
        if isinstance(record, dict):
            result.append(record)
    return result


def project_market_row_status(
    row: dict[str, Any],
    *,
    freshness_records: dict[str, dict[str, Any]] | None = None,
    corroboration_records: dict[str, dict[str, Any]] | None = None,
    authority_records: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Project a matrix row and its linked status records to one user label.

    Priority follows Slice AE: do not let a base ``verified`` hide conflicts,
    source restrictions, stale records, authority gaps, or missing materials.
    """
    freshness = _records_for_ids(_list(row.get("freshness_record_ids")), freshness_records or {})
    corroboration = _records_for_ids(_list(row.get("corroboration_record_ids")), corroboration_records or {})
    authority = _records_for_ids(_list(row.get("authority_verification_record_ids")), authority_records or {})
    base = _text(row.get("status"))

    if base == "not_executed":
        return "本轮未执行"
    if base == "not_applicable":
        return "暂不适用"
    if base == "conflict_pending_review":
        return "说法冲突待复核"
    if any(_text(item.get("corroboration_status")) in CORROBORATION_CONFLICT_STATUSES for item in corroboration):
        return "说法冲突待复核"
    if any(_text(item.get("verification_status")) in AUTHORITY_CONFLICT_STATUSES for item in authority):
        return "说法冲突待复核"
    if base == "source_restricted":
        return "来源受限"
    if any(_text(item.get("corroboration_status")) in CORROBORATION_RESTRICTED_STATUSES for item in corroboration):
        return "来源受限"
    if any(_text(item.get("freshness_status")) in FRESHNESS_STALE_STATUSES for item in freshness):
        return "资料过旧需复核"
    if any(_text(item.get("freshness_status")) in FRESHNESS_NEEDS_REVIEW_STATUSES for item in freshness):
        return "需权威/专业复核"
    if any(_text(item.get("verification_status")) in AUTHORITY_NEEDS_REVIEW_STATUSES for item in authority):
        return "需权威/专业复核"
    if any(_text(item.get("verification_status")) in AUTHORITY_SECONDARY_STATUSES for item in authority):
        if base in {"candidate", "preliminary_reference"}:
            return "可作为线索"
        return "需权威/专业复核"
    if base in SUPPLEMENT_REQUIRED_STATUSES:
        return "需补充资料"
    if base == "derived_calculation":
        return "按已知数据计算"
    if base == "verified":
        return "已有明确依据"
    if any(_text(item.get("corroboration_status")) == "multi_source_consistent" for item in corroboration):
        return "多来源方向一致"
    return project_base_status(base)


def market_row_status_basis(
    row: dict[str, Any],
    *,
    freshness_records: dict[str, dict[str, Any]] | None = None,
    corroboration_records: dict[str, dict[str, Any]] | None = None,
    authority_records: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Short human basis note for the projected status."""
    freshness = _records_for_ids(_list(row.get("freshness_record_ids")), freshness_records or {})
    corroboration = _records_for_ids(_list(row.get("corroboration_record_ids")), corroboration_records or {})
    authority = _records_for_ids(_list(row.get("authority_verification_record_ids")), authority_records or {})
    parts: list[str] = []
    for record in freshness[:1]:
        summary = record.get("user_visible_summary") or record.get("date_basis") or project_freshness_status(record.get("freshness_status"))
        parts.append(f"资料时效：{summary}")
    for record in authority[:1]:
        basis = record.get("verification_basis") or project_authority_status(record.get("verification_status"))
        parts.append(f"权威性：{basis}")
    for record in corroboration[:1]:
        summary = record.get("user_visible_summary") or project_corroboration_status(record.get("corroboration_status"))
        parts.append(f"互证：{summary}")
    base = _text(row.get("status"))
    if not parts:
        if base == "verified":
            parts.append("已打开/记录的来源支持当前字段本身")
        elif base == "derived_calculation":
            parts.append("按已知数字和明示公式计算")
        elif base in {"candidate", "preliminary_reference"}:
            parts.append("当前只能作为下一步核验方向")
        elif base in SUPPLEMENT_REQUIRED_STATUSES:
            parts.append("缺产品、技术、实物、订单或供应链材料")
        elif base == "professional_confirmation_required":
            parts.append("需要主管机关、报关行、认证机构、承运人或其它专业方复核")
        elif base == "source_restricted":
            parts.append("来源受限，不能把摘要或入口升级为事实")
        elif base == "not_executed":
            parts.append("本轮没有采集或运行该模块")
        elif base == "not_applicable":
            parts.append("按当前产品档案或贸易路径暂未触发")
        elif base == "conflict_pending_review":
            parts.append("来源或口径存在冲突，需人工复核")
        else:
            parts.append("依据状态待补充说明")
    return "；".join(str(part) for part in parts if _text(part))
