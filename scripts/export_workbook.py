#!/usr/bin/env python3
"""Export Superleads research graph to XLSX or UTF-8-SIG CSV workbook sheets."""
from __future__ import annotations

import argparse, csv, json, re
from pathlib import Path
from typing import Any
from _superleads_common import canonical_contact_user_status, ensure_list, graph_hash, load_json, write_json
from audit_delivery import audit_graph

MODE_TO_STATUS={"initial":"initial_lead_list","standard":"standard_development_list","full":"full_review_package"}
DEFAULT_SHEETS=["客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","风险与说明"]
FULL_SHEETS=["开发需求","关键词与搜索思路","初筛客户名单","客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","已排除客户","检查说明"]
INITIAL_SHEETS=["初筛客户名单","风险与说明"]

def idx(graph:dict[str,Any], key:str, field:str)->dict[str,dict[str,Any]]:
    return {item.get(field):item for item in ensure_list(graph,key) if isinstance(item,dict) and item.get(field)}

def stringify(value:Any)->str:
    if value is None: return ""
    if isinstance(value,(dict,list)): return json.dumps(value,ensure_ascii=False,sort_keys=True)
    return str(value)

def contact_user_status(export_status:str|None)->str:
    return canonical_contact_user_status(export_status)

def review_modes(graph:dict[str,Any])->set[str]:
    run=get_current_run(graph)
    return {str(run["review_mode"])} if run.get("review_mode") else set()

def get_current_run(graph:dict[str,Any])->dict[str,Any]:
    runs=[r for r in ensure_list(graph,"runs") if isinstance(r,dict)]
    return runs[-1] if runs else {}

def current_brief_id(graph:dict[str,Any])->str|None:
    run=get_current_run(graph)
    if run.get("brief_id"): return run.get("brief_id")
    briefs=[b for b in ensure_list(graph,"briefs") if isinstance(b,dict)]
    return briefs[-1].get("brief_id") if briefs else None

def assessment_for_current_brief(graph:dict[str,Any], entity_id:str, brief_id:str|None, run_id:str|None)->dict[str,Any]:
    matches=[a for a in ensure_list(graph,"assessments") if isinstance(a,dict) and a.get("entity_id")==entity_id and (brief_id is None or a.get("brief_id")==brief_id) and (run_id is None or a.get("run_id")==run_id)]
    return matches[-1] if matches else {}

def assessments_for_current_brief(graph:dict[str,Any], brief_id:str|None, run_id:str|None)->list[dict[str,Any]]:
    return [a for a in ensure_list(graph,"assessments") if isinstance(a,dict) and (brief_id is None or a.get("brief_id")==brief_id) and (run_id is None or a.get("run_id")==run_id)]

def exportable_contact_claims(graph:dict[str,Any])->list[dict[str,Any]]:
    return [cc for cc in ensure_list(graph,"contact_claims") if isinstance(cc,dict) and cc.get("export_status") in {"ready","export_with_source_note"}]

def hold_contact_values(graph:dict[str,Any])->set[str]:
    contacts=idx(graph,"contact_points","contact_id")
    values=set()
    for cc in ensure_list(graph,"contact_claims"):
        if not isinstance(cc,dict) or cc.get("export_status") not in {"hold_no_source","hold_inferred"}:
            continue
        cp=contacts.get(cc.get("contact_id"),{})
        for field in ("normalized_value","source_literal"):
            value=cp.get(field)
            if isinstance(value,str) and len(value.strip())>=3:
                values.add(value.strip())
    return values

def redact_delivery_value(value:Any, forbidden:set[str])->Any:
    if isinstance(value,str):
        result=value
        for token in sorted(forbidden,key=len,reverse=True):
            result=re.sub(re.escape(token),"[已隐藏联系方式]",result,flags=re.IGNORECASE)
        return result
    if isinstance(value,list): return [redact_delivery_value(item,forbidden) for item in value]
    if isinstance(value,dict): return {key:redact_delivery_value(item,forbidden) for key,item in value.items()}
    return value

def redact_delivery_sheets(sheets:dict[str,list[dict[str,Any]]], forbidden:set[str])->dict[str,list[dict[str,Any]]]:
    return {name:[redact_delivery_value(row,forbidden) for row in rows] for name,rows in sheets.items()}

def build_sheets(graph:dict[str,Any], audit:dict[str,Any], mode:str)->dict[str,list[dict[str,Any]]]:
    entities=idx(graph,"entities","entity_id"); contacts=idx(graph,"contact_points","contact_id"); sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id")
    run=get_current_run(graph)
    brief_id=current_brief_id(graph)
    run_id=run.get("run_id")
    current_assessments=assessments_for_current_brief(graph,brief_id,run_id)
    sheets:dict[str,list[dict[str,Any]]]={}
    sheets["开发需求"]=[{"brief_id":b.get("brief_id"),"任务模式":b.get("task_mode"),"产品/服务":b.get("product_or_service"),"范围轴":stringify(b.get("scope_axis")),"目标国家/地区":stringify(b.get("target_country_or_region")),"目标客户类型":stringify(b.get("target_customer_type")),"输出模式":b.get("output_mode"),"联系方式需求":b.get("contact_detail_level")} for b in ensure_list(graph,"briefs") if isinstance(b,dict)]
    sheets["关键词与搜索思路"]=[]
    for p in ensure_list(graph,"plans"):
        if not isinstance(p,dict): continue
        for q in p.get("query_groups",[]) or []:
            sheets["关键词与搜索思路"].append({"plan_id":p.get("plan_id"),"查询组":stringify(q),"来源类别":stringify(p.get("source_categories")),"联系方式目标":stringify(p.get("contact_collection_targets")),"降级策略":stringify(p.get("downgrade_strategy"))})
    sheets["初筛客户名单"]=[{"candidate_id":c.get("candidate_id"),"公司/线索名称":c.get("name") or c.get("company_name"),"线索状态":c.get("status") or "初筛线索","来源提示":c.get("source_hint") or c.get("source_url"),"说明":c.get("note") or "仅作为初筛，不代表事实核查完成"} for c in ensure_list(graph,"candidates") if isinstance(c,dict)]
    sheets["客户信息总表"]=[]
    for entity_id,entity in entities.items():
        a=assessment_for_current_brief(graph,entity_id,brief_id,run_id)
        sheets["客户信息总表"].append({"entity_id":entity_id,"公司名称":entity.get("name") or entity.get("legal_name"),"官网":entity.get("website") or entity.get("domain"),"国家/地区":entity.get("country_or_region"),"客户类型":entity.get("customer_type"),"开发分层":a.get("disposition"),"证据依据":stringify(a.get("basis_claim_ids")),"缺失项":stringify(a.get("missing_requirements")),"需人工核查":stringify(a.get("manual_review_required")),"说明":stringify(a.get("rationale_structured"))})
    contact_rows=[]
    for cc in exportable_contact_claims(graph):
        if not isinstance(cc,dict): continue
        cp=contacts.get(cc.get("contact_id"),{}); ent=entities.get(cc.get("entity_id"),{}); obs=observations.get(cc.get("association_observation_id"),{}); src=sources.get(obs.get("source_id"),{}) if isinstance(obs,dict) else {}
        contact_rows.append({"公司名称":ent.get("name") or cc.get("entity_id"),"联系方式类型":cp.get("contact_type"),"联系方式":cp.get("normalized_value"),"原文":cp.get("source_literal"),"联系人":cc.get("person_name"),"职位/部门":cc.get("job_title") or cc.get("department"),"状态":contact_user_status(cc.get("export_status")),"来源上下文":cc.get("source_context"),"归属证据":cc.get("association_evidence_text"),"来源链接":src.get("final_url") or src.get("canonical_url"),"需人工核查说明":cc.get("manual_check_note")})
    sheets["联系方式汇总"]=contact_rows
    sheets["开发建议"]=[{"公司名称":entities.get(a.get("entity_id"),{}).get("name") or a.get("entity_id"),"开发分层":a.get("disposition"),"建议依据":stringify(a.get("rationale_structured")),"关联开发角度":stringify(a.get("related_hypothesis_ids_for_outreach")),"缺失项":stringify(a.get("missing_requirements"))} for a in current_assessments]
    pending=[]
    for lead in ensure_list(graph,"unassigned_contact_leads"):
        if isinstance(lead,dict):
            # An unassigned lead is deliberately not an exported contact. Do
            # not leak its raw value through the pending-work sheet.
            pending.append({"类型":"联系方式待确认","对象":lead.get("contact_id"),"原因":lead.get("reason"),"建议动作":lead.get("suggested_manual_check")})
    for cc in ensure_list(graph,"contact_claims"):
        if isinstance(cc,dict) and cc.get("export_status")=="needs_manual_association_review":
            pending.append({"类型":"联系方式待确认","对象":cc.get("contact_claim_id"),"原因":cc.get("manual_check_note") or "归属仍需人工确认", "建议动作":"核查来源页面中的实体归属。"})
    for f in ensure_list(graph,"review_findings"):
        if isinstance(f,dict) and f.get("status") != "verified_fixed":
            pending.append({"类型":"复核问题","对象":f.get("target_artifact"),"原因":f.get("issue"),"建议动作":f.get("required_fix")})
    sheets["待核查事项"]=pending
    sheets["风险与说明"]=[{"级别":i.get("severity"),"代码":i.get("code"),"说明":i.get("message"),"位置":i.get("path")} for i in audit.get("issues",[])] or [{"级别":"info","代码":"no_blockers","说明":"交付前检查未发现 critical/major 阻断项。","位置":""}]
    if "self_review_fallback" in review_modes(graph):
        sheets["风险与说明"].append({"级别":"disclosure","代码":"self_review_fallback","说明":"本次为 self_review_fallback 复核，未运行独立复核；交付时需保留该说明。","位置":"runs[-1].review_mode"})
    sheets["官网与来源链接"]=[{"source_id":s.get("source_id"),"canonical_url":s.get("canonical_url"),"final_url":s.get("final_url"),"来源关系":s.get("publisher_relation"),"来源类型":s.get("medium"),"来源归属提示":s.get("owner_hint")} for s in ensure_list(graph,"sources") if isinstance(s,dict)]
    sheets["已排除客户"]=[{"公司名称":entities.get(a.get("entity_id"),{}).get("name") or a.get("entity_id"),"状态":a.get("disposition"),"原因":stringify(a.get("rationale_structured"))} for a in current_assessments if a.get("disposition") in {"暂不建议","排除"}]
    sheets["检查说明"]=[{"audit_id":audit.get("audit_id"),"audited_at":audit.get("audited_at"),"research_graph_hash":audit.get("research_graph_hash"),"delivery_status":audit.get("delivery_status"),"issue_count":audit.get("issue_count")}]
    wanted=INITIAL_SHEETS if mode=="initial" else FULL_SHEETS if mode=="full" else DEFAULT_SHEETS
    return {name:sheets.get(name,[]) for name in wanted}

def safe_filename(name:str)->str: return re.sub(r"[\\/:*?\"<>|]+","_",name)

def write_csv_sheets(sheets:dict[str,list[dict[str,Any]]], out:Path)->list[str]:
    out.mkdir(parents=True,exist_ok=True); written=[]
    for sheet,rows in sheets.items():
        path=out/f"{safe_filename(sheet)}.csv"; fields=[]
        for row in rows:
            for k in row.keys():
                if k not in fields: fields.append(k)
        if not fields: fields=["说明"]; rows=[{"说明":"无记录"}]
        with path.open("w",encoding="utf-8-sig",newline="") as h:
            w=csv.DictWriter(h,fieldnames=fields); w.writeheader()
            for row in rows: w.writerow({k:stringify(row.get(k)) for k in fields})
        written.append(str(path))
    return written

def write_xlsx_sheets(sheets:dict[str,list[dict[str,Any]]], out:Path)->list[str]:
    from openpyxl import Workbook  # type: ignore
    out.mkdir(parents=True,exist_ok=True); wb=Workbook(); wb.remove(wb.active)
    for sheet,rows in sheets.items():
        ws=wb.create_sheet(title=sheet[:31]); fields=[]
        for row in rows:
            for k in row.keys():
                if k not in fields: fields.append(k)
        if not fields: fields=["说明"]; rows=[{"说明":"无记录"}]
        ws.append(fields)
        for row in rows: ws.append([stringify(row.get(k)) for k in fields])
    path=out/"superleads_workbook.xlsx"; wb.save(path); return [str(path)]

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("graph"); p.add_argument("--output-dir",required=True); p.add_argument("--mode",choices=["initial","standard","full"],default="standard"); p.add_argument("--format",choices=["auto","xlsx","csv"],default="auto"); p.add_argument("--manifest"); a=p.parse_args()
    graph=load_json(a.graph)
    if not isinstance(graph,dict): raise SystemExit("Research graph must be a JSON object")
    requested_status=MODE_TO_STATUS[a.mode]
    audit=audit_graph(graph, requested_delivery_status=requested_status)
    if a.mode in {"standard","full"} and not audit.get("ok"):
        print("Refusing formal export because audit status is needs_correction")
        for item in audit.get("issues",[]): print(f"[{item['severity']}] {item['code']}: {item['message']}")
        return 1
    if requested_status not in audit.get("allowed_delivery_statuses", [requested_status]) and a.mode in {"standard","full"}:
        print(f"Refusing export because {requested_status} is not in allowed_delivery_statuses")
        return 1
    sheets=redact_delivery_sheets(build_sheets(graph,audit,a.mode),hold_contact_values(graph)); out=Path(a.output_dir); chosen=a.format
    if chosen=="auto":
        try: import openpyxl; chosen="xlsx"  # noqa
        except Exception: chosen="csv"
    if chosen=="xlsx":
        try: files=write_xlsx_sheets(sheets,out)
        except Exception as exc:
            if a.format=="xlsx": raise
            print(f"XLSX export unavailable ({exc}); falling back to UTF-8-SIG CSV"); files=write_csv_sheets(sheets,out); chosen="csv"
    else: files=write_csv_sheets(sheets,out)
    disclosures=["初筛/弱证据项仅用于销售人工核查，不代表事实核查完成。"] if a.mode=="initial" else []
    if "self_review_fallback" in review_modes(graph):
        disclosures.append("本次为 self_review_fallback 复核，未运行独立复核；交付时需保留该说明。")
    current_run=get_current_run(graph)
    brief_id=current_brief_id(graph)
    exported_contact_claims=exportable_contact_claims(graph)
    exported_assessments=assessments_for_current_brief(graph,brief_id,current_run.get("run_id"))
    review_cycle_id=current_run.get("review_cycle_id") or f"review_{current_run.get('run_id','current')}"
    manifest={"delivery_manifest_id":f"manifest_{audit.get('research_graph_hash','current')[:12]}","run_id":current_run.get("run_id"),"brief_id":current_run.get("brief_id") or brief_id,"plan_id":current_run.get("plan_id") or (ensure_list(graph,"plans") or [{}])[-1].get("plan_id"),"audit_id":audit.get("audit_id"),"audit_graph_hash":audit.get("audit_graph_hash"),"research_graph_hash":graph_hash(graph),"review_cycle_id":review_cycle_id,"generated_at":audit.get("audited_at"),"delivery_status":requested_status if audit.get("ok") or a.mode=="initial" else "needs_correction","output_mode":a.mode,"exported_entity_ids":[e.get("entity_id") for e in ensure_list(graph,"entities") if isinstance(e,dict) and e.get("entity_id")],"exported_contact_ids":[cc.get("contact_id") for cc in exported_contact_claims if cc.get("contact_id")],"exported_contact_claim_ids":[cc.get("contact_claim_id") for cc in exported_contact_claims if cc.get("contact_claim_id")],"exported_assessment_ids":[x.get("assessment_id") for x in exported_assessments if x.get("assessment_id")],"output_files":files,"warnings":[i.get("message") for i in audit.get("issues",[])],"disclosures":disclosures,"format":chosen,"audit_snapshot":audit}
    manifest=redact_delivery_value(manifest,hold_contact_values(graph))
    if a.manifest: write_json(a.manifest,manifest)
    print(json.dumps({"ok":True,"format":chosen,"files":files,"audit":audit,"manifest":manifest},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
