#!/usr/bin/env python3
"""Export Superleads research graph to XLSX or UTF-8-SIG CSV workbook sheets."""
from __future__ import annotations

import argparse, csv, json, re
from pathlib import Path
from typing import Any
from _superleads_common import (
    business_relevance_user_label,
    canonical_contact_user_status,
    connected_source_display,
    contains_local_path,
    ensure_list,
    public_signal_status_user_label,
    graph_hash,
    is_safe_public_http_url,
    is_safe_public_website_or_domain,
    load_json,
    safe_public_source_url,
    scope_status_user_label,
    source_evidence_scope,
    formal_exception_entity_ids,
    formal_exception_result_label,
    formal_targeting_contract_required,
    review_provenance_disclosure,
    review_provenance_snapshot,
    user_provided_source_display,
    write_json,
)
from background_report import background_contact_values_to_redact, build_background_report_sheets, validate_background_report

MODE_TO_STATUS={"initial":"initial_lead_list","standard":"standard_development_list","full":"full_review_package","inquiry":"inquiry_followup_queue"}
DEFAULT_SHEETS=["客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","风险与说明"]
FULL_SHEETS=["开发需求","关键词与搜索思路","发现候选池","客户信息总表","联系方式汇总","开发建议","官网与来源链接","待核查事项","已排除客户","检查说明"]
INITIAL_SHEETS=["发现候选池","联系方式汇总","官网与来源链接","搜索覆盖与收敛","待核查事项","已排除客户","风险与说明"]
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

DELIVERY_INTERNAL_KEYS={
    "query_text", "raw_search_summary", "search_summary", "executor_actor_id",
    "execution_session_id", "reviewer_actor_id", "reviewer_session_id",
    "concrete_tool", "capability", "capability_adapter_report", "capability_adapter_reports",
}

def redact_delivery_internals(value:Any)->Any:
    """Keep SearchLog/session/tool internals out of user artifacts."""
    if isinstance(value,list): return [redact_delivery_internals(item) for item in value]
    if isinstance(value,dict): return {key:redact_delivery_internals(item) for key,item in value.items() if key not in DELIVERY_INTERNAL_KEYS}
    return value

def source_display(source:dict[str,Any], observation:dict[str,Any]|None=None)->str:
    user_file=user_provided_source_display(source,observation or {})
    if user_file: return user_file
    connected=connected_source_display(source,observation or {})
    if connected: return connected
    return "公开来源" if safe_public_source_url(source) else "来源信息不可用"


def _safe_list(values:Any)->list[Any]:
    return [item for item in ensure_list({"items": values}, "items")]


def _status_and_detail(signal_state:Any)->tuple[str,str]:
    if not isinstance(signal_state,dict):
        return public_signal_status_user_label("not_searched"), ""
    status=public_signal_status_user_label(signal_state.get("status"))
    details=[]
    for item in ensure_list(signal_state,"items"):
        if isinstance(item,dict) and item.get("summary"):
            provenance=[]
            if item.get("source_label"):
                provenance.append(f"来源:{item.get('source_label')}")
            if is_safe_public_http_url(item.get("source_url")):
                provenance.append(f"URL:{item.get('source_url')}")
            period = [str(item.get(field)) for field in ("observed_at", "period") if item.get(field)]
            if period:
                provenance.append(f"日期/期间:{' / '.join(period)}")
            if item.get("locator"):
                provenance.append(f"定位:{item.get('locator')}")
            details.append(str(item.get("summary")) + (f"（{'；'.join(provenance)}）" if provenance else ""))
    if not details:
        details.extend(str(item) for item in ensure_list(signal_state,"searched_scopes") if item)
    if not details:
        details.extend(str(item) for item in ensure_list(signal_state,"notes") if item)
    return status, "；".join(details[:3])


def _candidate_entity(candidate:dict[str,Any], decisions_by_candidate:dict[str,dict[str,Any]], entities:dict[str,dict[str,Any]])->tuple[str|None,dict[str,Any]]:
    entity_id = candidate.get("entity_id")
    if not entity_id:
        decision = decisions_by_candidate.get(str(candidate.get("candidate_id")))
        if isinstance(decision,dict):
            entity_id = decision.get("entity_id")
    entity = entities.get(entity_id,{}) if entity_id else {}
    return (str(entity_id) if entity_id else None), (entity if isinstance(entity,dict) else {})


def _candidate_assessment(entity_id:str|None, brief_id:str|None, run_id:str|None, graph:dict[str,Any])->dict[str,Any]:
    if not entity_id:
        return {}
    return assessment_for_current_brief(graph, entity_id, brief_id, run_id)


def _candidate_relevance(candidate:dict[str,Any], entity:dict[str,Any], decision:dict[str,Any], assessment:dict[str,Any])->str:
    explicit = candidate.get("business_relevance_status")
    if explicit in {"directly_related","possibly_related","explicitly_excluded_or_unrelated","identity_pending","insufficient_information"}:
        return str(explicit)
    identity_status = str(candidate.get("identity_resolution_status") or "")
    if identity_status in {"pending","conflicted","unresolved"}:
        return "identity_pending"
    overall = decision.get("overall_status")
    if overall == "in_scope":
        return "directly_related"
    if overall in {"out_of_scope","reference_only"}:
        return "explicitly_excluded_or_unrelated"
    if overall == "needs_confirmation":
        return "identity_pending" if not entity else "insufficient_information"
    disposition = assessment.get("disposition")
    if disposition in {"重点开发","推荐跟进"}:
        return "directly_related"
    if disposition == "需人工核查":
        return "possibly_related"
    if disposition in {"暂不建议","排除"}:
        return "explicitly_excluded_or_unrelated"
    if entity or candidate.get("website") or candidate.get("domain") or candidate.get("source_url"):
        return "possibly_related"
    return "insufficient_information"


def _candidate_relevance_basis(candidate:dict[str,Any], decision:dict[str,Any], assessment:dict[str,Any])->str:
    basis=[str(item) for item in ensure_list(candidate,"business_relevance_basis") if item]
    basis.extend(str(item) for item in ensure_list(candidate,"business_relevance_notes") if item)
    if not basis and isinstance(decision,dict) and decision.get("decision_summary"):
        basis.append(str(decision.get("decision_summary")))
    if not basis and isinstance(assessment,dict) and assessment.get("disposition"):
        basis.append(f"当前状态：{assessment.get('disposition')}")
    if not basis and candidate.get("note"):
        basis.append(str(candidate.get("note")))
    return "；".join(dict.fromkeys(basis))


def _candidate_identity_label(candidate:dict[str,Any], entity:dict[str,Any])->str:
    explicit = str(candidate.get("identity_resolution_status") or "")
    mapping = {
        "matched": "已匹配主体",
        "pending": "主体待确认",
        "conflicted": "主体冲突待核",
        "unresolved": "主体未解析",
        "not_applicable": "不适用",
    }
    if explicit in mapping:
        return mapping[explicit]
    if entity:
        return "已匹配主体"
    return "主体待确认"


def _candidate_refs(candidate:dict[str,Any], search_logs:dict[str,dict[str,Any]])->tuple[str,str]:
    labels=[]
    urls=[]
    for ref in ensure_list(candidate,"discovery_refs"):
        if not isinstance(ref,dict):
            continue
        if ref.get("label"):
            labels.append(str(ref.get("label")))
        if is_safe_public_http_url(ref.get("url")):
            urls.append(str(ref.get("url")))
    if candidate.get("source_hint"):
        labels.append(str(candidate.get("source_hint")))
    if is_safe_public_http_url(candidate.get("source_url")):
        urls.append(str(candidate.get("source_url")))
    search_log_ids=[]
    if candidate.get("search_log_id"):
        search_log_ids.append(str(candidate.get("search_log_id")))
    search_log_ids.extend(str(item) for item in ensure_list(candidate,"search_log_ids") if item)
    for search_log_id in search_log_ids:
        log=search_logs.get(search_log_id,{})
        if isinstance(log,dict) and log.get("query_group_id"):
            labels.append(f"搜索组:{log.get('query_group_id')}")
        for ref in ensure_list(log,"result_refs"):
            if isinstance(ref,dict) and str(ref.get("candidate_id"))==str(candidate.get("candidate_id")):
                if ref.get("result_title"):
                    labels.append(str(ref.get("result_title")))
                if is_safe_public_http_url(ref.get("result_url")):
                    urls.append(str(ref.get("result_url")))
    return "；".join(dict.fromkeys([item for item in labels if item])), "；".join(dict.fromkeys([item for item in urls if item]))


def _safe_website_or_domain_output(record:dict[str,Any])->str:
    for field in ("website", "domain"):
        value = record.get(field)
        if value is not None and value != "":
            if is_safe_public_website_or_domain(value):
                return str(value)
    return ""


def _candidate_website_or_domain(candidate:dict[str,Any], entity:dict[str,Any])->str:
    for record in (candidate, entity):
        if isinstance(record,dict) and any(record.get(field) is not None and record.get(field) != "" for field in ("website", "domain")):
            safe_value = _safe_website_or_domain_output(record)
            if safe_value:
                return safe_value
    return ""


def _candidate_signal_summary(candidate:dict[str,Any], relevance:str)->dict[str,tuple[str,str]]:
    signal_summary = candidate.get("signal_summary") if isinstance(candidate.get("signal_summary"),dict) else {}
    result = {
        "website_contact": _status_and_detail(signal_summary.get("website_contact")),
        "trade_record": _status_and_detail(signal_summary.get("trade_record")),
        "china_relation": _status_and_detail(signal_summary.get("china_relation")),
        "product_description_or_hs": _status_and_detail(signal_summary.get("product_description_or_hs")),
    }
    if "business_match" not in signal_summary:
        fallback_status = "observed" if relevance in {"directly_related","possibly_related"} else "identity_pending" if relevance == "identity_pending" else "not_observed" if relevance == "explicitly_excluded_or_unrelated" else "not_searched"
        result["business_match"] = (public_signal_status_user_label(fallback_status), "")
    else:
        result["business_match"] = _status_and_detail(signal_summary.get("business_match"))
    return result


def initial_contact_rows(graph:dict[str,Any])->list[dict[str,Any]]:
    entities=idx(graph,"entities","entity_id"); contacts=idx(graph,"contact_points","contact_id"); sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id")
    rows=[]
    seen:set[tuple[str,str]] = set()
    for cc in ensure_list(graph,"contact_claims"):
        if not isinstance(cc,dict) or cc.get("export_status") in {"hold_no_source","hold_inferred"}:
            continue
        cp=contacts.get(cc.get("contact_id"),{})
        source_obs=observations.get(cp.get("source_observation_id")) if isinstance(cp,dict) else {}
        assoc_obs=observations.get(cc.get("association_observation_id"),{})
        source_src=sources.get(source_obs.get("source_id"),{}) if isinstance(source_obs,dict) else {}
        assoc_src=sources.get(assoc_obs.get("source_id"),{}) if isinstance(assoc_obs,dict) else {}
        export_status = cc.get("export_status")
        purpose = "contact_ready" if export_status == "ready" else "contact_with_source_note"
        if not (
            source_evidence_scope(source_src, source_obs, purpose)[0]
            and source_evidence_scope(assoc_src, assoc_obs, purpose)[0]
        ):
            continue
        display_obs = assoc_obs if isinstance(assoc_obs,dict) and assoc_obs else source_obs
        src=assoc_src if display_obs is assoc_obs else source_src
        contact_value = cp.get("normalized_value") if isinstance(cp,dict) else None
        key=(str(contact_value), str(cc.get("entity_id") or ""))
        if key in seen or not contact_value:
            continue
        seen.add(key)
        rows.append({
            "公司/线索名称": entities.get(cc.get("entity_id"),{}).get("name") or cc.get("entity_id") or "待确认归属线索",
            "联系方式类型": cp.get("contact_type"),
            "联系方式": contact_value,
            "原文": cp.get("source_literal"),
            "联系人": cc.get("person_name"),
            "职位/部门": cc.get("job_title") or cc.get("department"),
            "状态": contact_user_status(cc.get("export_status")),
            "归属状态说明": cc.get("manual_check_note") or cc.get("source_context"),
            "来源说明": source_display(src, display_obs if isinstance(display_obs,dict) else {}),
            "来源链接": safe_public_source_url(src),
            "归属证据/待确认原因": cc.get("association_evidence_text"),
        })
    for lead in ensure_list(graph,"unassigned_contact_leads"):
        if not isinstance(lead,dict):
            continue
        cp=contacts.get(lead.get("contact_id"),{})
        if not isinstance(cp,dict) or not cp.get("normalized_value"):
            continue
        source_obs=observations.get(cp.get("source_observation_id"),{})
        src=sources.get(source_obs.get("source_id"),{}) if isinstance(source_obs,dict) else {}
        if not source_evidence_scope(src, source_obs, "candidate_clue")[0]:
            continue
        key=(str(cp.get("normalized_value")), "")
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "公司/线索名称": "待确认归属线索",
            "联系方式类型": cp.get("contact_type"),
            "联系方式": cp.get("normalized_value"),
            "原文": cp.get("source_literal"),
            "联系人": None,
            "职位/部门": None,
            "状态": "待确认归属",
            "归属状态说明": lead.get("reason"),
            "来源说明": source_display(src, source_obs if isinstance(source_obs,dict) else {}),
            "来源链接": safe_public_source_url(src),
            "归属证据/待确认原因": lead.get("suggested_manual_check"),
        })
    return rows


def build_initial_sheets(graph:dict[str,Any], audit:dict[str,Any])->dict[str,list[dict[str,Any]]]:
    entities=idx(graph,"entities","entity_id"); sources=idx(graph,"sources","source_id"); observations=idx(graph,"observations","observation_id"); search_logs=idx(graph,"search_logs","search_log_id")
    run=get_current_run(graph); brief_id=current_brief_id(graph); run_id=run.get("run_id")
    briefs=idx(graph,"briefs","brief_id"); brief=briefs.get(brief_id,{}) if brief_id else {}
    contract = brief.get("customer_selection_contract") if isinstance(brief,dict) else {}
    sample_first = isinstance(contract,dict) and (contract.get("sample_first_required") is True or contract.get("scope_state") == "provisional")
    decisions=[d for d in ensure_list(graph,"scope_decisions") if isinstance(d,dict) and (brief_id is None or d.get("brief_id")==brief_id) and (run_id is None or d.get("run_id")==run_id)]
    decisions_by_candidate={str(d.get("candidate_id")):d for d in decisions if d.get("candidate_id")}
    decisions_by_entity={str(d.get("entity_id")):d for d in decisions if d.get("entity_id")}
    candidate_rows=[]; excluded_rows=[]; source_rows=[]; source_seen:set[tuple[str,str]] = set()
    for candidate in ensure_list(graph,"candidates"):
        if not isinstance(candidate,dict):
            continue
        entity_id, entity = _candidate_entity(candidate, decisions_by_candidate, entities)
        decision = decisions_by_candidate.get(str(candidate.get("candidate_id"))) or (decisions_by_entity.get(str(entity_id)) if entity_id else {})
        assessment = _candidate_assessment(entity_id, brief_id, run_id, graph)
        relevance = _candidate_relevance(candidate, entity, decision if isinstance(decision,dict) else {}, assessment)
        relevance_basis = _candidate_relevance_basis(candidate, decision if isinstance(decision,dict) else {}, assessment)
        signal_info = _candidate_signal_summary(candidate, relevance)
        source_labels, source_links = _candidate_refs(candidate, search_logs)
        default_note = "方向样本，等待确认后再扩展。" if sample_first else "发现线索保留待后续补证。"
        row = {
            "公司名称": candidate.get("company_name") or candidate.get("name") or entity.get("name") or entity.get("legal_name"),
            "国家/地区": candidate.get("country_or_region") or entity.get("country_or_region"),
            "官网/域名": _candidate_website_or_domain(candidate, entity),
            "发现来源": source_labels or candidate.get("source_hint"),
            "发现链接": source_links,
            "去重依据": "；".join(str(item) for item in ensure_list(candidate,"dedupe_basis") if item),
            "方向状态": scope_status_user_label(decision.get("overall_status") if isinstance(decision,dict) else None),
            "业务相关性": business_relevance_user_label(relevance),
            "相关性依据": relevance_basis,
            "业务/产品关联信号状态": signal_info["business_match"][0],
            "业务/产品关联信号说明": signal_info["business_match"][1],
            "已观察业务/产品/应用信号": "；".join(str(item) for item in ensure_list(candidate,"observed_business_signals") if item),
            "官网与联系方式信号状态": signal_info["website_contact"][0],
            "官网与联系方式信号说明": signal_info["website_contact"][1],
            "贸易记录状态": signal_info["trade_record"][0],
            "贸易记录说明": signal_info["trade_record"][1],
            "China 关联状态": signal_info["china_relation"][0],
            "China 关联说明": signal_info["china_relation"][1],
            "货描/HS 状态": signal_info["product_description_or_hs"][0],
            "货描/HS 说明": signal_info["product_description_or_hs"][1],
            "主体匹配状态": _candidate_identity_label(candidate, entity),
            "用户排除项/已观察冲突": "；".join(str(item) for item in ensure_list(candidate,"excluded_or_conflicting_signals") if item) or (decision.get("decision_summary") if isinstance(decision,dict) and relevance=="explicitly_excluded_or_unrelated" else ""),
            "未知项": "；".join(str(item) for item in ensure_list(candidate,"unknowns") if item),
            "来源受限": "；".join(str(item) for item in ensure_list(candidate,"source_restrictions") if item),
            "下一步待验证": "；".join(str(item) for item in ensure_list(candidate,"next_verification_steps") if item),
            "说明": default_note if sample_first else (candidate.get("note") or (decision.get("decision_summary") if isinstance(decision,dict) and decision.get("decision_summary") else default_note)),
        }
        if relevance == "explicitly_excluded_or_unrelated":
            excluded_rows.append(row)
        else:
            candidate_rows.append(row)
        for label, url in ((source_labels, source_links),):
            key=(str(row.get("公司名称")), str(url))
            if key in source_seen:
                continue
            source_seen.add(key)
            source_rows.append({
                "公司/线索名称": row.get("公司名称"),
                "来源说明": label or candidate.get("source_hint"),
                "来源链接": url,
            })
    contact_rows = initial_contact_rows(graph)
    pending=[]
    for candidate in ensure_list(graph,"candidates"):
        if not isinstance(candidate,dict):
            continue
        name = candidate.get("company_name") or candidate.get("name") or "待确认对象"
        for field, label in (("unknowns","未知项待核"),("source_restrictions","来源受限"),("next_verification_steps","下一步待验证")):
            for item in ensure_list(candidate,field):
                pending.append({"类型":label,"对象":name,"原因":item,"建议动作":item if field=="next_verification_steps" else "补充公开来源核查"})
    for cc in ensure_list(graph,"contact_claims"):
        if isinstance(cc,dict) and cc.get("export_status")=="needs_manual_association_review":
            pending.append({"类型":"联系方式待确认","对象":"待确认联系方式","原因":cc.get("manual_check_note") or "归属仍需人工确认","建议动作":"核查来源页面中的主体归属。"})
    for lead in ensure_list(graph,"unassigned_contact_leads"):
        if isinstance(lead,dict):
            pending.append({"类型":"联系方式待确认","对象":"待确认联系方式","原因":lead.get("reason"),"建议动作":lead.get("suggested_manual_check")})
    for f in ensure_list(graph,"review_findings"):
        if isinstance(f,dict) and f.get("status") != "verified_fixed":
            pending.append({"类型":"待处理问题","对象":"待处理项目","原因":f.get("issue"),"建议动作":f.get("required_fix")})
    coverage_rows=[]
    for log in ensure_list(graph,"search_logs"):
        if not isinstance(log,dict):
            continue
        coverage_rows.append({
            "查询组": log.get("query_group_id"),
            "语言": log.get("query_language"),
            "地域": stringify(log.get("targeted_geography_literals")),
            "来源类别": stringify(log.get("source_categories")),
            "新增唯一候选数": len([item for item in ensure_list(log,"new_candidate_ids") if item]) or len([item for item in ensure_list(log,"result_refs") if isinstance(item,dict) and item.get("candidate_id")]),
            "重复候选数": len([item for item in ensure_list(log,"duplicate_candidate_ids") if item]),
            "已访问来源数": len([item for item in ensure_list(log,"accessed_source_ids") if item]),
            "失败访问": "；".join(str(item) for item in ensure_list(log,"failed_source_refs") if item),
            "受限来源": "；".join(str(item) for item in ensure_list(log,"restricted_source_refs") if item),
            "去重依据": "；".join(str(item) for item in ensure_list(log,"dedupe_basis") if item),
            "覆盖/收敛说明": "；".join(str(item) for item in ensure_list(log,"coverage_notes") if item),
        })
    if not coverage_rows:
        coverage_rows=[{"查询组":"未记录搜索日志","覆盖/收敛说明":"当前交付未附带 SearchLog；仅交付已整理候选与公开信号。"}]
    risk_rows=[{"提示级别":i.get("severity"),"说明":i.get("message")} for i in audit.get("issues",[])] or [{"提示级别":"提示","说明":"本轮公开发现可继续扩展；当前输出不宣称已覆盖全部企业。"}]
    if "not_run" in review_modes(graph):
        risk_rows.append({"提示级别":"说明","说明":"本次为发现优先交付；严格复核、审计和正式开发名单门禁未启用。"})
    return {
        "发现候选池": candidate_rows or [{"说明":"未形成候选记录"}],
        "联系方式汇总": contact_rows or [{"说明":"未发现可展示的公开联系方式"}],
        "官网与来源链接": source_rows or [{"说明":"未记录可展示来源"}],
        "搜索覆盖与收敛": coverage_rows,
        "待核查事项": pending or [{"说明":"暂无额外待核查事项"}],
        "已排除客户": excluded_rows or [{"说明":"暂无明确排除记录"}],
        "风险与说明": risk_rows,
    }

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
    if mode=="initial":
        return build_initial_sheets(graph,audit)
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
            sheets["关键词与搜索思路"].append({"核查目的":q.get("query_purpose") or q.get("purpose") or "公开信息核查","搜索思路":"按当前需求与核查规则执行公开信息检索。","来源类别":stringify(p.get("source_categories")),"联系方式目标":stringify(p.get("contact_collection_targets")),"证据不足时":stringify(p.get("downgrade_strategy"))})
    sheets["发现候选池"]=[{"公司/线索名称":c.get("name") or c.get("company_name"),"方向状态":scope_status_user_label(next((d.get("overall_status") for d in ensure_list(graph,"scope_decisions") if isinstance(d,dict) and d.get("candidate_id")==c.get("candidate_id")),"needs_confirmation")),"线索状态":c.get("status") or "发现线索","来源提示":c.get("source_hint") or (c.get("source_url") if is_safe_public_http_url(c.get("source_url")) else None),"说明":c.get("note") or "方向样本，等待确认后再扩展。"} for c in ensure_list(graph,"candidates") if isinstance(c,dict)]
    sheets["客户信息总表"]=[]
    for entity_id,entity in entities.items():
        a=assessment_for_current_brief(graph,entity_id,brief_id,run_id)
        decision=scope_decision_for_current_brief(graph,entity_id,brief_id,run_id)
        if entity_id in allowed_entities:
            row={"公司名称":entity.get("name") or entity.get("legal_name"),"官网":_safe_website_or_domain_output(entity),"国家/地区":entity.get("country_or_region"),"客户类型":entity.get("customer_type"),"开发分层":a.get("disposition"),"缺失项":stringify(a.get("missing_requirements")),"需人工核查":stringify(a.get("manual_review_required"))}
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
    sheets["检查说明"]=[{"检查时间":audit.get("audited_at"),"交付级别":{"standard_development_list":"标准开发名单","full_review_package":"完整核查版"}.get(audit.get("delivery_status"),"发现候选池"),"检查结果":"未发现影响交付的问题" if not audit.get("issues") else "存在待处理问题"}]
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
    p=argparse.ArgumentParser(); p.add_argument("graph"); p.add_argument("output_path",nargs="?"); p.add_argument("--output-dir"); p.add_argument("--mode",choices=["initial","standard","full","inquiry","background"],default="standard"); p.add_argument("--format",choices=["auto","xlsx","csv"],default="auto"); p.add_argument("--manifest"); a=p.parse_args()
    if bool(a.output_path)==bool(a.output_dir): raise SystemExit("Provide exactly one of output_path or --output-dir")
    graph=load_json(a.graph)
    if not isinstance(graph,dict): raise SystemExit("Research graph must be a JSON object")
    if a.mode=="background":
        if a.manifest:
            raise SystemExit("--manifest is not supported for --mode background; background reports do not create DeliveryManifest records")
        scope, issues = validate_background_report(graph)
        if scope is None or issues:
            print("Refusing background export because background report validation failed")
            for item in issues:
                print(f"[{item['severity']}] {item['code']}: {item['message']}")
            return 1
        sheets=build_background_report_sheets(scope)
        hidden_contacts=hold_contact_values(graph) | background_contact_values_to_redact(scope["projection"])
        sheets=redact_local_paths(redact_delivery_sheets(sheets,hidden_contacts))
        out=Path(a.output_dir) if a.output_dir else Path(a.output_path).parent; chosen=a.format
        if a.output_path and Path(a.output_path).suffix.casefold()==".xlsx" and chosen=="auto": chosen="xlsx"
        if chosen=="auto":
            try: import openpyxl; chosen="xlsx"  # noqa
            except Exception: chosen="csv"
        if chosen=="xlsx":
            try: files=write_xlsx_sheets(sheets,out,Path(a.output_path).name if a.output_path else "superleads_background_report.xlsx")
            except Exception as exc:
                if a.format=="xlsx": raise
                print(f"XLSX export unavailable ({exc}); falling back to UTF-8-SIG CSV"); files=write_csv_sheets(sheets,out); chosen="csv"
        else: files=write_csv_sheets(sheets,out)
        print(json.dumps({"ok":True,"format":chosen,"files":files,"background_validation":{"issue_count":0},"manifest":None},ensure_ascii=False,indent=2)); return 0
    from audit_delivery import audit_graph
    requested_status=MODE_TO_STATUS[a.mode]
    audit=audit_graph(graph, requested_delivery_status=requested_status)
    if not audit.get("ok"):
        print("Refusing export because audit status is needs_correction")
        for item in audit.get("issues",[]): print(f"[{item['severity']}] {item['code']}: {item['message']}")
        return 1
    if requested_status not in audit.get("allowed_delivery_statuses", [requested_status]) and a.mode in {"standard","full","inquiry"}:
        print(f"Refusing export because {requested_status} is not in allowed_delivery_statuses")
        return 1
    current_run=get_current_run(graph)
    brief_id=current_brief_id(graph)
    provenance=review_provenance_snapshot(graph,current_run)
    provenance_disclosure=review_provenance_disclosure(provenance.get("review_provenance_level"))
    sheets=build_sheets(graph,audit,a.mode)
    if provenance_disclosure and provenance.get("review_provenance_level") in {"declared_separate_session", "not_run"} and "风险与说明" in sheets:
        sheets["风险与说明"].append({"提示级别":"说明","说明":provenance_disclosure})
    sheets=redact_local_paths(redact_delivery_sheets(sheets,hold_contact_values(graph))); out=Path(a.output_dir) if a.output_dir else Path(a.output_path).parent; chosen=a.format
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
    disclosures=["发现候选与弱证据项仅用于销售人工核查，不代表事实核查完成。"] if a.mode=="initial" else (["询盘信息仅记录来信中提及的内容，不代表企业资格或采购权已核验。"] if a.mode=="inquiry" else [])
    if provenance_disclosure and a.mode in {"standard","full"}:
        disclosures.append(provenance_disclosure)
    if provenance.get("review_provenance_level") == "not_run" and a.mode == "initial":
        disclosures.append(provenance_disclosure)
    exported_entity_ids=formal_export_entities(graph,brief_id,current_run.get("run_id")) if a.mode!="inquiry" else set()
    exported_contact_claims=exportable_contact_claims(graph,exported_entity_ids) if a.mode!="inquiry" else []
    exported_assessments=[item for item in assessments_for_current_brief(graph,brief_id,current_run.get("run_id")) if str(item.get("entity_id")) in exported_entity_ids] if a.mode!="inquiry" else []
    inquiry_contact_ids=[item.get("contact_id") for item in ensure_list(graph,"inquiries") if isinstance(item,dict) and item.get("contact_id")] if a.mode=="inquiry" else []
    review_cycle_id=current_run.get("review_cycle_id") if a.mode=="inquiry" else current_run.get("review_cycle_id") or f"review_{current_run.get('run_id','current')}"
    manifest={"delivery_manifest_id":f"manifest_{audit.get('research_graph_hash','current')[:12]}","run_id":current_run.get("run_id"),"brief_id":None if a.mode=="inquiry" else current_run.get("brief_id") or brief_id,"plan_id":None if a.mode=="inquiry" else current_run.get("plan_id") or (ensure_list(graph,"plans") or [{}])[-1].get("plan_id"),"audit_id":audit.get("audit_id"),"audit_graph_hash":audit.get("audit_graph_hash"),"research_graph_hash":graph_hash(graph),"review_cycle_id":review_cycle_id,"review_attestation_id":provenance.get("review_attestation_id"),"reviewed_subject_hash":provenance.get("reviewed_subject_hash"),"review_provenance_level":provenance.get("review_provenance_level"),"generated_at":audit.get("audited_at"),"delivery_status":requested_status if audit.get("ok") or a.mode=="initial" else "needs_correction","output_mode":a.mode,"exported_entity_ids":sorted(exported_entity_ids),"exported_contact_ids":inquiry_contact_ids or [cc.get("contact_id") for cc in exported_contact_claims if cc.get("contact_id")],"exported_contact_claim_ids":[cc.get("contact_claim_id") for cc in exported_contact_claims if cc.get("contact_claim_id")],"exported_assessment_ids":[x.get("assessment_id") for x in exported_assessments if x.get("assessment_id")],"search_log_ids":[item.get("search_log_id") for item in ensure_list(graph,"search_logs") if isinstance(item,dict) and item.get("search_log_id")],"search_log_count":len([item for item in ensure_list(graph,"search_logs") if isinstance(item,dict)]),"output_files":files,"warnings":[i.get("message") for i in audit.get("issues",[])],"disclosures":disclosures,"format":chosen,"audit_snapshot":audit}
    manifest=redact_delivery_internals(redact_local_paths(redact_delivery_value(manifest,hold_contact_values(graph))))
    if a.manifest: write_json(a.manifest,manifest)
    print(json.dumps({"ok":True,"format":chosen,"files":files,"audit":audit,"manifest":manifest},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
