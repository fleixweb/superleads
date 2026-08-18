#!/usr/bin/env python3
"""Export the three Superleads business routes as user-visible Markdown.

This is a thin delivery layer. It does not search, open sources, create facts,
rank customers, price products, or decide whether a market is worth entering.
It only renders already-audited workbook/matrix projections in business
language and then runs the user-visible Markdown contract validator.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from _superleads_common import ensure_list, has_text, load_json
from audit_delivery import audit_graph as audit_lead_graph
from audit_product_market_analysis import audit_graph as audit_market_graph
from background_report import (
    background_contact_values_to_redact,
    build_background_report_sheets,
    validate_background_report,
)
from export_product_market_workbook import build_sheets as build_market_sheets
from export_product_market_workbook import markdown_report as market_markdown_report
from export_workbook import (
    build_sheets as build_lead_sheets,
    current_brief_id,
    default_discovery_relevance_label_to_raw,
    project_default_discovery_basis_status,
    hold_contact_values,
    redact_delivery_sheets,
    redact_local_paths,
)
from superleads_execution_state import status_summary
from superleads_user_guidance import append_final_footer
from validate_product_market_analysis import load_market_fixture
from validate_superleads_user_visible_output import validate as validate_user_visible_markdown

ROUTES = (
    "bulk_customer_development",
    "customer_background_research",
    "product_outbound_market_analysis",
)

MIN_TABLES = {
    "bulk_customer_development": 10,
    "customer_background_research": 6,
    "product_outbound_market_analysis": 7,
}

PRODUCT_MODULE_LABELS = {
    "google_trends": "Google Trends 长期搜索趋势",
    "online_price": "线上市场 / 平台价格参考",
    "season_holiday": "节假日 / 季节销售窗口",
    "external_factors": "近期外部因素",
    "market_reports": "公开市场报告 / 行业资料",
    "destination_compliance": "目标国准入与合规",
    "import_tax": "进口税费",
    "export_requirements": "出口国要求",
    "logistics": "运输方式 / 路线 / 预申报",
}

PRODUCT_BASE_MODULES = (
    "google_trends",
    "online_price",
    "season_holiday",
    "external_factors",
    "market_reports",
)

INTERNAL_REPLACEMENTS = {
    "forbidden": "来源受限",
    "login_required": "来源受限",
    "login_wall": "来源受限",
    "not_accessed": "未访问",
    "EvidenceCard": "证据记录",
    "SearchLog": "搜索记录",
    "MatrixRow": "表格行",
    "ClaimEvidence": "证据关系",
    "Claim": "公开信息点",
    "graph": "资料包",
    "eval": "检查",
    "run_id": "记录编号",
    "brief_id": "需求编号",
    "source_id": "来源编号",
    "observation_id": "观察编号",
    "claim_id": "信息编号",
}


def _stringify(value: Any) -> str:
    if value is None:
        return "未提供"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        items = [_stringify(item) for item in value]
        items = [item for item in items if item and item != "未提供"]
        return "；".join(items) if items else "未提供"
    if isinstance(value, dict):
        items = [f"{key}：{_stringify(val)}" for key, val in value.items() if val is not None]
        return "；".join(items) if items else "未提供"
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return text if text else "未提供"


def _safe_text(value: Any) -> str:
    text = _stringify(value)
    text = redact_local_paths(text)
    for raw, replacement in sorted(INTERNAL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True):
        if re.fullmatch(r"[A-Za-z0-9_]+", raw):
            pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(raw)}(?![A-Za-z0-9_])", re.IGNORECASE)
            text = pattern.sub(replacement, text)
        else:
            text = text.replace(raw, replacement)
    return text


def _md_escape(value: Any) -> str:
    text = _safe_text(value)
    if len(text) > 420:
        text = text[:417].rstrip() + "…"
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _table(headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        rows = [{headers[0]: "暂无可展示记录"}]
    lines = [
        "| " + " | ".join(_md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
    return lines


def _append_table(lines: list[str], title: str, headers: list[str], rows: list[dict[str, Any]]) -> None:
    lines.extend([f"## {title}", ""])
    lines.extend(_table(headers, rows))
    lines.append("")


def _id_map(items: Any, key: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in ensure_list({"items": items}, "items"):
        if isinstance(item, dict) and has_text(item.get(key)):
            result[str(item[key])] = item
    return result


def _decode_pointer_token(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _patch_parent(document: object, pointer: str) -> tuple[object, str]:
    if not pointer.startswith("/"):
        raise ValueError(f"patch path must be a JSON Pointer: {pointer}")
    tokens = [_decode_pointer_token(token) for token in pointer[1:].split("/")]
    if not tokens:
        raise ValueError("patch path must target a value")
    current = document
    for token in tokens[:-1]:
        current = current[int(token)] if isinstance(current, list) else current[token]  # type: ignore[index]
    return current, tokens[-1]


def _apply_fixture_patches(graph: dict[str, Any], patches: object) -> dict[str, Any]:
    if not isinstance(patches, list):
        raise ValueError("fixture patches must be a list")
    result = deepcopy(graph)
    for patch in patches:
        if not isinstance(patch, dict):
            raise ValueError("fixture patch must be an object")
        parent, token = _patch_parent(result, str(patch.get("path", "")))
        operation = patch.get("op")
        if operation == "remove":
            if isinstance(parent, list):
                del parent[int(token)]
            elif isinstance(parent, dict):
                del parent[token]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "replace":
            if "value" not in patch:
                raise ValueError("replace patch lacks value")
            if isinstance(parent, list):
                parent[int(token)] = patch["value"]
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "add":
            if "value" not in patch:
                raise ValueError("add patch lacks value")
            if isinstance(parent, list):
                parent.insert(int(token), patch["value"])
            elif isinstance(parent, dict):
                parent[token] = patch["value"]
            else:
                raise ValueError("fixture patch parent is not mutable")
        elif operation == "append":
            if not isinstance(parent, list) or token != "-" or "value" not in patch:
                raise ValueError("append patch must target /-")
            parent.append(patch["value"])
        else:
            raise ValueError(f"unsupported fixture patch operation: {operation}")
    return result


def _load_lead_fixture(path: Path, seen: set[Path] | None = None) -> dict[str, Any]:
    seen = seen or set()
    path = path.resolve()
    if path in seen:
        raise ValueError(f"fixture inheritance cycle: {path.name}")
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must be a JSON object: {path.name}")
    if "extends" not in payload:
        return payload
    base_name = payload.get("extends")
    if not isinstance(base_name, str) or Path(base_name).name != base_name:
        raise ValueError(f"fixture base must be a local filename: {path.name}")
    base = _load_lead_fixture(path.parent / base_name, seen | {path})
    return _apply_fixture_patches(base, payload.get("patches"))


def _current_brief(graph: dict[str, Any]) -> dict[str, Any]:
    brief_id = current_brief_id(graph)
    for brief in ensure_list(graph, "briefs"):
        if isinstance(brief, dict) and brief.get("brief_id") == brief_id:
            return brief
    for brief in reversed(ensure_list(graph, "briefs")):
        if isinstance(brief, dict):
            return brief
    return {}


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _safe_text(value)
        if text and text != "未提供":
            return text
    return "未提供"


def _display_items(value: Any) -> list[str]:
    raw = value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                raw = json.loads(stripped)
            except Exception:
                raw = value
    if isinstance(raw, list):
        return [item for item in (_safe_text(item) for item in raw) if item and item != "未提供"]
    text = _safe_text(raw)
    return [text] if text and text != "未提供" else []


def _contact_lookup(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for row in rows:
        name = _safe_text(row.get("公司/线索名称") or row.get("公司名称") or row.get("主体"))
        value = _safe_text(row.get("联系方式") or row.get("公开联系入口"))
        status = _safe_text(row.get("状态") or row.get("联系方式状态"))
        if name == "未提供" or value == "未提供":
            continue
        lookup.setdefault(name, []).append(f"{value}（{status}）" if status != "未提供" else value)
    return lookup


def _source_lookup(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for row in rows:
        name = _safe_text(row.get("公司/线索名称") or row.get("公司名称") or row.get("对象"))
        source = _first_nonempty(row.get("来源说明"), row.get("来源"), row.get("发现来源"))
        link = _safe_text(row.get("来源链接") or row.get("发现链接"))
        combined = source if link == "未提供" else f"{source}；{link}"
        if name == "未提供" or combined == "未提供":
            continue
        lookup.setdefault(name, []).append(combined)
    return lookup


def _candidate_name(candidate: dict[str, Any]) -> str:
    return _safe_text(candidate.get("company_name") or candidate.get("name") or candidate.get("candidate_id"))


def _candidate_by_name(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    entities = {item.get("entity_id"): item for item in ensure_list(graph, "entities") if isinstance(item, dict) and item.get("entity_id")}
    for candidate in ensure_list(graph, "candidates"):
        if not isinstance(candidate, dict):
            continue
        name = _candidate_name(candidate)
        if name != "未提供":
            enriched = dict(candidate)
            entity = entities.get(candidate.get("entity_id"))
            if isinstance(entity, dict):
                enriched["entity"] = entity
            result.setdefault(name, enriched)
    return result


def _bulk_partition(relevance: str, status: str) -> str:
    if relevance in {"已排除", "不相关", "明确排除", "明确排除/不相关", "explicitly_excluded_or_unrelated"}:
        return "已排除 / 仅作参考"
    if relevance in {"直接相关", "可能相关", "directly_related", "possibly_related"} and status in {"已有明确依据", "多来源方向一致", "可作为线索"}:
        return "公开信号已匹配当前范围"
    return "待确认"


def _candidate_basis_status(candidate: dict[str, Any], row: dict[str, Any], relevance_label: str) -> str:
    explicit = _safe_text(row.get("依据状态"))
    if explicit != "未提供":
        return explicit
    normalized_relevance = default_discovery_relevance_label_to_raw(relevance_label)
    return project_default_discovery_basis_status(candidate, normalized_relevance)


def _candidate_country(candidate: dict[str, Any], row: dict[str, Any]) -> str:
    return _first_nonempty(
        row.get("国家/地区"),
        candidate.get("country_or_region"),
        candidate.get("country"),
        candidate.get("target_country_or_region"),
        "待确认",
    )


def _candidate_role(candidate: dict[str, Any], row: dict[str, Any]) -> str:
    entity = candidate.get("entity") if isinstance(candidate.get("entity"), dict) else {}
    raw = _first_nonempty(
        row.get("可能客户角色"),
        row.get("客户类型"),
        candidate.get("customer_role"),
        candidate.get("customer_type"),
        entity.get("customer_type"),
        candidate.get("channel_role"),
    )
    if raw in {"distributor", "dealer", "distribution"}:
        return "经销商 / 分销商"
    if raw in {"wholesaler", "wholesale"}:
        return "批发商"
    if raw in {"retailer", "retail", "retail chain"}:
        return "零售商 / 连锁"
    if raw in {"manufacturer", "oem"}:
        return "制造商 / OEM"
    if raw in {"industrial supplier", "supplier"}:
        return "工业供应商"
    return raw if raw != "未提供" else "待确认"


def _rows_from_sheet(rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append({target: _first_nonempty(*(row.get(src) for src in sources)) for target, sources in mapping.items()})
    return result


def _current_execution_state(graph: dict[str, Any]) -> dict[str, Any]:
    for run in reversed(ensure_list(graph, "runs")):
        if not isinstance(run, dict):
            continue
        execution_state = run.get("execution_state")
        if isinstance(execution_state, dict):
            return execution_state
    return {}


def _search_combination_rows(execution_state: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
    if not execution_state:
        return [], [], []
    summary = status_summary(execution_state)
    rows = [
        {
            "产品词": _safe_text(item.get("product_term")),
            "国家/市场": _safe_text(item.get("market")),
            "客户类型": _safe_text(item.get("customer_type")),
            "新增主体": _safe_text(item.get("new_candidate_count")),
        }
        for item in summary.get("search_combination_coverage", [])
        if isinstance(item, dict)
    ]
    hints = [item for item in summary.get("uncovered_combination_hints", []) if isinstance(item, str) and item.strip()]
    next_step_options = [item for item in summary.get("next_step_options", []) if isinstance(item, dict)]
    return rows, hints, next_step_options


def build_bulk_markdown(graph: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    audit = audit_lead_graph(graph, requested_delivery_status="initial_lead_list")
    if not audit.get("ok"):
        return None, list(audit.get("issues", []))

    sheets = build_lead_sheets(graph, audit, "initial")
    sheets = redact_local_paths(redact_delivery_sheets(sheets, hold_contact_values(graph)))
    brief = _current_brief(graph)
    product = _safe_text(brief.get("product_or_service"))
    target_country = _safe_text(brief.get("target_country_or_region"))
    target_customer = _safe_text(brief.get("target_customer_type"))
    contract = brief.get("customer_selection_contract") if isinstance(brief.get("customer_selection_contract"), dict) else {}
    excluded = _safe_text(contract.get("excluded_customer_types") if isinstance(contract, dict) else None)
    if excluded == "未提供":
        excluded = "未设置明确排除项；同行、原厂、参考品牌不自动当作正式客户。"

    intro_rows = [
        {"项目": "我理解你卖的是", "本轮写法": product},
        {"项目": "本次优先找", "本轮写法": "；".join(item for item in (target_country, target_customer) if item != "未提供") or "目标国家/客户类型待确认"},
        {"项目": "本次不纳入", "本轮写法": excluded},
        {"项目": "判断依据将重点看", "本轮写法": "公开业务/产品/应用信号、主体匹配、联系方式来源、来源受限和下一步待确认项。"},
    ]

    contacts = _contact_lookup(sheets.get("联系方式汇总", []))
    sources = _source_lookup(sheets.get("官网与来源链接", []))
    candidates_by_name = _candidate_by_name(graph)
    candidate_rows: list[dict[str, Any]] = []
    for row in sheets.get("发现候选池", []):
        if not isinstance(row, dict):
            continue
        name = _safe_text(row.get("公司名称") or row.get("公司/线索名称") or row.get("候选客户") or row.get("说明"))
        candidate = candidates_by_name.get(name, {})
        signal = _first_nonempty(
            row.get("已观察业务/产品/应用信号"),
            row.get("业务/产品关联信号说明"),
            row.get("相关性依据"),
            "公开业务信号待确认",
        )
        relevance = _first_nonempty(row.get("业务相关性"), row.get("方向状态"), "待确认")
        basis_status = _candidate_basis_status(candidate, row, relevance)
        contact_text = "；".join(contacts.get(name, [])) or _first_nonempty(row.get("官网/域名"), "待确认")
        source_text = "；".join(sources.get(name, [])) or _first_nonempty(row.get("发现来源"), row.get("发现链接"), "来源 / 来源状态待确认")
        confirm = "；".join(
            item for item in (
                _safe_text(row.get("下一步待验证")),
                _safe_text(row.get("未知项")),
                _safe_text(row.get("来源受限")),
            )
            if item != "未提供"
        ) or "采购角色、产品适配、区域和是否接受外部供应商资料待确认"
        candidate_rows.append({
            "分区": _bulk_partition(relevance, basis_status),
            "候选客户": name,
            "品牌名称": _first_nonempty(row.get("品牌名称"), candidate.get("brand_name")),
            "国家/地区": _candidate_country(candidate, row),
            "可能客户角色": _candidate_role(candidate, row),
            "当前看到的业务信号": signal,
            "业务相关性": relevance,
            "依据状态": basis_status,
            "可用联系入口": contact_text,
            "还要确认什么": confirm,
            "来源 / 来源状态": source_text,
        })

    excluded_rows: list[dict[str, Any]] = []
    for row in sheets.get("已排除客户", []):
        if not isinstance(row, dict):
            continue
        name = _safe_text(row.get("公司名称") or row.get("公司/线索名称") or row.get("候选客户") or row.get("说明"))
        if name == "未提供" or name == "暂无明确排除记录":
            name = _first_nonempty(row.get("说明"), "暂无明确排除记录")
        candidate = candidates_by_name.get(name, {})
        excluded_rows.append({
            "分区": "已排除 / 仅作参考",
            "对象": name,
            "归入原因": _first_nonempty(row.get("用户排除项/已观察冲突"), row.get("相关性依据"), row.get("说明"), "命中排除或仅作参考边界"),
            "依据状态": _candidate_basis_status(candidate, row, "明确排除/不相关") if candidate else "可作为线索",
            "是否可由用户改判": "可以；若用户确认该类主体仍可开发，应重新进入发现候选池核查。",
            "来源 / 来源状态": "；".join(sources.get(name, [])) or _first_nonempty(row.get("发现来源"), row.get("发现链接"), "来源 / 来源状态待确认"),
        })

    pending_rows: list[dict[str, Any]] = []
    for row in sheets.get("待核查事项", []):
        if not isinstance(row, dict):
            continue
        pending_rows.append({
            "对象": _first_nonempty(row.get("对象"), row.get("公司/线索名称"), "待确认对象"),
            "待确认事项": _first_nonempty(row.get("原因"), row.get("待确认事项"), row.get("说明")),
            "下一步": _first_nonempty(row.get("建议动作"), "补充公开来源或由销售人工核验"),
            "状态": "待确认",
        })

    contact_rows: list[dict[str, Any]] = []
    for row in sheets.get("联系方式汇总", []):
        if not isinstance(row, dict):
            continue
        contact_type = _first_nonempty(row.get("联系方式类型"), row.get("类型"), "待确认")
        contact_value = _first_nonempty(row.get("联系方式"), row.get("公开联系入口"), "待确认")
        person_parts = [
            value for value in (
                _safe_text(row.get("联系人")),
                _safe_text(row.get("职位/部门")),
            )
            if value != "未提供"
        ]
        person_clue = "；".join(person_parts) or "未记录"
        if contact_type in {"person_name", "job_title"}:
            # Names/titles are role clues, not usable contact endpoints.
            if person_clue == "未记录" and contact_value != "未提供":
                person_clue = contact_value
            contact_value = "未记录可用入口"
        status = _first_nonempty(row.get("状态"), row.get("联系方式状态"), "待确认归属")
        pending_reason = _first_nonempty(
            row.get("归属状态说明"),
            row.get("归属证据/待确认原因"),
            "无",
        )
        if status == "待确认归属" and pending_reason == "无":
            pending_reason = "需自行核实是否属于该公司"
        source_note = _first_nonempty(row.get("来源说明"), row.get("来源"))
        source_link = _safe_text(row.get("来源链接"))
        if source_note == "未提供" and source_link != "未提供":
            source_text = source_link
        elif source_note != "未提供" and source_link != "未提供":
            source_text = f"{source_note}；{source_link}"
        else:
            source_text = source_note if source_note != "未提供" else "来源状态待确认"
        contact_rows.append({
            "对象": _first_nonempty(row.get("公司/线索名称"), row.get("公司名称"), row.get("主体"), "待确认归属线索"),
            "联系人 / 公开职业线索": person_clue,
            "联系方式": contact_value,
            "类型": contact_type,
            "可用状态": status,
            "待确认原因": pending_reason,
            "来源 / 链接": source_text,
        })

    coverage_rows: list[dict[str, Any]] = []
    for row in sheets.get("搜索覆盖与收敛", []):
        if not isinstance(row, dict):
            continue
        coverage_rows.append({
            "本轮查了哪些方向": _first_nonempty(row.get("搜索方向"), "未记录搜索方向"),
            "覆盖国家/语言/来源类型": "；".join(
                _display_items(row.get("地域"))
                + _display_items(row.get("语言"))
                + _display_items(row.get("来源类别"))
            ) or "覆盖范围待确认",
            "新增/重复": f"新增 { _safe_text(row.get('新增唯一候选数')) }；重复 { _safe_text(row.get('重复候选数')) }",
            "来源受限或未执行": "；".join(item for item in (
                _safe_text(row.get("失败访问")),
                _safe_text(row.get("受限来源")),
            ) if item != "未提供") or "未记录明显受限来源",
            "覆盖/收敛说明": _first_nonempty(row.get("覆盖/收敛说明"), "收敛只表示本轮查询组合下新增减少，不代表找全全网客户。"),
        })

    source_rows: list[dict[str, Any]] = []
    for row in sheets.get("官网与来源链接", []):
        if not isinstance(row, dict):
            continue
        source_rows.append({
            "对象": _first_nonempty(row.get("公司/线索名称"), "候选线索"),
            "来源 / 来源状态": _first_nonempty(row.get("来源说明"), "公开入口待复核"),
            "链接": _safe_text(row.get("来源链接")),
        })

    search_combination_rows, uncovered_combination_hints, next_step_options = _search_combination_rows(
        _current_execution_state(graph)
    )

    social_rows = [row for row in sheets.get("社媒与公开职业线索", []) if isinstance(row, dict)]
    map_rows = [row for row in sheets.get("地图与经营地址", []) if isinstance(row, dict)]
    trade_rows = [row for row in sheets.get("第三方贸易摘要", []) if isinstance(row, dict)]

    risk_rows: list[dict[str, Any]] = []
    for row in sheets.get("风险与说明", []):
        if not isinstance(row, dict):
            continue
        risk_rows.append({
            "提示": _first_nonempty(row.get("提示级别"), "说明"),
            "说明": _first_nonempty(row.get("说明"), "本轮公开发现可继续扩展；当前输出不宣称已覆盖全部企业。"),
        })
    risk_rows.extend([
        {"提示": "交付边界", "说明": "候选池不是正式开发名单；公开业务信号只用于销售人工核查。"},
        {"提示": "联系入口边界", "说明": "公开联系入口不等于采购意愿，公开职位不等于采购负责人。"},
        {"提示": "弱证据边界", "说明": "多来源方向一致只能说明线索收敛，不能升级为已验证客户。"},
    ])

    lines = [
        "# 批量客户开发",
        "",
        "本次输出是发现候选池，不是正式开发名单；联系入口不等于采购意愿。",
        "",
    ]
    _append_table(lines, "先把开发方向说清", ["项目", "本轮写法"], intro_rows)
    _append_table(
        lines,
        "发现候选池样表（候选池不是正式开发名单）",
        ["分区", "候选客户", "品牌名称", "国家/地区", "可能客户角色", "当前看到的业务信号", "业务相关性", "依据状态", "可用联系入口", "还要确认什么", "来源 / 来源状态"],
        candidate_rows,
    )
    if search_combination_rows:
        _append_table(lines, "本轮搜索组合", ["产品词", "国家/市场", "客户类型", "新增主体"], search_combination_rows)
    if uncovered_combination_hints:
        lines.extend(["## 尚未覆盖的组合（可继续）", ""])
        lines.extend(f"· {hint}" for hint in uncovered_combination_hints)
        lines.append("")
    _append_table(
        lines,
        "联系方式汇总",
        ["对象", "联系人 / 公开职业线索", "联系方式", "类型", "可用状态", "待确认原因", "来源 / 链接"],
        contact_rows,
    )
    _append_table(
        lines,
        "社媒与公开职业线索",
        ["公司名称", "平台", "页面类型", "页面名称 / 人员", "公开职位或部门", "公开联系入口", "主体关联依据", "来源状态", "观察时间", "来源 / 链接", "不能推出的内容"],
        social_rows,
    )
    _append_table(
        lines,
        "地图与经营地址",
        ["公司名称", "地图平台", "商户名称", "地址", "公开电话", "经营场景", "主体关联依据", "来源状态", "观察时间", "来源 / 链接", "不能推出的内容"],
        map_rows,
    )
    lines.extend([
        "## 第三方贸易摘要",
        "",
        "第三方贸易数据聚合站公开摘要，非官方海关记录。只保留本轮可见字段，不代表完整贸易记录，也不能推出采购意愿、采购权限、从中国采购事实或未来订单。",
        "",
    ])
    lines.extend(_table(
        ["公司名称", "状态", "进出口方向", "对方名称", "记录日期", "产品名称或 HS", "起运地或目的地", "主体匹配状态", "来源 / 链接", "观察时间", "不能推出的内容"],
        trade_rows,
    ))
    lines.append("")
    _append_table(lines, "搜索覆盖与收敛", ["本轮查了哪些方向", "覆盖国家/语言/来源类型", "新增/重复", "来源受限或未执行", "覆盖/收敛说明"], coverage_rows)
    _append_table(lines, "待确认事项", ["对象", "待确认事项", "下一步", "状态"], pending_rows)
    _append_table(lines, "已排除 / 仅作参考", ["分区", "对象", "归入原因", "依据状态", "是否可由用户改判", "来源 / 来源状态"], excluded_rows)
    _append_table(lines, "信息从哪里来", ["对象", "来源 / 来源状态", "链接"], source_rows)
    _append_table(lines, "风险与说明", ["提示", "说明"], risk_rows)
    if next_step_options:
        lines.extend(["## 下一步可选", ""])
        lines.extend(f"· {_safe_text(item.get('text'))}" for item in next_step_options)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", []


def _overview_lookup(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = _safe_text(row.get("你最关心的事") or row.get("问题"))
        if key != "未提供":
            result[key] = row
    return result


def _sanitize_background_overview_row(row: dict[str, Any]) -> dict[str, Any]:
    question = _safe_text(row.get("你最关心的事") or row.get("问题"))
    detail = _safe_text(row.get("目前了解到的情况") or row.get("当前看到什么") or row.get("说明"))
    conclusion = _safe_text(row.get("结论") or row.get("状态"))
    if question == "值不值得继续跟":
        question = "是否具备继续核验基础"
        detail = "只能作为下一步人工核验入口；公开信息不能证明当前采购需求。"
        conclusion = "由用户结合业务自行判断"
    if "建议继续跟进" in conclusion:
        conclusion = conclusion.replace("建议继续跟进", "可继续人工核验")
    if "建议继续了解" in conclusion:
        conclusion = conclusion.replace("建议继续了解", "可继续补充核验")
    if question == "现在能不能开始联系":
        question = "公开联系入口与待确认事项"
        detail = "只汇总当前可核实的公开联系入口及其数量；入口存在不代表采购需求、采购权限或应跟进。"
        conclusion = "公开联系入口与具体负责范围仍需分别核验"
    if question == "下一步怎么做":
        question = "下一步待确认什么"
        conclusion = "保留为待确认事项，不代表是否应跟进的结论"
    return {
        "问题": question,
        "当前看到什么": detail,
        "状态": conclusion,
        "核验边界": "作为公开信息与待确认事项，不写成采购意愿、采购负责人或跟进结论。",
    }


def _background_target_text(scope: dict[str, Any], sheets: dict[str, list[dict[str, Any]]]) -> str:
    target = scope.get("target") if isinstance(scope.get("target"), dict) else {}
    overview = _overview_lookup(sheets.get("客户一眼看懂", []))
    who = overview.get("这是谁", {})
    business = overview.get("它公开在做什么", {})
    subject = _first_nonempty(who.get("目前了解到的情况"), target.get("user_statement"), "本次背调对象")
    business_text = _first_nonempty(business.get("目前了解到的情况"), "公开业务信息待补充")
    status = _first_nonempty(who.get("结论"), "主体待确认")
    return f"{subject}；主体状态：{status}；公开业务线索：{business_text}；公开信息不能证明当前采购需求或采购负责人。"


def _background_business_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append({
            "公开看到的信号": _first_nonempty(row.get("公开看到的信号"), row.get("说明")),
            "公开关联依据": _first_nonempty(row.get("公开关联依据"), "公开关联依据待补充"),
            "待核验事项": _first_nonempty(row.get("待核验事项"), "公开信息不代表采购需求、采购权限或合作安排。"),
            "状态": _first_nonempty(row.get("状态"), "待确认"),
        })
    return result


def _background_caution_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    has_restricted = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        text = _safe_text(row)
        if "来源受限" in text:
            has_restricted = True
        result.append({
            "待核验事项": _first_nonempty(row.get("待核验事项"), row.get("说明")),
            "公开依据或来源限制": _first_nonempty(row.get("公开依据或来源限制"), "公开依据或来源限制待补充"),
            "状态": _first_nonempty(row.get("状态"), "待确认"),
            "处理边界": _first_nonempty(row.get("处理边界"), "待确认前不作为公司事实或业务结论。"),
        })
    if not has_restricted:
        result.append({
            "待核验事项": "来源受限",
            "公开依据或来源限制": "未打开或受限来源不能用来补公司事实。",
            "状态": "待确认",
            "处理边界": "保留为待确认线索，不作为公司事实或业务结论。",
        })
    return result


def build_background_markdown(graph: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    scope, issues = validate_background_report(graph)
    if scope is None or issues:
        return None, list(issues)
    sheets = build_background_report_sheets(scope)
    projection = scope.get("projection") if isinstance(scope.get("projection"), dict) else graph
    hidden_contacts = hold_contact_values(graph) | background_contact_values_to_redact(projection)
    sheets = redact_local_paths(redact_delivery_sheets(sheets, hidden_contacts))

    overview_rows = [_sanitize_background_overview_row(row) for row in sheets.get("客户一眼看懂", []) if isinstance(row, dict)]
    overview_rows.extend([
        {
            "问题": "是否能直接说有采购需求",
            "当前看到什么": "公开资料未直接证明当前采购计划。",
            "状态": "待确认",
            "核验边界": "不写成正在采购或采购意愿已确认。",
        },
        {
            "问题": "是否能直接找采购负责人",
            "当前看到什么": "公开人员、董事、Founder 或 Owner 线索不等于采购负责人。",
            "状态": "待确认",
            "核验边界": "不猜采购负责人或未公开的采购权限。",
        },
    ])

    lines = [
        "# 单一客户背调",
        "",
    ]
    _append_table(lines, "一句话先说清", ["项目", "人话结论"], [{"项目": "当前判断", "人话结论": _background_target_text(scope, sheets)}])
    _append_table(lines, "客户一眼看懂", ["问题", "当前看到什么", "状态", "核验边界"], overview_rows)
    _append_table(lines, "客户、品牌与关联方", ["名称", "它是什么", "和客户的关系", "目前把握", "我们依据什么"], sheets.get("客户、品牌与关联方", []))
    _append_table(lines, "公开业务信号与待核验事项", ["公开看到的信号", "公开关联依据", "待核验事项", "状态"], _background_business_rows(sheets.get("公开业务信号与待核验事项", [])))
    contact_rows = [
        row for row in sheets.get("公开联系入口与关联依据", [])
        if isinstance(row, dict) and "已隐藏联系方式" not in _safe_text(row.get("公开联系入口或职业线索"))
    ]
    _append_table(lines, "公开联系入口与关联依据", ["公开联系入口或职业线索", "与主体的公开关联依据", "待核验事项", "状态"], contact_rows)
    _append_table(lines, "待核验事项与来源限制", ["待核验事项", "公开依据或来源限制", "状态", "处理边界"], _background_caution_rows(sheets.get("待核验事项与来源限制", [])))
    if "疑似进出口记录（第三方聚合，待核实）" in sheets:
        _append_table(
            lines,
            "疑似进出口记录（第三方聚合，待核实）",
            ["方向（原文口径）", "对方名称（原文）", "日期", "品名 / HS（原文）", "起运 / 目的地（原文）", "来源 / 状态 / 边界"],
            sheets["疑似进出口记录（第三方聚合，待核实）"],
        )
    _append_table(lines, "信息从哪里来", ["上面哪条信息", "来源", "链接或材料", "看到的原话或位置", "时间", "状态"], sheets.get("信息从哪里来", []))
    return "\n".join(lines).rstrip() + "\n", []


def _current_market_brief(graph: dict[str, Any]) -> dict[str, Any]:
    runs = [item for item in ensure_list(graph, "runs") if isinstance(item, dict)]
    run = runs[-1] if runs else {}
    brief_id = run.get("brief_id")
    for brief in ensure_list(graph, "briefs"):
        if isinstance(brief, dict) and brief.get("brief_id") == brief_id:
            return brief
    for brief in reversed(ensure_list(graph, "briefs")):
        if isinstance(brief, dict):
            return brief
    return {}


def _market_not_executed_modules(graph: dict[str, Any]) -> list[str]:
    modules: list[str] = []
    seen: set[str] = set()
    for run in ensure_list(graph, "runs"):
        if not isinstance(run, dict):
            continue
        for module in ensure_list(run, "not_executed_modules"):
            key = str(module or "").strip()
            if key and key not in seen:
                seen.add(key)
                modules.append(key)
    return modules


def _market_product_name(graph: dict[str, Any]) -> str:
    product = next((item for item in ensure_list(graph, "products") if isinstance(item, dict)), {})
    return _first_nonempty(product.get("product_name"), product.get("model"), "本次产品")


def _market_gap_rows(graph: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for gap in ensure_list(graph, "gaps"):
        if not isinstance(gap, dict):
            continue
        rows.append({
            "待补材料/事项": _first_nonempty(gap.get("missing_item"), gap.get("field_name")),
            "为什么要补": _first_nonempty(gap.get("user_visible_note"), "用于进一步核验"),
            "向谁要": _first_nonempty(gap.get("requested_from"), "用户/供应链/专业方"),
            "状态": _first_nonempty(gap.get("status"), "待确认"),
        })
    return rows


def _market_append_required_human_sections(text: str, graph: dict[str, Any]) -> str:
    if "## 先看这几个贸易前提" in text and "先看贸易前提" not in text:
        text = text.replace("## 先看这几个贸易前提", "## 先看贸易前提（先看这几个贸易前提）", 1)
    return text


def build_product_market_markdown(graph: dict[str, Any]) -> tuple[str | None, list[dict[str, Any]]]:
    audit = audit_market_graph(graph)
    if not audit.get("ok"):
        return None, list(audit.get("issues", []))
    sheets = build_market_sheets(graph)
    text = market_markdown_report(sheets, graph)
    text = _market_append_required_human_sections(text, graph)
    if not text.startswith("# 产品出海市场分析"):
        text = f"# 产品出海市场分析\n\n产品：{_md_escape(_market_product_name(graph))}\n\n" + text
    return text, []


def infer_route(payload: dict[str, Any]) -> str:
    if payload.get("graph_type") == "ProductMarketAnalysisGraph":
        return "product_outbound_market_analysis"
    for run in ensure_list(payload, "runs"):
        if isinstance(run, dict) and run.get("route") == "product_outbound_market_analysis":
            return "product_outbound_market_analysis"
    for brief in ensure_list(payload, "briefs"):
        if not isinstance(brief, dict):
            continue
        if brief.get("task_mode") == "customer_background_research" or brief.get("output_mode") == "客户背调报告":
            return "customer_background_research"
    return "bulk_customer_development"


def build_markdown(input_path: Path, route: str) -> tuple[str | None, list[dict[str, Any]], str]:
    raw = load_json(input_path)
    if not isinstance(raw, dict):
        return None, [{"severity": "critical", "code": "markdown_delivery_input_not_object", "message": "Input must be a JSON object", "path": str(input_path)}], route
    resolved_for_route = raw
    if route == "auto" and "extends" in raw:
        try:
            resolved_for_route = load_market_fixture(input_path)
        except Exception:
            try:
                resolved_for_route = _load_lead_fixture(input_path)
            except Exception:
                resolved_for_route = raw
    actual_route = infer_route(resolved_for_route) if route == "auto" else route
    if actual_route == "product_outbound_market_analysis":
        graph = load_market_fixture(input_path)
        text, issues = build_product_market_markdown(graph)
    elif actual_route == "customer_background_research":
        graph = resolved_for_route if resolved_for_route is not raw else raw
        text, issues = build_background_markdown(graph)
    elif actual_route == "bulk_customer_development":
        graph = resolved_for_route if resolved_for_route is not raw else raw
        text, issues = build_bulk_markdown(graph)
    else:
        return None, [{"severity": "critical", "code": "markdown_delivery_unknown_route", "message": f"Unknown route: {route}", "path": "route"}], actual_route
    if text is not None:
        text = append_final_footer(text)
    return text, issues, actual_route


def _issue_payload(code: str, message: str, path: str = "markdown") -> dict[str, str]:
    return {"severity": "critical", "code": code, "message": message, "path": path}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Research graph or ProductMarketAnalysisGraph JSON")
    parser.add_argument("--route", choices=("auto",) + ROUTES, default="auto")
    parser.add_argument("--output", type=Path, help="Markdown output path. If omitted with --format markdown, writes to stdout.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--skip-user-visible-validation", action="store_true", help="Generate without running the Slice T user-visible validator")
    args = parser.parse_args()

    text, issues, actual_route = build_markdown(args.input, args.route)
    if text is None:
        payload = {"ok": False, "route": actual_route, "stage": "build", "issue_count": len(issues), "issues": issues}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    validation_issues: list[dict[str, Any]] = []
    if not args.skip_user_visible_validation:
        min_tables = MIN_TABLES[actual_route]
        # A scoped market report intentionally has fewer module tables; its
        # fixed tables and requested module still need a real Markdown shape.
        if actual_route == "product_outbound_market_analysis" and "本轮范围：" in text:
            min_tables = 4
        validation_issues = validate_user_visible_markdown(text, actual_route, min_tables=min_tables)
    all_issues = list(issues) + [
        _issue_payload(str(item.get("code", "markdown_delivery_validation_failed")), str(item.get("message", item)))
        for item in validation_issues
    ]
    ok = not all_issues
    if ok and args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")

    payload = {
        "ok": ok,
        "route": actual_route,
        "stage": "ready" if ok else "user_visible_validation",
        "output": str(args.output) if args.output and ok else None,
        "table_count": text.count("\n| ---") + text.count("\n|---"),
        "issue_count": len(all_issues),
        "issues": all_issues,
        "notes": [
            "Markdown 交付器只渲染已审核工作簿/矩阵投影，不新增事实。",
            "交付前已执行用户可见输出合同检查。" if not args.skip_user_visible_validation else "本次跳过用户可见输出合同检查。",
        ],
    }
    if args.format == "markdown":
        if ok:
            if args.output:
                print(str(args.output))
            else:
                print(text, end="")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
