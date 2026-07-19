"""Build the scoped, non-delivery workbook view for customer background research."""
from __future__ import annotations

import copy
import json
from typing import Any

from _superleads_common import (
    CLAIM_SUPPORT_ALLOWED_CAPABILITIES,
    as_list,
    ensure_list,
    has_text,
    is_safe_public_http_url,
    issue,
    safe_public_source_url,
    source_evidence_scope,
    user_provided_source_display,
    connected_source_display,
)
from validate_research_graph import BLOCKED_ACCESS, validate_graph


BACKGROUND_SHEETS = [
    "背调报告",
    "客户与研究锚点",
    "主体与关系",
    "产品、渠道与经营信号",
    "公开联系入口与桥接候选",
    "开发切入点候选",
    "谈判前待确认问题",
    "未确认线索与来源受限",
    "证据包",
]

RELATION_ENDPOINT_FIELDS = (
    "source_entity_id", "from_entity_id", "parent_entity_id",
    "target_entity_id", "to_entity_id", "child_entity_id",
)
RELATION_LABELS = {
    "same_as": "同一主体关系",
    "brand_of": "品牌归属关系",
    "legal_entity_of": "法律主体关系",
    "branch_of": "分支机构关系",
    "dealer_of": "经销/分销关系",
    "formerly_known_as": "历史名称关系",
    "acquired_by": "收购关系",
    "unrelated_same_name": "同名但不同主体",
    "needs_manual_review": "待人工确认关系",
    "other": "其他关联关系",
}
CLAIM_LABELS = {
    "product_match": "产品/业务",
    "company_identity": "主体识别",
    "contact_route": "公开联系入口",
    "location": "地址/地区",
    "registration": "注册信息",
    "brand_trademark": "品牌/商标",
    "channel_role": "渠道/供应链角色",
    "ownership": "所有权/集团关系",
    "certification": "认证/资质",
}
MEDIUM_LABELS = {
    "website": "网站",
    "social": "公开社媒",
    "registry": "注册库",
    "directory": "目录",
    "map": "地图",
    "document": "文档",
    "spreadsheet": "表格",
    "image": "图片",
    "correspondence": "通信材料",
    "search_result": "搜索结果摘要",
}
ANCHOR_LABELS = {
    "candidate_id": "Candidate",
    "company_name": "公司名称",
    "brand_name": "品牌名称",
    "website_or_domain": "官网/域名",
    "address": "地址",
    "phone": "电话",
    "email": "邮箱",
    "user_material": "用户材料",
}


def _id_map(graph: dict[str, Any], key: str, field: str) -> dict[str, dict[str, Any]]:
    return {
        str(item.get(field)): item
        for item in ensure_list(graph, key)
        if isinstance(item, dict) and has_text(item.get(field))
    }


def _current_background_context(graph: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    runs = [item for item in ensure_list(graph, "runs") if isinstance(item, dict)]
    briefs = _id_map(graph, "briefs", "brief_id")
    run = runs[-1] if runs else None
    if not isinstance(run, dict):
        return None, [issue("critical", "background_export_current_run_missing", "Background export requires a current Run that references the background Brief", "runs")]
    brief = briefs.get(str(run.get("brief_id") or ""))
    if not isinstance(brief, dict):
        return None, [issue("critical", "background_export_current_brief_missing", "Background export requires the current Run to reference an existing Brief", "runs[-1].brief_id")]
    if brief.get("task_mode") != "customer_background_research":
        return None, [issue("critical", "background_export_task_mode_mismatch", "--mode background requires current Brief task_mode=customer_background_research", "briefs.current.task_mode")]
    if brief.get("output_mode") != "客户背调报告":
        return None, [issue("critical", "background_export_output_mode_mismatch", "--mode background requires current Brief output_mode=客户背调报告", "briefs.current.output_mode")]
    target = brief.get("background_research_target")
    if not isinstance(target, dict):
        return None, [issue("critical", "background_export_target_missing", "Background export requires background_research_target on the current Brief", "briefs.current.background_research_target")]
    return {"run": run, "brief": brief, "target": target}, []


def _formal_observation(observation: Any, sources: dict[str, dict[str, Any]]) -> bool:
    if not isinstance(observation, dict):
        return False
    source = sources.get(str(observation.get("source_id") or ""))
    return bool(
        isinstance(source, dict)
        and observation.get("capability") in CLAIM_SUPPORT_ALLOWED_CAPABILITIES
        and observation.get("access_status") not in BLOCKED_ACCESS
        and has_text(observation.get("raw_excerpt"))
        and source.get("medium") != "search_result"
        and source_evidence_scope(source, observation, "formal_claim")[0]
    )


def _claim_has_formal_support(
    claim_id: str,
    claim_evidence: list[dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> bool:
    return any(
        evidence.get("claim_id") == claim_id
        and evidence.get("relation") == "supports"
        and _formal_observation(observations.get(str(evidence.get("observation_id") or "")), sources)
        for evidence in claim_evidence
    )


def _relationship_is_supported(
    relationship: dict[str, Any],
    entities: dict[str, dict[str, Any]],
    claims: dict[str, dict[str, Any]],
    claim_evidence: list[dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> bool:
    endpoints = {str(relationship.get(field)) for field in RELATION_ENDPOINT_FIELDS if has_text(relationship.get(field))}
    if len(endpoints) < 2 or not endpoints.issubset(entities):
        return False
    claim_ids = [str(item) for item in as_list(relationship.get("evidence_claim_ids")) if has_text(item)]
    observation_ids = [str(item) for item in as_list(relationship.get("evidence_observation_ids")) if has_text(item)]
    if not claim_ids and not observation_ids:
        return False
    if any(
        not isinstance(claims.get(claim_id), dict)
        or claims[claim_id].get("entity_id") not in endpoints
        or not _claim_has_formal_support(claim_id, claim_evidence, observations, sources)
        for claim_id in claim_ids
    ):
        return False
    if any(
        not isinstance(observations.get(observation_id), dict)
        or observations[observation_id].get("entity_id") not in endpoints
        or not _formal_observation(observations[observation_id], sources)
        for observation_id in observation_ids
    ):
        return False
    return True


def _project_run(run: dict[str, Any]) -> dict[str, Any]:
    fields = ("run_id", "status", "created_at", "updated_at", "brief_id")
    result = {field: copy.deepcopy(run[field]) for field in fields if field in run}
    # The report projection deliberately has no delivery-review or host-adapter
    # semantics. Source/Observation evidence remains in the projection.
    result["platform"] = "background_report"
    return result


def _project_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(candidate)
    for field in ("run_id", "brief_id", "plan_id", "discovery_method", "search_log_id", "search_log_ids", "discovery_refs"):
        result.pop(field, None)
    return result


def _project_observation(observation: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(observation)
    result.pop("run_id", None)
    return result


def build_background_projection(graph: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    """Select only the current background subject and its evidence-backed closure."""
    context, issues = _current_background_context(graph)
    if context is None:
        return None, issues

    target = context["target"]
    entities = _id_map(graph, "entities", "entity_id")
    candidates = _id_map(graph, "candidates", "candidate_id")
    sources = _id_map(graph, "sources", "source_id")
    observations = _id_map(graph, "observations", "observation_id")
    claims = _id_map(graph, "claims", "claim_id")
    contact_points = _id_map(graph, "contact_points", "contact_id")
    claim_evidence = [item for item in ensure_list(graph, "claim_evidence") if isinstance(item, dict)]
    relationships = [item for item in ensure_list(graph, "entity_relationships") if isinstance(item, dict)]

    candidate_ids = {
        str(anchor.get("candidate_id"))
        for anchor in as_list(target.get("anchors"))
        if isinstance(anchor, dict) and anchor.get("kind") == "candidate_id" and has_text(anchor.get("candidate_id"))
    }
    source_ids = {
        str(anchor.get("source_id"))
        for anchor in as_list(target.get("anchors"))
        if isinstance(anchor, dict) and anchor.get("kind") == "user_material" and has_text(anchor.get("source_id"))
    }
    observation_ids = {str(item) for item in as_list(target.get("resolution_observation_ids")) if has_text(item)}
    entity_ids: set[str] = set()
    primary_entity_id = target.get("primary_subject_entity_id")
    if has_text(primary_entity_id):
        entity_ids.add(str(primary_entity_id))
    for candidate_id in candidate_ids:
        candidate = candidates.get(candidate_id)
        if isinstance(candidate, dict) and has_text(candidate.get("entity_id")):
            entity_ids.add(str(candidate["entity_id"]))

    for observation in observations.values():
        if observation.get("source_id") in source_ids or observation.get("candidate_id") in candidate_ids:
            observation_ids.add(str(observation["observation_id"]))
    for observation_id in list(observation_ids):
        observation = observations.get(observation_id)
        if isinstance(observation, dict):
            if has_text(observation.get("source_id")):
                source_ids.add(str(observation["source_id"]))
            if has_text(observation.get("entity_id")):
                entity_ids.add(str(observation["entity_id"]))

    relationship_ids: set[str] = set()
    relationship_entities = {str(primary_entity_id)} if has_text(primary_entity_id) else set()
    changed = True
    while changed and relationship_entities:
        changed = False
        for relationship in relationships:
            relationship_id = relationship.get("entity_relationship_id")
            endpoints = {str(relationship.get(field)) for field in RELATION_ENDPOINT_FIELDS if has_text(relationship.get(field))}
            if not endpoints & relationship_entities or not _relationship_is_supported(relationship, entities, claims, claim_evidence, observations, sources):
                continue
            if has_text(relationship_id):
                relationship_ids.add(str(relationship_id))
            new_entities = endpoints - entity_ids
            if new_entities:
                entity_ids.update(new_entities)
                relationship_entities.update(new_entities)
                changed = True

    for observation in observations.values():
        if observation.get("entity_id") in entity_ids:
            observation_ids.add(str(observation["observation_id"]))
    for observation_id in list(observation_ids):
        observation = observations.get(observation_id)
        if isinstance(observation, dict) and has_text(observation.get("source_id")):
            source_ids.add(str(observation["source_id"]))

    # Preserve Candidates only when an included Observation actually cites one.
    # This keeps the projected graph referentially valid without including an
    # unrelated bulk candidate pool.
    for observation_id in observation_ids:
        observation = observations.get(observation_id)
        if isinstance(observation, dict) and has_text(observation.get("candidate_id")):
            candidate_ids.add(str(observation["candidate_id"]))
    for candidate_id in candidate_ids:
        candidate = candidates.get(candidate_id)
        if isinstance(candidate, dict) and has_text(candidate.get("entity_id")):
            entity_ids.add(str(candidate["entity_id"]))

    claim_ids = {
        claim_id for claim_id, claim in claims.items()
        if claim.get("entity_id") in entity_ids
        and _claim_has_formal_support(claim_id, claim_evidence, observations, sources)
    }
    claim_evidence_ids: set[str] = set()
    for evidence in claim_evidence:
        if evidence.get("claim_id") not in claim_ids:
            continue
        observation = observations.get(str(evidence.get("observation_id") or ""))
        if not isinstance(observation, dict):
            continue
        source = sources.get(str(observation.get("source_id") or ""))
        if not isinstance(source, dict):
            continue
        if has_text(evidence.get("claim_evidence_id")):
            claim_evidence_ids.add(str(evidence["claim_evidence_id"]))
        observation_ids.add(str(observation["observation_id"]))
        source_ids.add(str(observation["source_id"]))

    contact_claims = [
        item for item in ensure_list(graph, "contact_claims")
        if isinstance(item, dict) and item.get("entity_id") in entity_ids
    ]
    contact_ids = {str(item.get("contact_id")) for item in contact_claims if has_text(item.get("contact_id"))}
    for contact_claim in contact_claims:
        for field in ("association_observation_id",):
            if has_text(contact_claim.get(field)):
                observation_ids.add(str(contact_claim[field]))
    for contact_id in list(contact_ids):
        contact = contact_points.get(contact_id)
        if isinstance(contact, dict) and has_text(contact.get("source_observation_id")):
            observation_ids.add(str(contact["source_observation_id"]))
    for observation_id in list(observation_ids):
        observation = observations.get(observation_id)
        if isinstance(observation, dict) and has_text(observation.get("source_id")):
            source_ids.add(str(observation["source_id"]))

    unassigned = []
    for lead in ensure_list(graph, "unassigned_contact_leads"):
        if not isinstance(lead, dict):
            continue
        contact = contact_points.get(str(lead.get("contact_id") or ""))
        observation = observations.get(str(contact.get("source_observation_id") or "")) if isinstance(contact, dict) else None
        if isinstance(observation, dict) and observation.get("observation_id") in observation_ids:
            unassigned.append(lead)
            contact_ids.add(str(contact["contact_id"]))

    hypotheses = [
        item for item in ensure_list(graph, "hypotheses")
        if isinstance(item, dict)
        and item.get("entity_id") in entity_ids
        and set(str(claim_id) for claim_id in as_list(item.get("basis_claim_ids"))).issubset(claim_ids)
    ]

    selected_relationships = [
        item for item in relationships
        if str(item.get("entity_relationship_id") or "") in relationship_ids
    ]
    projection = {
        "runs": [_project_run(context["run"])],
        "briefs": [copy.deepcopy(context["brief"])],
        "plans": [],
        "candidates": [_project_candidate(candidates[candidate_id]) for candidate_id in sorted(candidate_ids) if candidate_id in candidates],
        "sources": [copy.deepcopy(sources[source_id]) for source_id in sorted(source_ids) if source_id in sources],
        "observations": [_project_observation(observations[observation_id]) for observation_id in sorted(observation_ids) if observation_id in observations],
        "entities": [copy.deepcopy(entities[entity_id]) for entity_id in sorted(entity_ids) if entity_id in entities],
        "entity_relationships": copy.deepcopy(selected_relationships),
        "claims": [copy.deepcopy(claims[claim_id]) for claim_id in sorted(claim_ids)],
        "claim_evidence": [
            copy.deepcopy(item) for item in claim_evidence
            if str(item.get("claim_evidence_id") or "") in claim_evidence_ids
        ],
        "contact_points": [copy.deepcopy(contact_points[contact_id]) for contact_id in sorted(contact_ids) if contact_id in contact_points],
        "contact_claims": copy.deepcopy(contact_claims),
        "unassigned_contact_leads": copy.deepcopy(unassigned),
        "hypotheses": copy.deepcopy(hypotheses),
    }
    return {
        **context,
        "projection": projection,
        "entity_ids": entity_ids,
        "candidate_ids": candidate_ids,
        "source_ids": source_ids,
        "observation_ids": observation_ids,
        "claim_ids": claim_ids,
        "relationship_ids": relationship_ids,
    }, []


def validate_background_report(graph: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    """Validate only the evidence-backed background scope, never delivery history."""
    scope, issues = build_background_projection(graph)
    if scope is None:
        return None, issues
    return scope, validate_graph(scope["projection"])


def _source_display(source: dict[str, Any], observation: dict[str, Any] | None = None) -> str:
    user_file = user_provided_source_display(source, observation or {})
    if user_file:
        return user_file
    connected = connected_source_display(source, observation or {})
    if connected:
        return connected
    return "公开来源" if safe_public_source_url(source) else "来源信息不可用"


def _source_status(source: dict[str, Any], observation: dict[str, Any] | None = None) -> str:
    if isinstance(observation, dict) and observation.get("access_status") in BLOCKED_ACCESS:
        return "来源受限"
    if source.get("medium") == "search_result":
        return "搜索摘要线索，不作为事实证据"
    if source.get("provenance") in {"user_provided", "manual_input"}:
        return "用户提供第三方材料信号"
    if isinstance(observation, dict) and _formal_observation(observation, {str(source.get("source_id")): source}):
        return "已观察"
    return "待确认"


def _claim_value(claim: dict[str, Any]) -> str:
    value = claim.get("typed_value")
    if isinstance(value, dict) and has_text(value.get("text")):
        return str(value["text"])
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else str(value)


def _claim_summary(claim: dict[str, Any]) -> str:
    return " ".join(item for item in (str(claim.get("subject") or ""), str(claim.get("predicate") or ""), _claim_value(claim)) if item)


def _relationship_endpoints(relationship: dict[str, Any]) -> tuple[str | None, str | None]:
    source = next((relationship.get(field) for field in ("source_entity_id", "from_entity_id", "parent_entity_id") if has_text(relationship.get(field))), None)
    target = next((relationship.get(field) for field in ("target_entity_id", "to_entity_id", "child_entity_id") if has_text(relationship.get(field))), None)
    return (str(source) if source else None, str(target) if target else None)


def _role_pair(relationship_type: Any) -> tuple[str, str]:
    return {
        "brand_of": ("品牌", "品牌归属主体"),
        "legal_entity_of": ("法律主体", "关联品牌/运营主体"),
        "branch_of": ("分支机构", "所属主体"),
        "dealer_of": ("经销商/分销商", "品牌/供应主体"),
        "acquired_by": ("被收购主体", "收购主体"),
        "formerly_known_as": ("历史名称主体", "当前名称主体"),
    }.get(relationship_type, ("关联主体", "关联主体"))


def _claim_evidence_maps(scope: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_claim: dict[str, list[dict[str, Any]]] = {}
    by_observation: dict[str, list[dict[str, Any]]] = {}
    for evidence in ensure_list(scope["projection"], "claim_evidence"):
        if not isinstance(evidence, dict):
            continue
        by_claim.setdefault(str(evidence.get("claim_id")), []).append(evidence)
        by_observation.setdefault(str(evidence.get("observation_id")), []).append(evidence)
    return by_claim, by_observation


def _first_evidence_context(
    claim_id: str,
    evidence_by_claim: dict[str, list[dict[str, Any]]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    for evidence in evidence_by_claim.get(claim_id, []):
        observation = observations.get(str(evidence.get("observation_id") or ""))
        if isinstance(observation, dict):
            source = sources.get(str(observation.get("source_id") or ""))
            if isinstance(source, dict):
                return observation, source
    return {}, {}


def _empty_row(message: str) -> list[dict[str, Any]]:
    return [{"说明": message}]


def build_background_report_sheets(scope: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Render only the selected background-research scope into user-facing sheets."""
    projection = scope["projection"]
    target = scope["target"]
    entities = _id_map(projection, "entities", "entity_id")
    candidates = _id_map(projection, "candidates", "candidate_id")
    sources = _id_map(projection, "sources", "source_id")
    observations = _id_map(projection, "observations", "observation_id")
    claims = _id_map(projection, "claims", "claim_id")
    contacts = _id_map(projection, "contact_points", "contact_id")
    evidence_by_claim, evidence_by_observation = _claim_evidence_maps(scope)
    primary_entity_id = target.get("primary_subject_entity_id")
    primary_entity = entities.get(str(primary_entity_id or ""), {})
    resolution_status = target.get("subject_resolution_status")
    resolution_label = {
        "resolved": "已解析主体",
        "multiple_candidates": "存在多个候选主体",
        "unresolved": "主体尚未解析",
    }.get(resolution_status, "主体待确认")

    summary_rows = [
        {"模块": "研究对象", "状态": "已记录", "内容": target.get("user_statement")},
        {
            "模块": "主体解析",
            "状态": resolution_label,
            "内容": (primary_entity.get("legal_name") or primary_entity.get("name")) if primary_entity else "尚未形成可确认的法律主体结论",
        },
    ]
    if entities:
        summary_rows.append({"模块": "关联主体", "状态": "已观察", "内容": "；".join(str(entity.get("legal_name") or entity.get("name")) for entity in entities.values() if entity.get("legal_name") or entity.get("name"))})
    if any(observation.get("access_status") in BLOCKED_ACCESS for observation in observations.values()):
        summary_rows.append({"模块": "研究覆盖", "状态": "受限", "内容": "部分来源受访问限制，仅保留受限状态与待确认事项。"})
    if resolution_status != "resolved":
        summary_rows.append({"模块": "研究覆盖", "状态": "待确认", "内容": "需补充可检查公开来源或用户材料后再确认主体关系。"})
    if not sources:
        summary_rows.append({"模块": "研究覆盖", "状态": "需要用户材料", "内容": "当前只有研究锚点，尚无可检查来源。"})

    resolution_details = []
    for observation_id in as_list(target.get("resolution_observation_ids")):
        observation = observations.get(str(observation_id))
        source = sources.get(str(observation.get("source_id") or "")) if isinstance(observation, dict) else None
        if isinstance(observation, dict) and isinstance(source, dict):
            resolution_details.append(f"{_source_display(source, observation)}：{observation.get('raw_excerpt')}")
    anchor_rows = []
    for anchor in as_list(target.get("anchors")):
        if not isinstance(anchor, dict):
            continue
        candidate = candidates.get(str(anchor.get("candidate_id") or ""))
        source = sources.get(str(anchor.get("source_id") or ""))
        anchor_rows.append({
            "用户输入锚点": anchor.get("literal") or (candidate.get("name") or candidate.get("company_name") if isinstance(candidate, dict) else ""),
            "锚点类型": ANCHOR_LABELS.get(anchor.get("kind"), "其他锚点"),
            "Candidate 关联": (candidate.get("name") or candidate.get("company_name")) if isinstance(candidate, dict) else "",
            "Source 关联": _source_display(source) if isinstance(source, dict) else "",
            "主体解析状态": resolution_label,
            "主实体": primary_entity.get("legal_name") or primary_entity.get("name") if primary_entity else "",
            "解析依据": "；".join(resolution_details),
            "待确认项": "主体尚未解析" if resolution_status == "unresolved" else ("候选主体之间关系待确认" if resolution_status == "multiple_candidates" else ""),
        })

    relationship_rows = []
    for entity_id, entity in entities.items():
        entity_type = "法律主体" if entity_id == primary_entity_id else "关联主体"
        relationship_rows.append({
            "主体名称": entity.get("legal_name") or entity.get("name"),
            "主体类型": entity_type,
            "角色": "主研究主体" if entity_id == primary_entity_id else "待证实关联角色",
            "关系": "主体解析" if entity_id == primary_entity_id else "关联主体记录",
            "关系证据": "；".join(resolution_details) if entity_id == primary_entity_id else "",
            "当前/历史/未确认状态": "当前已解析" if entity_id == primary_entity_id else "待确认",
            "来源 URL": _safe_entity_url(entity),
            "观察时间": "",
        })
    for relationship in ensure_list(projection, "entity_relationships"):
        if not isinstance(relationship, dict):
            continue
        source_id, target_id = _relationship_endpoints(relationship)
        source_entity = entities.get(str(source_id or ""), {})
        target_entity = entities.get(str(target_id or ""), {})
        source_role, target_role = _role_pair(relationship.get("relationship_type"))
        evidence_text, evidence_url, observed_at = _relationship_evidence(relationship, claims, observations, sources, evidence_by_claim)
        relation_status = "待确认" if relationship.get("resolution_status") in {"manual_check", "rejected"} else ("历史" if relationship.get("relationship_type") == "formerly_known_as" else "当前/已观察")
        relationship_rows.extend([
            {
                "主体名称": source_entity.get("legal_name") or source_entity.get("name"),
                "主体类型": "关联主体",
                "角色": source_role,
                "关系": f"{RELATION_LABELS.get(relationship.get('relationship_type'), '关联关系')} -> {target_entity.get('legal_name') or target_entity.get('name') or ''}",
                "关系证据": evidence_text,
                "当前/历史/未确认状态": relation_status,
                "来源 URL": evidence_url,
                "观察时间": observed_at,
            },
            {
                "主体名称": target_entity.get("legal_name") or target_entity.get("name"),
                "主体类型": "关联主体",
                "角色": target_role,
                "关系": f"{RELATION_LABELS.get(relationship.get('relationship_type'), '关联关系')} <- {source_entity.get('legal_name') or source_entity.get('name') or ''}",
                "关系证据": evidence_text,
                "当前/历史/未确认状态": relation_status,
                "来源 URL": evidence_url,
                "观察时间": observed_at,
            },
        ])

    signal_rows = []
    for claim_id, claim in claims.items():
        observation, source = _first_evidence_context(claim_id, evidence_by_claim, observations, sources)
        if not observation or not source:
            continue
        scope_status = claim.get("claim_scope")
        signal_rows.append({
            "观察类型": CLAIM_LABELS.get(claim.get("claim_type"), "公开经营信号"),
            "主体": entities.get(str(claim.get("entity_id") or ""), {}).get("legal_name") or entities.get(str(claim.get("entity_id") or ""), {}).get("name"),
            "证据化观察": _claim_summary(claim),
            "状态": "历史信息" if scope_status in {"source_snapshot", "point_in_time"} else "已观察",
            "来源": _source_display(source, observation),
            "来源 URL": safe_public_source_url(source),
            "观察时间": observation.get("observed_at"),
        })

    contact_rows = _background_contact_rows(projection, entities, contacts, observations, sources)
    hypothesis_rows = _background_hypothesis_rows(projection, claims, observations, sources, evidence_by_claim)
    question_rows = _background_question_rows(scope, claims, observations, sources)
    unresolved_rows = _background_unresolved_rows(scope, claims, observations, sources)
    evidence_rows = _background_evidence_rows(projection, claims, observations, sources, evidence_by_observation)

    return {
        "背调报告": summary_rows,
        "客户与研究锚点": anchor_rows or _empty_row("未记录研究锚点"),
        "主体与关系": relationship_rows or _empty_row("主体尚未解析；暂无可展示的关系事实。"),
        "产品、渠道与经营信号": signal_rows or _empty_row("暂无具有可检查证据支持的产品、渠道或经营信号。"),
        "公开联系入口与桥接候选": contact_rows or _empty_row("暂无可展示的公开联系入口；不展示未确认或不可导出的联系方式值。"),
        "开发切入点候选": hypothesis_rows or _empty_row("暂无基于证据的切入点候选。"),
        "谈判前待确认问题": question_rows or _empty_row("暂无额外待确认问题。"),
        "未确认线索与来源受限": unresolved_rows or _empty_row("暂无已记录的未确认线索或来源限制。"),
        "证据包": evidence_rows or _empty_row("暂无可展示的来源记录。"),
    }


def _safe_entity_url(entity: dict[str, Any]) -> str:
    for field in ("website", "domain"):
        value = entity.get(field)
        if is_safe_public_http_url(value):
            return value
    return ""


def _relationship_evidence(
    relationship: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> tuple[str, str, str]:
    details: list[str] = []
    url = ""
    observed_at = ""
    for claim_id in as_list(relationship.get("evidence_claim_ids")):
        claim = claims.get(str(claim_id))
        if not isinstance(claim, dict):
            continue
        details.append(_claim_summary(claim))
        observation, source = _first_evidence_context(str(claim_id), evidence_by_claim, observations, sources)
        if observation and source:
            url = url or safe_public_source_url(source)
            observed_at = observed_at or str(observation.get("observed_at") or "")
    for observation_id in as_list(relationship.get("evidence_observation_ids")):
        observation = observations.get(str(observation_id))
        source = sources.get(str(observation.get("source_id") or "")) if isinstance(observation, dict) else None
        if isinstance(observation, dict) and isinstance(source, dict):
            details.append(str(observation.get("raw_excerpt") or ""))
            url = url or safe_public_source_url(source)
            observed_at = observed_at or str(observation.get("observed_at") or "")
    return "；".join(item for item in details if item), url, observed_at


def _background_contact_rows(
    projection: dict[str, Any],
    entities: dict[str, dict[str, Any]],
    contacts: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for claim in ensure_list(projection, "contact_claims"):
        if not isinstance(claim, dict):
            continue
        status = claim.get("export_status")
        if status in {"hold_no_source", "hold_inferred"}:
            continue
        contact = contacts.get(str(claim.get("contact_id") or ""), {})
        source_observation = observations.get(str(contact.get("source_observation_id") or "")) if isinstance(contact, dict) else None
        association_observation = observations.get(str(claim.get("association_observation_id") or ""))
        source = sources.get(str(source_observation.get("source_id") or "")) if isinstance(source_observation, dict) else None
        association_source = sources.get(str(association_observation.get("source_id") or "")) if isinstance(association_observation, dict) else None
        exposable = status in {"ready", "export_with_source_note"} and source_evidence_scope(source, source_observation, "contact_ready" if status == "ready" else "contact_with_source_note")[0] and source_evidence_scope(association_source, association_observation, "contact_ready" if status == "ready" else "contact_with_source_note")[0]
        person_or_title = " ".join(str(item) for item in (claim.get("person_name"), claim.get("job_title"), claim.get("department")) if item)
        bridge_note = "桥接候选，不默认等于采购负责人" if any(token in person_or_title.casefold() for token in ("founder", "owner", "创始人", "所有者")) else ""
        display_observation = association_observation if isinstance(association_observation, dict) else source_observation
        display_source = association_source if isinstance(association_source, dict) else source
        rows.append({
            "主体": entities.get(str(claim.get("entity_id") or ""), {}).get("legal_name") or entities.get(str(claim.get("entity_id") or ""), {}).get("name") or "待确认归属线索",
            "联系方式类型": contact.get("contact_type") if isinstance(contact, dict) else "",
            "公开联系入口": contact.get("normalized_value") if exposable and isinstance(contact, dict) else "待确认归属线索",
            "联系人/公开职业线索": person_or_title,
            "联系方式状态": {"ready": "可直接使用", "export_with_source_note": "建议核查后使用"}.get(status, "待确认归属"),
            "归属状态": "已记录公开归属" if exposable else "待确认归属",
            "说明": "；".join(item for item in (bridge_note, claim.get("manual_check_note"), claim.get("source_context")) if item),
            "来源": _source_display(display_source, display_observation) if isinstance(display_source, dict) else "来源信息不可用",
            "来源 URL": safe_public_source_url(display_source) if isinstance(display_source, dict) else "",
        })
    for lead in ensure_list(projection, "unassigned_contact_leads"):
        if not isinstance(lead, dict):
            continue
        contact = contacts.get(str(lead.get("contact_id") or ""), {})
        observation = observations.get(str(contact.get("source_observation_id") or "")) if isinstance(contact, dict) else None
        source = sources.get(str(observation.get("source_id") or "")) if isinstance(observation, dict) else None
        rows.append({
            "主体": "待确认归属线索",
            "联系方式类型": contact.get("contact_type") if isinstance(contact, dict) else "",
            "公开联系入口": "待确认归属线索",
            "联系人/公开职业线索": "",
            "联系方式状态": "待确认归属",
            "归属状态": "未分配线索",
            "说明": "；".join(item for item in (lead.get("reason"), lead.get("suggested_manual_check")) if item),
            "来源": _source_display(source, observation) if isinstance(source, dict) else "来源信息不可用",
            "来源 URL": safe_public_source_url(source) if isinstance(source, dict) else "",
        })
    return rows


def _background_hypothesis_rows(
    projection: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    evidence_by_claim: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    contact_claims = _id_map(projection, "contact_claims", "contact_claim_id")
    for hypothesis in ensure_list(projection, "hypotheses"):
        if not isinstance(hypothesis, dict):
            continue
        evidence = []
        urls = []
        for claim_id in as_list(hypothesis.get("basis_claim_ids")):
            claim = claims.get(str(claim_id))
            if not isinstance(claim, dict):
                continue
            evidence.append(_claim_summary(claim))
            observation, source = _first_evidence_context(str(claim_id), evidence_by_claim, observations, sources)
            if observation and source and safe_public_source_url(source):
                urls.append(safe_public_source_url(source))
        for contact_claim_id in as_list(hypothesis.get("basis_contact_claim_ids")):
            contact_claim = contact_claims.get(str(contact_claim_id))
            if not isinstance(contact_claim, dict):
                continue
            observation = observations.get(str(contact_claim.get("association_observation_id") or ""))
            source = sources.get(str(observation.get("source_id") or "")) if isinstance(observation, dict) else None
            status = contact_claim.get("export_status")
            if status in {"ready", "export_with_source_note"}:
                summary = contact_claim.get("association_evidence_text") or contact_claim.get("source_context")
            else:
                summary = "待确认联系方式归属线索：" + str(contact_claim.get("source_context") or "需人工核查")
            if has_text(summary):
                evidence.append(str(summary))
            if isinstance(source, dict) and safe_public_source_url(source):
                urls.append(safe_public_source_url(source))
        if evidence:
            rows.append({
                "候选切入点": hypothesis.get("hypothesis_text"),
                "证据概述": "；".join(evidence),
                "来源": "；".join(dict.fromkeys(urls)),
                "说明": "仅为基于证据的候选角度，需人工确认；不构成报价或谈判策略。",
            })
    return rows


def _background_question_rows(
    scope: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target = scope["target"]
    if target.get("subject_resolution_status") != "resolved":
        rows.append({"待确认问题": "当前研究锚点对应的法律主体是哪一个？", "依据/状态": "主体尚未解析或存在多个候选主体", "说明": "待验证问题，不是主体结论或谈判策略。"})
    for hypothesis in ensure_list(scope["projection"], "hypotheses"):
        if not isinstance(hypothesis, dict):
            continue
        for unknown in as_list(hypothesis.get("unknowns")):
            rows.append({"待确认问题": unknown, "依据/状态": "研究假设保留的未知项", "说明": "待验证问题，不是结论或谈判策略。"})
        if has_text(hypothesis.get("next_verification_action")):
            rows.append({"待确认问题": hypothesis.get("next_verification_action"), "依据/状态": "建议的下一步核验", "说明": "待验证问题，不是结论或谈判策略。"})
    for claim in claims.values():
        if claim.get("claim_scope") in {"source_snapshot", "point_in_time"}:
            rows.append({"待确认问题": f"确认历史信息是否仍有效：{_claim_summary(claim)}", "依据/状态": "历史来源信息", "说明": "待验证问题，不以历史信息替代当前事实。"})
    for relationship in ensure_list(scope["projection"], "entity_relationships"):
        if isinstance(relationship, dict) and relationship.get("resolution_status") in {"manual_check", "rejected"}:
            rows.append({"待确认问题": relationship.get("rationale") or "确认关联主体关系", "依据/状态": "关系尚未确认", "说明": "待验证问题，不是关系结论。"})
    return rows


def _background_unresolved_rows(
    scope: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    target = scope["target"]
    if target.get("subject_resolution_status") != "resolved":
        rows.append({"类型": "主体解析", "线索/来源": target.get("user_statement"), "状态": "待确认", "受限或冲突原因": "主体尚未形成唯一已解析 Entity", "建议": "补充可检查公开来源或用户材料。"})
    for observation in observations.values():
        source = sources.get(str(observation.get("source_id") or ""))
        if not isinstance(source, dict):
            continue
        if observation.get("access_status") in BLOCKED_ACCESS or source.get("medium") == "search_result" or source.get("provenance") in {"user_provided", "manual_input"}:
            reason = "；".join(item for item in (
                str(observation.get("access_status") or "") if observation.get("access_status") in BLOCKED_ACCESS else "",
                "搜索摘要不能作为事实证据" if source.get("medium") == "search_result" else "",
                "用户提供第三方材料信号，需独立核验" if source.get("provenance") in {"user_provided", "manual_input"} else "",
            ) if item)
            rows.append({"类型": "来源受限/材料线索", "线索/来源": _source_display(source, observation), "状态": _source_status(source, observation), "受限或冲突原因": reason, "建议": "保留线索并补充可检查来源；不据此形成公司事实。"})
    for claim in claims.values():
        if claim.get("contradiction_status") not in {None, "", "none"}:
            rows.append({"类型": "来源冲突", "线索/来源": _claim_summary(claim), "状态": "待确认", "受限或冲突原因": claim.get("contradiction_status"), "建议": "保留冲突并核验当前来源。"})
    return rows


def _background_evidence_rows(
    projection: dict[str, Any],
    claims: dict[str, dict[str, Any]],
    observations: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    evidence_by_observation: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    observed_source_ids: set[str] = set()
    for observation_id, observation in observations.items():
        source = sources.get(str(observation.get("source_id") or ""))
        if not isinstance(source, dict):
            continue
        observed_source_ids.add(str(source.get("source_id")))
        conclusions = []
        for evidence in evidence_by_observation.get(observation_id, []):
            claim = claims.get(str(evidence.get("claim_id") or ""))
            if isinstance(claim, dict):
                conclusions.append(_claim_summary(claim))
        rows.append({
            "来源标题/类型": observation.get("title") or _source_display(source, observation),
            "来源类型": MEDIUM_LABELS.get(source.get("medium"), "其他来源"),
            "URL": safe_public_source_url(source),
            "原文摘录或材料定位": observation.get("raw_excerpt") or observation.get("page_or_dom_locator") or "未获得可展示摘录",
            "观察时间": observation.get("observed_at"),
            "抓取/材料定位": observation.get("page_or_dom_locator") or "",
            "关联字段/结论": "；".join(conclusions) or "来源记录/待确认线索",
            "状态": _source_status(source, observation),
        })
    for source_id, source in sources.items():
        if source_id in observed_source_ids:
            continue
        rows.append({
            "来源标题/类型": _source_display(source),
            "来源类型": MEDIUM_LABELS.get(source.get("medium"), "其他来源"),
            "URL": safe_public_source_url(source),
            "原文摘录或材料定位": "尚未形成可展示摘录",
            "观察时间": "",
            "抓取/材料定位": "",
            "关联字段/结论": "研究锚点材料/待确认线索",
            "状态": _source_status(source),
        })
    return rows


def background_contact_values_to_redact(graph: dict[str, Any]) -> set[str]:
    """Hide non-exportable and unassigned contact values everywhere in a background report."""
    contacts = _id_map(graph, "contact_points", "contact_id")
    values: set[str] = set()

    def add_value(value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            return
        token = value.strip()
        values.add(token)
        if "," in token:
            before, after = [part.strip() for part in token.split(",", 1)]
            if before and after:
                values.add(f"{after} {before}")

    hidden_contact_ids = {
        str(claim.get("contact_id"))
        for claim in ensure_list(graph, "contact_claims")
        if isinstance(claim, dict) and claim.get("export_status") not in {"ready", "export_with_source_note"}
    }
    for claim in ensure_list(graph, "contact_claims"):
        if not isinstance(claim, dict) or claim.get("export_status") in {"ready", "export_with_source_note"}:
            continue
        person_fragments = [
            str(claim.get(field)).strip()
            for field in ("person_name", "job_title", "department")
            if isinstance(claim.get(field), str) and str(claim.get(field)).strip()
        ]
        if person_fragments:
            add_value(" ".join(person_fragments))
            add_value(person_fragments[0])
    hidden_contact_ids.update(
        str(lead.get("contact_id"))
        for lead in ensure_list(graph, "unassigned_contact_leads")
        if isinstance(lead, dict) and has_text(lead.get("contact_id"))
    )
    for contact_id in hidden_contact_ids:
        contact = contacts.get(contact_id)
        if not isinstance(contact, dict):
            continue
        for field in ("normalized_value", "source_literal"):
            add_value(contact.get(field))
    return values
