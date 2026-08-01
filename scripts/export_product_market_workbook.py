#!/usr/bin/env python3
"""Export ProductMarketAnalysisGraph as a safe CSV/Markdown workbook.

The exporter is deliberately boring: it does not research, complete, classify,
price, route, or rate anything.  It only moves already-reviewed
matrix_rows.user_visible_cells plus safe Gap/Conflict/Source notes into
human-readable tables.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _superleads_common import has_text, is_safe_public_http_url
from audit_product_market_analysis import audit_graph
from user_visible_status_projection import (
    humanize_enum_value,
    market_row_status_basis,
    project_base_status,
    project_market_row_status,
)
from validate_product_market_analysis import _looks_like_internal_leak, ensure_list, load_market_fixture

SHEET_COLUMNS: dict[str, list[str]] = {
    "市场事实总览": [
        "样本编号", "产品名称", "产品版本 / 型号", "目标销售国家/地区",
        "出口申报国（默认可改）", "原产国 / 制造来源（证据状态）",
        "实际起运地 / 起运港（待业务确认）", "卖方所在国/地区（如已知）",
        "目的节点（港口/机场/城市，如已知）", "已经有依据的信息", "还缺什么",
        "本轮状态", "依据状态", "依据说明", "资料观察日期", "边界说明",
    ],
    "产品档案与触发项": [
        "样本编号", "属性族", "属性", "当前值", "状态", "依据状态", "依据说明", "触发的核验路径",
        "来源/依据", "还缺什么 / 下一步核验", "不能推出什么",
    ],
    "长期需求与搜索趋势": [
        "样本编号", "关键词 / Topic", "语言 / 同义词", "国家/地区", "时间范围",
        "搜索类型 / 类目", "趋势状态", "指标口径", "数据日期", "状态", "依据状态", "依据说明",
        "来源/依据", "不能推出什么",
    ],
    "公开市场资料与行业信息": [
        "样本编号", "来源名称", "来源类型", "指标或主题", "可见内容", "时间范围",
        "地区", "状态", "依据状态", "依据说明", "来源 URL / 文件", "资料时效", "复核建议", "不能当最新结论", "不能推出什么",
    ],
    "线上市场与价格参考": [
        "样本编号", "渠道/平台", "产品/规格", "公开标价 / 价格参考", "币种",
        "税/运费/促销状态", "资料观察日期", "资料时效", "复核建议", "不能当最新结论", "状态", "依据状态", "依据说明", "来源 URL / 文件", "不能推出什么",
    ],
    "季节、节日与销售窗口": [
        "样本编号", "节点 / 窗口", "日期 / 周期", "国家/地区", "适用条件",
        "影响口径", "状态", "依据状态", "依据说明", "来源/依据", "资料时效", "复核建议", "不能当最新结论", "不能推出什么",
    ],
    "产品准入与合规要求": [
        "样本编号", "要求类别", "要求名称", "目标销售国家/地区",
        "原产国 / 出口国（不要混同）", "候选 HS/HTS（非最终归类）",
        "适用条件", "什么情况下需要", "可能接受的文件形式",
        "目标国是否要求原产地证明", "规则结论", "用户现在有没有可用材料", "用户材料状态", "目前依据",
        "资料时效", "复核建议", "不能当最新结论", "状态", "依据状态", "依据说明", "官方/优先依据",
        "来源身份", "适用范围", "可以当作什么", "不能当作什么", "权威性核实",
        "需要用户/供应链补什么", "不能写成什么", "边界说明",
    ],
    "进口税费": [
        "样本编号", "目的国", "候选 HS/HTS（非最终归类）", "税号描述", "税种",
        "税率/金额（非最终税额）", "适用条件", "计算税基", "资料时效", "复核建议", "不能当最新结论",
        "来源身份", "适用范围", "可以当作什么", "不能当作什么", "权威性核实", "状态", "依据状态", "依据说明",
        "来源/依据", "还缺什么 / 下一步核验",
    ],
    "出口国要求": [
        "样本编号", "出口申报国（默认可改）", "要求类别", "要求名称",
        "适用条件", "目前依据", "资料时效", "复核建议", "不能当最新结论",
        "来源身份", "适用范围", "可以当作什么", "不能当作什么", "权威性核实", "状态", "依据状态", "依据说明",
        "来源/依据", "还缺什么 / 下一步核验",
    ],
    "运输方式、路线、港口与申报节点": [
        "样本编号", "运输方式", "实际起运地 / 起运港（待业务确认）",
        "目的节点（港口/机场/城市，如已知）", "适用条件", "运输时间口径（常见区间/未执行）",
        "海关/承运人预申报", "订舱/截单节点", "资料时效", "复核建议", "不能当最新结论",
        "来源身份", "适用范围", "可以当作什么", "不能当作什么", "权威性核实", "状态", "依据状态", "依据说明", "来源/依据",
        "还缺什么 / 下一步核验",
    ],
    "近期外部因素": [
        "样本编号", "因素类型", "因素名称", "地区", "时间", "可能影响对象",
        "资料时效", "复核建议", "不能当最新结论", "状态", "依据状态", "依据说明", "来源/依据", "不能推出什么",
    ],
    "信息来源与待确认事项": [
        "样本编号", "来源编号", "来源名称", "来源类型", "URL / 文件名",
        "资料观察日期", "资料时效", "复核建议", "不能当最新结论", "支持字段", "状态", "依据状态", "依据说明", "待确认事项", "用户可见备注",
    ],
}

SHEET_ORDER = list(SHEET_COLUMNS)

STATUS_LABELS = {
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

CORROBORATION_STATUS_LABELS = {
    "multi_source_consistent": "多来源方向一致",
    "single_source_only": "可作为线索",
    "not_enough_independent_sources": "可作为线索",
    "conflict_present": "说法冲突待复核",
    "source_restricted": "来源受限",
    "not_executed": "本轮未执行",
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

AUTHORITY_LEVEL_LABELS = {
    "primary_official_authority": "主管官方来源",
    "official_service_or_portal": "官方服务/查询入口",
    "official_gazette_or_legal_database": "官方公报/法规库",
    "delegated_or_recognized_body": "被授权/认可机构",
    "intergovernmental_reference": "国际/政府间参考",
    "industry_or_professional_reference": "行业/专业参考",
    "commercial_market_reference": "商业/市场参考",
    "media_or_general_web_reference": "媒体/普通网页参考",
    "unknown_authority": "权威性未知",
}

AUTHORITY_ROLE_LABELS = {
    "destination_market": "目标销售国/地区",
    "import_customs": "进口海关",
    "export_declaration": "出口申报国",
    "origin_country": "原产国/制造来源",
    "departure_logistics": "实际起运地/物流节点",
    "transit": "中转地",
    "market_signal": "市场信号地区",
    "common_rule": "通用规则",
    "product_source": "产品原始来源",
    "global_or_international": "全球/国际口径",
    "unknown": "未知范围",
}

AUTHORITY_FACT_DOMAIN_LABELS = {
    "import_tax": "进口税费",
    "trade_remedy": "贸易救济",
    "certification_requirement": "认证/准入要求",
    "destination_requirement": "目标国准入要求",
    "origin_proof_requirement": "原产地证明 / COO",
    "export_requirement": "出口国要求",
    "export_control": "出口管制",
    "inspection_quarantine": "检验检疫",
    "dangerous_goods_transport": "危险品/锂电运输",
    "logistics_prefiling": "预申报/舱单要求",
    "logistics": "物流线索",
    "market_signal": "市场信号",
    "product_source": "产品来源",
}

ORIGIN_REQUIREMENT_LABELS = {
    "required": "目标国规则显示通常需要",
    "conditionally_required": "满足条件时需要（条件性需要，如优惠税率、海关要求、贸易救济等）",
    "normally_not_required": "当前场景通常不要求（普通进口通常不要求单独 COO）",
    "not_applicable": "本场景暂不适用",
    "unable_to_verify": "本轮未能核实目标国规则（未能用权威来源核实）",
}

ORIGIN_USER_MATERIAL_LABELS = {
    "user_provided_valid_for_scope": "用户已提供，范围初步匹配；仅限当前订单/批次/范围初步可用",
    "user_provided_needs_review": "用户已提供，需核对范围；仍需核验签章、编号、批次和适用范围",
    "user_not_provided_but_required": "当前未见用户材料，规则可能要求；用户未提供；若触发上述规则，需要补",
    "user_not_provided_and_not_required_for_current_scenario": "当前未见用户材料，且本场景暂未触发要求；用户未提供；当前场景通常不要求单独 COO",
    "user_material_status_unknown": "用户材料状态未知",
}

DESTINATION_REQUIREMENT_LABELS = {
    "required": "目标市场规则显示通常要求",
    "conditionally_required": "满足条件时要求",
    "normally_not_required": "当前场景通常不要求",
    "not_applicable": "本场景暂不适用",
    "unable_to_verify": "本轮未能核实目标市场规则",
    "not_executed": "本轮未核验此项",
}

CERTIFICATION_USER_MATERIAL_LABELS = {
    "user_material_not_requested_yet": "尚未向用户索取",
    "user_material_status_unknown": "用户材料状态未知",
    "user_not_provided_but_required": "当前未见用户材料，规则可能要求",
    "user_not_provided_and_not_required_for_current_scenario": "当前未见用户材料，且本场景暂未触发要求",
    "user_provided_needs_review": "用户已提供，需核对范围",
    "user_provided_valid_for_scope": "用户已提供，范围初步匹配",
    "user_provided_not_valid_for_scope": "用户已提供，但与本场景不匹配",
}

REQUIREMENT_FAMILY_LABELS = {
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

ORIGIN_EVIDENCE_LABELS = {
    "L0": "没有 SKU 级原产证据",
    "L1": "公开页面/产品资料线索",
    "L2": "供应商或业务文件线索",
    "L3": "订单/批次文件支持",
    "L4": "主管机关、海关或签证文件支持",
    "unknown": "证据等级未确认",
}

NOT_EXECUTED_MODULE_LABELS = {
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

SHEET_MODULE_KEYS = {
    "长期需求与搜索趋势": {"google_trends"},
    "线上市场与价格参考": {"online_price"},
    "季节、节日与销售窗口": {"season_holiday"},
    "近期外部因素": {"external_factors"},
    "公开市场资料与行业信息": {"market_reports"},
}

COLUMN_LABELS = {
    "样本ID": "样本编号",
    "产品版本/型号": "产品版本 / 型号",
    "目的国/地区": "目标销售国家/地区",
    "原产/制造来源": "原产国 / 制造来源（证据状态）",
    "出口申报国": "出口申报国（默认可改）",
    "实际起运地": "实际起运地 / 起运港（待业务确认）",
    "目的节点": "目的节点（港口/机场/城市，如已知）",
    "关键已核实": "已经有依据的信息",
    "关键缺口": "还缺什么",
    "总体状态": "本轮状态",
    "观察日期": "资料观察日期",
    "备注": "边界说明",
    "缺口/下一步": "还缺什么 / 下一步核验",
    "限制说明": "不能推出什么",
    "关键词/Topic": "关键词 / Topic",
    "语言/同义词": "语言 / 同义词",
    "搜索类型/类目": "搜索类型 / 类目",
    "来源URL/文件": "来源 URL / 文件",
    "价格": "公开标价 / 价格参考",
    "节点/窗口": "节点 / 窗口",
    "日期/周期": "日期 / 周期",
    "当前证据": "目前依据",
    "官方/优先来源": "官方/优先依据",
    "待补材料": "需要用户/供应链补什么",
    "禁止升级": "不能写成什么",
    "候选 HS/HTS": "候选 HS/HTS（非最终归类）",
    "税率/金额": "税率/金额（非最终税额）",
    "时间口径": "运输时间口径（常见区间/未执行）",
    "法定预申报": "海关/承运人预申报",
    "操作截点": "订舱/截单节点",
    "起运节点": "实际起运地 / 起运港（待业务确认）",
    "来源ID": "来源编号",
    "URL/文件名": "URL / 文件名",
    "原产地证明要求结论": "目标国是否要求原产地证明",
    "触发条件": "什么情况下需要",
    "可接受文件": "可能接受的文件形式",
    "用户材料状态": "用户现在有没有可用材料",
    "目标国认证/准入要求结论": "规则结论",
    "目标市场要求": "规则结论",
    "目标国要求": "规则结论",
    "目的国要求": "规则结论",
    "用户认证材料状态": "用户材料状态",
    "用户现有材料": "用户材料状态",
    "用户当前材料状态": "用户材料状态",
    "要求项": "要求名称",
    "用户现在要补什么": "需要用户/供应链补什么",
    "为什么可能需要": "适用条件",
    "原产国/制造来源": "原产国 / 制造来源（证据状态）",
    "原产国/出口国": "原产国 / 出口国（不要混同）",
}

BLOCKED_ACCESS = {"blocked", "login_wall", "login_required", "forbidden", "inaccessible", "not_accessed"}
ENUMISH_COLUMNS = {
    "状态",
    "本轮状态",
    "依据状态",
    "规则结论",
    "用户材料状态",
    "目标国是否要求原产地证明",
    "用户现在有没有可用材料",
    "要求类别",
}
INTERNAL_TERM_REPLACEMENTS = {
    "EvidenceCard": "证据记录",
    "SearchLog": "搜索结果记录",
    "MatrixRow": "矩阵信息行",
    "ClaimEvidence": "事实依据记录",
    "Claim": "事实记录",
}


def _status_label(value: Any) -> str:
    return STATUS_LABELS.get(str(value), str(value or "未提供"))


def _display_key(value: Any) -> str:
    text = str(value or "").strip()
    return COLUMN_LABELS.get(text, text)


def _replace_enum_tokens(text: str) -> str:
    replacements = {
        **STATUS_LABELS,
        **ORIGIN_REQUIREMENT_LABELS,
        **ORIGIN_USER_MATERIAL_LABELS,
        **DESTINATION_REQUIREMENT_LABELS,
        **CERTIFICATION_USER_MATERIAL_LABELS,
        **REQUIREMENT_FAMILY_LABELS,
        **FRESHNESS_STATUS_LABELS,
        **AUTHORITY_STATUS_LABELS,
        **AUTHORITY_LEVEL_LABELS,
    }
    result = text
    for raw, label in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(raw, label)
    return result


def _stringify(value: Any) -> str:
    if value is None:
        return "未提供"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_stringify(item) for item in value if item is not None and _stringify(item) != "未提供"]
        return "；".join(parts) if parts else "未提供"
    if isinstance(value, dict):
        parts = [f"{key}：{_stringify(val)}" for key, val in value.items() if val is not None]
        return "；".join(parts) if parts else "未提供"
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return text if text else "未提供"


def _safe_url(value: Any) -> str:
    url = _stringify(value)
    if url == "未提供":
        return "未提供"
    return url if is_safe_public_http_url(url) and not _looks_like_internal_leak(url) else "来源不适合导出"


def _safe_cell(value: Any) -> str:
    text = _stringify(value)
    if _looks_like_internal_leak(text):
        return "用户可见内容已隐藏"
    for raw, label in INTERNAL_TERM_REPLACEMENTS.items():
        text = re.sub(
            rf"(?<![A-Za-z0-9_-]){re.escape(raw)}(?![A-Za-z0-9_-])",
            label,
            text,
            flags=re.IGNORECASE,
        )
    return text


def _safe_human_enum_cell(value: Any) -> str:
    raw = _stringify(value)
    mapped = humanize_enum_value(raw)
    if mapped == raw:
        mapped = _replace_enum_tokens(raw)
    return _safe_cell(mapped)


def _safe_specific_enum_cell(value: Any, labels: dict[str, str]) -> str:
    raw = _stringify(value)
    result = raw
    for enum_value, label in sorted(labels.items(), key=lambda item: len(item[0]), reverse=True):
        result = result.replace(enum_value, label)
    return _safe_cell(result)


def _safe_export_cell(key: str, value: Any) -> str:
    safe_key = _display_key(key)
    if safe_key in ENUMISH_COLUMNS or str(key or "").strip() in ENUMISH_COLUMNS:
        return _safe_human_enum_cell(value)
    return _safe_cell(value)


def _corroboration_status_label(value: Any) -> str:
    return CORROBORATION_STATUS_LABELS.get(str(value), str(value or "未提供"))


def _first_sample_id(matrix_rows: list[dict[str, Any]]) -> str:
    for row in matrix_rows:
        cells = row.get("user_visible_cells")
        if not isinstance(cells, dict):
            continue
        for key in ("样本编号", "样本ID"):
            if has_text(cells.get(key)):
                return _safe_cell(cells.get(key))
    return "未提供"


def _current_run(graph: dict[str, Any]) -> dict[str, Any] | None:
    for run in reversed(ensure_list(graph, "runs")):
        if isinstance(run, dict):
            return run
    return None


def _current_brief(graph: dict[str, Any]) -> dict[str, Any] | None:
    run = _current_run(graph)
    if isinstance(run, dict) and has_text(run.get("brief_id")):
        for brief in ensure_list(graph, "briefs"):
            if isinstance(brief, dict) and brief.get("brief_id") == run.get("brief_id"):
                return brief
    for brief in reversed(ensure_list(graph, "briefs")):
        if isinstance(brief, dict):
            return brief
    return None


def _not_executed_modules(graph: dict[str, Any] | None) -> list[str]:
    if not isinstance(graph, dict):
        return []
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


def _module_label(module: str) -> str:
    return NOT_EXECUTED_MODULE_LABELS.get(module, module)


def _sheet_not_executed(sheet_name: str, graph: dict[str, Any] | None) -> bool:
    modules = set(_not_executed_modules(graph))
    return bool(modules & SHEET_MODULE_KEYS.get(sheet_name, set()))


def _origin_evidence_label(value: Any) -> str:
    return ORIGIN_EVIDENCE_LABELS.get(str(value), str(value or "证据状态未提供"))


def _brief_origin_note(graph: dict[str, Any]) -> str:
    brief = _current_brief(graph)
    origin = brief.get("origin_country_status") if isinstance(brief, dict) else None
    if isinstance(origin, dict) and has_text(origin.get("note")):
        return _safe_cell(origin.get("note"))
    return "正式原产地以订单、原产地文件、进口清关或主管机关口径确认"


def _format_origin_from_premise(premise: dict[str, Any], graph: dict[str, Any]) -> str:
    country = _safe_cell(premise.get("origin_country_or_region") or "待确认")
    evidence = _origin_evidence_label(premise.get("origin_evidence_level"))
    status = project_base_status(premise.get("status"))
    if country == "待确认":
        return f"待确认；{evidence}；状态：{status}"
    return f"{country}；{evidence}；状态：{status}；{_brief_origin_note(graph)}"


def _format_departure_from_premise(premise: dict[str, Any]) -> str:
    if has_text(premise.get("departure_node")):
        return _safe_cell(premise.get("departure_node"))
    country = premise.get("departure_country_or_region")
    if has_text(country):
        return f"{_safe_cell(country)}；具体港口/机场/场站待业务确认"
    return "待业务确认"


def _format_export_country_from_premise(premise: dict[str, Any], graph: dict[str, Any]) -> str:
    run = _current_run(graph)
    country = premise.get("export_declaration_country") or (run or {}).get("default_export_declaration_country")
    if not has_text(country):
        return "未提供"
    return f"{_safe_cell(country)}（本轮出口申报国；默认值可由用户设置）"


def _raw_export_country_from_premise(premise: dict[str, Any] | None, graph: dict[str, Any]) -> str:
    run = _current_run(graph)
    if isinstance(premise, dict) and has_text(premise.get("export_declaration_country")):
        return _safe_cell(premise.get("export_declaration_country"))
    if isinstance(run, dict) and has_text(run.get("default_export_declaration_country")):
        return _safe_cell(run.get("default_export_declaration_country"))
    return ""


def _origin_export_scope_for_preamble(premise: dict[str, Any] | None, graph: dict[str, Any]) -> str:
    export_country = _raw_export_country_from_premise(premise, graph)
    origin_country = ""
    if isinstance(premise, dict) and has_text(premise.get("origin_country_or_region")):
        origin_country = _safe_cell(premise.get("origin_country_or_region"))
    if export_country and origin_country:
        if export_country.strip().lower() == origin_country.strip().lower():
            return f"{export_country}（原产/出口口径；如实际不是该国家/地区可替换）"
        return f"出口申报国：{export_country}；原产/制造来源：{origin_country}（两者分开保留）"
    if export_country:
        return f"出口申报国：{export_country}；原产/制造来源待确认"
    if origin_country:
        return f"原产/制造来源：{origin_country}；出口申报国可按中国默认口径或用户口径设置"
    return "未提供；首轮可按中国默认出口口径启动，需向用户可见可改"


def _departure_scope_for_preamble(premise: dict[str, Any] | None) -> str:
    if isinstance(premise, dict) and has_text(premise.get("departure_node")):
        return _safe_cell(premise.get("departure_node"))
    if isinstance(premise, dict) and has_text(premise.get("departure_country_or_region")):
        return f"未指定具体港口/机场，本轮不猜（起运国家/地区：{_safe_cell(premise.get('departure_country_or_region'))}）"
    return "未指定，本轮不猜"


def _first_trade_premise(graph: dict[str, Any]) -> dict[str, Any] | None:
    for premise in ensure_list(graph, "trade_premises"):
        if isinstance(premise, dict):
            return premise
    return None


def _enrich_overview_row(exported: dict[str, str], graph: dict[str, Any]) -> None:
    premise = _first_trade_premise(graph)
    if not isinstance(premise, dict):
        return
    exported.setdefault("目标销售国家/地区", _safe_cell(premise.get("destination_country_or_region") or "未提供"))
    exported.setdefault("出口申报国（默认可改）", _format_export_country_from_premise(premise, graph))
    exported.setdefault("原产国 / 制造来源（证据状态）", _format_origin_from_premise(premise, graph))
    exported.setdefault("实际起运地 / 起运港（待业务确认）", _format_departure_from_premise(premise))
    exported.setdefault("卖方所在国/地区（如已知）", _safe_cell(premise.get("seller_country_or_region") or "未提供"))
    exported.setdefault("目的节点（港口/机场/城市，如已知）", _safe_cell(premise.get("destination_node") or "未提供"))
    exported.setdefault("本轮状态", project_base_status(premise.get("status")))
    exported.setdefault("依据状态", project_base_status(premise.get("status")))


def _trade_premise_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for premise in ensure_list(graph, "trade_premises"):
        if not isinstance(premise, dict):
            continue
        separation = premise.get("separation_check") if isinstance(premise.get("separation_check"), dict) else {}
        rows.append({
            "条目": "贸易前提拆分",
            "状态": project_base_status(premise.get("status")),
            "依据状态": project_base_status(premise.get("status")),
            "依据说明": "出口申报国、原产国/制造来源、实际起运地和目的国已分开记录；缺口仍需业务文件确认",
            "样本编号": sample_id,
            "目标销售国家/地区": _safe_cell(premise.get("destination_country_or_region") or "未提供"),
            "出口申报国（默认可改）": _format_export_country_from_premise(premise, graph),
            "原产国 / 制造来源（证据状态）": _format_origin_from_premise(premise, graph),
            "实际起运地 / 起运港（待业务确认）": _format_departure_from_premise(premise),
            "卖方所在国/地区（如已知）": _safe_cell(premise.get("seller_country_or_region") or "未提供"),
            "目的节点（港口/机场/城市，如已知）": _safe_cell(premise.get("destination_node") or "未提供"),
            "已经有依据的信息": "出口申报国、原产国/制造来源、实际起运地、目的国分开记录",
            "还缺什么": _safe_cell(premise.get("departure_node_basis") or "如涉及报关和运输，仍需订单/提单/订舱/报关文件确认"),
            "本轮状态": project_base_status(premise.get("status")),
            "边界说明": _safe_cell(separation.get("note") or "这些地理角色不能互相替代，也不能由工厂地址自动推出港口"),
        })
    return rows


def _is_origin_proof_row(row: dict[str, Any]) -> bool:
    return row.get("row_type") == "origin_proof_requirement" or isinstance(row.get("origin_proof_requirement"), dict)


def _is_certification_requirement_row(row: dict[str, Any]) -> bool:
    return row.get("row_type") in {"certification_requirement", "destination_requirement"} or isinstance(row.get("certification_requirement"), dict)


def _origin_proof_exported_row(
    row: dict[str, Any],
    corroboration_records: dict[str, dict[str, Any]] | None = None,
    freshness_records: dict[str, dict[str, Any]] | None = None,
    authority_ctx: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, str]:
    cells = row.get("user_visible_cells") if isinstance(row.get("user_visible_cells"), dict) else {}
    record = row.get("origin_proof_requirement") if isinstance(row.get("origin_proof_requirement"), dict) else {}
    requirement_value = cells.get("原产地证明要求结论") if has_text(cells.get("原产地证明要求结论")) else record.get("requirement_status")
    user_material_value = cells.get("用户材料状态") if has_text(cells.get("用户材料状态")) else record.get("user_material_status")
    origin_country = cells.get("原产国/出口国") or cells.get("原产国/制造来源") or record.get("origin_or_export_country")
    candidate_hs = cells.get("候选 HS/HTS") or record.get("candidate_hs_hts")
    exported = {
        "条目": _safe_cell(row.get("row_topic") or "原产地证明 / COO"),
        "样本编号": _safe_cell(record.get("sample_id") or cells.get("样本ID") or cells.get("样本编号")),
        "要求类别": _safe_cell(cells.get("要求类别") or "原产地证明 / COO"),
        "要求名称": _safe_cell(cells.get("要求名称") or "目标国原产地证明要求"),
        "目标销售国家/地区": _safe_cell(cells.get("目的国/地区") or record.get("target_country_or_region")),
        "原产国 / 出口国（不要混同）": _safe_cell(origin_country),
        "候选 HS/HTS（非最终归类）": _safe_cell(candidate_hs),
        "什么情况下需要": _safe_cell(record.get("trigger_conditions") or cells.get("触发条件")),
        "可能接受的文件形式": _safe_cell(record.get("acceptable_documents") or cells.get("可接受文件") or "未能核实"),
        "目标国是否要求原产地证明": _safe_specific_enum_cell(requirement_value, ORIGIN_REQUIREMENT_LABELS),
        "规则结论": _safe_specific_enum_cell(requirement_value, ORIGIN_REQUIREMENT_LABELS),
        "用户现在有没有可用材料": _safe_specific_enum_cell(user_material_value, ORIGIN_USER_MATERIAL_LABELS),
        "用户材料状态": _safe_specific_enum_cell(user_material_value, ORIGIN_USER_MATERIAL_LABELS),
        "目前依据": _safe_cell(cells.get("当前证据") or cells.get("目前依据")),
        "官方/优先依据": _safe_cell(cells.get("官方/优先来源") or cells.get("官方/优先依据")),
        "需要用户/供应链补什么": _safe_cell(cells.get("待补材料") or cells.get("需要用户/供应链补什么")),
        "不能写成什么": _safe_cell(cells.get("禁止升级") or cells.get("不能写成什么")),
        "边界说明": _safe_cell(record.get("limitation_note") or cells.get("边界说明")),
    }
    _apply_freshness_to_row(exported, row, freshness_records or {})
    _apply_corroboration_to_row(exported, row, corroboration_records or {})
    _apply_authority_to_row(exported, row, authority_ctx or {})
    _apply_status_projection(exported, row, freshness_records or {}, corroboration_records or {}, authority_ctx or {})
    return exported


def _observation_by_source(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for obs in ensure_list(graph, "observations"):
        if isinstance(obs, dict) and has_text(obs.get("source_id")):
            result.setdefault(str(obs["source_id"]), []).append(obs)
    return result


def _corroboration_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in ensure_list(graph, "corroboration_records"):
        if isinstance(record, dict) and has_text(record.get("corroboration_id")):
            result[str(record["corroboration_id"])] = record
    return result


def _freshness_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in ensure_list(graph, "freshness_records"):
        if isinstance(record, dict) and has_text(record.get("freshness_id")):
            result[str(record["freshness_id"])] = record
    return result


def _authority_profiles_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for profile in ensure_list(graph, "authority_profiles"):
        if isinstance(profile, dict) and has_text(profile.get("authority_profile_id")):
            result[str(profile["authority_profile_id"])] = profile
    return result


def _authority_verification_by_id(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in ensure_list(graph, "authority_verification_records"):
        if isinstance(record, dict) and has_text(record.get("authority_verification_id")):
            result[str(record["authority_verification_id"])] = record
    return result


def _authority_context(graph: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        "profiles": _authority_profiles_by_id(graph),
        "records": _authority_verification_by_id(graph),
    }


def _format_freshness(record: dict[str, Any]) -> dict[str, str]:
    status = FRESHNESS_STATUS_LABELS.get(str(record.get("freshness_status")), str(record.get("freshness_status") or "未提供"))
    window = record.get("review_window_days")
    window_text = f"复核窗口约 {window} 天" if isinstance(window, int) else "复核窗口未设"
    due = record.get("next_review_due_at")
    due_text = f"下次建议复核：{due}" if has_text(due) else "下次复核日期未设"
    next_steps = record.get("next_verification_steps") or due_text
    cannot = record.get("cannot_conclude") or "不能把未复核资料写成最新、现行或最终结论"
    return {
        "资料时效": _safe_cell(f"{status}；{window_text}；{record.get('user_visible_summary') or record.get('date_basis') or '未提供说明'}"),
        "复核建议": _safe_cell(next_steps),
        "不能当最新结论": _safe_cell(cannot),
    }


def _apply_freshness_to_row(exported: dict[str, str], row: dict[str, Any], freshness_records: dict[str, dict[str, Any]]) -> None:
    summaries: list[str] = []
    next_steps: list[str] = []
    cannot_latest: list[str] = []
    for record_id in ensure_list(row, "freshness_record_ids"):
        record = freshness_records.get(str(record_id))
        if not isinstance(record, dict):
            continue
        formatted = _format_freshness(record)
        summaries.append(formatted["资料时效"])
        next_steps.append(formatted["复核建议"])
        cannot_latest.append(formatted["不能当最新结论"])
    if summaries:
        exported["资料时效"] = "；".join(summaries)
    if next_steps:
        exported["复核建议"] = "；".join(next_steps)
    if cannot_latest:
        exported["不能当最新结论"] = "；".join(cannot_latest)


def _format_authority(record: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> dict[str, str]:
    profile = profiles.get(str(record.get("authority_profile_id") or ""), {})
    institution = profile.get("institution_name") or "来源机构未提供"
    jurisdiction = profile.get("jurisdiction_name") or "适用地区未提供"
    role = AUTHORITY_ROLE_LABELS.get(str(record.get("jurisdiction_role")), str(record.get("jurisdiction_role") or "未提供"))
    level = AUTHORITY_LEVEL_LABELS.get(str(profile.get("authority_level")), str(profile.get("authority_level") or "权威等级未提供"))
    status = AUTHORITY_STATUS_LABELS.get(str(record.get("verification_status")), str(record.get("verification_status") or "未提供"))
    domain = AUTHORITY_FACT_DOMAIN_LABELS.get(str(record.get("fact_domain")), str(record.get("fact_domain") or "未提供"))
    return {
        "来源身份": _safe_cell(f"{institution}；{level}"),
        "适用范围": _safe_cell(f"{jurisdiction} / {role} / {domain}"),
        "可以当作什么": _safe_cell(record.get("can_support") or "只能当该事实域的来源身份核实记录"),
        "不能当作什么": _safe_cell(record.get("cannot_support") or profile.get("known_limitations") or "不能当最终合规、最终税率或最终通关结论"),
        "权威性核实": _safe_cell(f"{status}；{record.get('verification_basis') or profile.get('authority_basis_summary') or '核实依据未提供'}"),
        "权威性下一步": _safe_cell(record.get("next_verification_steps") or "发货/申报前重新打开主管来源，并由对应专业方复核"),
    }


def _apply_authority_to_row(exported: dict[str, str], row: dict[str, Any], authority_ctx: dict[str, dict[str, dict[str, Any]]]) -> None:
    summaries: dict[str, list[str]] = {
        "来源身份": [],
        "适用范围": [],
        "可以当作什么": [],
        "不能当作什么": [],
        "权威性核实": [],
    }
    records = authority_ctx.get("records", {})
    profiles = authority_ctx.get("profiles", {})
    for record_id in ensure_list(row, "authority_verification_record_ids"):
        record = records.get(str(record_id))
        if not isinstance(record, dict):
            continue
        formatted = _format_authority(record, profiles)
        for key in summaries:
            summaries[key].append(formatted[key])
        if not has_text(exported.get("下一步核实")):
            exported["下一步核实"] = formatted["权威性下一步"]
    for key, values in summaries.items():
        if values:
            exported[key] = "；".join(values)


def _format_corroboration(record: dict[str, Any]) -> dict[str, str]:
    source_count = record.get("independent_source_count")
    status = _corroboration_status_label(record.get("corroboration_status"))
    count_text = f"{source_count} 个独立来源" if isinstance(source_count, int) else "独立来源数未提供"
    return {
        "多来源互证情况": _safe_cell(f"{status}；{count_text}；{record.get('user_visible_summary') or '未提供摘要'}"),
        "互证边界": _safe_cell(record.get("cannot_conclude") or "不能把多来源弱信号写成最终事实"),
        "下一步核实": _safe_cell(record.get("next_verification_steps") or "需要业务文件、权威来源或专业复核后再升级"),
    }


def _apply_corroboration_to_row(exported: dict[str, str], row: dict[str, Any], corroboration_records: dict[str, dict[str, Any]]) -> None:
    summaries: list[str] = []
    boundaries: list[str] = []
    next_steps: list[str] = []
    for record_id in ensure_list(row, "corroboration_record_ids"):
        record = corroboration_records.get(str(record_id))
        if not isinstance(record, dict):
            continue
        formatted = _format_corroboration(record)
        summaries.append(formatted["多来源互证情况"])
        boundaries.append(formatted["互证边界"])
        next_steps.append(formatted["下一步核实"])
    if summaries:
        exported["多来源互证情况"] = "；".join(summaries)
    if boundaries:
        exported["互证边界"] = "；".join(boundaries)
    if next_steps:
        exported["下一步核实"] = "；".join(next_steps)


def _apply_status_projection(
    exported: dict[str, str],
    row: dict[str, Any],
    freshness_records: dict[str, dict[str, Any]],
    corroboration_records: dict[str, dict[str, Any]],
    authority_ctx: dict[str, dict[str, dict[str, Any]]],
) -> None:
    authority_records = authority_ctx.get("records", {})
    user_status = project_market_row_status(
        row,
        freshness_records=freshness_records,
        corroboration_records=corroboration_records,
        authority_records=authority_records,
    )
    exported["依据状态"] = user_status
    exported["状态"] = user_status
    exported["依据说明"] = _safe_cell(
        market_row_status_basis(
            row,
            freshness_records=freshness_records,
            corroboration_records=corroboration_records,
            authority_records=authority_records,
        )
    )


def _certification_exported_row(
    row: dict[str, Any],
    corroboration_records: dict[str, dict[str, Any]] | None = None,
    freshness_records: dict[str, dict[str, Any]] | None = None,
    authority_ctx: dict[str, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, str]:
    cells = row.get("user_visible_cells") if isinstance(row.get("user_visible_cells"), dict) else {}
    record = row.get("certification_requirement") if isinstance(row.get("certification_requirement"), dict) else {}
    requirement_value = (
        cells.get("目标国认证/准入要求结论")
        or cells.get("目标市场要求")
        or cells.get("目标国要求")
        or cells.get("目的国要求")
        or record.get("applicability_status")
    )
    user_material_value = (
        cells.get("用户认证材料状态")
        or cells.get("用户材料状态")
        or cells.get("用户现有材料")
        or cells.get("用户当前材料状态")
        or record.get("user_material_status")
    )
    exported = {
        "条目": _safe_cell(row.get("row_topic") or record.get("requirement_name") or "目标国认证/准入要求"),
        "样本编号": _safe_cell(record.get("sample_id") or cells.get("样本ID") or cells.get("样本编号")),
        "要求类别": _safe_human_enum_cell(cells.get("要求类别") or record.get("requirement_family")),
        "要求名称": _safe_cell(cells.get("要求项") or cells.get("要求名称") or record.get("requirement_name")),
        "目标销售国家/地区": _safe_cell(cells.get("目的国/地区") or record.get("destination_country_or_region")),
        "候选 HS/HTS（非最终归类）": _safe_cell(cells.get("候选 HS/HTS") or record.get("candidate_hs_hts")),
        "适用条件": _safe_cell(cells.get("为什么可能需要") or record.get("trigger_conditions")),
        "什么情况下需要": _safe_cell(cells.get("触发条件") or record.get("trigger_conditions")),
        "可能接受的文件形式": _safe_cell(record.get("accepted_evidence_or_documents") or cells.get("可接受文件")),
        "规则结论": _safe_human_enum_cell(requirement_value),
        "用户材料状态": _safe_human_enum_cell(user_material_value),
        "用户现在有没有可用材料": _safe_human_enum_cell(user_material_value),
        "目前依据": _safe_cell(cells.get("来源状态") or cells.get("当前证据") or cells.get("目前依据")),
        "需要用户/供应链补什么": _safe_cell(cells.get("用户现在要补什么") or cells.get("待补材料") or cells.get("需要用户/供应链补什么")),
        "不能推出什么": _safe_cell(cells.get("不能推出什么") or record.get("cannot_conclude")),
        "不能写成什么": _safe_cell(cells.get("不能推出什么") or cells.get("禁止升级") or record.get("cannot_conclude")),
        "边界说明": _safe_cell(record.get("limitation_note") or cells.get("边界说明")),
    }
    _apply_freshness_to_row(exported, row, freshness_records or {})
    _apply_corroboration_to_row(exported, row, corroboration_records or {})
    _apply_authority_to_row(exported, row, authority_ctx or {})
    _apply_status_projection(exported, row, freshness_records or {}, corroboration_records or {}, authority_ctx or {})
    return exported


def _source_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    observations = _observation_by_source(graph)
    for idx, source in enumerate(ensure_list(graph, "sources"), start=1):
        if not isinstance(source, dict):
            continue
        source_observations = observations.get(str(source.get("source_id")), [])
        opened = any(obs.get("access_status") == "opened" for obs in source_observations if isinstance(obs, dict))
        restricted = any(str(obs.get("access_status") or "") in BLOCKED_ACCESS for obs in source_observations if isinstance(obs, dict))
        first_obs = next((obs for obs in source_observations if isinstance(obs, dict)), {})
        title = first_obs.get("title") if isinstance(first_obs, dict) else None
        observed_at = first_obs.get("observed_at") if isinstance(first_obs, dict) else None
        url = _safe_url(source.get("final_url") or source.get("canonical_url"))
        status = "来源受限" if restricted else ("已有明确依据" if opened else "可作为线索")
        rows.append({
            "条目": _safe_cell(title or f"公开来源 S{idx}"),
            "样本编号": sample_id,
            "来源编号": f"S{idx}",
            "来源名称": _safe_cell(title or source.get("publisher_relation") or source.get("medium") or "公开来源"),
            "来源类型": _safe_cell(source.get("medium") or "公开来源"),
            "URL / 文件名": url,
            "资料观察日期": _safe_cell(observed_at or "日期未见"),
            "资料时效": "来源表只显示观察日期；是否可当现行信息以对应矩阵行的资料时效为准",
            "复核建议": "法规、关税、价格、物流和外部因素应按对应字段复核窗口重新打开来源",
            "不能当最新结论": "不能仅凭来源列表或目录维护日期写成最新法规、最新税率、最新价格或最新行情",
            "支持字段": "来源本身仅作可追溯入口；具体支持字段以各矩阵行为准",
            "状态": status,
            "依据状态": status,
            "依据说明": "来源表只说明来源入口和观察情况；具体事实以对应矩阵行为准",
            "待确认事项": "无额外事项" if opened and not restricted else "需打开或复核原始来源",
            "用户可见备注": "不含本地路径、哈希或内部对象 ID",
        })
    return rows


def _gap_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, gap in enumerate(ensure_list(graph, "gaps"), start=1):
        if not isinstance(gap, dict):
            continue
        rows.append({
            "条目": _safe_cell(gap.get("field_name") or gap.get("missing_item") or f"待确认事项 G{idx}"),
            "样本编号": sample_id,
            "来源编号": f"G{idx}",
            "来源名称": _safe_cell(gap.get("missing_item") or gap.get("field_name") or "待确认事项"),
            "来源类型": "待确认事项",
            "URL / 文件名": "用户/供应链/专业方待提供",
            "资料观察日期": "日期未见",
            "资料时效": "待确认事项本身不是现行事实",
            "复核建议": "补齐材料或重新打开权威来源后再判断",
            "不能当最新结论": "不能把缺口行写成已满足、最新或最终结论",
            "支持字段": _safe_cell(" / ".join(str(item) for item in (gap.get("field_domain"), gap.get("field_name")) if has_text(item))),
            "状态": project_base_status(gap.get("status")),
            "依据状态": project_base_status(gap.get("status")),
            "依据说明": "待确认事项本身不是事实结论，补材料或复核来源后才能升级",
            "待确认事项": _safe_cell(gap.get("user_visible_note") or gap.get("missing_item") or "待确认"),
            "用户可见备注": _safe_cell(gap.get("requested_from") or "需补材料后复核"),
        })
    return rows


def _conflict_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, conflict in enumerate(ensure_list(graph, "conflicts"), start=1):
        if not isinstance(conflict, dict):
            continue
        rows.append({
            "条目": _safe_cell(conflict.get("field_name") or f"冲突待复核 C{idx}"),
            "样本编号": sample_id,
            "来源编号": f"C{idx}",
            "来源名称": _safe_cell(conflict.get("field_name") or "来源冲突"),
            "来源类型": "冲突待复核",
            "URL / 文件名": "见已打开来源；需人工复核",
            "资料观察日期": "日期未见",
            "资料时效": "来源冲突期间不能当现行结论",
            "复核建议": "重新打开原始来源，按更新日期、适用范围和权威等级复核",
            "不能当最新结论": "不能从冲突来源中挑一个直接写成最新或最终",
            "支持字段": _safe_cell(" / ".join(str(item) for item in (conflict.get("field_domain"), conflict.get("field_name")) if has_text(item))),
            "状态": project_base_status(conflict.get("status")),
            "依据状态": project_base_status(conflict.get("status")),
            "依据说明": "来源或口径存在冲突，需人工复核，不能强行合并为确定结论",
            "待确认事项": _safe_cell(conflict.get("summary") or "来源之间不一致，需复核"),
            "用户可见备注": "保留冲突，不强行合并为结论",
        })
    return rows


def build_sheets(graph: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    sheets: dict[str, list[dict[str, str]]] = {sheet: [] for sheet in SHEET_ORDER}
    matrix_rows = [row for row in ensure_list(graph, "matrix_rows") if isinstance(row, dict)]
    sample_id = _first_sample_id(matrix_rows)
    corroboration_records = _corroboration_by_id(graph)
    freshness_records = _freshness_by_id(graph)
    authority_ctx = _authority_context(graph)

    for row in matrix_rows:
        sheet_name = str(row.get("sheet_name") or "")
        if sheet_name not in sheets:
            continue
        if _is_origin_proof_row(row):
            exported = _origin_proof_exported_row(row, corroboration_records, freshness_records, authority_ctx)
            sheets[sheet_name].append(exported)
            continue
        if _is_certification_requirement_row(row):
            exported = _certification_exported_row(row, corroboration_records, freshness_records, authority_ctx)
            sheets[sheet_name].append(exported)
            continue
        cells = row.get("user_visible_cells")
        visible_cells = cells if isinstance(cells, dict) else {}
        exported: dict[str, str] = {"条目": _safe_cell(row.get("row_topic") or "未提供")}
        for key, value in visible_cells.items():
            if not has_text(key):
                continue
            safe_key = _safe_cell(_display_key(key))
            if safe_key == "用户可见内容已隐藏":
                continue
            exported[safe_key] = _safe_export_cell(safe_key, value)
        if sheet_name == "市场事实总览":
            _enrich_overview_row(exported, graph)
        _apply_freshness_to_row(exported, row, freshness_records)
        _apply_corroboration_to_row(exported, row, corroboration_records)
        _apply_authority_to_row(exported, row, authority_ctx)
        _apply_status_projection(exported, row, freshness_records, corroboration_records, authority_ctx)
        if "样本编号" in SHEET_COLUMNS[sheet_name] and not has_text(exported.get("样本编号")) and sample_id != "未提供":
            exported["样本编号"] = sample_id
        sheets[sheet_name].append(exported)

    trade_rows = _trade_premise_rows(graph, sample_id)
    if trade_rows:
        sheets["市场事实总览"][0:0] = trade_rows

    # The final sheet is explicitly allowed to include safe Source / Gap /
    # Conflict fields.  These rows do not introduce market facts; they expose
    # where the matrix came from and what remains to be checked.
    sheets["信息来源与待确认事项"].extend(_source_rows(graph, sample_id))
    sheets["信息来源与待确认事项"].extend(_gap_rows(graph, sample_id))
    sheets["信息来源与待确认事项"].extend(_conflict_rows(graph, sample_id))
    return sheets


def _headers_for_sheet(sheet_name: str, rows: list[dict[str, str]]) -> list[str]:
    base = ["条目"]
    for col in SHEET_COLUMNS[sheet_name]:
        if col not in base:
            base.append(col)
    if "状态" not in base:
        base.insert(1, "状态")
    for row in rows:
        for key in row:
            if key not in base:
                base.append(key)
    return base


def _brief_markdown_summary(graph: dict[str, Any]) -> list[str]:
    brief = _current_brief(graph)
    run = _current_run(graph)
    premise = _first_trade_premise(graph)
    if not isinstance(brief, dict) and not isinstance(premise, dict):
        return []
    destination = (
        premise.get("destination_country_or_region")
        if isinstance(premise, dict)
        else brief.get("target_country_or_region")
        if isinstance(brief, dict)
        else None
    )
    not_executed = _not_executed_modules(graph)
    origin_export_scope = _origin_export_scope_for_preamble(premise, graph)
    departure_scope = _departure_scope_for_preamble(premise)
    lines = [
        "## 先看贸易前提（本轮默认贸易口径）",
        "",
        "| 项目 | 本轮写法 | 对用户意味着什么 |",
        "| --- | --- | --- |",
        f"| 本轮默认贸易口径 | 原产/出口国：{_md_escape(origin_export_scope)}；目标市场：{_md_escape(destination or '未提供')} | 用最少输入先做市场、准入、税费、出口与物流分析；不是要求先补报关资料 |",
        f"| 实际起运港 | {_md_escape(departure_scope)} | 不影响首轮市场分析；正式订舱、申报或运输安排前再确认 |",
        "| 如果默认口径不对 | 直接告诉我实际出口国、原产国或目标市场，我会替换口径继续分析 | 适配非中国出口国、多国生产或转口贸易路径 |",
        "| 本轮结论边界 | 品类级 / 候选税号级分析；不输出最终归类、最终税率、已合规或可清关 | 保持不确定，但不停止研究 |",
        "",
    ]
    if not_executed:
        lines.extend([
            "## 本轮未执行项",
            "",
            "；".join(_md_escape(_module_label(module)) for module in not_executed) + "。",
            "",
            "这些项在表格里保留为“未执行”，不编造成趋势、价格、旺季或最新行情结论。",
            "",
        ])
    return lines


def _origin_proof_markdown_summary(sheets: dict[str, list[dict[str, str]]]) -> list[str]:
    rows = [
        row for row in sheets.get("产品准入与合规要求", [])
        if _safe_cell(row.get("要求类别")) == "原产地证明 / COO"
        or "原产地证明" in _safe_cell(row.get("条目"))
        or "COO" in _safe_cell(row.get("条目"))
    ]
    if not rows:
        return []
    headers = [
        "样本编号",
        "目标销售国家/地区",
        "原产国 / 出口国（不要混同）",
        "目标国是否要求原产地证明",
        "什么情况下需要",
        "用户现在有没有可用材料",
        "需要用户/供应链补什么",
        "不能写成什么",
    ]
    lines = [
        "## 原产地证明 / COO 怎么看",
        "",
        "这里先回答“目标国规则是否需要”，再回答“用户材料有没有准备”。用户没给 COO，不等于目标国不需要。",
        "",
        "| " + " | ".join(_md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
    lines.append("")
    return lines


def _freshness_markdown_summary(sheets: dict[str, list[dict[str, str]]]) -> list[str]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for sheet_name, sheet_rows in sheets.items():
        for row in sheet_rows:
            freshness = _safe_cell(row.get("资料时效"))
            if not has_text(freshness) or freshness == "未提供":
                continue
            key = (sheet_name, _safe_cell(row.get("条目")), freshness)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "表": sheet_name,
                "条目": _safe_cell(row.get("条目")),
                "资料时效": freshness,
                "复核建议": _safe_cell(row.get("复核建议")),
                "不能当最新结论": _safe_cell(row.get("不能当最新结论")),
            })
    if not rows:
        return []
    headers = ["表", "条目", "资料时效", "复核建议", "不能当最新结论"]
    lines = [
        "## 资料时效 / Freshness",
        "",
        "法规、关税、认证、价格、物流和近期外部因素都要看资料日期；旧资料或日期未见只能作参考，不能写成最新结论。",
        "",
        "| " + " | ".join(_md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows[:12]:
        lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
    lines.append("")
    return lines


def _authority_markdown_summary(sheets: dict[str, list[dict[str, str]]]) -> list[str]:
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for sheet_name, sheet_rows in sheets.items():
        for row in sheet_rows:
            authority = _safe_cell(row.get("权威性核实"))
            if not has_text(authority) or authority == "未提供":
                continue
            key = (sheet_name, _safe_cell(row.get("条目")), authority)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "表": sheet_name,
                "条目": _safe_cell(row.get("条目")),
                "来源身份": _safe_cell(row.get("来源身份")),
                "适用范围": _safe_cell(row.get("适用范围")),
                "可以当作什么": _safe_cell(row.get("可以当作什么")),
                "不能当作什么": _safe_cell(row.get("不能当作什么")),
                "权威性核实": authority,
            })
    if not rows:
        return []
    headers = ["表", "条目", "来源身份", "适用范围", "可以当作什么", "不能当作什么", "权威性核实"]
    lines = [
        "## 来源权威性 / Authority",
        "",
        "来源是否权威要看机构身份、事实域、管辖范围、可见身份核验证据和资料时效；Source Pack、搜索摘要、博客和多弱来源一致不能直接当官方结论。",
        "",
        "| " + " | ".join(_md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows[:12]:
        lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
    lines.append("")
    return lines


def _empty_sheet_note(sheet_name: str, graph: dict[str, Any] | None = None) -> str:
    if _sheet_not_executed(sheet_name, graph):
        return "本轮未执行；不形成趋势、价格、旺季或最新影响结论。"
    return "本表暂无矩阵行。"


def _safe_filename(index: int, sheet_name: str) -> str:
    return f"{index:02d}-{sheet_name}.csv"


def write_csv_sheets(sheets: dict[str, list[dict[str, str]]], output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    for index, sheet_name in enumerate(SHEET_ORDER, start=1):
        rows = sheets.get(sheet_name, [])
        headers = _headers_for_sheet(sheet_name, rows)
        filename = _safe_filename(index, sheet_name)
        path = output_dir / filename
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "未提供") for header in headers})
        generated.append({"sheet_name": sheet_name, "filename": filename, "row_count": len(rows)})
    return generated


def _md_escape(value: Any) -> str:
    text = _safe_cell(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def markdown_report(sheets: dict[str, list[dict[str, str]]], graph: dict[str, Any] | None = None) -> str:
    lines: list[str] = [
        "# 产品出海市场分析",
        "",
        "本报告只搬运已审核矩阵行和安全的来源/待确认字段；未执行、待确认和冲突项会保留显示。",
        "",
    ]
    if isinstance(graph, dict):
        lines.extend(_brief_markdown_summary(graph))
    lines.extend(_origin_proof_markdown_summary(sheets))
    lines.extend(_freshness_markdown_summary(sheets))
    lines.extend(_authority_markdown_summary(sheets))
    for sheet_name in SHEET_ORDER:
        rows = sheets.get(sheet_name, [])
        headers = _headers_for_sheet(sheet_name, rows)
        lines.append(f"## {sheet_name}")
        lines.append("")
        if not rows:
            lines.append(_empty_sheet_note(sheet_name, graph))
            lines.append("")
            continue
        lines.append("| " + " | ".join(_md_escape(header) for header in headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in rows:
            lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _scan_exported_files(files: list[Path]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _looks_like_internal_leak(line):
                issues.append({
                    "severity": "critical",
                    "code": "market_export_internal_leak",
                    "message": "Exported file leaks local path, hash, tokenized URL, or internal ID",
                    "path": f"{path.name}:{line_no}",
                })
    return issues


def export_graph(
    graph: dict[str, Any],
    output_dir: Path,
    markdown_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    audit = audit_graph(graph)
    if not audit.get("ok"):
        return {
            "ok": False,
            "stage": "audit",
            "audit": audit,
            "generated_files": [],
            "issue_count": audit.get("issue_count", 0),
            "issues": audit.get("issues", []),
        }

    sheets = build_sheets(graph)
    generated = write_csv_sheets(sheets, output_dir)
    written_paths = [output_dir / item["filename"] for item in generated]

    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown_report(sheets, graph), encoding="utf-8")
        generated.append({"sheet_name": "Markdown 报告", "filename": markdown_path.name, "row_count": None})
        written_paths.append(markdown_path)

    manifest: dict[str, Any] = {
        "ok": True,
        "route": "product_outbound_market_analysis",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "delivery_status": audit.get("delivery_status"),
        "audit_status": audit.get("audit_status"),
        "limitation_count": audit.get("limitation_count"),
        "files": generated,
        "notes": [
            "CSV/Markdown 只搬运已审核用户可见矩阵、来源、缺口和冲突字段。",
            "导出器不补税率、不猜港口、不生成趋势、价格、认证或物流结论。",
        ],
    }

    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        written_paths.append(manifest_path)

    leak_issues = _scan_exported_files(written_paths)
    if leak_issues:
        return {
            "ok": False,
            "stage": "post_export_scan",
            "audit": audit,
            "generated_files": generated,
            "issue_count": len(leak_issues),
            "issues": leak_issues,
        }

    return {
        "ok": True,
        "stage": "export",
        "delivery_status": audit.get("delivery_status"),
        "audit_status": audit.get("audit_status"),
        "limitation_count": audit.get("limitation_count"),
        "generated_files": generated,
        "issue_count": 0,
        "issues": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="ProductMarketAnalysisGraph JSON fixture")
    parser.add_argument("--output-dir", required=True, help="Directory for 12 CSV files")
    parser.add_argument("--format", choices=["csv"], default="csv")
    parser.add_argument("--markdown", help="Optional Markdown report path")
    parser.add_argument("--manifest", help="Optional manifest JSON path")
    args = parser.parse_args()

    try:
        graph = load_market_fixture(Path(args.graph))
    except Exception as exc:
        result = {
            "ok": False,
            "stage": "load",
            "issue_count": 1,
            "issues": [{
                "severity": "critical",
                "code": "market_fixture_load_failed",
                "message": f"Could not load market fixture: {exc}",
                "path": "graph",
            }],
            "generated_files": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result = export_graph(
        graph,
        Path(args.output_dir),
        Path(args.markdown) if args.markdown else None,
        Path(args.manifest) if args.manifest else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
