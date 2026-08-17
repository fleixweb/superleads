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
_VERSION_VALUE = re.compile(r"^v?(\d+(?:\.\d+){0,3})$", re.IGNORECASE)

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
_SUPERLEADS_UPDATE_COMMAND = re.compile(r"^@superleads\s+update\s*[?.!]*$", re.IGNORECASE)
_GITHUB_VERSION_REQUEST = re.compile(
    r"(?:github|git\s*hub).{0,48}(?:更新|最新版本|新版本|version)|"
    r"(?:更新|最新版本|新版本|version).{0,48}(?:github|git\s*hub)",
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
_STATUS_REQUEST = re.compile(
    r"(?:当前|现在|本次).{0,12}(?:状态|进度)|(?:状态|进度).{0,12}(?:当前|现在|本次)|"
    r"\b(?:current|task)\s+status\b|\bstatus\s+(?:of|for)\s+superleads\b",
    re.IGNORECASE,
)
_EXPORT_HELP_REQUEST = re.compile(
    r"(?:怎么|如何|怎样).{0,12}导出|\bhow\s+(?:do\s+i|can\s+i|to)\s+export\b",
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
    "找",
    "找客户",
    "找买家",
    "开发客户",
    "客户名单",
    "背调",
    "背景调查",
    "调查",
    "核查",
    "市场分析",
    "出海市场",
    "出口要求",
    "进口要求",
    "进口商",
    "经销商",
    "分销商",
    "批发商",
    "零售商",
    "代理商",
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
        normalized == "@"
        or
        normalized.casefold() == "@superleads"
        or _CHINESE_HELP.fullmatch(normalized) is not None
        or _ENGLISH_HELP.fullmatch(normalized) is not None
    )


def is_explicit_update_request(text: str) -> bool:
    """Return whether the user explicitly asked to check for an update."""
    normalized = _normalized(text)
    return (
        _SUPERLEADS_UPDATE_COMMAND.fullmatch(normalized) is not None
        or _UPDATE_REQUEST.search(normalized) is not None
        or _GITHUB_VERSION_REQUEST.search(normalized) is not None
    )


def is_status_request(text: str) -> bool:
    """Return whether this is a current-task status request."""
    return _STATUS_REQUEST.search(_normalized(text)) is not None


def is_export_help_request(text: str) -> bool:
    """Return whether this asks how to export, rather than asking to export."""
    return _EXPORT_HELP_REQUEST.search(_normalized(text)) is not None


def _is_metadata_request(text: str) -> bool:
    normalized = _normalized(text)
    version_request = _VERSION_REQUEST.search(normalized) is not None
    version_metadata = version_request and (
        "superleads" in normalized or not _contains(text, _BUSINESS_MARKERS)
    )
    return (
        _is_help_request(text)
        or version_metadata
        or _CAPABILITY_REQUEST.search(normalized) is not None
        or _FEEDBACK_REQUEST.search(normalized) is not None
        or is_status_request(text)
        or is_export_help_request(text)
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


def _normalized_version(value: Any) -> str | None:
    if not isinstance(value, (str, int, float)):
        return None
    match = _VERSION_VALUE.fullmatch(str(value).strip())
    return match.group(1) if match is not None else None


def _version_parts(value: str | None) -> tuple[int, ...] | None:
    normalized = _normalized_version(value)
    return tuple(int(part) for part in normalized.split(".")) if normalized is not None else None


def normalize_remote_version(payload: Any) -> dict[str, Any]:
    """Normalize an injected GitHub version response without performing I/O."""
    if isinstance(payload, (str, int, float)):
        payload = {"version": payload}
    if not isinstance(payload, dict):
        raise ValueError("remote version response must be an object")

    version = _normalized_version(payload.get("version"))
    if version is None:
        raise ValueError("remote version response is missing a valid version")

    declared_kind = payload.get("source_kind")
    if declared_kind not in {None, "github_release", "tag_manifest", "repository_version", "unknown"}:
        raise ValueError("remote version response has an unsupported source kind")
    if payload.get("branch"):
        # A branch is never a stable release, even if a caller supplied a
        # contradictory source_kind label.
        source_kind = "repository_version"
    elif declared_kind is None:
        release_url = payload.get("release_url") or payload.get("html_url")
        if isinstance(release_url, str) and "/releases/" in release_url:
            source_kind = "github_release"
        elif payload.get("branch"):
            source_kind = "repository_version"
        elif payload.get("tag") or payload.get("tag_name"):
            source_kind = "tag_manifest"
        else:
            source_kind = "unknown"
    else:
        source_kind = declared_kind

    source_url = payload.get("source_url") or payload.get("url") or payload.get("html_url")
    release_url = payload.get("release_url") or (payload.get("html_url") if source_kind == "github_release" else None)
    return {
        "version": version,
        "source_kind": source_kind,
        "source_url": str(source_url) if isinstance(source_url, str) and source_url.strip() else None,
        "stable": source_kind == "github_release",
        "release_url": str(release_url) if isinstance(release_url, str) and release_url.strip() else None,
    }


def _version_result(
    *,
    local_version: str | None,
    remote_version: str | None,
    source_kind: str,
    source_url: str | None,
    checked_at: str | None,
    status: str,
    stable: bool,
    release_url: str | None = None,
    cache_marker: str = "not_cached",
) -> dict[str, Any]:
    result = {
        "local_version": _normalized_version(local_version),
        "remote_version": remote_version,
        "source_kind": source_kind,
        "source_url": source_url,
        "checked_at": checked_at,
        "status": status,
        "stable": stable,
        "cache_marker": cache_marker,
        "message_zh": LATEST_VERSION_UNCONFIRMED if status in {"check_failed", "not_checked"} else None,
        "message_en": "Unable to confirm the remote version this time" if status in {"check_failed", "not_checked"} else None,
    }
    if release_url is not None:
        result["release_url"] = release_url
    return result


def _status_for_versions(local_version: str | None, remote_version: str) -> str:
    local_parts = _version_parts(local_version)
    remote_parts = _version_parts(remote_version)
    if local_parts is None:
        return "checked"
    return "update_available" if remote_parts > local_parts else "up_to_date"


def check_latest_version(
    fetch: Callable[[], Any] | None,
    session_cache: MutableMapping[str, Any] | None,
    *,
    local_version: str | None = None,
    checked_at: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Perform an injected explicit update check using only host session state.

    ``fetch`` is deliberately supplied by the host. This helper has no network,
    global cache, filesystem scan, or background-update behavior.
    """
    if session_cache is not None and not force_refresh:
        cached = session_cache.get(_LATEST_VERSION_CACHE_KEY)
        if isinstance(cached, dict):
            remote = _normalized_version(cached.get("remote_version"))
            if remote is not None:
                result = _version_result(
                    local_version=local_version,
                    remote_version=remote,
                    source_kind=str(cached.get("source_kind") or "unknown"),
                    source_url=cached.get("source_url") if isinstance(cached.get("source_url"), str) else None,
                    checked_at=cached.get("checked_at") if isinstance(cached.get("checked_at"), str) else None,
                    status=_status_for_versions(local_version, remote),
                    stable=bool(cached.get("stable")),
                    release_url=cached.get("release_url") if isinstance(cached.get("release_url"), str) else None,
                    cache_marker="host_session_cache",
                )
                session_cache[_LATEST_VERSION_CACHE_KEY] = result
                return result
    if fetch is None:
        return _version_result(
            local_version=local_version,
            remote_version=None,
            source_kind="unknown",
            source_url=None,
            checked_at=checked_at,
            status="not_checked",
            stable=False,
        )
    try:
        remote = normalize_remote_version(fetch())
        result = _version_result(
            local_version=local_version,
            remote_version=remote["version"],
            source_kind=remote["source_kind"],
            source_url=remote["source_url"],
            checked_at=checked_at,
            status=_status_for_versions(local_version, remote["version"]),
            stable=remote["stable"],
            release_url=remote["release_url"],
            cache_marker="host_session_cache" if session_cache is not None else "not_cached",
        )
    except Exception:
        result = _version_result(
            local_version=local_version,
            remote_version=None,
            source_kind="unknown",
            source_url=None,
            checked_at=checked_at,
            status="check_failed",
            stable=False,
        )
    if session_cache is not None:
        session_cache[_LATEST_VERSION_CACHE_KEY] = result
    return result


def _update_response_line(result: dict[str, Any], language: str) -> str:
    remote = result.get("remote_version")
    local = result.get("local_version")
    source_kind = result.get("source_kind")
    source_label_zh = {
        "github_release": "GitHub 稳定发布",
        "tag_manifest": "GitHub 标签 manifest",
        "repository_version": "GitHub 仓库版本（非稳定发布）",
    }.get(source_kind, "远端版本来源")
    source_label_en = {
        "github_release": "GitHub stable release",
        "tag_manifest": "GitHub tag manifest",
        "repository_version": "GitHub repository version (not a stable release)",
    }.get(source_kind, "remote version source")
    if result.get("status") in {"check_failed", "not_checked"}:
        return result["message_zh"] if language == "zh" else result["message_en"]
    if language == "zh":
        if result.get("status") == "update_available":
            return f"发现可用更新：{remote}（当前 {local}；{source_label_zh}）。"
        return f"已确认远端版本：{remote}（{source_label_zh}）。"
    if result.get("status") == "update_available":
        return f"Update available: {remote} (current {local}; {source_label_en})."
    return f"Confirmed remote version: {remote} ({source_label_en})."


def detect_language(text: str) -> str:
    """Choose the response language from the submitted prompt."""
    return "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"


def metadata_response(
    text: str,
    *,
    active_root: str | Path | None = None,
    fetch_latest_version: Callable[[], Any] | None = None,
    session_cache: MutableMapping[str, Any] | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    """Return a metadata response without any implicit cache or network access."""
    language = detect_language(text)
    normalized = _normalized(text)
    version_request = _VERSION_REQUEST.search(normalized) is not None
    update_request = is_explicit_update_request(text)
    version = (
        read_active_plugin_version(active_root)
        if (version_request or update_request) and active_root is not None
        else None
    )
    latest_version = (
        check_latest_version(
            fetch_latest_version,
            session_cache,
            local_version=version,
            checked_at=checked_at,
        )
        if update_request
        else None
    )

    if language == "zh":
        if latest_version is not None:
            lines = [_update_response_line(latest_version, language)]
        elif is_status_request(text):
            lines = ["当前没有正在处理的 Superleads 任务。"]
        elif is_export_help_request(text):
            lines = ["导出需要已有本轮已核验结果；完成后可要求整理为 Excel 或 CSV。"]
        elif _CAPABILITY_REQUEST.search(normalized) is not None:
            lines = ["当前可用能力取决于本会话明确提供的工具；此元数据入口不会执行预检或能力探测。"]
        elif _FEEDBACK_REQUEST.search(normalized) is not None:
            lines = ["反馈入口：GitHub Issues（https://github.com/fleixweb/superleads/issues）。"]
        elif version is not None:
            lines = [f"当前激活的 Superleads 版本：{version}"]
        else:
            lines = ["未提供当前激活的 Superleads 插件目录，无法读取版本。"]
    elif latest_version is not None:
        lines = [_update_response_line(latest_version, language)]
    elif is_status_request(text):
        lines = ["There is no Superleads task currently in progress."]
    elif is_export_help_request(text):
        lines = ["Export needs a validated result from the current task; after that, you can request Excel or CSV."]
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
        "update_result": latest_version,
        "response_lines": lines,
    }
