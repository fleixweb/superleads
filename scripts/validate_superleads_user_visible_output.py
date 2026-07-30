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
        "可优先人工跟进",
        "已排除 / 仅作参考",
        "联系方式汇总",
        "搜索覆盖与收敛",
        "风险与说明",
        "待确认",
    ],
    "customer_background_research": [
        "一句话先说清",
        "客户一眼看懂",
        "客户、品牌与关联方",
        "怎么联系、先找谁",
        "跟进前要注意什么",
        "信息从哪里来",
        "采购需求",
        "采购负责人",
        "待确认",
        "来源受限",
    ],
    "product_outbound_market_analysis": [
        "先看贸易前提",
        "目标销售国家/地区",
        "出口申报国",
        "原产国 / 制造来源",
        "实际起运地 / 起运港",
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
]

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
        window = text[max(0, match.start() - 36):match.start()].casefold()
        after_window = text[match.end():match.end() + 36].casefold()
        negated_before = any(marker.casefold() in window for marker in NEGATION_MARKERS)
        negated_after = any(marker.casefold() in after_window for marker in AFTER_NEGATION_MARKERS)
        if not (negated_before or negated_after):
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


def validate(text: str, route: str, *, min_tables: int = 3, extra_required: list[str] | None = None) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    required = ROUTE_REQUIRED.get(route)
    if required is None:
        return [_issue("user_visible_unknown_route", f"unknown route: {route}", route)]

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
        if _phrase_matches(text, phrase, allow_negated=True):
            issues.append(_issue("user_visible_value_judgment", f"value judgment present: {phrase}", phrase))

    for phrase in GENERIC_EVIDENCE_UPGRADES:
        if _phrase_matches(text, phrase, allow_negated=True):
            issues.append(_issue("user_visible_evidence_upgrade", f"evidence boundary upgrade present: {phrase}", phrase))

    if route in {"product_outbound_market_analysis", "bulk_customer_development"}:
        if not any(status in text for status in PRODUCT_USER_VISIBLE_STATUSES):
            message = "output must expose at least one Slice AE user-visible status"
            issues.append(_issue("user_visible_status_missing", message))
    if route == "product_outbound_market_analysis":
        for token in PRODUCT_INTERNAL_STATUS_TOKENS:
            if _phrase_matches(text, token):
                issues.append(_issue("user_visible_internal_status_token", f"internal product-market status token leaked: {token}", token))

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
