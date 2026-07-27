#!/usr/bin/env python3
"""Classify a Superleads user intake prompt into the first route.

This is a small deterministic guardrail for Skill routing.  It is not a
research engine and does not create a Brief, Candidate, Lead, or market graph.
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any

COUNTRY_HINTS = (
    "美国", "德国", "加拿大", "英国", "法国", "意大利", "西班牙", "越南", "中国", "日本",
    "韩国", "澳大利亚", "欧盟", "墨西哥", "巴西", "印度", "土耳其", "沙特", "阿联酋",
    "united states", "usa", "u.s.", "america", "germany", "canada", "uk", "eu",
    "european union", "vietnam", "china", "japan", "korea", "australia", "mexico",
)
MARKET_MARKERS = (
    "产品出海市场分析", "出海市场", "出口", "进入", "市场", "趋势", "google trends",
    "价格", "淡旺季", "节假日", "认证", "包装", "标签", "准入", "关税", "税率",
    "物流", "运输", "海运", "空运", "快递", "铁路", "陆运", "散杂", "滚装",
    "coo", "原产地证书", "原产地证明", "proof of origin", "商检", "检验检疫",
    "出口管制", "外部因素",
)
MARKET_FACT_DOMAIN_MARKERS = (
    "产品出海市场分析", "出海市场", "分析市场", "趋势", "google trends",
    "能不能做", "好不好卖", "市场怎么样",
    "价格", "淡旺季", "节假日", "认证", "包装", "标签", "准入", "关税", "税率",
    "物流", "运输", "海运", "空运", "快递", "铁路", "陆运", "散杂", "滚装",
    "coo", "原产地证书", "原产地证明", "proof of origin", "商检", "检验检疫",
    "出口管制", "外部因素",
)
CUSTOMER_MARKERS = (
    "找客户", "找买家", "找进口商", "开发客户", "客户名单", "买家名单", "进口商名单",
    "客户", "买家", "进口商", "采购商",
    "leads", "lead list", "buyers", "importers", "prospects",
)
BACKGROUND_MARKERS = (
    "背调", "客户背调", "背景调查", "调查一下", "尽调", "due diligence", "background check",
)
TABLE_MARKERS = ("客户表", "客户名单表", "excel", "csv", "表格补全", "补全表格", "补全已有")
PRODUCT_MARKERS = (
    "产品", "型号", "电池", "锂电", "纺织", "衬衫", "面料", "化工", "农产品", "机械",
    "steel", "battery", "textile", "fabric", "shirt", "product",
)


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    haystack = norm(text)
    return any(marker.casefold() in haystack for marker in markers)


def _target_hint(text: str) -> str:
    low = norm(text)
    for country in COUNTRY_HINTS:
        if country.casefold() in low:
            return country
    return "待确认目标国家/地区"


def _export_country_hint(text: str) -> str:
    low = norm(text)
    patterns = (
        ("越南", ("越南原产", "越南制造", "从越南", "越南出口")),
        ("中国", ("中国原产", "中国制造", "从中国", "按中国为默认出口国", "以中国为默认出口国")),
        ("土耳其", ("土耳其原产", "从土耳其")),
    )
    for country, markers in patterns:
        if any(marker in low for marker in markers):
            return country
    return "中国（默认，可修改）"


def _product_hint(text: str) -> str:
    stripped = text.strip()
    # Prefer the text before the first obvious destination phrase.  This is a
    # display hint only; formal product identity still belongs in the Brief.
    for sep in ("，", ",", "到", "出口", "进入"):
        if sep in stripped:
            candidate = stripped.split(sep, 1)[0].strip()
            previous = None
            while previous != candidate:
                previous = candidate
                candidate = re.sub(r"^(做一个|帮我|请|麻烦|分析|做|看一下)\s*", "", candidate).strip()
                candidate = re.sub(r"^产品出海市场分析[:：]?\s*", "", candidate).strip()
            if candidate:
                return candidate[:80]
    return stripped[:80] if stripped else "待确认产品"


def _market_response(text: str, split_customer_development: bool) -> list[str]:
    product = _product_hint(text)
    target = _target_hint(text)
    export_country = _export_country_hint(text)
    lines = [
        "我理解你要做的是：产品出海市场分析。",
        f"本轮对象：{product} → {target}。",
        f"默认出口申报国：{export_country}；原产国、起运地、最终税号和技术文件不足时会保留待确认。",
        "我会整理趋势、公开价格参考、准入、税费、出口要求、物流和外部因素；不生成客户名单，也不判断是否值得进入。",
    ]
    if split_customer_development:
        lines.append("你提到找客户的部分建议放到第二阶段，等你看完市场分析后再单独启动批量客户开发。")
    return lines


def classify(text: str) -> dict[str, Any]:
    has_market = contains_any(text, MARKET_MARKERS)
    has_customer = contains_any(text, CUSTOMER_MARKERS)
    has_background = contains_any(text, BACKGROUND_MARKERS)
    has_table = contains_any(text, TABLE_MARKERS)
    has_product = contains_any(text, PRODUCT_MARKERS)
    has_country = contains_any(text, COUNTRY_HINTS)
    direct_market = "产品出海市场分析" in text

    if has_background and not direct_market:
        return {
            "route": "customer_background_research",
            "next_skill": "researching-customer-background",
            "split_customer_development": False,
            "missing_fields": [],
            "response_lines": [
                "我理解你要做的是：客户背调报告。",
                "本轮会围绕你指定的公司/品牌/域名/材料做核验，不扩展成批量找客户。",
            ],
        }

    if has_table and has_customer and not direct_market:
        return {
            "route": "existing_table_enrichment",
            "next_skill": "scoping-lead-research",
            "split_customer_development": False,
            "missing_fields": [],
            "response_lines": [
                "我理解你要处理的是：已有客户表格补全。",
                "本轮只围绕你提供的表格行/单元格补充，不自动创建新的客户开发方向。",
            ],
        }

    if has_customer and not direct_market:
        # Customer words have priority unless the user also asks for explicit
        # market/compliance/tax/logistics analysis; “找美国锂电池进口商客户”
        # is customer development, while “分析市场然后找客户” is split-stage.
        if not contains_any(text, MARKET_FACT_DOMAIN_MARKERS):
            return {
                "route": "bulk_customer_development",
                "next_skill": "scoping-lead-research",
                "split_customer_development": False,
                "missing_fields": [] if has_product or has_country else ["product_or_scope"],
                "response_lines": [
                    "我理解你要做的是：批量客户开发。",
                    "我会先确认你卖什么、本次优先找什么、不纳入什么，以及用哪些公开信号判断。",
                ],
            }

    if direct_market or (has_market and (has_product or has_country)):
        missing_fields: list[str] = []
        if not has_country:
            missing_fields.append("target_country_or_region")
        if not has_product and not direct_market:
            missing_fields.append("product_identity")
        return {
            "route": "product_outbound_market_analysis",
            "next_skill": "analyzing-product-outbound-market",
            "split_customer_development": has_customer,
            "missing_fields": missing_fields,
            "response_lines": _market_response(text, has_customer),
        }

    if has_customer:
        return {
            "route": "bulk_customer_development",
            "next_skill": "scoping-lead-research",
            "split_customer_development": False,
            "missing_fields": [] if has_product or has_country else ["product_or_scope"],
            "response_lines": [
                "我理解你要做的是：批量客户开发。",
                "我会先确认你卖什么、本次优先找什么、不纳入什么，以及用哪些公开信号判断。",
            ],
        }

    return {
        "route": "unknown",
        "next_skill": "using-superleads",
        "split_customer_development": False,
        "missing_fields": ["task_intent"],
        "response_lines": [
            "我还不能确定你要做产品市场分析、找客户、客户背调，还是补全表格。",
            "请补一句你的目标：分析产品市场、找客户、背调某家公司，或补全已有客户表。",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="User intake prompt")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()
    print(json.dumps(classify(args.text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
