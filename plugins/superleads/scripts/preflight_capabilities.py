#!/usr/bin/env python3
"""Preflight Superleads tool capability availability."""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from typing import Any
from _superleads_common import (
    CODEX_CLI_ADAPTER_OWNED_CAPABILITIES,
    adapter_reports_from_run,
    is_canonical_platform_id,
    load_json,
    resolve_capability_adapter_reports,
    write_json,
)

CAPABILITY_RULES={
"search.web":("发现候选池 / 搜索记录","不能支撑 Claim"),"source.open":("Observation","可形成来源记录"),"browser.render":("Observation","可形成来源记录"),"document.extract":("Observation","可形成文档来源记录"),"image.inspect":("Observation / Candidate clue","OCR 与视觉线索；不能支撑正式 Claim 或 ready 联系方式"),"mail.read":("Inquiry / source-note contact","只读入站邮件摘录；不能支撑正式 Claim、Assessment 或 ready 联系方式"),"source.capture":("Observation","保存摘录、定位、哈希"),"url.canonicalize":("Source / Entity","只做归一化"),"entity.dedupe":("Provisional Entity","不等于最终身份判定"),"translate.text":("Observation transform","必须保留原文"),"company.enrich":("Candidate clue / contextual","不能单独支撑主表"),"email.verify":("contact quality","不证明来源"),"domain.check":("technical Observation","不证明公司归属"),"social.visible.read":("Observation","不自动证明采购权"),"registry.lookup":("Observation","可支撑实体类 Claim"),"trademark.lookup":("Observation","可支撑品牌/商标类 Claim"),"maps.lookup":("Observation","可支撑地图联系方式/地址类 Claim"),"memory.recall":("Plan priority","不能进 Claim / Assessment")}
AVAILABLE={True,"true","available","yes","present","enabled"}; UNAVAILABLE={False,"false","unavailable","no","missing","disabled"}
FORMAL_RESEARCH_MESSAGE = "本轮环境无法联网检索并打开可记录来源，不能完成 Superleads 正式外贸研究。请切换到具备 Web Search 和来源打开能力的 Agent/环境后重试。若只需整理已有资料，可以继续，但那不是市场分析或客户开发报告。"
NOT_ASSESSED_MESSAGE = "未提供可判断的宿主能力信息，本次未评估。请先清点当前会话实际暴露的检索与来源打开操作，再以 --input 传入后重跑；或直接按无脚本路径检查宿主能力。"

def normalize_status(raw: Any) -> str:
    value=raw.strip().lower() if isinstance(raw,str) else raw
    if value in AVAILABLE: return "available"
    if value in UNAVAILABLE: return "missing"
    return "unknown"

def _is_adapter_payload(payload: dict[str, Any]) -> bool:
    return (
        isinstance(payload.get("capability_adapter_report"), dict)
        or isinstance(payload.get("capability_adapter_reports"), list)
        or any(key in payload for key in ("host_tools", "adapter"))
    )


def _has_assessable_capability_signal(payload: dict[str, Any]) -> bool:
    """Return whether a payload contains a non-null known capability value."""
    wrapped = payload.get("capabilities")
    if isinstance(wrapped, dict) and any(
        capability in wrapped and wrapped[capability] is not None
        for capability in CAPABILITY_RULES
    ):
        return True
    return any(
        capability in payload and payload[capability] is not None
        for capability in CAPABILITY_RULES
    )


def _is_not_assessed_payload(payload: dict[str, Any] | None) -> bool:
    """Keep absent capability evidence distinct from a failed assessment."""
    if payload is None:
        return True
    return (
        isinstance(payload, dict)
        and not _has_assessable_capability_signal(payload)
        and not _is_adapter_payload(payload)
        and not bool(payload.get("host_tool_inventory_complete"))
    )


def _adapter_reports_from_payload(payload: dict[str, Any]) -> list[Any]:
    reports = adapter_reports_from_run(payload)
    if not reports and any(key in payload for key in ("host_tools", "adapter")):
        reports.append(payload)
    return reports


def _missing_codex_adapter_result() -> dict[str, Any]:
    return {
        "recognized": False,
        "valid": False,
        "owned_capabilities": sorted(CODEX_CLI_ADAPTER_OWNED_CAPABILITIES),
        "mapped_capabilities": {capability: "unknown" for capability in CODEX_CLI_ADAPTER_OWNED_CAPABILITIES},
        "raw_mapped_capabilities": {capability: "unknown" for capability in CODEX_CLI_ADAPTER_OWNED_CAPABILITIES},
        "issues": [{
            "code": "codex_native_capability_adapter_required",
            "message": "Codex CLI capability requires a valid capability adapter report",
            "path": "capability_adapter_reports",
        }],
    }


def _invalid_platform_result() -> dict[str, Any]:
    owned = sorted(CODEX_CLI_ADAPTER_OWNED_CAPABILITIES)
    return {
        "recognized": False,
        "valid": False,
        "owned_capabilities": owned,
        "mapped_capabilities": {capability: "unknown" for capability in owned},
        "raw_mapped_capabilities": {capability: "unknown" for capability in owned},
        "issues": [{
            "code": "run_platform_not_canonical",
            "message": "Platform must be a non-empty canonical host ID before search/source capabilities may be promoted",
            "path": "platform",
        }],
    }


def _web_run_capability_failure(reports: list[Any], platform: str | None = None) -> dict[str, Any] | None:
    """Classify one failed host probe without scheduling another probe.

    Adapter resolution remains the source of truth for capability mapping. This
    small projection only turns a concrete `web__run` failure into a stable,
    user-actionable terminal state so callers do not retry a known-bad host
    operation for minutes.
    """
    if platform != "codex_cli":
        return None
    for report in reports:
        if not isinstance(report, dict):
            continue
        adapter = report.get("adapter")
        if (
            report.get("platform") != "codex_cli"
            or not isinstance(adapter, dict)
            or adapter.get("adapter_id") != "codex_cli_web_run"
        ):
            continue
        web_run = (report.get("host_tools") or {}).get("web__run")
        if not isinstance(web_run, dict):
            continue
        operations = web_run.get("operations")
        if not isinstance(operations, dict):
            continue
        for capability, name in (("search.web", "search_query"), ("source.open", "open")):
            operation = operations.get(name)
            records = operation if isinstance(operation, list) else [operation]
            for record in records:
                if not isinstance(record, dict) or _host_failure_status(record) != "failed":
                    continue
                status = record.get("http_status")
                error = " ".join(str(record.get(key) or "") for key in ("error", "message", "detail", "status_text")).casefold()
                if status == 404 or "404" in error:
                    reason = "http_404"
                elif "timeout" in error or "timed out" in error:
                    reason = "timeout"
                else:
                    reason = "host_operation_failed"
                return {
                    "capability": capability,
                    "reason": reason,
                    "retry": False,
                    "attempts": 1,
                }
    return None


def _host_failure_status(operation: dict[str, Any]) -> str:
    value = operation.get("status")
    return value.strip().casefold() if isinstance(value, str) else "unknown"


def preflight(payload: dict[str,Any]|None) -> dict[str,Any]:
    provided: dict[str, Any] = {}
    adapter_result: dict[str, Any] | None = None
    reports: list[Any] = []
    not_assessed = _is_not_assessed_payload(payload)
    if isinstance(payload, dict) and not not_assessed:
        has_capability_wrapper = "capabilities" in payload
        generic = payload.get("capabilities", {})
        if has_capability_wrapper and isinstance(generic, dict):
            provided = dict(generic)
        elif not has_capability_wrapper and any(capability in payload for capability in CAPABILITY_RULES):
            provided = dict(payload)
        reports = _adapter_reports_from_payload(payload)
        has_platform = "platform" in payload
        platform_is_canonical = not has_platform or is_canonical_platform_id(payload.get("platform"))
        if not platform_is_canonical:
            adapter_result = _invalid_platform_result()
            for capability in adapter_result["owned_capabilities"]:
                provided[capability] = adapter_result["mapped_capabilities"][capability]
        elif _is_adapter_payload(payload):
            adapter_result = resolve_capability_adapter_reports(reports)
            if has_platform and any(
                not isinstance(report, dict) or report.get("platform") != payload.get("platform")
                for report in reports
            ):
                adapter_result["valid"] = False
                adapter_result["issues"].append({
                    "code": "capability_adapter_run_platform_mismatch",
                    "message": "Capability adapter report platform must match the canonical Run platform",
                    "path": "capability_adapter_reports",
                })
            if payload.get("platform") == "codex_cli":
                capabilities_to_map = CODEX_CLI_ADAPTER_OWNED_CAPABILITIES
            else:
                # Non-Codex hosts report the capabilities actually exposed by
                # their own runtime. A stray Codex adapter probe must not erase
                # a verified ChatGPT Desktop, Claude, Hermes, or WorkBuddy
                # native capability.
                capabilities_to_map = ()
            for capability in capabilities_to_map:
                if capability in adapter_result["mapped_capabilities"]:
                    provided[capability] = adapter_result["mapped_capabilities"][capability]
                elif normalize_status(provided.get(capability)) == "available":
                    provided[capability] = "unknown"
        elif payload.get("platform") == "codex_cli" and any(
            normalize_status(provided.get(capability)) == "available"
            for capability in CODEX_CLI_ADAPTER_OWNED_CAPABILITIES
        ):
            adapter_result = _missing_codex_adapter_result()
            for capability in adapter_result["owned_capabilities"]:
                provided[capability] = adapter_result["mapped_capabilities"][capability]
    platform = payload.get("platform") if isinstance(payload, dict) else None
    capability_failure = _web_run_capability_failure(reports, platform)
    if capability_failure is not None:
        # A concrete failed host operation is stronger than an otherwise
        # malformed multi-capability report. Preserve fail-closed behavior for
        # every other capability, but never conceal the known unavailable one.
        provided[capability_failure["capability"]] = "missing"
    capabilities={cap:{"status":normalize_status(provided.get(cap)),"highest_layer":layer,"rule":rule} for cap,(layer,rule) in CAPABILITY_RULES.items()}
    source_capable=any(capabilities[c]["status"]=="available" for c in ("source.open","browser.render","document.extract"))
    search_capable=capabilities["search.web"]["status"]=="available"
    host_inventory_complete = bool(payload.get("host_tool_inventory_complete")) if isinstance(payload, dict) else False
    if not_assessed:
        discovery_status = "not_assessed"
        discovery_message = NOT_ASSESSED_MESSAGE
    elif search_capable and source_capable:
        discovery_status = "ready"
        discovery_message = "当前宿主已报告可用的搜索与来源读取能力，可以开始快速候选池。"
    elif search_capable:
        discovery_status = "degraded_search_only"
        discovery_message = "当前宿主可搜索但尚未验证来源读取；可以保留候选 URL 和搜索线索，事实与联系方式必须标为未核验。"
    elif capability_failure is not None and not host_inventory_complete:
        discovery_status = "needs_host_capability_check"
        discovery_message = "当前失败只说明该 Codex 适配器不可用。请先检查宿主实际暴露的原生搜索工具；不要重复调用同一失败适配器。"
    else:
        discovery_status = "blocked"
        discovery_message = "当前宿主未报告可用搜索能力；只能整理用户资料或返回查询计划，不能生成公开来源候选池。"
    formal_issues: list[dict[str, str]] = []
    if not not_assessed and not search_capable:
        formal_issues.append({
            "code": "formal_research_search_capability_missing",
            "message": "Formal research requires an available search.web capability.",
        })
    if not not_assessed and not source_capable:
        formal_issues.append({
            "code": "formal_research_source_open_capability_missing",
            "message": "Formal research requires source.open, browser.render, or document.extract.",
        })
    formal_ready = not not_assessed and not formal_issues
    if not_assessed:
        max_output = "formal_research_not_assessed"
        notes = []
        formal_message = NOT_ASSESSED_MESSAGE
    elif formal_ready:
        max_output = "formal_research_ready"
        notes: list[str] = []
        formal_message = "已具备搜索与来源打开能力，可以进入正式外贸研究；仍须按 Source/Observation/evidence/audit 门禁交付。"
    else:
        max_output = "formal_research_blocked"
        notes = [FORMAL_RESEARCH_MESSAGE]
        formal_message = FORMAL_RESEARCH_MESSAGE
        if capability_failure is not None:
            if capability_failure["reason"] == "http_404":
                failure_note = "web__run 返回 HTTP 404，已将该能力标为不可用；本轮只预检一次，不会重复重试。"
            elif capability_failure["reason"] == "timeout":
                failure_note = "web__run 预检超时，已将该能力标为不可用；本轮只预检一次，不会重复重试。"
            else:
                failure_note = "web__run 预检失败，已将该能力标为不可用；本轮只预检一次，不会重复重试。"
            notes.append(failure_note)
            formal_message = f"{FORMAL_RESEARCH_MESSAGE} {failure_note}"
    result = {
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "capabilities": capabilities,
        "max_output_without_manual_sources": max_output,
        "formal_research_status": "not_assessed" if not_assessed else ("ready" if formal_ready else "blocked"),
        "formal_research_issues": formal_issues,
        "formal_research_message": formal_message,
        "discovery_snapshot_status": discovery_status,
        "discovery_snapshot_message": discovery_message,
        "downgrade_notes": notes,
    }
    if capability_failure is not None:
        result["capability_failure"] = capability_failure
    if adapter_result is not None:
        result["adapter_report"] = {
            "recognized": adapter_result["recognized"],
            "valid": adapter_result["valid"],
            "owned_capabilities": adapter_result["owned_capabilities"],
            "mapped_capabilities": adapter_result["mapped_capabilities"],
            "issues": adapter_result["issues"],
        }
        if "adapter_results" in adapter_result:
            result["adapter_reports"] = [{
                "adapter_id": item.get("adapter_id"),
                "recognized": item.get("recognized"),
                "valid": item.get("valid"),
                "owned_capabilities": item.get("owned_capabilities"),
                "mapped_capabilities": item.get("mapped_capabilities"),
                "issues": item.get("issues"),
            } for item in adapter_result["adapter_results"]]
    return result

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--input"); p.add_argument("--output"); p.add_argument("--require-formal-research", action="store_true"); p.add_argument("--format",choices=["text","json"],default="text"); a=p.parse_args()
    result=preflight(load_json(a.input) if a.input else None)
    if a.output: write_json(a.output,result)
    if a.format=="json": print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"max_output_without_manual_sources: {result['max_output_without_manual_sources']}")
        if result["formal_research_status"] == "not_assessed":
            print("formal_research_status: not_assessed")
        for note in result["downgrade_notes"]: print(f"downgrade: {note}")
    if not a.require_formal_research or result["formal_research_status"] == "ready":
        return 0
    return 2 if result["formal_research_status"] == "not_assessed" else 1
if __name__=="__main__": raise SystemExit(main())
