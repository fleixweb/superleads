#!/usr/bin/env python3
"""Preflight Superleads tool capability availability."""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from typing import Any
from _superleads_common import load_json, write_json

CAPABILITY_RULES={
"search.web":("初筛客户 / 搜索记录","不能支撑 Claim"),"source.open":("Observation","可形成来源记录"),"browser.render":("Observation","可形成来源记录"),"document.extract":("Observation","可形成文档来源记录"),"source.capture":("Observation","保存摘录、定位、哈希"),"url.canonicalize":("Source / Entity","只做归一化"),"entity.dedupe":("Provisional Entity","不等于最终身份判定"),"translate.text":("Observation transform","必须保留原文"),"company.enrich":("Candidate clue / contextual","不能单独支撑主表"),"email.verify":("contact quality","不证明来源"),"domain.check":("technical Observation","不证明公司归属"),"social.visible.read":("Observation","不自动证明采购权"),"registry.lookup":("Observation","可支撑实体类 Claim"),"trademark.lookup":("Observation","可支撑品牌/商标类 Claim"),"maps.lookup":("Observation","可支撑地图联系方式/地址类 Claim"),"memory.recall":("Plan priority","不能进 Claim / Assessment")}
AVAILABLE={True,"true","available","yes","present","enabled"}; UNAVAILABLE={False,"false","unavailable","no","missing","disabled"}

def normalize_status(raw: Any) -> str:
    value=raw.strip().lower() if isinstance(raw,str) else raw
    if value in AVAILABLE: return "available"
    if value in UNAVAILABLE: return "missing"
    return "unknown"

def preflight(payload: dict[str,Any]|None) -> dict[str,Any]:
    provided={}
    if isinstance(payload,dict):
        provided=payload.get("capabilities",payload)
        if not isinstance(provided,dict): provided={}
    capabilities={cap:{"status":normalize_status(provided.get(cap)),"highest_layer":layer,"rule":rule} for cap,(layer,rule) in CAPABILITY_RULES.items()}
    source_capable=any(capabilities[c]["status"]=="available" for c in ("source.open","browser.render","document.extract"))
    search_capable=capabilities["search.web"]["status"]=="available"
    if source_capable: max_output="standard_development_list"; notes=[]
    elif search_capable: max_output="initial_lead_list"; notes=["No opened-source capability detected; do not create Claims or formal development list."]
    else: max_output="research_plan_only"; notes=["No search or source-opening capability detected; prepare plan or use user-provided materials only."]
    return {"checked_at":datetime.now(timezone.utc).replace(microsecond=0).isoformat(),"capabilities":capabilities,"max_output_without_manual_sources":max_output,"downgrade_notes":notes}

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
