#!/usr/bin/env python3
"""Pure planning and delivery helpers for composite Superleads requests."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from superleads_user_guidance import append_final_footer


_BACKGROUND = re.compile(r"调查|背调|核查|查一下|背景|尽调|background check|due diligence", re.IGNORECASE)
_MARKET = re.compile(r"出口|出海|市场.*(?:准入|认证|关税|税费|物流|价格)|(?:准入|认证|关税|税费|物流|价格).*市场", re.IGNORECASE)
_BATCH = re.compile(r"找客户|找进口商|找经销商|开发客户|客户名单|find importers|lead list|prospects", re.IGNORECASE)
_CUSTOMER_TYPE = re.compile(r"客户|进口商|经销商|批发商|零售商|distributors?|importers?|buyers?|prospects?", re.IGNORECASE)
_DISCOVERY_ACTION = re.compile(r"找|寻找|开发|发现|find|source|develop", re.IGNORECASE)
_TABLE = re.compile(
    r"客户表|客户名单表|excel|csv|表格补全|补全表格|补全已有|client list|client table|customer list|customer table|attached list|attached table",
    re.IGNORECASE,
)
_CONTACT = re.compile(r"联系人|联系方式|公开邮箱|邮箱|电话|contact|email|phone", re.IGNORECASE)
_SEPARATE_CONTACT = re.compile(
    r"(?:核查|验证|check|verify).{0,12}(?:公开)?(?:联系人|联系方式|邮箱|电话|contact(?:s| person)?|email|phone)|"
    r"(?:补充|补全|supplement|enrich).{0,12}(?:公开)?(?:联系人|contact(?:s| person)?)|"
    r"(?:联系人|contact(?:s| person)?).{0,12}(?:核查|验证|check|verify)",
    re.IGNORECASE,
)
_EXPORT = re.compile(r"导出|\bexport\b", re.IGNORECASE)
_PRODUCT = re.compile(r"保温杯|水杯|工业传感器|锂电|电池|阀门|纺织|面料|机械|产品|product|battery|sensor|valve|mug", re.IGNORECASE)
_COUNTRY = re.compile(r"德国|美国|越南|英国|法国|意大利|西班牙|加拿大|澳大利亚|欧盟|germany|united states|usa|vietnam|uk|canada|australia", re.IGNORECASE)
_SUBJECT = re.compile(r"https?://|www\.|[a-z0-9.-]+\.[a-z]{2,}|\b(?:gmbh|ltd|inc|llc|company|corp)\b|公司|品牌|地址", re.IGNORECASE)

_DISPLAY_NAMES = {
    "zh": {
        "customer_background_research": "客户公开背景核查",
        "product_outbound_market_analysis": "产品市场准入信息整理",
        "bulk_customer_development": "批量发现公开客户信息",
        "existing_table_enrichment": "已有客户表补全",
        "contact_supplement": "公开联系人补充",
        "export_delivery": "最终导出",
    },
    "en": {
        "customer_background_research": "Customer public background",
        "product_outbound_market_analysis": "Product market and access information",
        "bulk_customer_development": "Batch public customer discovery",
        "existing_table_enrichment": "Existing customer table enrichment",
        "contact_supplement": "Public contact supplementation",
        "export_delivery": "Final export",
    },
}

_STATUS_LABELS = {
    "zh": {
        "completed": "已完成",
        "source_restricted": "来源受限",
        "waiting_for_required_input": "等待必要信息",
        "waiting_for_upstream_result": "等待上游结果",
        "unable_to_execute": "无法执行",
        "status_pending": "状态待记录",
        "no_recorded_status": "未记录状态",
        "partially_completed": "部分完成",
        "in_progress": "进行中",
    },
    "en": {
        "completed": "Completed",
        "source_restricted": "Source restricted",
        "waiting_for_required_input": "Waiting for required information",
        "waiting_for_upstream_result": "Waiting for upstream results",
        "unable_to_execute": "Unable to execute",
        "status_pending": "Status pending",
        "no_recorded_status": "No recorded status",
        "partially_completed": "Partially complete",
        "in_progress": "In progress",
    },
}

_PARENT_TITLES = {
    "zh": "本次范围与子任务状态",
    "en": "Scope and subtask status",
}

_PROGRESS_FIELDS = (
    ("completed_query_group_count", "查询组", "query groups"),
    ("candidate_count", "候选", "candidates"),
    ("opened_source_count", "已打开来源", "opened sources"),
    ("confirmed_count", "已确认", "confirmed"),
    ("pending_count", "待确认", "pending"),
    ("source_restricted_count", "来源受限", "source restricted"),
    ("not_executed_count", "本轮未执行", "not executed this round"),
)

_COMMERCIAL_JUDGMENT_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"值得开发",
        r"重点开发",
        r"(?:推荐|推荐为)(?:优先)?(?:跟进|联系|开发|客户)",
        r"建议(?:优先)?(?:跟进|联系|开发|进入)",
        r"开发建议",
        r"暂不建议",
        r"值得进入",
        r"(?:会|将会|一定会)(?:采购|购买)",
        r"(?:已确认|确定)(?:采购意愿|会采购|会购买)",
        r"(?:high[ -]priority (?:prospect|lead)|priority lead)",
        r"recommend(?:ed|ing)?\s+(?:follow(?:ing)?[ -]?up|contacting|pursuing|developing)",
        r"recommended\s+(?:follow[ -]?up|contact|pursuit|development)",
        r"should\s+(?:follow up|contact|pursue|develop|enter)",
        r"worth\s+(?:pursuing|developing|entering)",
        r"development recommendation",
        r"(?:will|likely to)\s+(?:purchase|buy)",
        r"(?:confirmed|clear)\s+(?:purchase|buyer)\s+intent",
        r"purchase\s+(?:likelihood|probability|potential)",
        r"(?:high[- ]value|valuable|ideal|excellent)\s+(?:customer|client|prospect)",
        r"(?:high\s+)?customer\s+value(?:\s+is)?\s+(?:high|strong|great)",
        r"likely\s+(?:buyer|customer|purchaser)",
        r"(?:attractive|promising)\s+market",
        r"market\s+attractiveness",
        r"suitable\s+for\s+(?:market\s+)?entry",
        r"市场(?:很)?有吸引力",
        r"(?:采购可能性|采购概率|采购潜力|可能采购|采购需求|采购意愿)",
        r"(?:高价值|优质|理想|优秀)(?:客户|买家|线索)",
        r"(?:客户|买家)(?:价值)(?:很高|高|强)",
        r"(?:适合|值得|应该)(?:进入|开发)(?:这个|该)?市场",
        r"市场(?:很)?(?:适合|值得|应该)进入",
        r"(?:市场潜力高|市场有吸引力)",
    )
)

_INTERNAL_TERM_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\brun\s*id\b",
        r"\bclaim\b",
        r"\bgraph\b",
        r"\baudit\b",
        r"\bvalidator\b",
        r"\brule\s*id\b",
        r"\bsubtask[_ ]?id\b",
        r"\bpath\b",
        r"(?:^|[\s(])(?:scripts?|tests?|docs?)/[A-Za-z0-9_.-]+",
        r"(?:^|[\s(])(?:/[A-Za-z0-9_.-]+)+(?:\.[A-Za-z0-9_.-]+)?",
        r"\b[A-Za-z]:[\\/][^\s]+",
    )
)


def _has(pattern: re.Pattern[str], text: str) -> bool:
    return pattern.search(text or "") is not None


def _language(value: Any) -> str:
    return "en" if str(value or "zh").lower().startswith("en") else "zh"


def _display_name(route: str, language: str) -> str:
    return _DISPLAY_NAMES[_language(language)][route]


def _status_label(status: str, language: str) -> str:
    return _STATUS_LABELS[_language(language)].get(status, _STATUS_LABELS[_language(language)]["status_pending"])


def _parent_title(language: str) -> str:
    return _PARENT_TITLES[_language(language)]


def _subtask(
    route: str,
    *,
    missing_fields: list[str] | None = None,
    dependencies: list[str] | None = None,
    language: str = "zh",
) -> dict[str, Any]:
    missing = list(missing_fields or [])
    dependent = list(dependencies or [])
    status = "waiting_for_required_input" if missing else "waiting_for_upstream_result" if dependent else "ready"
    return {
        "subtask_id": route,
        "route": route,
        "status": status,
        "missing_fields": missing,
        "dependencies": dependent,
        "execution_order": "serial" if dependent else "independent",
        "display_name": _display_name(route, language),
    }


def plan_composite_task(
    text: str,
    supplied_context: dict[str, Any] | None = None,
    *,
    language: str | None = None,
) -> dict[str, Any]:
    """Plan only explicit, independently bounded business objectives.

    The helper does not search, open sources, infer missing product/country
    values, create a Run, or promote any evidence.
    """
    context = supplied_context or {}
    response_language = _language(language if language is not None else context.get("language"))
    subject = _has(_SUBJECT, text)
    text_background = _has(_BACKGROUND, text) and subject
    text_market = _has(_MARKET, text)
    text_batch = (_has(_BATCH, text) or (_has(_DISCOVERY_ACTION, text) and _has(_CUSTOMER_TYPE, text))) and re.search(
        r"(?:不|不要|无需|先不|暂不).{0,12}(?:客户名单|找客户|找进口商|开发客户)|"
        r"\b(?:do not|don't|no)\b.{0,12}(?:lead list|customers|importers)",
        text or "",
        re.IGNORECASE,
    ) is None
    text_table = _has(_TABLE, text) and bool(re.search(r"上传|附件|provided|attached|补全|enrich", text or "", re.IGNORECASE))
    text_contact = _has(_CONTACT, text) and _has(_SEPARATE_CONTACT, text)
    text_export = _has(_EXPORT, text)
    has_background = bool(context.get("has_background", text_background))
    has_market = bool(context.get("has_market", text_market))
    has_batch = bool(context.get("has_batch", text_batch))
    has_table = bool(context.get("has_table", text_table))
    has_contact = bool(context.get("has_contact", text_contact))
    has_export = bool(context.get("has_export", text_export))
    has_product = bool(context.get("has_product", _has(_PRODUCT, text)))
    has_country = bool(context.get("has_country", _has(_COUNTRY, text)))
    subtasks: list[dict[str, Any]] = []

    if has_background:
        subtasks.append(_subtask("customer_background_research", language=response_language))
    if has_market:
        missing = []
        if not has_product:
            missing.append("product_identity")
        if not has_country:
            missing.append("target_country_or_region")
        market_subtask = _subtask(
            "product_outbound_market_analysis",
            missing_fields=missing,
            language=response_language,
        )
        requested_modules = context.get("analysis_modules_requested", context.get("requested_market_modules"))
        if requested_modules is not None:
            market_subtask["analysis_modules_requested"] = requested_modules
        subtasks.append(market_subtask)
    if has_batch:
        subtasks.append(_subtask("bulk_customer_development", language=response_language))
    if has_table:
        subtasks.append(_subtask("existing_table_enrichment", language=response_language))
    if has_contact:
        requested_scope = str(context.get("contact_scope") or "").strip().casefold()
        requires_upstream = context.get("contact_requires_upstream")
        if requires_upstream is None:
            if requested_scope in {"same_request", "same-run", "direct", "independent"}:
                requires_upstream = False
            elif requested_scope in {"upstream", "enrichment", "dependency"}:
                requires_upstream = True
            else:
                # Preserve the legacy planner default; intake supplies an
                # explicit scope whenever the user wording makes it clear.
                requires_upstream = True
        if has_table:
            dependencies = ["existing_table_enrichment"]
        elif requires_upstream and has_background:
            dependencies = ["customer_background_research"]
        elif requires_upstream and has_batch:
            dependencies = ["bulk_customer_development"]
        else:
            dependencies = []
        if dependencies or (not requires_upstream and (has_background or has_batch or has_table)):
            contact_subtask = _subtask("contact_supplement", dependencies=dependencies, language=response_language)
            contact_subtask["contact_scope"] = "upstream" if dependencies else "same_request"
            contact_subtask["contact_requires_upstream"] = bool(dependencies)
            subtasks.append(contact_subtask)
    if has_export and subtasks:
        dependencies = [
            item["route"]
            for item in subtasks
            if item["status"] != "waiting_for_required_input"
        ]
        if dependencies:
            subtasks.append(_subtask("export_delivery", dependencies=dependencies, language=response_language))

    return {
        "route": "composite" if len(subtasks) > 1 else "single_or_unknown",
        "language": response_language,
        "parent_title": _parent_title(response_language),
        "subtasks": subtasks,
        "scheduling": {
            "execution_style": "parallel_if_host_supported",
            "parallelizable": [
                item["subtask_id"]
                for item in subtasks
                if item["execution_order"] == "independent" and item["status"] != "waiting_for_required_input"
            ],
            "serial_boundaries": [
                "same_subject_identity_merge",
                "same_source_conflict_resolution",
                "evidence_promotion",
                "declared_subtask_dependencies",
                "final_validation_export_and_parent_delivery",
            ],
        },
    }


def register_subtask_source_use(subtask_id: str, url: str, fact_domain: str, *, purpose: str) -> dict[str, str]:
    """Record a scoped reference to a source without creating an Observation."""
    normalized_subtask_id = str(subtask_id).strip()
    normalized_purpose = str(purpose).strip()
    if not normalized_subtask_id:
        raise ValueError("source use subtask_id must not be empty")
    if not normalized_purpose:
        raise ValueError("source use purpose must not be empty")
    parsed = urlsplit(str(url).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("source use URL must be absolute HTTP(S)")
    if fact_domain not in {"company_business", "company_contact", "market_access"}:
        raise ValueError("source use fact_domain is not supported")
    return {
        "subtask_id": normalized_subtask_id,
        "source_key": urlunsplit((parsed.scheme.casefold(), parsed.netloc.casefold(), parsed.path.rstrip("/"), parsed.query, "")),
        "fact_domain": fact_domain,
        "purpose": normalized_purpose,
        "observation_boundary": "subtask_scoped_reference_only",
    }


def source_use_can_support(
    source_use: dict[str, Any],
    requested_domain: str,
    requesting_subtask_id: str | None = None,
) -> bool:
    """Keep references within their recorded fact domain family."""
    domain = source_use.get("fact_domain")
    owner = str(source_use.get("subtask_id") or "").strip()
    requester = str(requesting_subtask_id or "").strip()
    return (
        bool(owner and requester)
        and owner == requester
        and domain in {"company_business", "company_contact", "market_access"}
        and requested_domain == domain
    )


def _state_for_subtask(item: dict[str, Any], subtask_states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = subtask_states.get(item.get("subtask_id")) or subtask_states.get(item.get("route")) or {}
    return state if isinstance(state, dict) else {}


def _recorded_count(state: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = state.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, (list, tuple, set)):
            return len(value)
    return None


def parent_progress_summary(parent: dict[str, Any], subtask_states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Project only host-recorded per-subtask progress; unknown counts remain unknown."""
    language = _language(parent.get("language"))
    subtasks = []
    for item in parent.get("subtasks", []):
        if not isinstance(item, dict):
            continue
        state = _state_for_subtask(item, subtask_states)
        query_group_count = _recorded_count(
            state,
            "completed_query_group_count",
            "query_group_count",
            "query_groups",
        )
        subtasks.append({
            "route": item.get("route"),
            "subtask_id": item.get("subtask_id"),
            "display_name": item.get("display_name") or _display_name(item["route"], language),
            "status": str(state["status"]) if state.get("status") else None,
            "query_group_count": query_group_count,
            "completed_query_group_count": query_group_count,
            "candidate_count": _recorded_count(state, "candidate_count", "candidates"),
            "opened_source_count": _recorded_count(state, "opened_source_count", "opened_sources"),
            "confirmed_count": _recorded_count(state, "confirmed_count", "confirmed"),
            "pending_count": _recorded_count(state, "pending_count", "pending"),
            "source_restricted_count": _recorded_count(state, "source_restricted_count", "restricted"),
            "not_executed_count": _recorded_count(state, "not_executed_count", "not_executed"),
        })
    recorded_subtask_count = sum(
        bool(_state_for_subtask(item, subtask_states))
        for item in parent.get("subtasks", [])
        if isinstance(item, dict)
    )
    return {
        "language": language,
        "status": _status_label("no_recorded_status", language) if not recorded_subtask_count else None,
        "recorded_subtask_count": recorded_subtask_count,
        "subtasks": subtasks,
    }


def composite_status_summary(parent: dict[str, Any], subtask_states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Aggregate recorded subtask states without exposing internal IDs or evidence."""
    progress = parent_progress_summary(parent, subtask_states)
    language = progress["language"]
    statuses = []
    recorded_statuses = []
    for item in parent.get("subtasks", []):
        if not isinstance(item, dict):
            continue
        state = _state_for_subtask(item, subtask_states)
        recorded_status = state.get("status")
        if recorded_status:
            recorded_statuses.append(str(recorded_status))
        statuses.append(str(recorded_status or item.get("status")))
    completed = recorded_statuses.count("completed")
    if not recorded_statuses:
        status = _status_label("no_recorded_status", language)
    elif statuses and completed == len(statuses):
        status = _status_label("completed", language)
    elif completed:
        status = _status_label("partially_completed", language)
    elif statuses and all(value == "waiting_for_required_input" for value in statuses):
        status = _status_label("waiting_for_required_input", language)
    elif statuses and all(value == "source_restricted" for value in statuses):
        status = _status_label("source_restricted", language)
    elif statuses and all(value == "unable_to_execute" for value in statuses):
        status = _status_label("unable_to_execute", language)
    else:
        status = _status_label("in_progress", language)
    return {
        "status": status,
        "subtask_count": len(statuses),
        "recorded_subtask_count": progress["recorded_subtask_count"],
        "completed_count": completed,
        "source_restricted_count": recorded_statuses.count("source_restricted"),
        "waiting_for_required_input_count": recorded_statuses.count("waiting_for_required_input"),
        "subtasks": progress["subtasks"],
    }


def _contains_commercial_judgment(text: str) -> bool:
    for pattern in _COMMERCIAL_JUDGMENT_PATTERNS:
        for match in pattern.finditer(text):
            clause_start = max(
                text.rfind("\n", 0, match.start()),
                text.rfind("。", 0, match.start()),
                text.rfind("！", 0, match.start()),
                text.rfind("？", 0, match.start()),
                text.rfind("；", 0, match.start()),
                text.rfind(".", 0, match.start()),
                text.rfind("!", 0, match.start()),
                text.rfind("?", 0, match.start()),
            )
            prefix = text[clause_start + 1:match.start()].casefold()
            boundary = re.search(
                r"(?:不替(?:用户|你)?(?:判断|决定)?|不(?:判断|决定)(?:是否)?|不(?:做|作|给|提供)推荐|"
                r"不能(?:据此|因此)?(?:判断|证明|推出|说)?|(?:does not|do not|don't|cannot|can't)\s+"
                r"(?:decide|judge|conclude|infer))(?:[^\n。！？；.!?]{0,48})$",
                prefix,
                re.IGNORECASE,
            )
            if not boundary:
                return True
    return False


def _contains_internal_term(text: str) -> bool:
    return any(pattern.search(text) for pattern in _INTERNAL_TERM_PATTERNS)


def _progress_line(progress: dict[str, Any], language: str) -> str | None:
    parts = []
    for field, zh_label, en_label in _PROGRESS_FIELDS:
        value = progress.get(field)
        if value is not None:
            parts.append(f"{zh_label} {value}" if language == "zh" else f"{en_label} {value}")
    if not parts:
        return None
    return "进度：" + "；".join(parts) + "。" if language == "zh" else "Progress: " + "; ".join(parts) + "."


def render_composite_delivery(
    parent: dict[str, Any],
    deliveries: dict[str, str],
    subtask_states: dict[str, dict[str, Any]] | None = None,
) -> str:
    """Render objective, separated terminal sections for a composite parent."""
    states = subtask_states or {}
    language = _language(parent.get("language"))
    for delivery in deliveries.values():
        raw_delivery = str(delivery)
        if _contains_commercial_judgment(raw_delivery):
            raise ValueError("terminal delivery contains a commercial judgment")
        if _contains_internal_term(raw_delivery):
            raise ValueError("terminal delivery contains an internal term or identifier")

    progress_summary = parent_progress_summary(parent, states)
    progress_by_route = {
        str(item["route"]): item
        for item in progress_summary["subtasks"]
    }
    if language == "zh":
        lines = [f"# {parent.get('parent_title') or _parent_title(language)}"]
        neutral_message = "未提供本任务交付或状态。"
        status_prefix = "状态："
        status_notes_title = "交付状态说明"
        status_notes = "请以各子任务已提供的交付、来源和状态为准。"
        source_title = "来源与检查时间"
        source_notes = "请以各子任务本轮实际打开的来源和观察时间为准。"
    else:
        lines = [f"# {parent.get('parent_title') or _parent_title(language)}"]
        neutral_message = "No delivery or recorded status was provided for this task."
        status_prefix = "Status: "
        status_notes_title = "Delivery status notes"
        status_notes = "Use the delivery, source, and status supplied for each subtask."
        source_title = "Sources and observation time"
        source_notes = "Use the sources actually opened in this run and their observation time for each subtask."
    if progress_summary["status"]:
        lines.extend(["", f"{status_prefix}{progress_summary['status']}"])
    for item in parent.get("subtasks", []):
        if not isinstance(item, dict):
            continue
        route = item.get("route")
        subtask_id = item.get("subtask_id")
        display_name = item.get("display_name") or _display_name(route, language)
        delivery = deliveries.get(subtask_id, deliveries.get(route))
        progress = progress_by_route.get(str(route), {})
        recorded_status = progress.get("status")
        planned_status = item.get("status")

        lines.extend(["", f"## {display_name}"])
        if recorded_status:
            lines.append(f"{status_prefix}{_status_label(str(recorded_status), language)}")
        elif planned_status in {"waiting_for_required_input", "waiting_for_upstream_result"}:
            lines.append(f"{status_prefix}{_status_label(str(planned_status), language)}")
        progress_line = _progress_line(progress, language)
        if progress_line:
            lines.append(progress_line)
        if delivery:
            lines.append(delivery)
        elif not recorded_status and planned_status not in {"waiting_for_required_input", "waiting_for_upstream_result"}:
            lines.append(neutral_message)
    lines.extend([
        "", f"## {status_notes_title}", status_notes,
        "", f"## {source_title}", source_notes,
    ])
    return append_final_footer("\n".join(lines), language)
