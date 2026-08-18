#!/usr/bin/env python3
"""Validate Superleads user-visible Markdown output samples.

This is a static guardrail for the three product routes. It checks the words
users see, not live source freshness or graph-level evidence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from superleads_user_guidance import SUPPORT_FOOTER_MARKER, has_exactly_one_final_footer


ROUTE_REQUIRED: dict[str, list[str]] = {
    "bulk_customer_development": [
        "我理解你卖的是",
        "本次优先找",
        "本次不纳入",
        "判断依据将重点看",
        "候选客户",
        "当前看到的业务信号",
        "业务相关性",
        "依据状态",
        "可用联系入口",
        "还要确认什么",
        "来源 / 来源状态",
        "候选池",
        "公开信号已匹配当前范围",
        "已排除 / 仅作参考",
        "联系方式汇总",
        "社媒与公开职业线索",
        "地图与经营地址",
        "第三方贸易摘要",
        "第三方贸易数据聚合站公开摘要，非官方海关记录",
        "搜索覆盖与收敛",
        "风险与说明",
        "待确认",
    ],
    "customer_background_research": [
        "一句话先说清",
        "客户一眼看懂",
        "客户、品牌与关联方",
        "公开业务信号与待核验事项",
        "公开联系入口与关联依据",
        "待核验事项与来源限制",
        "信息从哪里来",
        "采购需求",
        "采购负责人",
        "待确认",
        "来源受限",
    ],
    "product_outbound_market_analysis": [
        "先看贸易前提",
        "本轮默认贸易口径",
        "目标市场",
        "实际起运港",
        "如果默认口径不对",
        "本轮结论边界",
        "依据状态",
        "产品档案与触发项",
        "准入",
        "进口税费",
        "运输方式",
        "信息来源与待确认事项",
        "待确认",
        "不能",
    ],
}

ROUTE_FORBIDDEN: dict[str, list[str]] = {
    "bulk_customer_development": [
        "产品出海市场分析",
        "市场与准入信息矩阵",
        "客户背调报告",
        "推荐客户",
        "最佳客户",
        "采购概率",
    ],
    "customer_background_research": [
        "候选客户池",
        "批量客户开发",
        "产品出海市场分析",
        "推荐客户",
        "采购概率",
        "我们看到的业务机会",
        "公开业务信号与可沟通角度",
        "可以怎么问",
        "怎么联系、先找谁",
        "建议联系谁/哪里",
        "为什么先找这里",
        "联系时先问什么",
        "跟进前要注意什么",
        "建议动作",
    ],
    "product_outbound_market_analysis": [
        "候选客户池",
        "客户背调报告",
        "推荐客户",
        "目标客户群",
        "客户名单",
    ],
}

GENERIC_INTERNAL_LANGUAGE = [
    "EvidenceCard",
    "SearchLog",
    "MatrixRow",
    "ClaimEvidence",
    "Claim",
    "rule id",
    "run_id",
    "brief_id",
    "source_id",
    "observation_id",
    "claim_id",
    "graph",
    "eval",
    "card-",
    "gap-",
    "conflict-",
    "file://",
    "/home/",
    "/tmp/",
    "jsonschema",
    "openpyxl",
    "python3",
    "python.exe",
    "pip install",
    "venv",
    "Traceback",
    "ImportError",
    "ModuleNotFoundError",
    "解释器",
    "依赖缺失",
    "模块名",
]

GENERIC_VALUE_JUDGMENTS = [
    "推荐客户",
    "推荐市场",
    "最佳客户",
    "采购概率",
    "值得进入",
    "建议进入",
    "值得开发",
    "建议开发",
    "市场潜力高",
    "必然成交",
    "最佳路线",
    "最佳运输方式",
    "推荐报价",
    "推荐价格",
    "最终税率就是",
    "承诺交期",
    # User-visible delivery describes public evidence and open questions, not
    # which company the model thinks should be pursued.
    "重点开发",
    "推荐跟进",
    "暂不建议",
    "开发建议",
    "开发分层",
    "可优先人工跟进",
    "建议继续跟进",
    "建议继续了解",
    "重点跟进",
    "值不值得继续跟",
    "建议优先联系",
    "建议先联系",
    "建议联系这家公司",
    "继续跟进",
    "priority lead",
    "high priority prospect",
    "recommended follow-up",
    "recommend following up",
    "recommend contacting",
    "should follow up",
    "do not recommend pursuing",
    "worth pursuing",
    "worth developing",
    "development recommendation",
    "best prospect",
    "high-value lead",
    "worth continuing to follow up",
]

CHINESE_VALUE_JUDGMENT_TERMS = tuple(
    phrase for phrase in GENERIC_VALUE_JUDGMENTS if re.search(r"[\u4e00-\u9fff]", phrase)
)

GENERIC_EVIDENCE_UPGRADES = [
    "搜索摘要已核实",
    "搜索摘要就是事实",
    "搜索结果证明",
    "Google Trends 证明销量",
    "Google Trends 显示销量",
    "Google Trends 等于销量",
    "平台价就是成交价",
    "平台价就是批发价",
    "平台价就是推荐报价",
    "候选 HTSUS 就是最终归类",
    "候选税号就是最终税率",
    "证书入口证明已具备 UN38.3",
    "证书入口证明已具备 SDS",
    "网页标签已完全合规",
    "Production 等于 COO",
    "Production China 等于 COO",
    "Production Vietnam 等于 COO",
    "Made in 等于 COO",
    "董事是采购负责人",
    "董事就是采购负责人",
    "Founder 是采购负责人",
    "Founder 就是采购负责人",
    "Owner 是采购负责人",
    "Owner 就是采购负责人",
    "老板就是采购负责人",
    "采购负责人已确认",
    "已确认采购负责人",
    "已确认有采购需求",
    "确定有采购需求",
    "已确认采购意愿",
    "确认有采购意愿",
    "wholesale 页面说明有采购意愿",
    "contact 页面说明有采购意愿",
    "supplier portal 说明有采购意愿",
    "公开联系入口说明有采购意愿",
    "wholesale 入口说明正在采购",
    "从中国采购",
    "海关数据显示",
    "年进口量",
]

PRODUCT_USER_VISIBLE_STATUSES = [
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
]

PRODUCT_INTERNAL_STATUS_TOKENS = [
    "derived_calculation",
    "preliminary_reference",
    "business_confirmation_required",
    "technical_docs_required",
    "physical_verification_required",
    "professional_confirmation_required",
    "source_restricted",
    "not_executed",
    "not_applicable",
    "not_provided",
    "conflict_pending_review",
    "multi_source_consistent",
    "single_source_only",
    "not_enough_independent_sources",
    "conflict_present",
    "current_enough_for_scope",
    "date_unknown_recently_observed",
    "stale_needs_recheck",
    "date_unknown_needs_recheck",
    "not_time_sensitive",
    "verified_for_fact_domain",
    "candidate_needs_check",
    "secondary_reference_only",
    "unable_to_verify",
    "conflicting_identity",
    "conditionally_required",
    "normally_not_required",
    "unable_to_verify",
    "user_material_not_requested_yet",
    "user_material_status_unknown",
    "user_not_provided_but_required",
    "user_not_provided_and_not_required_for_current_scenario",
    "user_provided_needs_review",
    "user_provided_valid_for_scope",
    "user_provided_not_valid_for_scope",
]

BASIS_STATUS_INTERNAL_LEAK_VALUES = (
    "已观察",
    "未检索",
    "主体待确认",
    "已解析",
)
BASIS_STATUS_INTERNAL_COMPOSITES = (
    "已观察；需确认",
    "已观察；来源受限",
    "已观察；待确认",
    "已观察;需确认",
    "已观察;来源受限",
    "已观察;待确认",
)

NEGATION_MARKERS = (
    "不", "未", "非", "无", "勿", "禁止", "不得", "不能", "不可",
    "不是", "不等于", "无法", "不能推导", "不能替代", "不能写成", "不得写成",
    "not", "does not", "cannot", "can not", "must not", "should not", "no ",
)
AFTER_NEGATION_MARKERS = (
    "错误", "错误理解", "误解", "不成立", "不应", "不能", "不可", "不得",
    "不能推出", "不能据此", "并不", "并非", "not", "invalid", "wrong",
)

ENGLISH_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
BULK_SOURCE_RESTRICTED_MARKERS = (
    "来源受限",
    "需登录",
    "登录墙",
    "付费墙",
    "未打开",
    "未能打开",
    "只能看到片段",
    "摘要页",
    "目录详情页需登录",
    "403",
    "401",
    "429",
)


def _phrase_matches(text: str, phrase: str, *, allow_negated: bool = False) -> bool:
    """Match a phrase without hitting English substrings inside normal words.

    User-visible guardrails should catch leaked internal tokens such as
    ``graph`` and ``eval`` while leaving source names / words like
    ``The Telegraph``, ``Photograph``, ``paragraph`` and ``evaluation`` alone.
    For value judgments and evidence-upgrade phrases, compliant negated
    wording such as “不判断是否值得进入” should not fail the report.
    """
    if not phrase:
        return False
    if ENGLISH_TOKEN_RE.fullmatch(phrase):
        pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(phrase)}(?![A-Za-z0-9_-])", re.IGNORECASE)
        matches = list(pattern.finditer(text))
    else:
        matches = [match for match in re.finditer(re.escape(phrase), text, re.IGNORECASE)]
    if not allow_negated:
        return bool(matches)
    for match in matches:
        # Negation must live in the same visible line or sentence as the
        # phrase.  A later support footer says “请勿提交密码”, for example,
        # and must not excuse a positive recommendation immediately before it.
        before_break = max(
            text.rfind("\n", 0, match.start()),
            text.rfind("。", 0, match.start()),
            text.rfind("！", 0, match.start()),
            text.rfind("？", 0, match.start()),
            text.rfind("，", 0, match.start()),
            text.rfind(",", 0, match.start()),
            text.rfind(";", 0, match.start()),
        )
        after_candidates = [
            index for index in (
                text.find("\n", match.end()),
                text.find("。", match.end()),
                text.find("！", match.end()),
                text.find("？", match.end()),
                text.find("，", match.end()),
                text.find(",", match.end()),
                text.find(";", match.end()),
            ) if index >= 0
        ]
        after_break = min(after_candidates) if after_candidates else len(text)
        window = text[max(before_break + 1, match.start() - 36):match.start()].casefold()
        after_window = text[match.end():min(after_break, match.end() + 36)].casefold()
        negated_before = any(marker.casefold() in window for marker in NEGATION_MARKERS)
        negated_after = any(marker.casefold() in after_window for marker in AFTER_NEGATION_MARKERS)
        if not (negated_before or negated_after):
            return True
    return False


def _value_judgment_matches(text: str, phrase: str) -> bool:
    """Return true for a commercial judgment that is not a local boundary rule.

    A broad search for any earlier ``不``/``not`` let prose such as “公开信息
    不足但仍推荐跟进” evade the guardrail.  A negative boundary is allowed only
    when the negation directly governs the phrase in that same clause.
    """
    if ENGLISH_TOKEN_RE.fullmatch(phrase):
        pattern = re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(phrase)}(?![A-Za-z0-9_-])", re.IGNORECASE)
    else:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
    for match in pattern.finditer(text):
        line_start = text.rfind("\n", 0, match.start()) + 1
        sentence_start = max(
            line_start,
            text.rfind("。", line_start, match.start()) + 1,
            text.rfind("！", line_start, match.start()) + 1,
            text.rfind("？", line_start, match.start()) + 1,
            text.rfind("，", line_start, match.start()) + 1,
            text.rfind(",", line_start, match.start()) + 1,
            text.rfind("；", line_start, match.start()) + 1,
            text.rfind(";", line_start, match.start()) + 1,
            text.rfind(".", line_start, match.start()) + 1,
            text.rfind("!", line_start, match.start()) + 1,
            text.rfind("?", line_start, match.start()) + 1,
        )
        prefix = text[sentence_start:match.start()].casefold()
        chinese_terms = "|".join(re.escape(term) for term in CHINESE_VALUE_JUDGMENT_TERMS)
        chinese_boundary = (
            re.search(
                r"(?:(?:也|仍|都)?不替用户|(?:也|仍|都)?不(?:做|作|给|提供|产生|生成|写成)|(?:也|仍|都)?不能(?:作为|用于|证明|写成)?|(?:也|仍|都)?不得(?:作为|用于|写成)?|不(?:做|作)?判断\s*是否|不决定\s*是否)\s*$",
                prefix,
            )
            or re.search(
                rf"(?:不(?:做|作|给|提供|产生|生成|写成)|不能(?:作为|用于|证明|写成)|不得(?:作为|用于|写成))(?:(?:{chinese_terms})|[、或和及与\s])*$",
                prefix,
            )
        )
        english_boundary = re.search(
            r"(?:superleads|this assistant)\s+(?:does not|do not)\s+(?:decide|judge)\s+(?:whether\s+)?(?:it\s+is\s+)?$|(?:superleads|this assistant)\s+(?:does not|do not)\s+$",
            prefix,
        )
        if not (chinese_boundary or english_boundary):
            return True
    return False


def _count_markdown_tables(text: str) -> int:
    lines = text.splitlines()
    count = 0
    for index in range(len(lines) - 1):
        line = lines[index].strip()
        next_line = lines[index + 1].strip()
        if line.startswith("|") and line.endswith("|") and re.match(r"^\|[\s:\-|]+\|$", next_line):
            count += 1
    return count


def _issue(code: str, message: str, value: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if value is not None:
        payload["value"] = value
    return payload


def _split_markdown_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    body = stripped[1:-1]
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in body:
        if char == "|" and not escaped:
            cells.append("".join(current).strip().replace("\\|", "|"))
            current = []
            escaped = False
            continue
        current.append(char)
        escaped = (char == "\\" and not escaped)
        if char != "\\":
            escaped = False
    cells.append("".join(current).strip().replace("\\|", "|"))
    return cells


def _is_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("|") and stripped.endswith("|") and re.fullmatch(r"\|[\s:\-|]+\|", stripped) and "---" in stripped)


def _bulk_basis_status_consistency_issues(text: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines) - 1:
        if not (lines[index].strip().startswith("|") and _is_table_separator(lines[index + 1])):
            index += 1
            continue
        headers = _split_markdown_row(lines[index])
        if "业务相关性" not in headers or "依据状态" not in headers:
            index += 2
            continue
        relevance_index = headers.index("业务相关性")
        basis_index = headers.index("依据状态")
        row_index = index + 2
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            if _is_table_separator(lines[row_index]):
                row_index += 1
                continue
            cells = _split_markdown_row(lines[row_index])
            if len(cells) > max(relevance_index, basis_index):
                basis = cells[basis_index]
                row_text = " | ".join(cells)
                has_restricted_marker = any(marker in row_text for marker in BULK_SOURCE_RESTRICTED_MARKERS)
                negated_restricted = any(marker in row_text for marker in ("无来源受限", "未记录明显受限来源"))
                if basis == "已有明确依据" and has_restricted_marker and not negated_restricted:
                    issues.append(_issue(
                        "bulk_basis_status_source_restricted_promoted",
                        "bulk row with source-restricted material must not project basis status as 已有明确依据",
                        cells[relevance_index],
                    ))
            row_index += 1
        index = row_index
    return issues


def _is_internal_basis_status(value: str) -> bool:
    normalized = re.sub(r"\s+", "", value.strip())
    if not normalized:
        return False
    if any(composite in normalized for composite in BASIS_STATUS_INTERNAL_COMPOSITES):
        return True
    return any(token in normalized for token in BASIS_STATUS_INTERNAL_LEAK_VALUES)


def _basis_status_internal_leak_issues(text: str) -> list[dict[str, str]]:
    """Catch internal signal/status labels leaked into user-facing 依据状态.

    The frozen Slice AE status words are the only user-facing basis-status
    vocabulary.  Real-business UAT showed Agents hand-writing reports with
    ``依据状态 = 已观察`` after looking at public signal status columns.  That
    must fail even if the rest of the report looks plausible.
    """
    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    def add_issue(value: str) -> None:
        compact = re.sub(r"\s+", " ", value.strip())
        if not compact or compact in seen:
            return
        seen.add(compact)
        issues.append(_issue(
            "user_visible_basis_status_internal_leak",
            "依据状态 must use Slice AE user-visible status words, not internal public-signal status labels",
            compact,
        ))

    lines = text.splitlines()
    index = 0
    while index < len(lines) - 1:
        if not (lines[index].strip().startswith("|") and _is_table_separator(lines[index + 1])):
            index += 1
            continue
        headers = _split_markdown_row(lines[index])
        basis_indexes = [pos for pos, header in enumerate(headers) if header == "依据状态"]
        row_index = index + 2
        while row_index < len(lines) and lines[row_index].strip().startswith("|"):
            if _is_table_separator(lines[row_index]):
                row_index += 1
                continue
            cells = _split_markdown_row(lines[row_index])
            for basis_index in basis_indexes:
                if len(cells) > basis_index and _is_internal_basis_status(cells[basis_index]):
                    add_issue(cells[basis_index])
            for cell_index, cell in enumerate(cells[:-1]):
                if cell == "依据状态" and _is_internal_basis_status(cells[cell_index + 1]):
                    add_issue(cells[cell_index + 1])
            row_index += 1
        index = row_index

    for line in lines:
        match = re.match(r"^\s*(?:[-*]\s*)?依据状态\s*[:：]?\s+(.+?)\s*$", line)
        if match and _is_internal_basis_status(match.group(1)):
            add_issue(match.group(1))
    return issues


def validate(text: str, route: str, *, min_tables: int = 3, extra_required: list[str] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ROUTE_REQUIRED.get(route)
    if required is None:
        return [_issue("user_visible_unknown_route", f"unknown route: {route}", route)]
    if route == "product_outbound_market_analysis" and "本轮范围：" in text:
        # A scoped report names both the selected scope and the modules not
        # executed this round. It still renders only fixed tables plus the
        # selected modules.
        required = [
            "本轮范围：",
            "本轮未执行：",
            "依据状态",
            "产品档案与触发项",
            "信息来源与待确认事项",
            "待确认",
            "不能",
        ]

    table_count = _count_markdown_tables(text)
    if table_count < min_tables:
        issues.append(_issue("user_visible_not_markdown_table", f"expected at least {min_tables} markdown tables, got {table_count}", str(table_count)))

    for phrase in required + list(extra_required or []):
        if phrase not in text:
            issues.append(_issue("user_visible_missing_required_text", f"missing required phrase: {phrase}", phrase))

    for phrase in ROUTE_FORBIDDEN.get(route, []):
        if _phrase_matches(text, phrase, allow_negated=True):
            issues.append(_issue("user_visible_route_crossed", f"route-forbidden phrase present: {phrase}", phrase))

    for phrase in GENERIC_INTERNAL_LANGUAGE:
        if _phrase_matches(text, phrase):
            issues.append(_issue("user_visible_internal_language", f"internal language leaked: {phrase}", phrase))

    for phrase in GENERIC_VALUE_JUDGMENTS:
        if _value_judgment_matches(text, phrase):
            issues.append(_issue("user_visible_value_judgment", f"value judgment present: {phrase}", phrase))

    for phrase in GENERIC_EVIDENCE_UPGRADES:
        if _phrase_matches(text, phrase, allow_negated=True):
            issues.append(_issue("user_visible_evidence_upgrade", f"evidence boundary upgrade present: {phrase}", phrase))

    if route in {"product_outbound_market_analysis", "bulk_customer_development"}:
        if not any(status in text for status in PRODUCT_USER_VISIBLE_STATUSES):
            message = "output must expose at least one Slice AE user-visible status"
            issues.append(_issue("user_visible_status_missing", message))
    issues.extend(_basis_status_internal_leak_issues(text))
    if route == "bulk_customer_development":
        issues.extend(_bulk_basis_status_consistency_issues(text))
    if route == "product_outbound_market_analysis":
        for token in PRODUCT_INTERNAL_STATUS_TOKENS:
            if _phrase_matches(text, token):
                issues.append(_issue("user_visible_internal_status_token", f"internal product-market status token leaked: {token}", token))

    footer_count = text.count(SUPPORT_FOOTER_MARKER)
    if footer_count == 0:
        issues.append(_issue("user_visible_support_footer_missing", "final delivery must include the Superleads support and security footer"))
    elif footer_count != 1 or not has_exactly_one_final_footer(text):
        issues.append(_issue("user_visible_support_footer_duplicated", "final delivery must include one complete terminal support and security footer"))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("--route", required=True, choices=sorted(ROUTE_REQUIRED))
    parser.add_argument("--min-tables", type=int, default=3)
    parser.add_argument("--must-contain", action="append", default=[])
    parser.add_argument("--format", choices=["json", "text"], default="json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = args.markdown.read_text(encoding="utf-8")
    issues = validate(text, args.route, min_tables=args.min_tables, extra_required=list(args.must_contain))
    payload: dict[str, Any] = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route": args.route,
        "markdown": str(args.markdown),
        "table_count": _count_markdown_tables(text),
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("ok" if payload["ok"] else "\n".join(f"{item['code']}: {item['message']}" for item in issues))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
