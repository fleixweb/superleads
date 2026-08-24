#!/usr/bin/env python3
"""Classify a Superleads user intake prompt into the first route.

This is a small deterministic guardrail for Skill routing.  It is not a
research engine and does not create a Brief, Candidate, Lead, or market graph.
"""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import Any

from superleads_user_guidance import static_help_response
from superleads_composite_tasks import plan_composite_task
from superleads_task_modes import (
    classify_task_mode,
    detect_language,
    is_export_help_request,
    is_status_request,
    metadata_response,
)

COUNTRY_HINTS = (
    "美国", "德国", "加拿大", "英国", "法国", "意大利", "西班牙", "越南", "中国", "日本",
    "韩国", "澳大利亚", "欧盟", "墨西哥", "巴西", "印度", "土耳其", "沙特", "阿联酋",
    "中东", "东南亚", "欧洲", "南美", "北美", "非洲", "爱尔兰",
    "united states", "usa", "u.s.", "america", "germany", "canada", "uk", "eu",
    "european union", "vietnam", "china", "japan", "korea", "australia", "mexico", "ireland",
)
MARKET_TOPIC_MARKERS = (
    "产品出海市场分析", "出海市场", "分析市场", "市场分析", "出口要求", "进入门槛",
    "进入要求", "进口要求", "google trends", "淡旺季", "节假日", "外部因素",
)
MARKET_FACT_DOMAIN_MARKERS = (
    "趋势", "google trends", "公开价格", "价格区间", "价格带",
    "能不能做", "好不好卖", "市场怎么样", "风险", "风险判断",
    "淡旺季", "节假日", "认证", "标签要求", "包装要求", "准入", "关税", "税率",
    "进口税", "vat", "gst", "hts", "htsus", "hs code", "taric", "tariff", "tariffs", "duty", "anti-dumping", "反倾销", "301",
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
    "正式开发名单",
)
CUSTOMER_TYPE_MARKERS = (
    "客户", "买家", "进口商", "采购商", "经销商", "批发商", "零售商", "代理商",
    "渠道商", "分销商", "连锁", "维修商", "服务商", "零件渠道", "贸易商",
    "经销", "批发", "零售", "代理", "dealer", "distributor", "wholesaler",
    "retailer", "importer", "buyer", "reseller", "agent", "chain",
    "service company", "repair shop", "repair companies",
)
TERSE_CUSTOMER_TYPE_MARKERS = (
    "买家", "进口商", "采购商", "经销商", "批发商", "零售商", "代理商",
    "渠道商", "分销商", "连锁", "维修商", "服务商", "零件渠道", "贸易商",
    "dealer", "distributor", "wholesaler", "retailer", "importer", "buyer",
    "reseller", "agent", "chain", "service company", "repair shop", "repair companies",
)
CUSTOMER_ACTION_MARKERS = (
    "找", "寻找", "开发", "开拓", "拓展", "拓客", "获客", "挖掘", "收集",
    "整理", "列出", "筛选", "给我一批", "给我找", "帮我找", "名单",
    "find", "source", "develop", "prospect", "list",
)
EXPLICIT_DISCOVERY_ACTION_MARKERS = (
    "找", "寻找", "开发", "开拓", "拓展", "拓客", "获客", "挖掘", "收集",
    "find", "source", "develop", "prospect",
)
BACKGROUND_MARKERS = (
    "背调", "客户背调", "背景调查", "调查", "尽调", "due diligence", "background check",
    "full report", "deep background check",
    "背景",
    "靠不靠谱", "是否靠谱", "靠谱不靠谱", "真买家", "真实买家", "中间商", "背后的公司",
    "是谁", "公司是谁", "核实一下", "查一下", "查查", "查下",
)
SUBJECT_ANCHOR_MARKERS = (
    "这家公司", "这个公司", "该公司", "这个客户", "这个网站", "官网", "域名", "邮箱",
    "linkedin", "领英", "facebook", "instagram", "whatsapp", "网址", "网站",
)
TABLE_MARKERS = (
    "客户表", "客户名单表", "excel", "csv", "表格补全", "补全表格", "补全已有",
    "client list", "client table", "customer list", "customer table",
    "attached client", "attached customer", "attached list", "attached table",
)
CONTACT_REQUEST_MARKERS = ("联系人", "联系方式", "公开邮箱", "邮箱", "电话", "contact", "email", "phone")
EXPORT_REQUEST_MARKERS = ("导出", "export")
FEEDBACK_CORRECTION_MARKERS = ("不符合要求", "不符合", "这个候选不对", "纠正", "does not match", "not suitable")
SINGLE_OBJECT_REQUEST_MARKERS = (
    "这家公司", "这个公司", "该公司", "这个客户", "这个网站", "官网", "域名", "网址", "网站",
    "linkedin", "领英", "facebook", "instagram", "whatsapp", "地址",
)
PRODUCT_MARKERS = (
    "产品", "型号", "电池", "锂电", "纺织", "衬衫", "面料", "化工", "农产品", "机械",
    "配件", "零件", "汽车配件", "户外家具", "柴油发电机", "发电机", "电水壶", "保温杯",
    "音响", "巡演音响", "专业音响", "扩声系统", "传感器", "工业传感器", "刹车片",
    "钢材", "粮食", "矿产", "水果", "蔬菜", "茶", "工装", "灯芯绒",
    "steel", "battery", "textile", "fabric", "shirt", "product", "parts",
    "accessories", "furniture", "generator", "kettle", "kettles", "mug", "mugs",
    "audio", "sound system", "touring sound", "sensor", "sensors", "brake pad", "brake pads",
)
MARKET_QUESTION_OR_ANALYSIS_MARKERS = (
    "分析", "查", "查询", "核实", "确认", "判断", "看一下", "了解", "研究", "评估",
    "要不要", "需不需要", "是否需要", "需要什么", "需要哪些", "需要", "要求是什么",
    "有什么要求", "要什么文件", "还要什么文件", "怎么办", "到底要不要",
    "need", "needs", "require", "required", "requirement", "requirements", "analyze", "analysis",
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
MARKET_ANALYSIS_MODULES = (
    ("market_trends", "趋势", ("趋势", "google trends", "淡旺季", "节假日", "搜索热度")),
    ("public_price", "公开价格", ("公开价格", "价格区间", "价格带", "价格")),
    ("market_access", "准入", ("准入", "认证", "测试", "注册", "标签", "sds", "un38.3", "un 38.3", "ce", "ul", "fcc", "fda")),
    ("import_tax", "税费", ("关税", "税率", "税费", "进口税", "vat", "gst", "hts", "htsus", "hs code", "taric", "tariff", "duty", "anti-dumping", "反倾销", "301")),
    ("export_requirements", "出口要求", ("出口文件", "出口报关", "商检", "检验检疫", "出口管制")),
    ("logistics", "物流", ("物流", "运输", "海运", "空运", "快递", "铁路", "陆运", "清关", "预申报")),
    ("external_factors", "外部因素", ("外部因素", "汇率", "政策变化", "制裁", "地缘")),
)
COMPLETE_MARKET_ANALYSIS_MARKERS = (
    "完整市场分析",
    "整体市场分析",
    "全面市场分析",
    "完整报告",
    "整体分析",
    "全面分析",
    "complete analysis",
    "complete market analysis",
    "full market analysis",
    "overall market analysis",
)


def norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def _part_number_anchor(text: str) -> str | None:
    """Return an explicit model/part-number token without identifying its product."""
    token_chars = r"A-Za-z0-9._/-"
    pattern = rf"(?<![{token_chars}])(?=[{token_chars}]{{5,32}}(?![{token_chars}]))(?=[{token_chars}]*\d)[A-Za-z0-9][{token_chars}]{{4,31}}"
    for match in re.finditer(pattern, text):
        value = match.group(0).strip("._/-")
        prefix = text[max(0, match.start() - 32):match.start()]
        if re.search(r"(?i)(?:api\s*key|token|secret|password|密码|密钥|令牌)\s*[:：=]?\s*$", prefix):
            continue
        if not value or re.fullmatch(r"(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}", value):
            continue
        if re.fullmatch(r"\d{1,2}[-/.]\d{1,2}[-/.](?:19|20)\d{2}", value):
            continue
        if re.match(r"(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[tT_]\d", value):
            continue
        if re.fullmatch(r"(?i)v?\d+(?:\.\d+){2,}", value):
            continue
        if re.match(r"(?i)version[._/-]", value):
            continue
        if re.match(r"(?i)(?:un|iso|iec|en|din|astm|ul|fcc|gbt?)[._/-]?\d", value):
            continue
        if re.fullmatch(r"(?:\d{1,3}\.){3}\d{1,3}", value):
            continue
        compact_digits = re.sub(r"[._/-]", "", value)
        if compact_digits.isdigit():
            if len(compact_digits) >= 9:
                continue
            if re.fullmatch(r"(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])", compact_digits):
                continue
        if re.match(
            r"(?i)(?:sk|pk|api[_-]?key|token|secret)[._-]|(?:akia|asia)[a-z0-9]|gh[pousr]_|github_pat_|xox[baprs]-|aiza",
            value,
        ):
            continue
        return value
    return None


def _remove_intake_markers(text: str, markers: tuple[str, ...]) -> str:
    result = text
    for marker in sorted(set(markers), key=len, reverse=True):
        normalized_marker = norm(marker)
        if re.fullmatch(r"[a-z0-9][a-z0-9 ._-]*", normalized_marker):
            result = re.sub(
                rf"(?<![a-z0-9]){re.escape(normalized_marker)}(?![a-z0-9])",
                " ",
                result,
                flags=re.IGNORECASE,
            )
        else:
            result = result.replace(normalized_marker, " ")
    return result


def _has_explicit_bulk_product_scope(text: str) -> bool:
    """Detect a user-written product phrase without maintaining a closed product catalog."""
    cleaned = _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    if re.search(
        r"(?i)api\s*key|token|secret|password|密码|密钥|令牌|"
        r"(?:sk|pk)[._-][a-z0-9]|(?:akia|asia)[a-z0-9]|gh[pousr]_|github_pat_|xox[baprs]-|aiza",
        cleaned,
    ):
        return False
    cleaned = _remove_intake_markers(
        cleaned,
        COUNTRY_HINTS + CUSTOMER_TYPE_MARKERS + CUSTOMER_ACTION_MARKERS + CUSTOMER_DEVELOPMENT_MARKERS,
    )
    cleaned = re.sub(
        r"(?i)(?:有|需要|具备)?\s*(?:ce|ul|fcc|fda|rohs|reach|ukca)\s*(?:认证)?\s*(?:需求|要求)?(?:的)?",
        " ",
        cleaned,
    )
    cleaned = re.sub(
        r"(?:帮我|请|我要|我想|给我|一份|我们|工厂|做|卖|想|最新版本|正式|产品|有|需要|需求|要求|认证|的)",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"[\s+＋,，。；;:：!?！？()（）\[\]{}]+", " ", cleaned).strip(" ._/-")
    if not cleaned:
        return False
    if re.fullmatch(r"\d{1,2}[-/.]\d{1,2}[-/.](?:19|20)\d{2}", cleaned):
        return False
    if re.match(r"(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}[tT_]\d", cleaned):
        return False
    if re.fullmatch(r"(?i)(?:v?\d+(?:\.\d+){2,}|version[._/-].+)", cleaned):
        return False
    if re.fullmatch(r"\d{9,}", re.sub(r"[._/-]", "", cleaned)):
        return False
    return bool(re.search(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}", cleaned))


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    haystack = norm(text)
    for marker in markers:
        normalized_marker = marker.casefold()
        if re.fullmatch(r"[a-z0-9][a-z0-9 ._-]*", normalized_marker):
            if re.search(rf"(?<![a-z0-9]){re.escape(normalized_marker)}(?![a-z0-9])", haystack):
                return True
        elif normalized_marker in haystack:
            return True
    return False


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
    if re.search(r"\b(?:gmbh|ltd|limited|inc\.?|llc|corp\.?|co\.?|s\.a\.?|s\.r\.l\.?)\b|(?:有限责任公司|股份有限公司)", low):
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
    if contains_any(clean, TERSE_CUSTOMER_TYPE_MARKERS) and (
        contains_any(clean, COUNTRY_HINTS) or _part_number_anchor(clean)
    ):
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
    if (
        contains_any(clean, COMPLETE_MARKET_ANALYSIS_MARKERS)
        and contains_any(clean, PRODUCT_MARKERS)
        and contains_any(clean, COUNTRY_HINTS)
        and any(marker in clean for marker in ("出口", "进入", "进口", "销往", "卖到", "发到", "export", "import", "into", "to"))
    ):
        return True
    if (
        "市场" in clean
        and contains_any(clean, MARKET_QUESTION_OR_ANALYSIS_MARKERS)
        and (contains_any(clean, PRODUCT_MARKERS) or contains_any(clean, COUNTRY_HINTS))
    ):
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


def _requested_market_modules(text: str) -> list[str]:
    if contains_any(text, COMPLETE_MARKET_ANALYSIS_MARKERS):
        return [module for module, _, _ in MARKET_ANALYSIS_MODULES]
    # A same-sentence exclusion such as “不要趋势、价格” must not select
    # those modules merely because its keywords are present.
    requested_text = re.sub(
        r"(?:不|不要|不用|无需|先不|暂不|别)(?:要|做|查|看|包含|纳入)?[^，,。；;！？!?]{0,64}",
        " ",
        norm(text),
    )
    return [
        module
        for module, _, markers in MARKET_ANALYSIS_MODULES
        if contains_any(requested_text, markers)
    ]


def _market_module_labels(modules: list[str]) -> list[str]:
    selected = set(modules)
    return [label for module, label, _ in MARKET_ANALYSIS_MODULES if module in selected]


def _market_response(text: str, split_customer_development: bool) -> list[str]:
    product = _product_hint(text)
    target = _target_hint(text)
    export_country = _export_country_hint(text)
    modules = _requested_market_modules(text)
    scope_labels = _market_module_labels(modules)
    complete = len(modules) == len(MARKET_ANALYSIS_MODULES)
    lines = [
        "我理解你要做的是：产品出海市场分析。",
        f"本轮对象：{product} → {target}。",
        f"默认出口申报国：{export_country}；原产国、起运地、最终税号和技术文件不足时会保留待确认。",
    ]
    if complete:
        lines.append("本轮范围：完整市场分析，覆盖趋势、公开价格、准入、税费、出口要求、物流和外部因素；不生成客户名单，也不判断是否值得进入。")
    elif scope_labels:
        unexecuted = _market_module_labels([
            module
            for module, _, _ in MARKET_ANALYSIS_MODULES
            if module not in modules
        ])
        lines.append(
            f"本轮范围：{'、'.join(scope_labels)}；未点名模块不纳入本轮。"
            "不生成客户名单，也不判断是否值得进入。"
        )
        lines.append(f"本轮未执行：{'、'.join(unexecuted)}。")
    else:
        lines.append("请说明本轮想了解：趋势、公开价格、准入、税费、出口要求、物流或外部因素；收到范围后再开始相应研究。不生成客户名单，也不判断是否值得进入。")
    if split_customer_development:
        lines.append("你提到找客户的部分建议放到第二阶段，等你看完市场分析后再单独启动批量客户开发。")
    if _has_concrete_subject_anchor(text) and re.search(r"https?://|www\.", text, re.IGNORECASE):
        lines.append("已识别到产品链接；本轮先把它作为产品资料线索，型号、规格和适用条件仍需从打开来源核对。")
    return lines


def _with_interaction_mode(response: dict[str, Any], interaction_mode: str) -> dict[str, Any]:
    response["interaction_mode"] = interaction_mode
    return response


def _material_triage_response(text: str) -> dict[str, Any]:
    language = detect_language(text)
    if language == "zh":
        lines = [
            "我理解你要做的是：资料初审。",
            "本轮只整理你提供的材料与待确认项，不创建 Run/Brief，不做预检、公开搜索、来源打开、缓存扫描或导出。",
        ]
    else:
        lines = [
            "I understand this as material triage (资料初审).",
            "This only organizes the material you supplied and items to confirm; it does not create a Run/Brief or perform preflight, public research, source opens, cache scans, or exports.",
        ]
    return {
        "route": "material_triage",
        "next_skill": "using-superleads",
        "split_customer_development": False,
        "secondary_routes": [],
        "route_order": [],
        "missing_fields": [],
        "response_contract": "material_triage",
        "language": language,
        "interaction_mode": "material_triage",
        "operations": [],
        "response_lines": lines,
    }


def _status_response(text: str, execution_state: dict[str, Any] | None) -> dict[str, Any]:
    language = detect_language(text)
    has_state = isinstance(execution_state, dict)
    lines = (
        ["本轮任务状态由宿主记录的阶段信息决定；当前没有可显示的任务状态。"]
        if language == "zh" and not has_state
        else ["Task status is available only from host-recorded stage information; there is no current task status to show."]
        if not has_state
        else ["本轮任务正在按已记录的阶段处理。"]
        if language == "zh"
        else ["The current task is being handled in recorded stages."]
    )
    return {
        "route": "metadata",
        "next_skill": "using-superleads",
        "split_customer_development": False,
        "secondary_routes": [],
        "route_order": [],
        "missing_fields": [],
        "response_contract": "current_status",
        "language": language,
        "interaction_mode": "metadata",
        "operations": [],
        "response_lines": lines,
    }


def _export_help_response(text: str) -> dict[str, Any]:
    language = detect_language(text)
    lines = (
        ["导出需要已有本轮已核验结果；完成后可要求整理为 Excel 或 CSV。"]
        if language == "zh"
        else ["Export needs a validated result from the current task; after that, you can request Excel or CSV."]
    )
    return {
        "route": "metadata",
        "next_skill": "using-superleads",
        "split_customer_development": False,
        "secondary_routes": [],
        "route_order": [],
        "missing_fields": [],
        "response_contract": "export_help",
        "language": language,
        "interaction_mode": "metadata",
        "operations": [],
        "response_lines": lines,
    }


def _has_single_object_contact_request(text: str) -> bool:
    low = norm(text)
    has_literal_subject = re.search(
        r"https?://|www\.|[a-z0-9.-]+\.[a-z]{2,}|[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}",
        low,
    ) is not None
    contact_only = re.search(
        r"(?:只|仅).{0,12}(?:联系人|联系方式|公开邮箱|邮箱|电话)|"
        r"\b(?:only|just)\s+(?:public\s+)?(?:contact|email|phone)\b",
        low,
        re.IGNORECASE,
    ) is not None
    return (
        contact_only
        and contains_any(text, CONTACT_REQUEST_MARKERS)
        and (has_literal_subject or contains_any(text, SINGLE_OBJECT_REQUEST_MARKERS))
    )


def _has_export_request(text: str) -> bool:
    table_enrichment = contains_any(text, TABLE_MARKERS) and contains_any(
        text,
        ("补全", "enrich", "enrichment"),
    )
    return (
        contains_any(text, EXPORT_REQUEST_MARKERS)
        and not is_export_help_request(text)
        and not table_enrichment
    )


def _has_feedback_correction(text: str) -> bool:
    return contains_any(text, FEEDBACK_CORRECTION_MARKERS)


def _bulk_execution_contract(interaction_mode: str) -> dict[str, Any]:
    """Keep formal bulk delivery metadata distinct from the fast snapshot."""
    if interaction_mode == "formal_research":
        return {
            "task_mode": "formal_research",
            "delivery_mode": "formal_report",
        }
    return {
        "task_mode": "discovery_snapshot",
        "delivery_mode": "fast_candidate_pool",
        "first_batch_candidate_target": 10,
        "max_candidates_per_group": 10,
        "max_candidates_per_run": 10,
        "include_social": False,
        "include_maps": False,
        "include_trade_records": False,
        "ask_expansion_after_first_batch": True,
    }


def classify(
    text: str,
    *,
    active_root: str | Path | None = None,
    fetch_latest_version: Callable[[], Any] | None = None,
    session_cache: MutableMapping[str, str] | None = None,
    current_result_valid: bool = False,
    current_run_id: str | None = None,
    current_execution_state: dict[str, Any] | None = None,
    preflight_callback: Callable[[], Any] | None = None,
    network_callback: Callable[[], Any] | None = None,
    cache_scan_callback: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Route intake without invoking caller-supplied operational callbacks."""
    del preflight_callback, network_callback, cache_scan_callback
    interaction_mode = classify_task_mode(text)
    if interaction_mode == "metadata":
        static_help = static_help_response(text)
        if static_help is not None:
            return static_help
        if is_status_request(text):
            return _status_response(text, current_execution_state)
        if is_export_help_request(text):
            return _export_help_response(text)
        return metadata_response(
            text,
            active_root=active_root,
            fetch_latest_version=fetch_latest_version,
            session_cache=session_cache,
        )
    if interaction_mode == "material_triage":
        return _material_triage_response(text)

    has_table = contains_any(text, TABLE_MARKERS)
    has_customer_development = _has_customer_development_intent(text)
    if has_table and not contains_any(text, EXPLICIT_DISCOVERY_ACTION_MARKERS):
        # A supplied customer table is a bounded enrichment scope. “整理客户表”
        # must not create a new discovery task merely because it contains 客户.
        has_customer_development = False
    has_background = _has_background_intent(text) or (
        _has_concrete_subject_anchor(text) and contains_any(text, BACKGROUND_MARKERS)
    )
    part_number = _part_number_anchor(text)
    product_scope_text = _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    has_country = contains_any(text, COUNTRY_HINTS)
    has_product = (
        contains_any(product_scope_text, PRODUCT_MARKERS)
        or part_number is not None
        or (
            has_customer_development
            and has_country
            and contains_any(text, TERSE_CUSTOMER_TYPE_MARKERS)
            and _has_explicit_bulk_product_scope(text)
        )
    )
    direct_market = "产品出海市场分析" in _strip_patterns(text, NEGATED_MARKET_PATTERNS)
    market_intent = _has_market_intent(text)
    has_product_material = has_product or (market_intent and _has_concrete_subject_anchor(text))
    requested_market_modules = _requested_market_modules(text)
    language = detect_language(text)
    product_anchor_contract = (
        {"product_anchor_type": "part_number", "product_anchor": part_number}
        if part_number is not None
        else {}
    )
    # Table enrichment may include public email, phone, or a contact field. It
    # becomes a separate contact subtask only when the user explicitly asks to
    # verify or supplement public contacts, rather than merely fill a column.
    contact_requested = re.search(
        r"(?:核查|验证|check|verify).{0,12}(?:公开)?(?:联系人|联系方式|邮箱|电话|contact(?:s| person)?|email|phone)|"
        r"(?:补充|补全|supplement|enrich).{0,12}(?:公开)?(?:联系人|contact(?:s| person)?)|"
        r"(?:联系人|contact(?:s| person)?).{0,12}(?:核查|验证|check|verify)",
        text,
        re.IGNORECASE,
    ) is not None
    composite_market_intent = (
        (direct_market or market_intent)
        and not (
            _looks_like_customer_attribute_request(text)
            and not _has_explicit_split_market_clause(text)
        )
    )

    composite = plan_composite_task(text, {
        "has_background": has_background,
        "has_market": composite_market_intent,
        "has_batch": has_customer_development,
        "has_table": has_table and bool(re.search(r"上传|附件|provided|attached|补全|enrich", text, re.IGNORECASE)),
        "has_contact": contact_requested,
        "has_export": contains_any(text, EXPORT_REQUEST_MARKERS) and not is_export_help_request(text),
        "has_product": has_product_material,
        "has_country": has_country,
        "analysis_modules_requested": requested_market_modules,
        "language": language,
        "contact_scope": (
            "upstream"
            if has_table or has_customer_development
            else "same_request"
            if has_background
            else None
        ),
        "contact_requires_upstream": bool(has_table or has_customer_development),
    })
    if composite["route"] == "composite":
        subtasks = composite["subtasks"]
        first = next((item for item in subtasks if item["status"] == "ready"), subtasks[0])
        skill_by_route = {
            "customer_background_research": "researching-customer-background",
            "product_outbound_market_analysis": "analyzing-product-outbound-market",
            "bulk_customer_development": "using-superleads",
            "existing_table_enrichment": "using-superleads",
            "contact_supplement": "using-superleads",
            "export_delivery": "using-superleads",
        }
        stage_by_route = {
            "existing_table_enrichment": "shared/internal-stages/scoping-lead-research.md",
            "contact_supplement": "shared/internal-stages/collecting-contact-intelligence.md",
            "export_delivery": "shared/internal-stages/exporting-lead-workbooks.md",
        }
        names = ("、" if language == "zh" else ", ").join(item["display_name"] for item in subtasks)
        status_lines = (
            [
                f"本次包含 {len(subtasks)} 项工作：{names}。",
                "每项会保留独立的公开来源、待确认项和来源受限状态；只有明确依赖时才等待。",
            ]
            if language == "zh"
            else [
                f"This request contains {len(subtasks)} work items: {names}.",
                "Each item keeps separate public sources, items to confirm, and source restrictions; it waits only for explicit dependencies.",
            ]
        )
        for item in subtasks:
            if item["status"] == "waiting_for_required_input":
                status_lines.append(
                    f"{item['display_name']}：等待必要信息。"
                    if language == "zh"
                    else f"{item['display_name']}: Waiting for required information."
                )
            elif item["status"] == "ready":
                status_lines.append(
                    f"{item['display_name']}：正在规划本轮公开信息范围。"
                    if language == "zh"
                    else f"{item['display_name']}: Planning the public-information scope for this run."
                )
        payload = {
            "route": "composite_superleads_task",
            "next_skill": skill_by_route[first["route"]],
            "split_customer_development": False,
            "secondary_routes": [item["route"] for item in subtasks[1:]],
            "route_order": [item["route"] for item in subtasks],
            "subtasks": subtasks,
            "scheduling": composite["scheduling"],
            "analysis_modules_requested": requested_market_modules,
            "missing_fields": [],
            "language": language,
            "parent_title": composite["parent_title"],
            "response_lines": status_lines,
        }
        if first["route"] in stage_by_route:
            payload["next_stage_reference"] = stage_by_route[first["route"]]
        return _with_interaction_mode(payload, interaction_mode)

    if _has_feedback_correction(text):
        if current_run_id:
            return _with_interaction_mode({
                "route": "current_run_feedback_correction",
                "next_skill": "using-superleads",
                "next_stage_reference": "shared/internal-stages/learning-from-feedback.md",
                "split_customer_development": False,
                "secondary_routes": [],
                "route_order": ["current_run_feedback_correction"],
                "missing_fields": [],
                "feedback_scope": "current_run",
                "feedback_action": "current_run_correction",
                "response_lines": ["我会只在本轮结果中记录这项范围或事实纠正，不会自动保存为长期偏好。"],
            }, interaction_mode)
        return _with_interaction_mode({
            "route": "feedback_requires_current_run",
            "next_skill": "using-superleads",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": [],
            "missing_fields": ["current_run"],
            "response_lines": ["请先说明这项反馈对应哪一轮当前结果；没有当前结果时不会自动保存为长期偏好。"],
        }, interaction_mode)

    if _has_export_request(text):
        if current_result_valid:
            return _with_interaction_mode({
                "route": "export_delivery",
                "next_skill": "using-superleads",
                "next_stage_reference": "shared/internal-stages/exporting-lead-workbooks.md",
                "split_customer_development": False,
                "secondary_routes": [],
                "route_order": ["export_delivery"],
                "missing_fields": [],
                "response_lines": ["已识别到本轮已核验结果，可以开始准备导出。"],
            }, interaction_mode)
        return _with_interaction_mode({
            "route": "export_requires_current_result",
            "next_skill": "using-superleads",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": [],
            "missing_fields": ["current_validated_result"],
            "response_lines": ["导出需要已有本轮已核验结果；当前不会生成空白或猜测性文件。"],
        }, interaction_mode)

    if _has_single_object_contact_request(text):
        return _with_interaction_mode({
            "route": "single_object_contact",
            "next_skill": "researching-customer-background",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["single_object_contact"],
            "missing_fields": [],
            "response_lines": ["我会围绕这个指定对象核对公开联系方式及其公开关联，不扩展为批量找客户。"],
        }, interaction_mode)

    if has_background and not direct_market:
        missing_fields = [] if _has_concrete_subject_anchor(text) else ["target_subject"]
        return _with_interaction_mode({
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
        }, interaction_mode)

    if has_table and not direct_market:
        return _with_interaction_mode({
            "route": "existing_table_enrichment",
            "next_skill": "using-superleads",
            "next_stage_reference": "shared/internal-stages/scoping-lead-research.md",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["existing_table_enrichment"],
            "missing_fields": [],
            "response_lines": [
                "我理解你要处理的是：已有客户表格补全。",
                "本轮只围绕你提供的表格行/单元格补充，不自动创建新的客户开发方向。",
            ],
        }, interaction_mode)

    if market_intent and has_customer_development and not (
        _looks_like_customer_attribute_request(text) and not _has_explicit_split_market_clause(text)
    ):
        missing_fields: list[str] = []
        if not has_country:
            missing_fields.append("target_country_or_region")
        if not has_product_material:
            missing_fields.append("product_identity")
        return _with_interaction_mode({
            "route": "product_outbound_market_analysis",
            "next_skill": "analyzing-product-outbound-market",
            "split_customer_development": True,
            "secondary_routes": ["bulk_customer_development"],
            "route_order": ["product_outbound_market_analysis", "bulk_customer_development"],
            "missing_fields": missing_fields,
            "analysis_modules_requested": _requested_market_modules(text),
            "response_lines": _market_response(text, True),
        }, interaction_mode)

    if has_customer_development and not direct_market:
        # Customer words have priority unless the user also asks for explicit
        # market/compliance/tax/logistics analysis; “找美国锂电池进口商客户”
        # is customer development, while “分析市场然后找客户” is split-stage.
        return _with_interaction_mode({
            "route": "bulk_customer_development",
            "next_skill": "using-superleads",
            "next_stage_reference": "shared/internal-stages/scoping-lead-research.md",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["bulk_customer_development"],
            "missing_fields": [] if has_product else ["product_or_scope"],
            **product_anchor_contract,
            **_bulk_execution_contract(interaction_mode),
            "response_lines": [
                "我理解你要做的是：批量客户开发。",
                *([f"产品锚点：番号/料号 {part_number}；先通过公开检索核对产品身份，这不是模型推断。"] if part_number else []),
                "先返回发现候选池：每家保留官网或搜索结果来源、业务匹配理由、公开联系方式状态和每条公开信号的主体关联状态。社媒、地图、贸易记录和深度联系人本轮先标为未核验。",
                "首批完成后会附上下一步选项：可指定扩展至 30 / 50 / 100 家或直接说数量、换搜索组合、只补社媒 / 地图 / 贸易记录信号（记录主体关联状态，不做深度联系人归属核验；较快，仍属候选池），或对整份名单做深度核验 → 标准开发名单（含社媒 / 地图 / 贸易记录 + 联系人归属核验；交付表格文件 + 配套报告；较慢；可分批产出）。",
            ],
        }, interaction_mode)

    if direct_market or market_intent:
        missing_fields: list[str] = []
        if not has_country:
            missing_fields.append("target_country_or_region")
        if not has_product_material and not direct_market:
            missing_fields.append("product_identity")
        return _with_interaction_mode({
            "route": "product_outbound_market_analysis",
            "next_skill": "analyzing-product-outbound-market",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["product_outbound_market_analysis"],
            "missing_fields": missing_fields,
            "analysis_modules_requested": _requested_market_modules(text),
            "response_lines": _market_response(text, False),
        }, interaction_mode)

    if has_customer_development:
        return _with_interaction_mode({
            "route": "bulk_customer_development",
            "next_skill": "using-superleads",
            "next_stage_reference": "shared/internal-stages/scoping-lead-research.md",
            "split_customer_development": False,
            "secondary_routes": [],
            "route_order": ["bulk_customer_development"],
            "missing_fields": [] if has_product else ["product_or_scope"],
            **product_anchor_contract,
            **_bulk_execution_contract(interaction_mode),
            "response_lines": [
                "我理解你要做的是：批量客户开发。",
                *([f"产品锚点：番号/料号 {part_number}；先通过公开检索核对产品身份，这不是模型推断。"] if part_number else []),
                "先返回发现候选池：每家保留官网或搜索结果来源、业务匹配理由、公开联系方式状态和每条公开信号的主体关联状态。社媒、地图、贸易记录和深度联系人本轮先标为未核验。",
                "首批完成后会附上下一步选项：可指定扩展至 30 / 50 / 100 家或直接说数量、换搜索组合、只补社媒 / 地图 / 贸易记录信号（记录主体关联状态，不做深度联系人归属核验；较快，仍属候选池），或对整份名单做深度核验 → 标准开发名单（含社媒 / 地图 / 贸易记录 + 联系人归属核验；交付表格文件 + 配套报告；较慢；可分批产出）。",
            ],
        }, interaction_mode)

    return _with_interaction_mode({
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
    }, interaction_mode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="User intake prompt")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()
    print(json.dumps(classify(args.text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
