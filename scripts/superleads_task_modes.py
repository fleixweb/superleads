#!/usr/bin/env python3
"""Pure intake-mode and explicit-version helpers for Superleads."""
from __future__ import annotations

import json
import re
from collections.abc import Callable, MutableMapping
from pathlib import Path
from typing import Any


TASK_MODES = (
    "metadata",
    "material_triage",
    "discovery_snapshot",
    "formal_research",
)
LATEST_VERSION_UNCONFIRMED = "本次未能确认远端版本"
_LATEST_VERSION_CACHE_KEY = "superleads.latest_version"

_CHINESE_HELP = re.compile(
    r"^(?:superleads\s*)?(?:你能干嘛|你能做什么|能做什么|你会什么|怎么用|如何使用|使用方法|帮助|帮助手册|新手入门)[？?]?$",
    re.IGNORECASE,
)
_ENGLISH_HELP = re.compile(
    r"^(?:what can (?:you|superleads) do|what do you do|how (?:do i|can i|to) use (?:this|superleads)|(?:superleads )?help)[?.!]*$",
    re.IGNORECASE,
)
_VERSION_REQUEST = re.compile(
    r"(?:当前|目前|已安装|安装的|本地|最新|current|installed|latest|newest).{0,32}(?:版本|version)|(?:版本|version).{0,32}(?:多少|是什么|what|installed|current|latest|newest)",
    re.IGNORECASE,
)
_UPDATE_REQUEST = re.compile(
    r"(?:检查|查看|确认).{0,24}(?:更新|最新版本|新版本)|\b(?:check|look|see)\b.{0,32}\b(?:updates?|(?:latest|new)(?:\s+[a-z0-9_-]+){0,3}\s+version)\b",
    re.IGNORECASE,
)
_CAPABILITY_REQUEST = re.compile(
    r"(?:当前|目前|可用).{0,12}(?:能力|功能)|(?:能力|功能).{0,12}(?:当前|目前|可用)|\b(?:current|available).{0,24}\bcapabilities?\b",
    re.IGNORECASE,
)
_FEEDBACK_REQUEST = re.compile(
    r"(?:反馈入口|怎么反馈|提交反馈|反馈渠道)|\b(?:send|submit|give).{0,20}\bfeedback\b|\bfeedback\b.{0,20}\b(?:where|link|entry)\b",
    re.IGNORECASE,
)
_FORMAL_MARKERS = (
    "完整市场分析",
    "完整报告",
    "正式开发名单",
    "标准交付",
    "深度背调",
    "联系人归属核验",
    "full report",
    "complete analysis",
    "formal delivery",
    "standard delivery",
    "deep due diligence",
    "deep background check",
    "contact ownership verification",
)
_MATERIAL_MARKERS = (
    "pdf",
    "excel",
    "xlsx",
    "xls",
    "csv",
    "截图",
    "screenshot",
    "扫描件",
    "附件",
    "上传",
    "image",
    "png",
    "jpg",
    "jpeg",
    "webp",
)
_TRIAGE_MARKERS = ("资料初审", "初审", "整理资料", "梳理资料", "material triage", "triage")
_MATERIAL_CONTEXT_MARKERS = ("附件", "上传", "我发的", "provided", "attached", "uploaded")
_MATERIAL_FILENAME = re.compile(
    r"[^\s/\\]+\.(?:pdf|xlsx|xls|csv|png|jpe?g|webp)\b",
    re.IGNORECASE,
)
_TABLE_ENRICHMENT_OR_EXPORT_MARKERS = (
    "补全",
    "enrich",
    "enrichment",
    "导出",
    "export",
)
_BUSINESS_MARKERS = (
    "找客户",
    "找买家",
    "开发客户",
    "客户名单",
    "背调",
    "背景调查",
    "市场分析",
    "出海市场",
    "出口要求",
    "进口要求",
    "find importers",
    "lead list",
    "background check",
    "market analysis",
)


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().casefold()


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    lowered = _normalized(text)
    return any(marker.casefold() in lowered for marker in markers)


def _is_help_request(text: str) -> bool:
    normalized = text.strip()
    return (
        normalized.casefold() == "@superleads"
        or _CHINESE_HELP.fullmatch(normalized) is not None
        or _ENGLISH_HELP.fullmatch(normalized) is not None
    )


def is_explicit_update_request(text: str) -> bool:
    """Return whether the user explicitly asked to check for an update."""
    return _UPDATE_REQUEST.search(_normalized(text)) is not None


def _is_metadata_request(text: str) -> bool:
    normalized = _normalized(text)
    return (
        _is_help_request(text)
        or _VERSION_REQUEST.search(normalized) is not None
        or _CAPABILITY_REQUEST.search(normalized) is not None
        or _FEEDBACK_REQUEST.search(normalized) is not None
        or is_explicit_update_request(text)
    )


def _is_material_only_request(text: str) -> bool:
    has_material = _contains(text, _MATERIAL_MARKERS)
    if not has_material:
        return False
    if _contains(text, _TABLE_ENRICHMENT_OR_EXPORT_MARKERS):
        return False
    if _contains(text, _TRIAGE_MARKERS):
        return True
    has_explicit_filename = _MATERIAL_FILENAME.search(text) is not None
    return (
        (_contains(text, _MATERIAL_CONTEXT_MARKERS) or has_explicit_filename)
        and not _contains(text, _BUSINESS_MARKERS)
    )


def classify_task_mode(text: str) -> str:
    """Classify intake intent without reading files, caches, or the network."""
    if _is_metadata_request(text):
        return "metadata"
    if _contains(text, _FORMAL_MARKERS):
        return "formal_research"
    if _is_material_only_request(text):
        return "material_triage"
    return "discovery_snapshot"


def read_active_plugin_version(active_root: str | Path) -> str | None:
    """Read only the explicitly supplied active plugin manifest version."""
    manifest = Path(active_root) / ".codex-plugin" / "plugin.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    version = payload.get("version") if isinstance(payload, dict) else None
    return str(version) if isinstance(version, (str, int, float)) else None


def check_latest_version(
    fetch: Callable[[], Any] | None,
    session_cache: MutableMapping[str, str] | None,
) -> str:
    """Run an injected explicit-update fetch at most once per session."""
    cache = session_cache if session_cache is not None else {}
    if _LATEST_VERSION_CACHE_KEY in cache:
        return cache[_LATEST_VERSION_CACHE_KEY]
    if fetch is None:
        return LATEST_VERSION_UNCONFIRMED
    try:
        result = fetch()
        if isinstance(result, dict):
            result = result.get("version")
        if not isinstance(result, (str, int, float)) or not str(result).strip():
            raise ValueError("latest version response is missing a version")
        version = str(result).strip()
    except Exception:
        version = LATEST_VERSION_UNCONFIRMED
    cache[_LATEST_VERSION_CACHE_KEY] = version
    return version


def detect_language(text: str) -> str:
    """Choose the response language from the submitted prompt."""
    return "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"


def metadata_response(
    text: str,
    *,
    active_root: str | Path | None = None,
    fetch_latest_version: Callable[[], Any] | None = None,
    session_cache: MutableMapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return a metadata response without any implicit cache or network access."""
    language = detect_language(text)
    latest_version = check_latest_version(fetch_latest_version, session_cache) if is_explicit_update_request(text) else None
    normalized = _normalized(text)
    version_request = _VERSION_REQUEST.search(normalized) is not None
    version = (
        read_active_plugin_version(active_root)
        if latest_version is None and version_request and active_root is not None
        else None
    )

    if language == "zh":
        if latest_version is not None:
            lines = [latest_version]
        elif _CAPABILITY_REQUEST.search(normalized) is not None:
            lines = ["当前可用能力取决于本会话明确提供的工具；此元数据入口不会执行预检或能力探测。"]
        elif _FEEDBACK_REQUEST.search(normalized) is not None:
            lines = ["反馈入口：GitHub Issues（https://github.com/fleixweb/superleads/issues）。"]
        elif version is not None:
            lines = [f"当前激活的 Superleads 版本：{version}"]
        else:
            lines = ["未提供当前激活的 Superleads 插件目录，无法读取版本。"]
    elif latest_version is not None:
        lines = [latest_version]
    elif _CAPABILITY_REQUEST.search(normalized) is not None:
        lines = ["Current capabilities depend on tools explicitly available in this session; this metadata path does not run preflight or capability detection."]
    elif _FEEDBACK_REQUEST.search(normalized) is not None:
        lines = ["Feedback: GitHub Issues (https://github.com/fleixweb/superleads/issues)."]
    elif version is not None:
        lines = [f"Active Superleads version: {version}"]
    else:
        lines = ["No active Superleads plugin root was supplied, so no version was read."]

    return {
        "route": "metadata",
        "next_skill": "using-superleads",
        "split_customer_development": False,
        "secondary_routes": [],
        "route_order": [],
        "missing_fields": [],
        "response_contract": "metadata",
        "language": language,
        "interaction_mode": "metadata",
        "operations": [],
        "response_lines": lines,
    }
