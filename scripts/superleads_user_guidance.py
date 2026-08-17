#!/usr/bin/env python3
"""Pure helpers for the static Superleads first-use guidance path."""
from __future__ import annotations

import re
from time import perf_counter
from typing import Any


SUPPORT_FOOTER_MARKER = "<!-- superleads-support-and-safety -->"
GUIDANCE_REFERENCE = "shared/references/superleads-user-guidance.md"

# One business-content model drives the compact guide and every terminal footer.
# Languages share the same section and field structure; no separate Skill, locale,
# or standalone English guide is maintained.
_GUIDE_CONTENT = {
    "zh": {
        "identity": "我是 Superleads，帮助外贸人完成：批量开发客户、单一客户背调、目标市场分析。",
        "start": "开始使用：在输入框中输入 @，选择 Superleads，再直接描述需求。",
        "input_label": "输入格式",
        "example_label": "示例",
        "entries": (
            ("批量开发客户", "产品关键词 + 目标市场 + 客户类型", "找德国做工业传感器的进口商"),
            ("单一客户背调", "公司网址或公司名称", "查一下 example.com 这家公司做什么、有没有公开联系方式"),
            ("目标市场分析", "产品 + 目标市场 + 想了解的信息", "分析中国出口保温杯到越南的市场、公开价格和准入要求"),
        ),
        "more_title": "更多用法",
        "more_items": (
            "导出 Excel / CSV：将本次客户开发、客户背调或市场分析结果整理为表格。",
            "补全客户表：上传已有客户表，并说明需要补充的字段，例如官网、主营业务、公开联系方式或目标市场信息。",
            "联系人核查：提供公司名称及邮箱、电话或 LinkedIn 链接，核查其公开信息与该企业的关联情况。",
        ),
        "boundary_title": "证据和决策边界",
        "boundary": "Superleads 只整理公开来源、可验证事实、来源信息和待确认项。不黑盒猜测，不胡编乱造，也不把搜索结果直接当成确定事实。不替你判断哪个客户值得开发，不替你决定是否进入某个市场。候选客户池不是已经确认的正式开发名单，弱证据不会包装成确定结论。",
        "footer_heading": "Superleads 支持",
        "footer_support": "在使用 Superleads 过程中，如遇问题或有改进建议，欢迎通过 GitHub Issues（https://github.com/fleixweb/superleads/issues）或在小红书搜索 Fleixweb 联系 Fleix。",
        "footer_safety": "使用 AI 开发客户时，请勿提交密码、API Key 或未经脱敏的客户敏感资料。",
    },
    "en": {
        "identity": "I am Superleads. I help foreign-trade professionals with batch customer development, single-customer background research, and target market analysis.",
        "start": "To begin: type @ in the message box, select Superleads, then describe your need.",
        "input_label": "Input format",
        "example_label": "Example",
        "entries": (
            ("Batch customer development", "Product keywords + target market + customer type", "Find importers of industrial sensors in Germany"),
            ("Single-customer background research", "Company website or company name", "Check what example.com does and whether it has public contact details"),
            ("Target market analysis", "Product + target market + information needed", "Analyze the Vietnam market, public prices, and access requirements for insulated tumblers exported from China"),
        ),
        "more_title": "More ways to use Superleads",
        "more_items": (
            "Export Excel / CSV: organize the current customer-development, background-research, or market-analysis result into a spreadsheet.",
            "Enrich a customer table: upload your existing customer table and state the fields to add, such as websites, products, public contacts, or market information.",
            "Check a contact: provide a company name and an email address, phone number, or LinkedIn link to check its public connection with that company.",
        ),
        "boundary_title": "Evidence and decision boundaries",
        "boundary": "Superleads only organizes public sources, verifiable facts, source details, and items to confirm. It does not guess, fabricate, treat search results as confirmed facts, choose customers for you, or decide whether to enter a market. A candidate pool is not a confirmed development list, and weak evidence is not presented as a certain conclusion.",
        "footer_heading": "Superleads Support",
        "footer_support": "If you encounter a problem or have an improvement suggestion while using Superleads, please use GitHub Issues (https://github.com/fleixweb/superleads/issues) or search Xiaohongshu for Fleixweb to contact Fleix.",
        "footer_safety": "Do not submit passwords, API keys, or customer sensitive data that has not been de-identified.",
    },
}

_CHINESE_HELP = re.compile(
    r"^(?:superleads\s*)?(?:你能干嘛|你能做什么|能做什么|你会什么|怎么用|如何使用|使用方法|帮助|帮助手册|新手入门)[？?]?$",
    re.IGNORECASE,
)
_ENGLISH_HELP = re.compile(
    r"^(?:what can (?:you|superleads) do|what do you do|how (?:do i|can i|to) use (?:this|superleads)|(?:superleads )?help)[?.!]*$",
    re.IGNORECASE,
)


def _content(language: str) -> dict[str, Any]:
    return _GUIDE_CONTENT["en" if language.lower().startswith("en") else "zh"]


def _canonical_footer(language: str = "zh") -> str:
    content = _content(language)
    return "\n\n".join(
        (
            SUPPORT_FOOTER_MARKER,
            f"## {content['footer_heading']}",
            str(content["footer_support"]),
            str(content["footer_safety"]),
        )
    )


def _is_complete_terminal_footer(text: str) -> bool:
    return any(text.rstrip().endswith(_canonical_footer(language)) for language in ("zh", "en"))


def _guide_lines(language: str) -> list[str]:
    content = _content(language)
    lines = ["# Superleads", "", str(content["identity"]), "", str(content["start"]), ""]
    for title, input_format, example in content["entries"]:
        lines.extend((f"## {title}", "", f"{content['input_label']}：{input_format}", "", f"{content['example_label']}：{example}", ""))
    lines.extend((f"## {content['more_title']}", ""))
    lines.extend(f"- {item}" for item in content["more_items"])
    lines.extend(("", f"## {content['boundary_title']}", "", str(content["boundary"]), "", _canonical_footer(language)))
    return lines


def _compact_guide_lines(language: str) -> list[str]:
    """Render the fast first-use contract without loading the long reference."""
    content = _content(language)
    lines = ["# Superleads", "", str(content["identity"]), "", str(content["start"]), ""]
    for title, input_format, example in content["entries"]:
        lines.extend((f"## {title}", f"{content['input_label']}：{input_format}", f"{content['example_label']}：{example}", ""))
    lines.extend(("证据边界：只整理公开来源和可验证事实；搜索结果是线索，不是确定事实。不猜联系方式，也不替你判断客户价值或市场决策。", "", _canonical_footer(language)))
    return lines


def static_help_response(text: str) -> dict[str, Any] | None:
    """Return a narrow, static help response without research operations."""
    started = perf_counter()
    normalized = text.strip()
    compact = normalized.lower() in {"@", "@superleads"}
    if compact:
        language = "zh"
    elif _CHINESE_HELP.fullmatch(normalized):
        language = "zh"
    elif _ENGLISH_HELP.fullmatch(normalized):
        language = "en"
    else:
        return None

    return {
        "route": "first_use_guide",
        "next_skill": None if compact else "using-superleads",
        "split_customer_development": False,
        "secondary_routes": [],
        "route_order": [],
        "missing_fields": [],
        "response_contract": "static_compact_help" if compact else "static_first_use_help",
        "language": language,
        "guidance_reference": None if compact else GUIDANCE_REFERENCE,
        "fast_path": compact,
        "elapsed_seconds": perf_counter() - started,
        "interaction_mode": "metadata",
        "operations": [],
        "response_lines": _compact_guide_lines(language) if compact else _guide_lines(language),
    }


def append_final_footer(text: str, language: str = "zh") -> str:
    """Append the single terminal footer or reject malformed markers."""
    footer = _canonical_footer(language)
    marker_count = text.count(SUPPORT_FOOTER_MARKER)
    if marker_count:
        if marker_count == 1 and _is_complete_terminal_footer(text):
            return text
        raise ValueError("text contains a malformed or non-terminal support footer")
    return text.rstrip() + "\n\n" + footer


def has_exactly_one_final_footer(text: str) -> bool:
    """Return whether exactly one complete canonical footer is terminal."""
    return text.count(SUPPORT_FOOTER_MARKER) == 1 and _is_complete_terminal_footer(text)


def guidance_side_effects() -> list[str]:
    """Declare that static guidance never performs external operations."""
    return []
