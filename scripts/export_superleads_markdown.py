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
import sys
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
    hold_contact_values,
    redact_delivery_sheets,
    redact_local_paths,
)
from validate_product_market_analysis import load_market_fixture
from validate_superleads_user_visible_output import validate as validate_user_visible_markdown

ROUTES = (
    "bulk_customer_development",
    "customer_background_research",
    "product_outbound_market_analysis",
)

MIN_TABLES = {
    "bulk_customer_development": 3,
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
    for raw, replacement in INTERNAL_REPLACEMENTS.items():
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
    candidate_rows: list[dict[str, Any]] = []
    for row in sheets.get("发现候选池", []):
        if not isinstance(row, dict):
            continue
        name = _safe_text(row.get("公司名称") or row.get("公司/线索名称") or row.get("候选客户") or row.get("说明"))
        signal = _first_nonempty(
            row.get("已观察业务/产品/应用信号"),
            row.get("业务/产品关联信号说明"),
            row.get("相关性依据"),
            "公开业务信号待确认",
        )
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
            "候选客户": name,
            "当前看到的业务信号": signal,
            "相关性状态": _first_nonempty(row.get("业务相关性"), row.get("方向状态"), "待确认"),
            "可用联系入口": contact_text,
            "还要确认什么": confirm,
            "来源 / 来源状态": source_text,
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

    source_rows: list[dict[str, Any]] = []
    for row in sheets.get("官网与来源链接", []):
        if not isinstance(row, dict):
            continue
        source_rows.append({
            "对象": _first_nonempty(row.get("公司/线索名称"), "候选线索"),
            "来源 / 来源状态": _first_nonempty(row.get("来源说明"), "公开入口待复核"),
            "链接": _safe_text(row.get("来源链接")),
        })

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
        ["候选客户", "当前看到的业务信号", "相关性状态", "可用联系入口", "还要确认什么", "来源 / 来源状态"],
        candidate_rows,
    )
    _append_table(lines, "待确认事项", ["对象", "待确认事项", "下一步", "状态"], pending_rows)
    _append_table(lines, "信息从哪里来", ["对象", "来源 / 来源状态", "链接"], source_rows)
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
    return {
        "问题": question,
        "当前看到什么": detail,
        "状态": conclusion,
        "业务上怎么用": "作为沟通前核验依据，不写成采购意愿或采购负责人已确认。",
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
            "公开看到的信号": _first_nonempty(row.get("我们看到的情况"), row.get("说明")),
            "可以怎么问": _first_nonempty(row.get("建议怎么切入"), "先问流程、负责部门和资料要求"),
            "状态": _first_nonempty(row.get("把握程度"), "待确认"),
            "不能推出什么": "不代表客户已有采购需求、采购量或采购决定。",
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
            "要注意的事": _first_nonempty(row.get("要注意的事"), row.get("说明")),
            "可能影响": _first_nonempty(row.get("可能影响"), "影响判断把握"),
            "建议动作": _first_nonempty(row.get("建议动作"), "人工核验后再使用"),
            "当前状态": _first_nonempty(row.get("目前状态"), row.get("状态"), "待确认"),
        })
    if not has_restricted:
        result.append({
            "要注意的事": "来源受限",
            "可能影响": "未打开或受限来源不能用来补公司事实。",
            "建议动作": "保留为待确认线索，补充可打开来源后再判断。",
            "当前状态": "待确认",
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
            "业务上怎么用": "只能把公开业务入口当作询问方向，不能写成正在采购。",
        },
        {
            "问题": "是否能直接找采购负责人",
            "当前看到什么": "公开人员、董事、Founder 或 Owner 线索不等于采购负责人。",
            "状态": "待确认",
            "业务上怎么用": "优先通过公开业务入口请求转接，不猜负责人。",
        },
    ])

    lines = [
        "# 单一客户背调",
        "",
    ]
    _append_table(lines, "一句话先说清", ["项目", "人话结论"], [{"项目": "当前判断", "人话结论": _background_target_text(scope, sheets)}])
    _append_table(lines, "客户一眼看懂", ["问题", "当前看到什么", "状态", "业务上怎么用"], overview_rows)
    _append_table(lines, "客户、品牌与关联方", ["名称", "它是什么", "和客户的关系", "目前把握", "我们依据什么"], sheets.get("客户、品牌与关联方", []))
    _append_table(lines, "公开业务信号与可沟通角度", ["公开看到的信号", "可以怎么问", "状态", "不能推出什么"], _background_business_rows(sheets.get("我们看到的业务机会", [])))
    contact_rows = [
        row for row in sheets.get("怎么联系、先找谁", [])
        if isinstance(row, dict) and "已隐藏联系方式" not in _safe_text(row.get("建议联系谁/哪里"))
    ]
    _append_table(lines, "怎么联系、先找谁", ["建议联系谁/哪里", "为什么先找这里", "联系时先问什么", "状态"], contact_rows)
    _append_table(lines, "跟进前要注意什么", ["要注意的事", "可能影响", "建议动作", "当前状态"], _background_caution_rows(sheets.get("跟进前要注意什么", [])))
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
    brief = _current_market_brief(graph)
    requested = {str(item) for item in ensure_list(brief, "analysis_modules_requested") if item}
    for module in PRODUCT_BASE_MODULES:
        if module not in requested and module not in seen:
            seen.add(module)
            modules.append(module)
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
    elif "先看贸易前提" not in text:
        text += "\n## 先看贸易前提\n\n本轮会把目标销售国家/地区、出口申报国、原产国 / 制造来源、实际起运地 / 起运港分开展示。\n"

    append_lines: list[str] = []
    not_executed = _market_not_executed_modules(graph)
    if "Google Trends" not in text:
        rows = [{
            "模块": "Google Trends 长期搜索趋势",
            "本轮状态": "未执行",
            "怎么理解": "Google Trends 只能作为相对搜索兴趣信号，不等于销量、GMV、进口量或真实采购需求。",
            "下一步": "如用户需要，后续按目标国家/地区和关键词单独查询。",
        }]
        _append_table(append_lines, "Google Trends / 长期搜索趋势", ["模块", "本轮状态", "怎么理解", "下一步"], rows)
    if "本轮未执行项" not in text or not_executed:
        rows = [{
            "未执行模块": PRODUCT_MODULE_LABELS.get(module, module),
            "状态": "未执行",
            "不能写成什么": "不能编造成趋势、价格、旺季或最新行情结论。",
        } for module in not_executed]
        if rows:
            _append_table(append_lines, "本轮未执行项补充", ["未执行模块", "状态", "不能写成什么"], rows)
    if "COO / 原产地证明" not in text:
        rows = [{
            "事项": "COO / 原产地证明",
            "当前状态": "待权威来源确认",
            "用户材料状态": "用户是否提供材料需单独记录",
            "不能写成什么": "不能因用户未提供 COO 就写“不需要”；也不能把 Production / Made in 直接写成 COO 文件。",
        }]
        _append_table(append_lines, "COO / 原产地证明", ["事项", "当前状态", "用户材料状态", "不能写成什么"], rows)
    if "海运拼箱" not in text or "国际快递" not in text:
        rows = [
            {
                "运输方式": "海运拼箱",
                "本轮状态": "待确认",
                "适用边界": "需看货物属性、包装、承运人/拼箱仓接受条件和目的港/CFS。",
                "不能写成什么": "不能写成唯一确定路线或固定交付日期。",
            },
            {
                "运输方式": "国际快递",
                "本轮状态": "待确认",
                "适用边界": "需看禁限运、申报价值、件数、账号和目的国清关规则。",
                "不能写成什么": "不能写成一定可走或固定到达日期。",
            },
        ]
        _append_table(append_lines, "运输方式补充：海运拼箱 / 国际快递", ["运输方式", "本轮状态", "适用边界", "不能写成什么"], rows)
    if "待补材料清单" not in text:
        _append_table(append_lines, "待补材料清单", ["待补材料/事项", "为什么要补", "向谁要", "状态"], _market_gap_rows(graph))
    if append_lines:
        text = text.rstrip() + "\n\n" + "\n".join(append_lines).rstrip() + "\n"
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
            resolved_for_route = raw
    actual_route = infer_route(resolved_for_route) if route == "auto" else route
    if actual_route == "product_outbound_market_analysis":
        graph = load_market_fixture(input_path)
        text, issues = build_product_market_markdown(graph)
    elif actual_route == "customer_background_research":
        text, issues = build_background_markdown(raw)
    elif actual_route == "bulk_customer_development":
        text, issues = build_bulk_markdown(raw)
    else:
        return None, [{"severity": "critical", "code": "markdown_delivery_unknown_route", "message": f"Unknown route: {route}", "path": "route"}], actual_route
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
        validation_issues = validate_user_visible_markdown(text, actual_route, min_tables=MIN_TABLES[actual_route])
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
