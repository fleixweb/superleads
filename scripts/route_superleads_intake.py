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
    "中东", "东南亚", "欧洲", "南美", "北美", "非洲",
    "united states", "usa", "u.s.", "america", "germany", "canada", "uk", "eu",
    "european union", "vietnam", "china", "japan", "korea", "australia", "mexico",
)
MARKET_TOPIC_MARKERS = (
    "产品出海市场分析", "出海市场", "分析市场", "市场分析", "出口要求", "进入门槛",
    "进入要求", "进口要求", "google trends", "淡旺季", "节假日", "外部因素",
)
MARKET_FACT_DOMAIN_MARKERS = (
    "趋势", "google trends", "公开价格", "价格区间", "价格带",
    "能不能做", "好不好卖", "市场怎么样", "风险", "风险判断",
    "淡旺季", "节假日", "认证", "标签要求", "包装要求", "准入", "关税", "税率",
    "进口税", "vat", "gst", "hts", "htsus", "hs code", "taric", "反倾销", "301",
    "物流", "运输", "海运", "空运", "快递", "铁路", "陆运", "散杂", "滚装", "清关",
    "sds", "un38.3", "un 38.3", "msds", "coo", "原产地证书", "原产地证明", "原产地证",
    "产地证", "certificate of origin", "proof of origin", "商检", "检验检疫", "检疫",
    "出口管制", "外部因素", "ce", "fcc", "fda", "ul", "etl", "rohs", "reach", "ukca",
    "cb", "saber", "saso", "eac", "ccc", "bis", "kc", "pse", "jis", "技术文件",
    "测试报告", "进口许可", "注册", "危险品", "锂电运输",
)
CUSTOMER_DEVELOPMENT_MARKERS = (
    "找客户", "找买家", "找进口商", "找采购商", "找经销商", "找批发商", "找零售商",
    "找代理商", "找渠道商", "开发客户", "开发市场", "开拓市场", "拓展市场",
    "客户名单", "买家名单", "进口商名单", "采购商名单", "经销商名单", "批发商名单",
    "零售商名单", "代理商名单",
    "leads", "lead list", "buyers", "importers", "prospects", "distributor",
    "distributors", "wholesaler", "wholesalers", "retailer", "retailers", "retail chains",
    "dealer", "dealers", "reseller", "resellers", "agent", "agents", "prospect list",
)
CUSTOMER_TYPE_MARKERS = (
    "客户", "买家", "进口商", "采购商", "经销商", "批发商", "零售商", "代理商",
    "渠道商", "分销商", "连锁", "维修商", "服务商", "零件渠道", "贸易商",
    "经销", "批发", "零售", "代理", "dealer", "distributor", "wholesaler",
    "retailer", "importer", "buyer", "reseller", "agent", "chain",
    "service company", "repair shop", "repair companies",
)
CUSTOMER_ACTION_MARKERS = (
    "找", "寻找", "开发", "开拓", "拓展", "拓客", "获客", "挖掘", "收集",
    "整理", "列出", "筛选", "给我一批", "给我找", "帮我找", "名单",
    "find", "source", "develop", "prospect", "list",
)
BACKGROUND_MARKERS = (
    "背调", "客户背调", "背景调查", "调查一下", "尽调", "due diligence", "background check",
    "靠不靠谱", "是否靠谱", "靠谱不靠谱", "真买家", "真实买家", "中间商", "背后的公司",
    "是谁", "公司是谁", "核实一下", "查一下", "查查", "查下",
)
SUBJECT_ANCHOR_MARKERS = (
    "这家公司", "这个公司", "该公司", "这个客户", "这个网站", "官网", "域名", "邮箱",
    "linkedin", "领英", "facebook", "instagram", "whatsapp", "网址", "网站",
)
TABLE_MARKERS = ("客户表", "客户名单表", "excel", "csv", "表格补全", "补全表格", "补全已有")
PRODUCT_MARKERS = (
    "产品", "型号", "电池", "锂电", "纺织", "衬衫", "面料", "化工", "农产品", "机械",
    "配件", "零件", "汽车配件", "户外家具", "柴油发电机", "发电机", "电水壶",
    "钢材", "粮食", "矿产", "水果", "蔬菜", "茶", "工装", "灯芯绒",
    "steel", "battery", "textile", "fabric", "shirt", "product", "parts",
    "accessories", "furniture", "generator", "kettle",
)
MARKET_QUESTION_OR_ANALYSIS_MARKERS = (
    "分析", "查", "查询", "核实", "确认", "判断", "看一下", "了解", "研究", "评估",
    "要不要", "需不需要", "是否需要", "需要什么", "需要哪些", "需要", "要求是什么",
    "有什么要求", "要什么文件", "还要什么文件", "怎么办", "到底要不要",
    "need", "needs", "require", "required", "requirement", "requirements",
)
NEGATED_CUSTOMER_PATTERNS = (
    r"(?:不|不要|不用|无需|先不|暂不|别)(?:帮我)?(?:再)?(?:找|开发|生成|整理|输出|给).{0,10}(?:客户|买家|进口商|采购商|经销商|批发商|零售商|代理商|客户名单|名单|leads)",
    r"(?:不生成|不要生成|不输出|不要输出|不做).{0,10}(?:客户名单|客户|买家|leads)",
    r"(?:不|不要|不用|无需|先不|暂不|别)(?:要|需要)?(?:帮我)?(?:再)?(?:做|进行|启动|安排)?(?:客户开发|找客户|找买家|找进口商|找采购商|找经销商|找批发商|找零售商|找代理商|客户名单|名单|leads)",
    r"(?:不|不要|不用|无需|先不|暂不|别)[^，,。；;！？!?\n]{0,24}(?:客户开发|找客户|找买家|找进口商|找采购商|找经销商|找批发商|找零售商|找代理商|客户名单|名单|leads)",
)
NEGATED_MARKET_PATTERNS = (
    r"(?:不|不要|不用|无需|先不|暂不|别)(?:做|分析|生成|整理|输出).{0,10}(?:市场分析|产品出海市场分析|准入分析|关税分析|认证分析)",
)
EXPLICIT_SPLIT_MARKERS = (
    "并分析", "再分析", "顺便分析", "同时分析", "另外分析", "分析一下", "市场分析",
    "产品出海市场分析", "顺便确认", "同时确认", "另外确认", "顺便查", "同时查",
    "并查", "再查", "关税和准入", "准入和关税",
)
EXPLICIT_MARKET_SCOPE_MARKERS = ("只做", "仅做", "只要", "仅要")
EXPLICIT_MARKET_SCOPE_LABELS = (
    ("准入", ("准入", "认证", "测试", "注册", "标签", "sds", "un38.3", "un 38.3", "ce", "ul", "fcc", "fda")),
    ("税费", ("关税", "税率", "税费", "进口税", "hts", "htsus", "hs code", "taric")),
    ("出口要求", ("出口文件", "出口报关", "商检", "检验检疫", "出口管制")),
    ("物流", ("物流", "运输", "海运", "空运", "快递", "清关", "预申报")),
)


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    haystack = norm(text)
    return any(marker.casefold() in haystack for marker in markers)


def _strip_patterns(text: str, patterns: tuple[str, ...]) -> str:
    result = norm(text)
    for pattern in patterns:
        result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip()


def _has_question_punctuation(text: str) -> bool:
    return any(token in text for token in ("?", "？", "吗", "么"))


def _has_concrete_subject_anchor(text: str) -> bool:
    low = norm(text)
    if re.search(r"https?://|www\.|[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", low):
        return True
    return contains_any(text, SUBJECT_ANCHOR_MARKERS)


def _has_customer_development_intent(text: str) -> bool:
    clean = _strip_patterns(text, NEGATED_CUSTOMER_PATTERNS)
    if not clean:
        return False
    if contains_any(clean, CUSTOMER_DEVELOPMENT_MARKERS):
        return True
    has_action = contains_any(clean, CUSTOMER_ACTION_MARKERS)
    has_type = contains_any(clean, CUSTOMER_TYPE_MARKERS)
    if has_action and has_type:
        return True
    if has_type and contains_any(clean, PRODUCT_MARKERS):
        return True
    # 外贸口语里“开发某某市场”常等于找该地区客户；只有同时问准入/税费/认证等，
    # 才拆成产品市场分析 + 后续客户开发。
    if re.search(r"(?:开发|开拓|拓展).{0,16}(?:市场|国家|地区)", clean):
        return True
    return False


def _has_background_intent(text: str) -> bool:
    if not contains_any(text, BACKGROUND_MARKERS):
        return False
    if _has_customer_development_intent(text):
        return False
    low = norm(text)
    if any(marker in low for marker in ("背调", "背景调查", "尽调", "due diligence", "background check")):
        return True
    return _has_concrete_subject_anchor(text)


def _has_market_intent(text: str) -> bool:
    clean = _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    if not clean:
        return False
    if "产品出海市场分析" in clean:
        return True
    if contains_any(clean, MARKET_TOPIC_MARKERS):
        return True
    fact = contains_any(clean, MARKET_FACT_DOMAIN_MARKERS)
    if not fact:
        return False
    has_question_or_analysis = contains_any(clean, MARKET_QUESTION_OR_ANALYSIS_MARKERS) or _has_question_punctuation(clean)
    if has_question_or_analysis:
        return True
    if contains_any(clean, PRODUCT_MARKERS) and contains_any(clean, COUNTRY_HINTS) and any(
        marker in clean for marker in ("出口", "进入", "进口", "销往", "卖到", "发到", "到")
    ):
        return True
    return False


def _looks_like_customer_attribute_request(text: str) -> bool:
    """Return true when compliance words describe the target customer type.

    Example: “找需要 UL 认证的进口商” means customer development with a
    compliance-related customer attribute, not a request to answer the
    destination-market UL requirement.
    """

    clean = _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    customer_type_pattern = r"(?:客户|买家|进口商|采购商|经销商|批发商|零售商|代理商|渠道商|分销商|维修商|贸易商|importers?|buyers?|distributors?|dealers?|retailers?|wholesalers?)"
    compliance_pattern = r"(?:认证|证书|准入|许可|合规|ce|ul|fcc|fda|rohs|reach|saber|saso|un38\.3|sds|msds)"
    if re.search(rf"(?:找|寻找|开发|筛选|list|find).{{0,18}}(?:需要|有|带|具备).{{0,24}}{compliance_pattern}.{{0,24}}{customer_type_pattern}", clean, re.IGNORECASE):
        return True
    if re.search(rf"(?:找|寻找|开发|筛选|list|find).{{0,18}}{compliance_pattern}.{{0,10}}(?:需求|资质).{{0,24}}{customer_type_pattern}", clean, re.IGNORECASE):
        return True
    return False


def _has_explicit_split_market_clause(text: str) -> bool:
    clean = _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    return contains_any(clean, EXPLICIT_SPLIT_MARKERS)


def _target_hint(text: str) -> str:
    low = norm(text)
    destination_verbs = ("出口到", "出口", "进入", "销往", "卖到", "发到", "运到", "到")
    for verb in destination_verbs:
        for country in COUNTRY_HINTS:
            if f"{verb}{country.casefold()}" in low:
                return country
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


def _explicit_market_scope_labels(text: str) -> list[str]:
    if not contains_any(text, EXPLICIT_MARKET_SCOPE_MARKERS):
        return []
    return [
        label
        for label, markers in EXPLICIT_MARKET_SCOPE_LABELS
        if contains_any(text, markers)
    ]


def _market_response(text: str, split_customer_development: bool) -> list[str]:
    product = _product_hint(text)
    target = _target_hint(text)
    export_country = _export_country_hint(text)
    scope_labels = _explicit_market_scope_labels(text)
    lines = [
        "我理解你要做的是：产品出海市场分析。",
        f"本轮对象：{product} → {target}。",
        f"默认出口申报国：{export_country}；原产国、起运地、最终税号和技术文件不足时会保留待确认。",
    ]
    if scope_labels:
        lines.append(
            f"本轮范围：{'、'.join(scope_labels)}；未点名模块不纳入本轮。"
            "不生成客户名单，也不判断是否值得进入。"
        )
    else:
        lines.append("我会整理趋势、公开价格参考、准入、税费、出口要求、物流和外部因素；不生成客户名单，也不判断是否值得进入。")
    if split_customer_development:
        lines.append("你提到找客户的部分建议放到第二阶段，等你看完市场分析后再单独启动批量客户开发。")
    if _has_concrete_subject_anchor(text) and re.search(r"https?://|www\.", text, re.IGNORECASE):
        lines.append("已识别到产品链接；本轮先把它作为产品资料线索，型号、规格和适用条件仍需从打开来源核对。")
    return lines


def classify(text: str) -> dict[str, Any]:
    has_customer_development = _has_customer_development_intent(text)
    has_background = _has_background_intent(text)
    has_table = contains_any(text, TABLE_MARKERS)
    has_product = contains_any(text, PRODUCT_MARKERS)
    has_country = contains_any(text, COUNTRY_HINTS)
    direct_market = "产品出海市场分析" in _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    market_intent = _has_market_intent(text)
    has_product_material = has_product or (market_intent and _has_concrete_subject_anchor(text))

    if has_background and not direct_market:
        missing_fields = [] if _has_concrete_subject_anchor(text) else ["target_subject"]
        return {
            "route": "customer_background_research",
            "next_skill": "researching-customer-background",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["customer_background_research"],
            "missing_fields": missing_fields,
            "response_lines": [
                "我理解你要做的是：客户背调报告。",
                "本轮会围绕你指定的公司/品牌/域名/材料做核验，不扩展成批量找客户。",
            ],
        }

    if has_table and has_customer_development and not direct_market:
        return {
            "route": "existing_table_enrichment",
            "next_skill": "scoping-lead-research",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["existing_table_enrichment"],
            "missing_fields": [],
            "response_lines": [
                "我理解你要处理的是：已有客户表格补全。",
                "本轮只围绕你提供的表格行/单元格补充，不自动创建新的客户开发方向。",
            ],
        }

    if market_intent and has_customer_development and not (
        _looks_like_customer_attribute_request(text) and not _has_explicit_split_market_clause(text)
    ):
        missing_fields: list[str] = []
        if not has_country:
            missing_fields.append("target_country_or_region")
        if not has_product_material:
            missing_fields.append("product_identity")
        return {
            "route": "product_outbound_market_analysis",
            "next_skill": "analyzing-product-outbound-market",
            "split_customer_development": True,
            "secondary_routes": ["bulk_customer_development"],
            "route_order": ["product_outbound_market_analysis", "bulk_customer_development"],
            "missing_fields": missing_fields,
            "response_lines": _market_response(text, True),
        }

    if has_customer_development and not direct_market:
        # Customer words have priority unless the user also asks for explicit
        # market/compliance/tax/logistics analysis; “找美国锂电池进口商客户”
        # is customer development, while “分析市场然后找客户” is split-stage.
        return {
            "route": "bulk_customer_development",
            "next_skill": "scoping-lead-research",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["bulk_customer_development"],
            "missing_fields": [] if has_product or has_country else ["product_or_scope"],
            "response_lines": [
                "我理解你要做的是：批量客户开发。",
                "我会先确认你卖什么、本次优先找什么、不纳入什么，以及用哪些公开信号判断。",
            ],
        }

    if direct_market or market_intent:
        missing_fields: list[str] = []
        if not has_country:
            missing_fields.append("target_country_or_region")
        if not has_product_material and not direct_market:
            missing_fields.append("product_identity")
        return {
            "route": "product_outbound_market_analysis",
            "next_skill": "analyzing-product-outbound-market",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["product_outbound_market_analysis"],
            "missing_fields": missing_fields,
            "response_lines": _market_response(text, False),
        }

    if has_customer_development:
        return {
            "route": "bulk_customer_development",
            "next_skill": "scoping-lead-research",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["bulk_customer_development"],
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
        "secondary_routes": [],
        "route_order": [],
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
