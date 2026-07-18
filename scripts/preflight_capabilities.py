#!/usr/bin/env python3
"""Preflight Superleads tool capability availability."""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from typing import Any
from _superleads_common import (
    CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES,
    CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES,
    adapter_reports_from_run,
    is_canonical_platform_id,
    load_json,
    resolve_capability_adapter_reports,
    write_json,
)

CAPABILITY_RULES={
"search.web":("发现候选池 / 搜索记录","不能支撑 Claim"),"source.open":("Observation","可形成来源记录"),"browser.render":("Observation","可形成来源记录"),"document.extract":("Observation","可形成文档来源记录"),"image.inspect":("Observation / Candidate clue","OCR 与视觉线索；不能支撑正式 Claim 或 ready 联系方式"),"mail.read":("Inquiry / source-note contact","只读入站邮件摘录；不能支撑正式 Claim、Assessment 或 ready 联系方式"),"source.capture":("Observation","保存摘录、定位、哈希"),"url.canonicalize":("Source / Entity","只做归一化"),"entity.dedupe":("Provisional Entity","不等于最终身份判定"),"translate.text":("Observation transform","必须保留原文"),"company.enrich":("Candidate clue / contextual","不能单独支撑主表"),"email.verify":("contact quality","不证明来源"),"domain.check":("technical Observation","不证明公司归属"),"social.visible.read":("Observation","不自动证明采购权"),"registry.lookup":("Observation","可支撑实体类 Claim"),"trademark.lookup":("Observation","可支撑品牌/商标类 Claim"),"maps.lookup":("Observation","可支撑地图联系方式/地址类 Claim"),"memory.recall":("Plan priority","不能进 Claim / Assessment")}
AVAILABLE={True,"true","available","yes","present","enabled"}; UNAVAILABLE={False,"false","unavailable","no","missing","disabled"}

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


def _adapter_reports_from_payload(payload: dict[str, Any]) -> list[Any]:
    reports = adapter_reports_from_run(payload)
    if not reports and any(key in payload for key in ("host_tools", "adapter")):
        reports.append(payload)
    return reports


def _missing_codex_adapter_result() -> dict[str, Any]:
    return {
        "recognized": False,
        "valid": False,
        "owned_capabilities": sorted(set(CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES) | set(CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES)),
        "mapped_capabilities": {capability: "unknown" for capability in set(CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES) | set(CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES)},
        "raw_mapped_capabilities": {capability: "unknown" for capability in set(CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES) | set(CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES)},
        "issues": [{
            "code": "codex_native_capability_adapter_required",
            "message": "Codex CLI native search/source capability requires a valid capability adapter report",
            "path": "capability_adapter_reports",
        }],
    }


def _invalid_platform_result() -> dict[str, Any]:
    owned = sorted(set(CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES) | set(CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES))
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


def preflight(payload: dict[str,Any]|None) -> dict[str,Any]:
    provided: dict[str, Any] = {}
    adapter_result: dict[str, Any] | None = None
    if isinstance(payload, dict):
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
                for capability in adapter_result["owned_capabilities"]:
                    adapter_result["mapped_capabilities"][capability] = "unknown"
            for capability in adapter_result["owned_capabilities"]:
                provided[capability] = adapter_result["mapped_capabilities"][capability]
        elif payload.get("platform") == "codex_cli" and any(
            normalize_status(provided.get(capability)) == "available"
            for capability in set(CODEX_NATIVE_WEB_SEARCH_OWNED_CAPABILITIES) | set(CODEX_SHELL_HTTP_SOURCE_OPEN_OWNED_CAPABILITIES)
        ):
            adapter_result = _missing_codex_adapter_result()
            for capability in adapter_result["owned_capabilities"]:
                provided[capability] = adapter_result["mapped_capabilities"][capability]
    capabilities={cap:{"status":normalize_status(provided.get(cap)),"highest_layer":layer,"rule":rule} for cap,(layer,rule) in CAPABILITY_RULES.items()}
    source_capable=any(capabilities[c]["status"]=="available" for c in ("source.open","browser.render","document.extract"))
    search_capable=capabilities["search.web"]["status"]=="available"
    if source_capable: max_output="standard_development_list"; notes=[]
    elif search_capable: max_output="initial_lead_list"; notes=["No opened-source capability detected; stay in discovery candidate pool mode and do not create Claims or a formal development list."]
    else: max_output="research_plan_only"; notes=["No search or source-opening capability detected; prepare a research plan or use user-provided materials only."]
    result = {"checked_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"capabilities":capabilities,"max_output_without_manual_sources":max_output,"downgrade_notes":notes}
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
    p=argparse.ArgumentParser(); p.add_argument("--input"); p.add_argument("--output"); p.add_argument("--format",choices=["text","json"],default="text"); a=p.parse_args()
    result=preflight(load_json(a.input) if a.input else None)
    if a.output: write_json(a.output,result)
    if a.format=="json": print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print(f"max_output_without_manual_sources: {result['max_output_without_manual_sources']}")
        for note in result["downgrade_notes"]: print(f"downgrade: {note}")
    return 0
if __name__=="__main__": raise SystemExit(main())
