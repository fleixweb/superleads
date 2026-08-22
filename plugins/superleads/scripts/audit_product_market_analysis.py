#!/usr/bin/env python3
"""Audit Superleads ProductMarketAnalysisGraph delivery readiness.

This gate is intentionally smaller than the full customer-development audit.
It answers one practical question for the new 产品出海市场分析 route:

Can the already-built user-visible matrix be delivered without upgrading
candidate/limited evidence into facts?
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _superleads_common import SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE, has_text, is_non_blocking_trace_issue, issue
from validate_product_market_analysis import as_list, ensure_list, load_market_fixture, validate_graph

READY_STATUS = "ready_with_limitations"
BLOCKED_STATUS = "blocked_needs_input"
CORRECTION_STATUS = "needs_correction"

DELIVERY_STATUSES = {READY_STATUS, BLOCKED_STATUS, CORRECTION_STATUS}
PRE_DELIVERY_STATUSES = {"planning_only", "draft_matrix"}

LIMITATION_STATUSES = {
    "candidate",
    "preliminary_reference",
    "business_confirmation_required",
    "technical_docs_required",
    "physical_verification_required",
    "professional_confirmation_required",
    "source_restricted",
    "not_executed",
    "not_provided",
    "conflict_pending_review",
}

LIMITED_FRESHNESS_STATUSES = {
    "stale_needs_recheck",
    "date_unknown_needs_recheck",
    "date_unknown_recently_observed",
}

LIMITED_AUTHORITY_STATUSES = {
    "candidate_needs_check",
    "secondary_reference_only",
    "unable_to_verify",
    "conflicting_identity",
    "not_executed",
}

FRESHNESS_STATUS_LABELS = {
    "current_enough_for_scope": "本轮复核日期在当前口径内",
    "date_unknown_recently_observed": "来源日期未见，但本轮已观察",
    "stale_needs_recheck": "资料偏旧，需重新复核",
    "date_unknown_needs_recheck": "来源日期未见，需复核后再当现行信息",
    "not_time_sensitive": "非强时效字段",
    "not_executed": "未执行",
}

AUTHORITY_STATUS_LABELS = {
    "verified_for_fact_domain": "已核实：仅限该事实域",
    "candidate_needs_check": "候选来源，待核实身份",
    "secondary_reference_only": "二级/参考来源，不能当主管结论",
    "unable_to_verify": "未能核实权威性",
    "conflicting_identity": "来源身份有冲突",
    "not_executed": "未执行",
}

STATUS_LABELS = {
    "verified": "已核实",
    "derived_calculation": "派生计算",
    "candidate": "候选",
    "preliminary_reference": "初步参考",
    "business_confirmation_required": "待业务确认",
    "technical_docs_required": "待技术资料确认",
    "physical_verification_required": "待实物核验",
    "professional_confirmation_required": "待专业确认",
    "source_restricted": "来源受限",
    "not_executed": "未执行",
    "not_applicable": "不适用",
    "not_provided": "未提供",
    "conflict_pending_review": "有冲突待复核",
}

INPUT_BLOCKING_CODES = {
    "market_audit_missing_run",
    "market_audit_missing_brief",
    "market_audit_missing_product",
    "market_audit_missing_matrix_rows",
    "market_audit_run_brief_missing",
    "market_audit_brief_product_missing",
    "market_audit_run_blocked_needs_input",
    "market_audit_delivery_not_ready",
}


def _current_run(graph: dict[str, Any]) -> dict[str, Any] | None:
    for run in reversed(ensure_list(graph, "runs")):
        if isinstance(run, dict):
            return run
    return None


def _id_map(graph: dict[str, Any], key: str, id_field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in ensure_list(graph, key):
        if isinstance(item, dict) and has_text(item.get(id_field)):
            result[str(item[id_field])] = item
    return result


def _status_label(status: Any) -> str:
    return STATUS_LABELS.get(
        str(status),
        FRESHNESS_STATUS_LABELS.get(str(status), AUTHORITY_STATUS_LABELS.get(str(status), str(status or "未提供"))),
    )


def _add_issue(issues: list[dict[str, str]], severity: str, code: str, message: str, path: str) -> None:
    issues.append(issue(severity, code, message, path))


def _minimum_delivery_issues(
    graph: dict[str, Any],
    requested_delivery_status: str | None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if graph.get("graph_type") != "ProductMarketAnalysisGraph":
        _add_issue(issues, "critical", "market_audit_wrong_graph_type", "Product market audit requires ProductMarketAnalysisGraph", "graph_type")

    run = _current_run(graph)
    briefs = _id_map(graph, "briefs", "brief_id")
    products = _id_map(graph, "products", "product_subject_id")

    if not run:
        _add_issue(issues, "major", "market_audit_missing_run", "产品出海市场分析交付需要至少一个 Run", "runs")
    elif run.get("route") != "product_outbound_market_analysis":
        _add_issue(issues, "critical", "market_audit_wrong_route", "当前 Run 不是 product_outbound_market_analysis 路线", "runs[-1].route")

    if not briefs:
        _add_issue(issues, "major", "market_audit_missing_brief", "产品出海市场分析交付需要 Brief", "briefs")
    if not products:
        _add_issue(issues, "major", "market_audit_missing_product", "产品出海市场分析交付需要产品档案", "products")
    if not ensure_list(graph, "matrix_rows"):
        _add_issue(issues, "major", "market_audit_missing_matrix_rows", "产品出海市场分析交付需要用户可见矩阵行", "matrix_rows")

    if isinstance(run, dict):
        brief_id = str(run.get("brief_id") or "")
        brief = briefs.get(brief_id)
        if has_text(brief_id) and brief_id not in briefs:
            _add_issue(issues, "critical", "market_audit_run_brief_missing", "当前 Run 引用的 Brief 不存在", "runs[-1].brief_id")
        if isinstance(brief, dict) and run.get("brief_version_id") != brief.get("brief_version_id"):
            _add_issue(issues, "critical", "market_audit_run_brief_version_mismatch", "当前 Run 与 Brief version 不一致，需要重跑或降级", "runs[-1].brief_version_id")
        product_id = str(brief.get("product_subject_id") or "") if isinstance(brief, dict) else ""
        if has_text(product_id) and product_id not in products:
            _add_issue(issues, "critical", "market_audit_brief_product_missing", "当前 Brief 引用的产品档案不存在", "briefs.product_subject_id")

    delivery_status = requested_delivery_status
    if delivery_status is None and isinstance(run, dict):
        raw_status = run.get("delivery_status")
        delivery_status = str(raw_status) if has_text(raw_status) else None

    if delivery_status:
        if delivery_status == BLOCKED_STATUS:
            _add_issue(issues, "major", "market_audit_run_blocked_needs_input", "当前 Run 标记为需要用户/业务资料补齐，不能进入导出交付", "runs[-1].delivery_status")
        elif delivery_status in PRE_DELIVERY_STATUSES:
            _add_issue(issues, "major", "market_audit_delivery_not_ready", f"当前 Run 仍是 {delivery_status}，不能作为最终导出交付", "runs[-1].delivery_status")
        elif delivery_status not in DELIVERY_STATUSES:
            _add_issue(issues, "critical", "market_audit_unknown_delivery_status", f"未知 delivery_status: {delivery_status}", "runs[-1].delivery_status")
        elif delivery_status == CORRECTION_STATUS:
            _add_issue(issues, "critical", "market_audit_run_needs_correction", "当前 Run 标记为需要修正，不能导出交付", "runs[-1].delivery_status")

    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        if row.get("internal_refs_hidden") is not True:
            _add_issue(issues, "critical", "market_audit_internal_refs_not_hidden", "用户可见矩阵行必须隐藏内部引用", f"matrix_rows[{idx}].internal_refs_hidden")
    return issues


def _limitation(
    code: str,
    message: str,
    status: Any,
    path: str,
    sheet_name: Any = None,
    topic: Any = None,
) -> dict[str, str]:
    payload = {
        "code": code,
        "message": message,
        "status": str(status or "未提供"),
        "status_label": _status_label(status),
        "path": path,
    }
    if has_text(sheet_name):
        payload["sheet_name"] = str(sheet_name)
    if has_text(topic):
        payload["topic"] = str(topic)
    return payload


def _collect_limitations(graph: dict[str, Any]) -> list[dict[str, str]]:
    limitations: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(item: dict[str, str]) -> None:
        key = (item.get("code", ""), item.get("path", ""), item.get("message", ""))
        if key not in seen:
            seen.add(key)
            limitations.append(item)

    for run_idx, run in enumerate(ensure_list(graph, "runs")):
        if not isinstance(run, dict):
            continue
        for module in as_list(run.get("not_executed_modules")):
            if has_text(module):
                add(_limitation(
                    "market_module_not_executed",
                    f"本轮未执行模块：{module}",
                    "not_executed",
                    f"runs[{run_idx}].not_executed_modules",
                ))

    for idx, row in enumerate(ensure_list(graph, "matrix_rows")):
        if not isinstance(row, dict):
            continue
        status = str(row.get("status") or "")
        if status in LIMITATION_STATUSES:
            add(_limitation(
                "market_matrix_row_limitation",
                f"{row.get('sheet_name') or '未命名工作表'} / {row.get('row_topic') or '未命名行'}：{_status_label(status)}",
                status,
                f"matrix_rows[{idx}]",
                row.get("sheet_name"),
                row.get("row_topic"),
            ))

    for idx, gap in enumerate(ensure_list(graph, "gaps")):
        if not isinstance(gap, dict):
            continue
        status = str(gap.get("status") or "")
        if status in LIMITATION_STATUSES:
            note = gap.get("user_visible_note") or gap.get("missing_item") or "存在待确认事项"
            add(_limitation(
                "market_gap_visible",
                str(note),
                status,
                f"gaps[{idx}]",
                gap.get("field_domain"),
                gap.get("field_name"),
            ))

    for idx, conflict in enumerate(ensure_list(graph, "conflicts")):
        if not isinstance(conflict, dict):
            continue
        status = str(conflict.get("status") or "")
        if status == "conflict_pending_review":
            add(_limitation(
                "market_conflict_pending_review",
                str(conflict.get("summary") or "存在来源冲突，需复核"),
                status,
                f"conflicts[{idx}]",
                conflict.get("field_domain"),
                conflict.get("field_name"),
            ))

    for idx, freshness in enumerate(ensure_list(graph, "freshness_records")):
        if not isinstance(freshness, dict):
            continue
        status = str(freshness.get("freshness_status") or "")
        if status in LIMITED_FRESHNESS_STATUSES:
            add(_limitation(
                "market_freshness_limitation",
                str(freshness.get("user_visible_summary") or freshness.get("date_basis") or "资料时效需复核"),
                status,
                f"freshness_records[{idx}]",
                freshness.get("field_domain"),
                freshness.get("field_name"),
            ))

    for idx, authority in enumerate(ensure_list(graph, "authority_verification_records")):
        if not isinstance(authority, dict):
            continue
        status = str(authority.get("verification_status") or "")
        if status in LIMITED_AUTHORITY_STATUSES:
            add(_limitation(
                "market_authority_limitation",
                str(authority.get("verification_basis") or "来源权威性未能核实或仅可作参考，不能支撑确定性官方结论"),
                status,
                f"authority_verification_records[{idx}]",
                authority.get("fact_domain"),
                authority.get("jurisdiction_role"),
            ))

    for idx, premise in enumerate(ensure_list(graph, "trade_premises")):
        if not isinstance(premise, dict):
            continue
        for field in ("status", "departure_node_status"):
            status = str(premise.get(field) or "")
            if status in LIMITATION_STATUSES:
                note = premise.get("departure_node_basis") if field == "departure_node_status" else None
                add(_limitation(
                    "market_trade_premise_limitation",
                    str(note or f"贸易前提字段 {field} 仍为{_status_label(status)}"),
                    status,
                    f"trade_premises[{idx}].{field}",
                    "原产地与贸易前提",
                    field,
                ))

    for idx, observation in enumerate(ensure_list(graph, "observations")):
        if not isinstance(observation, dict):
            continue
        access_status = str(observation.get("access_status") or "")
        if access_status in {"blocked", "login_wall", "login_required", "forbidden", "inaccessible", "not_accessed"}:
            add(_limitation(
                "market_source_access_limited",
                f"来源访问受限：{observation.get('title') or access_status}",
                "source_restricted",
                f"observations[{idx}].access_status",
            ))
    return limitations


def _delivery_issue_blocks(item: dict[str, Any]) -> bool:
    if item.get("severity") == "critical":
        return True
    if item.get("severity") != "major":
        return False
    return not is_non_blocking_trace_issue(item)


def _delivery_status_from_issues(issues: list[dict[str, str]]) -> str:
    blocking = [item for item in issues if _delivery_issue_blocks(item)]
    if not blocking:
        return READY_STATUS
    codes = {item.get("code") for item in blocking}
    if codes and codes.issubset(INPUT_BLOCKING_CODES):
        return BLOCKED_STATUS
    return CORRECTION_STATUS


def audit_graph(graph: dict[str, Any], requested_delivery_status: str | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    validation_issues = validate_graph(graph)
    schema_profile_unavailable = any(
        validation_issue.get("code") == "schema_profile_unavailable"
        for validation_issue in validation_issues
    )
    for validation_issue in validation_issues:
        if validation_issue.get("severity") in {"critical", "major"}:
            issues.append(dict(validation_issue))
    issues.extend(_minimum_delivery_issues(graph, requested_delivery_status))

    delivery_status = _delivery_status_from_issues(issues)
    ok = delivery_status == READY_STATUS
    limitations = _collect_limitations(graph) if ok else []
    disclosures = [SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE] if schema_profile_unavailable else []
    return {
        "ok": ok,
        "audit_status": "passed" if ok else ("blocked" if delivery_status == BLOCKED_STATUS else "failed"),
        "delivery_status": delivery_status,
        "allowed_delivery_statuses": [READY_STATUS] if ok else [],
        "disclosure_required": bool(disclosures),
        "disclosures": disclosures,
        "issue_count": len(issues),
        "issues": issues,
        "limitation_count": len(limitations),
        "limitations": limitations,
    }


def audit_file(path: Path, requested_delivery_status: str | None = None) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    try:
        graph = load_market_fixture(path)
    except Exception as exc:
        result = {
            "ok": False,
            "audit_status": "failed",
            "delivery_status": CORRECTION_STATUS,
            "allowed_delivery_statuses": [],
            "issue_count": 1,
            "issues": [issue("critical", "market_fixture_load_failed", f"Could not load market fixture: {exc}", str(path))],
            "limitation_count": 0,
            "limitations": [],
        }
        return None, result
    if not isinstance(graph, dict):
        result = {
            "ok": False,
            "audit_status": "failed",
            "delivery_status": CORRECTION_STATUS,
            "allowed_delivery_statuses": [],
            "issue_count": 1,
            "issues": [issue("critical", "market_graph_not_object", "Product market analysis graph must be a JSON object", "$")],
            "limitation_count": 0,
            "limitations": [],
        }
        return None, result
    return graph, audit_graph(graph, requested_delivery_status)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="ProductMarketAnalysisGraph JSON fixture")
    parser.add_argument("--requested-delivery-status", help="Override the delivery status being audited")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    path = Path(args.graph)
    _, result = audit_file(path, args.requested_delivery_status)
    result = dict(result)
    result["checked_file"] = str(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
