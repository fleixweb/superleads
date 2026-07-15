#!/usr/bin/env python3
"""Export Superleads research graph to XLSX or UTF-8-SIG CSV workbook sheets."""
from __future__ import annotations

import argparse, csv, json, re
from pathlib import Path
from typing import Any
from _superleads_common import (
    canonical_contact_user_status,
    connected_source_display,
    contains_local_path,
    ensure_list,
    graph_hash,
    load_json,
    safe_public_source_url,
    scope_status_user_label,
    source_evidence_scope,
    formal_exception_entity_ids,
    formal_exception_result_label,
    formal_targeting_contract_required,
    user_provided_source_display,
    write_json,
)
from audit_delivery import audit_graph

MODE_TO_STATUS={"initial":"initial_lead_list","standard":"standard_development_list","full":"full_review_package","inquiry":"inquiry_followup_queue"}
DEFAULT_SHEETS=["客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","风险与说明"]
FULL_SHEETS=["开发需求","关键词与搜索思路","初筛客户名单","客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","已排除客户","检查说明"]
INITIAL_SHEETS=["初筛客户名单","风险与说明"]
INQUIRY_SHEETS=["询盘待办","来信联系人","询盘信息摘要","待补充信息","来源说明"]

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

def scope_decision_for_current_brief(graph:dict[str,Any], entity_id:str, brief_id:str|None, run_id:str|None)->dict[str,Any]:
    matches=[d for d in ensure_list(graph,"scope_decisions") if isinstance(d,dict) and d.get("entity_id")==entity_id and (brief_id is None or d.get("brief_id")==brief_id) and (run_id is None or d.get("run_id")==run_id)]
    return matches[-1] if matches else {}

def formal_export_entities(graph:dict[str,Any], brief_id:str|None, run_id:str|None)->set[str]:
    briefs=idx(graph,"briefs","brief_id")
    brief=briefs.get(brief_id)
    contract_required=formal_targeting_contract_required(brief)
    exception_entities=formal_exception_entity_ids(brief)
    exception_label=formal_exception_result_label(brief)
    result:set[str]=set()
    for assessment in assessments_for_current_brief(graph,brief_id,run_id):
        entity_id=str(assessment.get("entity_id"))
        if assessment.get("disposition") not in {"重点开发","推荐跟进"}:
            continue
        if exception_label:
            eligible=entity_id in exception_entities
        elif contract_required:
            eligible=scope_decision_for_current_brief(graph,entity_id,brief_id,run_id).get("overall_status")=="in_scope"
        else:
            eligible=True
        if eligible:
            result.add(entity_id)
    return result

def exportable_contact_claims(graph:dict[str,Any], allowed_entity_ids:set[str]|None=None)->list[dict[str,Any]]:
    sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id"); contacts=idx(graph,"contact_points","contact_id")
    result=[]
    for cc in ensure_list(graph,"contact_claims"):
        if not isinstance(cc,dict) or cc.get("export_status") not in {"ready","export_with_source_note"}:
            continue
        if allowed_entity_ids is not None and str(cc.get("entity_id")) not in allowed_entity_ids:
            continue
        purpose="contact_ready" if cc.get("export_status")=="ready" else "contact_with_source_note"
        cp=contacts.get(cc.get("contact_id"),{})
        source_obs=observations.get(cp.get("source_observation_id")) if isinstance(cp,dict) else None
        assoc_obs=observations.get(cc.get("association_observation_id"))
        source_source=sources.get(source_obs.get("source_id")) if isinstance(source_obs,dict) else None
        assoc_source=sources.get(assoc_obs.get("source_id")) if isinstance(assoc_obs,dict) else None
        if source_evidence_scope(source_source,source_obs,purpose)[0] and source_evidence_scope(assoc_source,assoc_obs,purpose)[0]:
            result.append(cc)
    return result

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

LOCAL_PATH_PATTERNS=(
    re.compile(r"(?i)file://[^\s\"']+"),
    re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s\"']*"),
    re.compile(r"(?<![:\w])/(?:home|users|tmp|var|etc|mnt|private|volumes)(?:/[^\s\"']*)?",re.IGNORECASE),
)

def redact_local_paths(value:Any)->Any:
    if isinstance(value,str):
        result=value
        if contains_local_path(result):
            result="[已隐藏本地路径]"
        for pattern in LOCAL_PATH_PATTERNS:
            result=pattern.sub("[已隐藏本地路径]",result)
        return result
    if isinstance(value,list): return [redact_local_paths(item) for item in value]
    if isinstance(value,dict): return {key:redact_local_paths(item) for key,item in value.items()}
    return value

def redact_delivery_sheets(sheets:dict[str,list[dict[str,Any]]], forbidden:set[str])->dict[str,list[dict[str,Any]]]:
    return {name:[redact_delivery_value(row,forbidden) for row in rows] for name,rows in sheets.items()}

def source_display(source:dict[str,Any], observation:dict[str,Any]|None=None)->str:
    user_file=user_provided_source_display(source,observation or {})
    if user_file: return user_file
    connected=connected_source_display(source,observation or {})
    if connected: return connected
    return "公开来源" if safe_public_source_url(source) else "来源信息不可用"

def build_inquiry_sheets(graph:dict[str,Any])->dict[str,list[dict[str,Any]]]:
    entities=idx(graph,"entities","entity_id"); contacts=idx(graph,"contact_points","contact_id"); sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id")
    contact_claims=[cc for cc in ensure_list(graph,"contact_claims") if isinstance(cc,dict)]
    hold_contact_ids={cc.get("contact_id") for cc in contact_claims if cc.get("export_status") in {"hold_no_source","hold_inferred"}}
    todo=[]; people=[]; summaries=[]; missing=[]; source_rows=[]; used_sources:set[str]=set()
    for inquiry in ensure_list(graph,"inquiries"):
        if not isinstance(inquiry,dict): continue
        source=sources.get(inquiry.get("source_id"),{}); observation=observations.get(inquiry.get("observation_id"),{})
        entity=entities.get(inquiry.get("entity_id"),{})
        entity_name=entity.get("name") or entity.get("legal_name") or "待解析主体"
        received=str(inquiry.get("received_at") or "")[:10]
        todo.append({"来信日期":received,"公司/主体":entity_name,"优先级":inquiry.get("priority"),"待办":inquiry.get("requested_action"),"状态":inquiry.get("inquiry_status")})
        summaries.append({"来信日期":received,"公司/主体":entity_name,"邮件中提及的信息":inquiry.get("mentioned_product_or_need"),"请求摘要":inquiry.get("request_excerpt"),"主体解析状态":inquiry.get("entity_resolution_status"),"外部核验状态":inquiry.get("external_verification_status")})
        for item in inquiry.get("missing_information") or []:
            missing.append({"公司/主体":entity_name,"待补充信息":item,"建议动作":inquiry.get("requested_action")})
        contact_id=inquiry.get("contact_id"); point=contacts.get(contact_id,{})
        if isinstance(point,dict) and contact_id not in hold_contact_ids and point.get("normalized_value"):
            people.append({"公司/主体":entity_name,"联系方式":point.get("normalized_value"),"联系方式类型":point.get("contact_type"),"状态":"来信联系人/待核验","来源说明":source_display(source,observation if isinstance(observation,dict) else {})})
        if isinstance(source,dict) and source.get("source_id") not in used_sources:
            used_sources.add(source.get("source_id"))
            source_rows.append({"来源说明":source_display(source,observation if isinstance(observation,dict) else {}),"来信日期":received})
    return {"询盘待办":todo,"来信联系人":people,"询盘信息摘要":summaries,"待补充信息":missing,"来源说明":source_rows}

def build_sheets(graph:dict[str,Any], audit:dict[str,Any], mode:str)->dict[str,list[dict[str,Any]]]:
    if mode=="inquiry":
        return build_inquiry_sheets(graph)
    entities=idx(graph,"entities","entity_id"); contacts=idx(graph,"contact_points","contact_id"); sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id")
    run=get_current_run(graph)
    brief_id=current_brief_id(graph)
    run_id=run.get("run_id")
    briefs=idx(graph,"briefs","brief_id")
    brief=briefs.get(brief_id)
    exception_label=formal_exception_result_label(brief)
    current_assessments=assessments_for_current_brief(graph,brief_id,run_id)
    allowed_entities=formal_export_entities(graph,brief_id,run_id)
    sheets:dict[str,list[dict[str,Any]]]={}
    sheets["开发需求"]=[{"产品/服务":b.get("product_or_service"),"范围轴":stringify(b.get("scope_axis")),"目标国家/地区":stringify(b.get("target_country_or_region")),"目标客户类型":stringify(b.get("target_customer_type")),"输出模式":b.get("output_mode"),"联系方式需求":b.get("contact_detail_level")} for b in ensure_list(graph,"briefs") if isinstance(b,dict)]
    sheets["关键词与搜索思路"]=[]
    for p in ensure_list(graph,"plans"):
        if not isinstance(p,dict): continue
        for q in p.get("query_groups",[]) or []:
            if not isinstance(q,dict):
                continue
            sheets["关键词与搜索思路"].append({"核查目的":q.get("query_purpose") or q.get("purpose") or "公开信息核查","搜索思路":stringify(q.get("queries")),"来源类别":stringify(p.get("source_categories")),"联系方式目标":stringify(p.get("contact_collection_targets")),"证据不足时":stringify(p.get("downgrade_strategy"))})
    sheets["初筛客户名单"]=[{"公司/线索名称":c.get("name") or c.get("company_name"),"方向状态":scope_status_user_label(next((d.get("overall_status") for d in ensure_list(graph,"scope_decisions") if isinstance(d,dict) and d.get("candidate_id")==c.get("candidate_id")),"needs_confirmation")),"线索状态":c.get("status") or "初筛线索","来源提示":c.get("source_hint") or c.get("source_url"),"说明":c.get("note") or "方向样本，等待确认后再扩展。"} for c in ensure_list(graph,"candidates") if isinstance(c,dict)]
    sheets["客户信息总表"]=[]
    for entity_id,entity in entities.items():
        a=assessment_for_current_brief(graph,entity_id,brief_id,run_id)
        decision=scope_decision_for_current_brief(graph,entity_id,brief_id,run_id)
        if entity_id in allowed_entities:
            row={"公司名称":entity.get("name") or entity.get("legal_name"),"官网":entity.get("website") or entity.get("domain"),"国家/地区":entity.get("country_or_region"),"客户类型":entity.get("customer_type"),"开发分层":a.get("disposition"),"缺失项":stringify(a.get("missing_requirements")),"需人工核查":stringify(a.get("manual_review_required"))}
            if exception_label:
                row.update({"结果类型":exception_label,"说明":"仅针对当前用户指定输入完成核查，不表示符合本次开发方向。"})
            else:
                row.update({"方向状态":scope_status_user_label(decision.get("overall_status")),"说明":"已按本次方向核查公开业务信息。"})
            sheets["客户信息总表"].append(row)
    observations_by_source:dict[str,dict[str,Any]]={}
    for observation in observations.values():
        if isinstance(observation,dict) and observation.get("source_id") not in observations_by_source:
            observations_by_source[observation.get("source_id")]=observation
    contact_rows=[]
    for cc in exportable_contact_claims(graph,allowed_entities):
        if not isinstance(cc,dict): continue
        cp=contacts.get(cc.get("contact_id"),{}); ent=entities.get(cc.get("entity_id"),{}); obs=observations.get(cc.get("association_observation_id"),{}); src=sources.get(obs.get("source_id"),{}) if isinstance(obs,dict) else {}
        contact_rows.append({"公司名称":ent.get("name") or cc.get("entity_id"),"联系方式类型":cp.get("contact_type"),"联系方式":cp.get("normalized_value"),"原文":cp.get("source_literal"),"联系人":cc.get("person_name"),"职位/部门":cc.get("job_title") or cc.get("department"),"状态":contact_user_status(cc.get("export_status")),"来源上下文":cc.get("source_context"),"归属证据":cc.get("association_evidence_text"),"来源说明":source_display(src,obs),"来源链接":safe_public_source_url(src),"需人工核查说明":cc.get("manual_check_note")})
    sheets["联系方式汇总"]=contact_rows
    hypotheses=idx(graph,"hypotheses","hypothesis_id")
    sheets["开发建议"]=[]
    for assessment in current_assessments:
        if str(assessment.get("entity_id")) not in allowed_entities:
            continue
        row={"公司名称":entities.get(assessment.get("entity_id"),{}).get("name") or assessment.get("entity_id"),"开发分层":assessment.get("disposition"),"建议切入点":"；".join(str(hypotheses.get(hypothesis_id,{}).get("hypothesis_text") or "") for hypothesis_id in assessment.get("related_hypothesis_ids_for_outreach",[]) if hypotheses.get(hypothesis_id)) or "结合公开业务信息准备首次沟通。","缺失项":stringify(assessment.get("missing_requirements"))}
        if exception_label:
            row["结果类型"]=exception_label
        else:
            row["方向状态"]="符合本次方向"
        sheets["开发建议"].append(row)
    pending=[]
    for lead in ensure_list(graph,"unassigned_contact_leads"):
        if isinstance(lead,dict):
            # An unassigned lead is deliberately not an exported contact. Do
            # not leak its raw value through the pending-work sheet.
            pending.append({"类型":"联系方式待确认","对象":"待确认联系方式","原因":lead.get("reason"),"建议动作":lead.get("suggested_manual_check")})
    for cc in ensure_list(graph,"contact_claims"):
        if isinstance(cc,dict) and cc.get("export_status")=="needs_manual_association_review":
            pending.append({"类型":"联系方式待确认","对象":"待确认联系方式","原因":cc.get("manual_check_note") or "归属仍需人工确认", "建议动作":"核查来源页面中的实体归属。"})
    for f in ensure_list(graph,"review_findings"):
        if isinstance(f,dict) and f.get("status") != "verified_fixed":
            pending.append({"类型":"待处理问题","对象":"待处理项目","原因":f.get("issue"),"建议动作":f.get("required_fix")})
    for decision in ensure_list(graph,"scope_decisions"):
        if not isinstance(decision,dict) or decision.get("brief_id")!=brief_id or decision.get("run_id")!=run_id or decision.get("overall_status")=="in_scope":
            continue
        entity=entities.get(decision.get("entity_id"),{})
        candidate=next((item for item in ensure_list(graph,"candidates") if isinstance(item,dict) and item.get("candidate_id")==decision.get("candidate_id")),{})
        pending.append({"类型":"方向核查","对象":entity.get("name") or candidate.get("name") or candidate.get("company_name") or "待确认对象","原因":scope_status_user_label(decision.get("overall_status")),"建议动作":"根据本次方向补充公开证据或等待确认。"})
    sheets["待核查事项"]=pending
    sheets["风险与说明"]=[{"提示级别":i.get("severity"),"说明":i.get("message")} for i in audit.get("issues",[])] or [{"提示级别":"提示","说明":"交付前检查未发现影响交付的问题。"}]
    if "self_review_fallback" in review_modes(graph):
        sheets["风险与说明"].append({"提示级别":"说明","说明":"本次未运行独立复核，建议在使用前进行人工确认。"})
    sheets["官网与来源链接"]=[{"来源说明":source_display(s,observations_by_source.get(s.get("source_id"))),"来源链接":safe_public_source_url(s),"来源关系":s.get("publisher_relation"),"来源类型":s.get("medium")} for s in ensure_list(graph,"sources") if isinstance(s,dict)]
    sheets["已排除客户"]=[{"公司名称":entities.get(d.get("entity_id"),{}).get("name") or d.get("candidate_id") or "待确认对象","方向状态":scope_status_user_label(d.get("overall_status")),"说明":d.get("decision_summary")} for d in ensure_list(graph,"scope_decisions") if isinstance(d,dict) and d.get("brief_id")==brief_id and d.get("run_id")==run_id and d.get("overall_status") in {"out_of_scope","reference_only"}]
    sheets["检查说明"]=[{"检查时间":audit.get("audited_at"),"交付级别":{"standard_development_list":"标准开发名单","full_review_package":"完整核查版"}.get(audit.get("delivery_status"),"初筛客户名单"),"检查结果":"未发现影响交付的问题" if not audit.get("issues") else "存在待处理问题"}]
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
        written.append(path.name)
    return written

def write_xlsx_sheets(sheets:dict[str,list[dict[str,Any]]], out:Path, filename:str="superleads_workbook.xlsx")->list[str]:
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
    path=out/safe_filename(filename); wb.save(path); return [path.name]

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("graph"); p.add_argument("output_path",nargs="?"); p.add_argument("--output-dir"); p.add_argument("--mode",choices=["initial","standard","full","inquiry"],default="standard"); p.add_argument("--format",choices=["auto","xlsx","csv"],default="auto"); p.add_argument("--manifest"); a=p.parse_args()
    if bool(a.output_path)==bool(a.output_dir): raise SystemExit("Provide exactly one of output_path or --output-dir")
    graph=load_json(a.graph)
    if not isinstance(graph,dict): raise SystemExit("Research graph must be a JSON object")
    requested_status=MODE_TO_STATUS[a.mode]
    audit=audit_graph(graph, requested_delivery_status=requested_status)
    if a.mode in {"standard","full","inquiry"} and not audit.get("ok"):
        print("Refusing export because audit status is needs_correction")
        for item in audit.get("issues",[]): print(f"[{item['severity']}] {item['code']}: {item['message']}")
        return 1
    if requested_status not in audit.get("allowed_delivery_statuses", [requested_status]) and a.mode in {"standard","full","inquiry"}:
        print(f"Refusing export because {requested_status} is not in allowed_delivery_statuses")
        return 1
    sheets=redact_local_paths(redact_delivery_sheets(build_sheets(graph,audit,a.mode),hold_contact_values(graph))); out=Path(a.output_dir) if a.output_dir else Path(a.output_path).parent; chosen=a.format
    if a.output_path and Path(a.output_path).suffix.casefold()==".xlsx" and chosen=="auto": chosen="xlsx"
    if chosen=="auto":
        try: import openpyxl; chosen="xlsx"  # noqa
        except Exception: chosen="csv"
    if chosen=="xlsx":
        try: files=write_xlsx_sheets(sheets,out,Path(a.output_path).name if a.output_path else "superleads_workbook.xlsx")
        except Exception as exc:
            if a.format=="xlsx": raise
            print(f"XLSX export unavailable ({exc}); falling back to UTF-8-SIG CSV"); files=write_csv_sheets(sheets,out); chosen="csv"
    else: files=write_csv_sheets(sheets,out)
    disclosures=["初筛/弱证据项仅用于销售人工核查，不代表事实核查完成。"] if a.mode=="initial" else (["询盘信息仅记录来信中提及的内容，不代表企业资格或采购权已核验。"] if a.mode=="inquiry" else [])
    if "self_review_fallback" in review_modes(graph):
        disclosures.append("本次为 self_review_fallback 复核，未运行独立复核；交付时需保留该说明。")
    current_run=get_current_run(graph)
    brief_id=current_brief_id(graph)
    exported_entity_ids=formal_export_entities(graph,brief_id,current_run.get("run_id")) if a.mode!="inquiry" else set()
    exported_contact_claims=exportable_contact_claims(graph,exported_entity_ids) if a.mode!="inquiry" else []
    exported_assessments=[item for item in assessments_for_current_brief(graph,brief_id,current_run.get("run_id")) if str(item.get("entity_id")) in exported_entity_ids] if a.mode!="inquiry" else []
    inquiry_contact_ids=[item.get("contact_id") for item in ensure_list(graph,"inquiries") if isinstance(item,dict) and item.get("contact_id")] if a.mode=="inquiry" else []
    review_cycle_id=current_run.get("review_cycle_id") if a.mode=="inquiry" else current_run.get("review_cycle_id") or f"review_{current_run.get('run_id','current')}"
    manifest={"delivery_manifest_id":f"manifest_{audit.get('research_graph_hash','current')[:12]}","run_id":current_run.get("run_id"),"brief_id":None if a.mode=="inquiry" else current_run.get("brief_id") or brief_id,"plan_id":None if a.mode=="inquiry" else current_run.get("plan_id") or (ensure_list(graph,"plans") or [{}])[-1].get("plan_id"),"audit_id":audit.get("audit_id"),"audit_graph_hash":audit.get("audit_graph_hash"),"research_graph_hash":graph_hash(graph),"review_cycle_id":review_cycle_id,"generated_at":audit.get("audited_at"),"delivery_status":requested_status if audit.get("ok") or a.mode=="initial" else "needs_correction","output_mode":a.mode,"exported_entity_ids":sorted(exported_entity_ids),"exported_contact_ids":inquiry_contact_ids or [cc.get("contact_id") for cc in exported_contact_claims if cc.get("contact_id")],"exported_contact_claim_ids":[cc.get("contact_claim_id") for cc in exported_contact_claims if cc.get("contact_claim_id")],"exported_assessment_ids":[x.get("assessment_id") for x in exported_assessments if x.get("assessment_id")],"output_files":files,"warnings":[i.get("message") for i in audit.get("issues",[])],"disclosures":disclosures,"format":chosen,"audit_snapshot":audit}
    manifest=redact_local_paths(redact_delivery_value(manifest,hold_contact_values(graph)))
    if a.manifest: write_json(a.manifest,manifest)
    print(json.dumps({"ok":True,"format":chosen,"files":files,"audit":audit,"manifest":manifest},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
