#!/usr/bin/env python3
"""Generate a Product Outbound Market Analysis Source Pack query plan.

This script is intentionally planning-only.  It reads a market-analysis brief,
selects seed Source Packs, and emits auditable query steps.  It does not search,
open URLs, create EvidenceCards, create MatrixRows, or output market facts.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _superleads_common import contains_local_path, is_safe_public_http_url

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "shared" / "source_packs" / "product_market_seed_packs.json"

EXECUTION_LEVEL = "source_plan_only"
ROUTE = "product_outbound_market_analysis_source_plan"
ALLOWED_OUTPUT = "source_or_query_plan_only"
NOT_EVIDENCE_NOTE = "not_evidence: Source Pack 和 Query Plan 只是来源/查询计划；未打开来源前不能写成事实。"

COUNTRY_ALIASES = {
    "us": "United States",
    "usa": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "america": "United States",
    "美国": "United States",
    "united states": "United States",
    "china": "China",
    "prc": "China",
    "中国": "China",
    "vietnam": "Vietnam",
    "viet nam": "Vietnam",
    "越南": "Vietnam",
}

COUNTRY_TO_PACK = {
    "United States": {
        "destination": [
            "seed_us_market_access_general",
            "seed_us_import_tax_general",
            "seed_us_origin_proof_general",
            "seed_market_signal_global_to_us",
        ],
    },
    "China": {"export": ["seed_cn_export_general"]},
    "Vietnam": {"export": ["seed_vn_export_general"]},
}

COMMON_TRIGGER_PACKS = {
    "lithium_battery": ["seed_lithium_battery_common_rules", "seed_transpacific_logistics_general"],
    "battery_standalone": ["seed_lithium_battery_common_rules", "seed_transpacific_logistics_general"],
    "battery_installed": ["seed_lithium_battery_common_rules", "seed_transpacific_logistics_general"],
    "dangerous_goods": ["seed_lithium_battery_common_rules", "seed_transpacific_logistics_general"],
    "electrical": ["seed_lithium_battery_common_rules"],
    "textile": ["seed_textile_apparel_common_rules"],
    "apparel": ["seed_textile_apparel_common_rules"],
    "cotton": ["seed_textile_apparel_common_rules"],
    "woven": ["seed_textile_apparel_common_rules"],
    "knit": ["seed_textile_apparel_common_rules"],
    "skin_contact": ["seed_textile_apparel_common_rules"],
    "bulk_cargo": ["seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "breakbulk": ["seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "roro": ["seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "heavy_lift": ["seed_transpacific_logistics_general"],
    "oversize": ["seed_transpacific_logistics_general"],
    "project_goods": ["seed_transpacific_logistics_general"],
    "commodity_index_reference": ["seed_market_signal_global_to_us"],
    "steel": ["seed_market_signal_global_to_us", "seed_transpacific_logistics_general"],
    "grain": ["seed_market_signal_global_to_us", "seed_transpacific_logistics_general"],
    "mineral": ["seed_market_signal_global_to_us", "seed_transpacific_logistics_general"],
    "energy": ["seed_market_signal_global_to_us", "seed_transpacific_logistics_general"],
    "food": ["seed_us_market_access_general", "seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "fresh_produce": ["seed_us_market_access_general", "seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "flower": ["seed_us_market_access_general", "seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "tea": ["seed_us_market_access_general", "seed_transpacific_logistics_general", "seed_market_signal_global_to_us"],
    "plant_material": ["seed_us_market_access_general", "seed_transpacific_logistics_general"],
    "cold_chain": ["seed_transpacific_logistics_general"],
}

MODULE_TO_QUERY_GROUPS = {
    "product_profile": {"product_original_sources"},
    "destination_compliance": {"destination_compliance", "origin_proof_requirement"},
    "origin_proof_requirement": {"origin_proof_requirement"},
    "import_tax": {"import_tax", "origin_proof_requirement"},
    "export_requirements": {"export_requirements"},
    "logistics": {"logistics", "lithium_battery_common_rules"},
    "google_trends": {"market_signal"},
    "online_price": {"market_signal"},
    "market_reports": {"market_signal"},
    "season_holiday": {"season_holiday"},
    "external_factors": {"external_factors"},
}

BOUNDARY_BLOCKED_FACTS = [
    "battery_un38_3_or_sds_compliance_conclusion",
    "general_cargo_or_transportability_conclusion",
    "customs_final_rate_or_final_classification_conclusion",
    "guessed_departure_port_or_default_port",
    "physical_label_or_full_bom_compliance_conclusion",
    "origin_marking_or_user_file_promoted_to_origin_proof_rule",
    "route_preference_or_transit_commitment",
    "market_entry_or_customer_type_recommendation",
    "price_recommendation_or_transaction_price_upgrade",
    "google_trends_promoted_to_sales_or_demand",
    "platform_listing_promoted_to_deal_price",
]

REGISTRY_FORBIDDEN_FIELD_PATTERNS = (
    re.compile(r"final[_-]?(duty|tariff|classification|hts|hs)", re.I),
    re.compile(r"latest[_-]?tariff[_-]?rate", re.I),
    re.compile(r"certification[_-]?required", re.I),
    re.compile(r"origin[_-]?proof[_-]?required", re.I),
    re.compile(r"coo[_-]?required", re.I),
    re.compile(r"is[_-]?compliant", re.I),
    re.compile(r"can[_-]?(import|export|ship|transport)", re.I),
    re.compile(r"best[_-]?route", re.I),
    re.compile(r"guaranteed[_-]?transit", re.I),
    re.compile(r"target[_-]?price", re.I),
    re.compile(r"recommended[_-]?(price|customer)", re.I),
    re.compile(r"trend[_-]?is[_-]?growing", re.I),
    re.compile(r"market[_-]?potential", re.I),
)

REGISTRY_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"最终税率为|最终税率就是|已合规|可出运|普通货运输|默认海防港|建议进入|推荐价格|推荐客户类型"),
    re.compile(r"\b\d+(?:\.\d+)?\s*%\b"),
)


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _country(value: Any) -> str | None:
    text = _norm(value)
    if not text:
        return None
    return COUNTRY_ALIASES.get(text.casefold(), text)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _str_list(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        text = _norm(item)
        if text:
            result.append(text)
    return result


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _maybe_brief_from_graph(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("graph_type") != "ProductMarketAnalysisGraph":
        return payload
    briefs = [item for item in _as_list(payload.get("briefs")) if isinstance(item, dict)]
    products = {str(item.get("product_subject_id")): item for item in _as_list(payload.get("products")) if isinstance(item, dict)}
    attributes = [item for item in _as_list(payload.get("attributes")) if isinstance(item, dict)]
    if not briefs:
        return payload
    brief = dict(briefs[-1])
    product = products.get(str(brief.get("product_subject_id")), {})
    if isinstance(product, dict):
        brief.setdefault("product_name", product.get("display_name"))
        brief.setdefault("manufacturer_or_brand", product.get("manufacturer_or_brand"))
        versions = product.get("version_identifiers")
        if versions:
            brief.setdefault("model_or_sku", "; ".join(str(item) for item in _as_list(versions)))
        unknowns = product.get("unknown_key_attributes")
        if unknowns:
            brief.setdefault("unknown_key_attributes", unknowns)
    trigger_tags: list[str] = []
    for attr in attributes:
        for path in _str_list(attr.get("trigger_paths")):
            low = path.casefold()
            if "锂" in path or "battery" in low:
                trigger_tags.extend(["lithium_battery", "dangerous_goods"])
            if "纺织" in path or "textile" in low or "label" in low:
                trigger_tags.extend(["textile", "apparel"])
    if trigger_tags:
        brief.setdefault("product_trigger_tags", _dedupe(trigger_tags))
    origin = brief.get("origin_country_status")
    if isinstance(origin, dict) and origin.get("country_or_region"):
        brief.setdefault("origin_country_or_region", origin.get("country_or_region"))
    return brief


def _brief_value(brief: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in brief and brief[name] not in (None, ""):
            return brief[name]
    return None


def _brief_product_tags(brief: dict[str, Any]) -> list[str]:
    tags = _str_list(_brief_value(brief, "product_trigger_tags", "trigger_tags", "tags"))
    attrs = _brief_value(brief, "attributes", "product_attributes")
    attr_text = json.dumps(attrs, ensure_ascii=False).casefold() if attrs is not None else ""
    product_text = " ".join([
        _norm(_brief_value(brief, "product_name", "display_name", "product")),
        _norm(_brief_value(brief, "product_family")),
        _norm(_brief_value(brief, "model_or_sku", "model", "sku")),
        attr_text,
    ]).casefold()
    inferred: list[str] = []
    if any(marker in product_text for marker in ("lifepo4", "lithium", "锂电")):
        inferred.extend(["lithium_battery", "dangerous_goods", "electrical"])
    if "battery" in product_text or "电池" in product_text:
        inferred.append("battery_standalone")
    if any(marker in product_text for marker in ("textile", "fabric", "apparel", "shirt", "纺织", "面料", "衬衫", "服装")):
        inferred.extend(["textile", "apparel"])
    if any(marker in product_text for marker in ("cotton", "棉")):
        inferred.append("cotton")
    if any(marker in product_text for marker in ("woven", "corduroy", "机织", "灯芯绒")):
        inferred.extend(["woven", "skin_contact"])
    if any(marker in product_text for marker in ("bulk", "散杂", "breakbulk")):
        inferred.extend(["bulk_cargo", "breakbulk"])
    if any(marker in product_text for marker in ("roro", "滚装")):
        inferred.append("roro")
    if any(marker in product_text for marker in ("heavy", "大型机械", "矿山机械", "超重")):
        inferred.append("heavy_lift")
    if any(marker in product_text for marker in ("steel", "钢")):
        inferred.extend(["steel", "commodity_index_reference", "bulk_cargo"])
    if any(marker in product_text for marker in ("grain", "粮")):
        inferred.extend(["grain", "commodity_index_reference", "bulk_cargo"])
    if any(marker in product_text for marker in ("mineral", "矿")):
        inferred.extend(["mineral", "commodity_index_reference", "bulk_cargo"])
    if any(marker in product_text for marker in ("fresh", "vegetable", "fruit", "蔬菜", "水果", "鲜")):
        inferred.extend(["fresh_produce", "food", "cold_chain"])
    if "tea" in product_text or "茶" in product_text:
        inferred.extend(["tea", "food", "plant_material"])
    return _dedupe(tags + inferred + ["general_goods"])



def _transpacific_pack_applies(target: str | None, export_country: str | None, departure_country: str | None, origin_country: str | None) -> bool:
    return target == "United States" and any(
        country in {"China", "Vietnam"}
        for country in (export_country, departure_country, origin_country)
    )

def _registry_maps(registry: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    packs = {str(item.get("source_pack_id")): item for item in _as_list(registry.get("source_packs")) if isinstance(item, dict)}
    entries = {str(item.get("source_entry_id")): item for item in _as_list(registry.get("source_entries")) if isinstance(item, dict)}
    templates = {str(item.get("query_template_id")): item for item in _as_list(registry.get("query_templates")) if isinstance(item, dict)}
    obs = {str(item.get("observation_requirement_id")): item for item in _as_list(registry.get("observation_requirements")) if isinstance(item, dict)}
    rules = {str(item.get("route_rule_id")): item for item in _as_list(registry.get("route_rules")) if isinstance(item, dict)}
    return packs, entries, templates, obs, rules


def _walk_registry_for_forbidden(value: Any, path: str = "$") -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, val in value.items():
            key_text = str(key)
            if any(pattern.search(key_text) for pattern in REGISTRY_FORBIDDEN_FIELD_PATTERNS):
                issues.append({"code": "market_pack_fact_field_forbidden", "path": f"{path}.{key_text}", "message": f"Source Pack registry field looks fact-like: {key_text}"})
            issues.extend(_walk_registry_for_forbidden(val, f"{path}.{key_text}"))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(_walk_registry_for_forbidden(item, f"{path}[{idx}]"))
    elif isinstance(value, str):
        if contains_local_path(value) or value.startswith("file://"):
            issues.append({"code": "market_pack_internal_leak", "path": path, "message": "Source Pack registry contains local path or file URI"})
        # Allow safe public URL values, but still fail obvious factual conclusions.
        for pattern in REGISTRY_FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(value):
                issues.append({"code": "market_pack_fact_value_forbidden", "path": path, "message": "Source Pack registry contains a forbidden factual conclusion phrase or rate-like value"})
                break
    return issues


def validate_registry(registry: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if registry.get("registry_type") != "product_market_source_pack_registry":
        issues.append({"code": "market_pack_registry_type_invalid", "path": "registry_type", "message": "registry_type must be product_market_source_pack_registry"})
    boundary = registry.get("execution_boundary")
    if not isinstance(boundary, dict) or boundary.get("execution_level") != EXECUTION_LEVEL or boundary.get("not_evidence") is not True:
        issues.append({"code": "market_pack_registry_boundary_missing", "path": "execution_boundary", "message": "Registry must declare source_plan_only and not_evidence"})
    packs, entries, templates, obs, rules = _registry_maps(registry)
    required_pack_fields = {
        "source_pack_id", "display_name", "pack_type", "trade_role", "jurisdiction_type", "jurisdiction_name",
        "fact_domains_supported", "fact_domains_not_supported", "product_trigger_tags", "required_brief_fields",
        "entry_ids", "query_template_ids", "observation_requirement_ids", "route_rule_ids", "status", "version",
        "review_cycle_policy", "pack_boundary_note", "blocked_outputs",
    }
    for pack_id, pack in packs.items():
        missing = sorted(field for field in required_pack_fields if field not in pack)
        if missing:
            issues.append({"code": "market_pack_required_field_missing", "path": f"source_packs.{pack_id}", "message": ", ".join(missing)})
        note = _norm(pack.get("pack_boundary_note"))
        if "入口" not in note or not any(marker in note for marker in ("不能", "不", "仅")):
            issues.append({"code": "market_pack_missing_boundary_note", "path": f"source_packs.{pack_id}.pack_boundary_note", "message": "Pack must state it is only a source-entry directory"})
        if not _str_list(pack.get("blocked_outputs")):
            issues.append({"code": "market_pack_blocked_outputs_missing", "path": f"source_packs.{pack_id}.blocked_outputs", "message": "Pack must list blocked outputs"})
        if pack.get("pack_type") in {"destination_market_access_pack", "destination_duty_tax_pack", "destination_origin_proof_pack", "export_country_pack"}:
            authority_levels = {str(entries.get(eid, {}).get("source_authority_level")) for eid in _str_list(pack.get("entry_ids"))}
            if "primary_official" not in authority_levels and "secondary_official" not in authority_levels:
                issues.append({"code": "market_pack_no_official_entry", "path": f"source_packs.{pack_id}.entry_ids", "message": "Regulatory/tax/export Pack needs official or authority entry"})
        for eid in _str_list(pack.get("entry_ids")):
            if eid not in entries:
                issues.append({"code": "market_pack_entry_missing", "path": f"source_packs.{pack_id}.entry_ids", "message": f"Unknown SourceEntry {eid}"})
        for qid in _str_list(pack.get("query_template_ids")):
            if qid not in templates:
                issues.append({"code": "market_pack_query_template_missing", "path": f"source_packs.{pack_id}.query_template_ids", "message": f"Unknown QueryTemplate {qid}"})
        for oid in _str_list(pack.get("observation_requirement_ids")):
            if oid not in obs:
                issues.append({"code": "market_pack_observation_requirement_missing", "path": f"source_packs.{pack_id}.observation_requirement_ids", "message": f"Unknown ObservationRequirement {oid}"})
        for rid in _str_list(pack.get("route_rule_ids")):
            if rid not in rules:
                issues.append({"code": "market_pack_route_rule_missing", "path": f"source_packs.{pack_id}.route_rule_ids", "message": f"Unknown PackRouteRule {rid}"})
    for entry_id, item in entries.items():
        pack_id = str(item.get("source_pack_id"))
        if pack_id not in packs:
            issues.append({"code": "market_entry_pack_missing", "path": f"source_entries.{entry_id}.source_pack_id", "message": f"Unknown pack {pack_id}"})
        locator = _norm(item.get("landing_url_or_locator_template"))
        if locator.startswith("http") and not is_safe_public_http_url(locator):
            issues.append({"code": "market_pack_entry_locator_unsafe", "path": f"source_entries.{entry_id}.landing_url_or_locator_template", "message": "Entry locator URL is not a safe public HTTP URL"})
    for qid, item in templates.items():
        pack_id = str(item.get("source_pack_id"))
        if pack_id not in packs:
            issues.append({"code": "market_query_template_pack_missing", "path": f"query_templates.{qid}.source_pack_id", "message": f"Unknown pack {pack_id}"})
        if item.get("reject_if_only_snippet") is not True:
            issues.append({"code": "market_pack_query_snippet_claim", "path": f"query_templates.{qid}.reject_if_only_snippet", "message": "QueryTemplate must reject snippet-only facts"})
    issues.extend(_walk_registry_for_forbidden(registry))
    return issues


def _select_pack_ids(brief: dict[str, Any], registry: dict[str, Any]) -> tuple[list[str], list[dict[str, str]], list[str]]:
    tags = _brief_product_tags(brief)
    target = _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region"))
    export_country = _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country"))
    origin_country = _country(_brief_value(brief, "origin_country_or_region", "origin_country", "production_country"))
    departure_country = _country(_brief_value(brief, "departure_country_or_region", "departure_country"))
    candidate_hs = _norm(_brief_value(brief, "candidate_hs_hts", "candidate_hs", "candidate_hts"))
    requested_modules = set(_str_list(_brief_value(brief, "analysis_modules_requested", "modules_requested")))

    selected: list[str] = []
    warnings: list[dict[str, str]] = []
    route_notes: list[str] = []

    if target in COUNTRY_TO_PACK and "destination" in COUNTRY_TO_PACK[target]:
        selected.extend(COUNTRY_TO_PACK[target]["destination"])
        route_notes.append(f"target_country_or_region={target} -> destination/import/origin-proof/market-signal packs")
    elif target:
        warnings.append({"code": "market_source_pack_destination_missing", "message": f"目标国家/地区 {target} 暂无内置目的国 Source Pack；只能保留人工 Query Plan。"})
    else:
        warnings.append({"code": "market_source_plan_missing_target_country", "message": "缺少目标销售国家/地区；目的国准入、税费、COO 和市场信号查询只能停在计划缺口。"})

    if export_country in COUNTRY_TO_PACK and "export" in COUNTRY_TO_PACK[export_country]:
        selected.extend(COUNTRY_TO_PACK[export_country]["export"])
        route_notes.append(f"export_declaration_country={export_country} -> export-country pack")
    elif export_country:
        warnings.append({"code": "market_source_pack_export_country_missing", "message": f"出口申报国 {export_country} 暂无内置出口国 Source Pack；只能保留人工 Query Plan。"})
    elif origin_country:
        warnings.append({"code": "market_export_country_unconfirmed", "message": f"只看到原产/制造来源 {origin_country}，不能自动当成出口申报国；出口国要求查询需用户确认。"})
    else:
        warnings.append({"code": "market_source_plan_missing_export_country", "message": "未设置出口申报国；默认出口国应由用户可见设置，不从原产国或卖方国猜。"})

    transpacific_applies = _transpacific_pack_applies(target, export_country, departure_country, origin_country)

    if transpacific_applies:
        selected.append("seed_transpacific_logistics_general")
        route_notes.append("US target + China/Vietnam trade premise -> transpacific logistics pack")

    for tag in tags:
        for pack_id in COMMON_TRIGGER_PACKS.get(tag, []):
            if pack_id == "seed_transpacific_logistics_general" and not transpacific_applies:
                continue
            selected.append(pack_id)
            route_notes.append(f"product_trigger_tag={tag} -> {pack_id}")

    if _norm(_brief_value(brief, "product_name", "display_name", "product")) or _brief_value(brief, "product_source_urls", "source_urls", "user_files"):
        selected.append("seed_product_original_sources")
        route_notes.append("product identity/source material present -> product original sources pack")

    if candidate_hs and target == "United States":
        selected.extend(["seed_us_import_tax_general", "seed_us_origin_proof_general"])
        route_notes.append("candidate_hs_hts present + target US -> official tariff/origin-proof query packs")

    # If the user explicitly requested a module, keep its pack even if trigger tags are sparse.
    if requested_modules:
        if requested_modules & {"logistics"}:
            if transpacific_applies:
                selected.append("seed_transpacific_logistics_general")
            else:
                warnings.append({"code": "market_source_pack_logistics_lane_missing", "message": "当前贸易前提不满足中国/越南至美国物流 Pack；物流只能保留人工查询计划或待补路线 Pack。"})
        if requested_modules & {"google_trends", "online_price", "market_reports", "season_holiday", "external_factors"} and target == "United States":
            selected.append("seed_market_signal_global_to_us")
        if requested_modules & {"destination_compliance", "origin_proof_requirement"} and target == "United States":
            selected.extend(["seed_us_market_access_general", "seed_us_origin_proof_general"])
        if requested_modules & {"import_tax"} and target == "United States":
            selected.append("seed_us_import_tax_general")
        if requested_modules & {"export_requirements"}:
            if export_country == "China":
                selected.append("seed_cn_export_general")
            elif export_country == "Vietnam":
                selected.append("seed_vn_export_general")

    packs, _, _, _, _ = _registry_maps(registry)
    selected = [pack_id for pack_id in _dedupe(selected) if pack_id in packs]
    return selected, warnings, _dedupe(route_notes)


def _template_should_run(template: dict[str, Any], brief: dict[str, Any], pack_id: str) -> tuple[bool, str | None]:
    group = str(template.get("query_group_id") or "")
    tags = set(_brief_product_tags(brief))
    required_tags = set(_str_list(template.get("required_product_trigger_tags")))
    requested_modules = set(_str_list(_brief_value(brief, "analysis_modules_requested", "modules_requested")))
    target = _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region"))
    export_country = _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country"))

    if required_tags and not required_tags.intersection(tags):
        return False, "required product trigger tags not present"
    if group == "export_requirements":
        if pack_id == "seed_cn_export_general" and export_country != "China":
            return False, "export declaration country is not China"
        if pack_id == "seed_vn_export_general" and export_country != "Vietnam":
            return False, "export declaration country is not Vietnam"
    if group in {"destination_compliance", "import_tax", "origin_proof_requirement", "market_signal", "season_holiday", "external_factors"} and target != "United States":
        return False, "seed destination pack currently covers United States only"
    # When modules are supplied, keep required module groups; product_original and trigger-specific docs are always useful.
    if requested_modules:
        allowed = set().union(*(MODULE_TO_QUERY_GROUPS.get(module, set()) for module in requested_modules))
        always = {"product_original_sources", "lithium_battery_common_rules", "textile_apparel_common_rules", "export_requirements"}
        if group not in allowed | always:
            # Still keep trigger/source/export query groups because they are boundary checks, not facts.
            return False, f"query group {group} not requested"
    return True, None


def _inputs_used_for_template(template: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
    aliases = {
        "destination_country_or_region": "target_country_or_region",
        "model_or_sku": "model_or_sku",
        "candidate_hs_hts": "candidate_hs_hts",
        "origin_country_or_region": "origin_country_or_region",
        "departure_country_or_region": "departure_country_or_region",
    }
    used: dict[str, Any] = {}
    for slot in _str_list(template.get("term_slots")) + _str_list(template.get("required_brief_fields")):
        key = aliases.get(slot, slot)
        value = _brief_value(brief, key, slot)
        if value is None and slot == "product_trigger_tags":
            value = _brief_product_tags(brief)
        if value is None and slot == "target_country_or_region":
            value = _country(_brief_value(brief, "destination_country_or_region"))
        if value is not None:
            used[slot] = value
    # Always include these visible trade roles when known so the plan does not merge them.
    for key in ("target_country_or_region", "export_declaration_country", "origin_country_or_region", "departure_country_or_region", "departure_node", "destination_node", "candidate_hs_hts"):
        value = _brief_value(brief, key)
        if value is not None:
            used.setdefault(key, value)
    return used


def _fill_blueprint(template: str, inputs: dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        value = inputs.get(key)
        if isinstance(value, list):
            return " ".join(str(item) for item in value if item)
        if value is None or value == "":
            return f"<{key}:待确认>"
        return str(value)
    return re.sub(r"\{([A-Za-z0-9_]+)\}", repl, template)


def _manual_gap_steps(brief: dict[str, Any], selected_pack_ids: list[str], templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    target = _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region"))
    export_country = _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country"))
    if target and target != "United States":
        steps.append({
            "query_plan_id": "qp_manual_destination_pack_gap",
            "pack_id": None,
            "template_id": "manual_destination_source_pack_gap",
            "query_group_id": "destination_pack_gap",
            "purpose": f"目标国家/地区 {target} 暂无内置目的国 Source Pack，先生成人工计划入口清单。",
            "inputs_used": {"target_country_or_region": target, "product_name": _brief_value(brief, "product_name", "display_name", "product")},
            "query_strings": [f"{target} official customs import requirements <product/HS>", f"{target} official tariff lookup <candidate HS>"],
            "source_entry_ids": [],
            "required_source_priority": ["primary_official"],
            "must_open_source": True,
            "reject_if_only_snippet": True,
            "not_evidence": True,
            "allowed_output": ALLOWED_OUTPUT,
            "expected_observation_fields": ["source_name", "url", "date", "applicability", "limitations"],
            "expected_matrix_sheet": "信息来源与待确认事项",
            "fallback_status": "source_pack_missing_manual_plan_only",
            "handoff_target_skill": "analyzing-product-outbound-market",
            "blocked_outputs": BOUNDARY_BLOCKED_FACTS,
            "boundary_note": NOT_EVIDENCE_NOTE,
        })
    logistics_requested = "logistics" in set(_str_list(_brief_value(brief, "analysis_modules_requested", "modules_requested")))
    origin_country = _country(_brief_value(brief, "origin_country_or_region", "origin_country", "production_country"))
    departure_country = _country(_brief_value(brief, "departure_country_or_region", "departure_country"))
    if logistics_requested and not _transpacific_pack_applies(target, export_country, departure_country, origin_country):
        steps.append({
            "query_plan_id": "qp_manual_logistics_lane_pack_gap",
            "pack_id": None,
            "template_id": "manual_logistics_lane_pack_gap",
            "query_group_id": "logistics_pack_gap",
            "purpose": "当前起运国/目的国组合暂无可直接套用的物流 Source Pack，先生成人工物流来源计划。",
            "inputs_used": {"target_country_or_region": target, "export_declaration_country": export_country, "departure_country_or_region": departure_country, "origin_country_or_region": origin_country, "product_name": _brief_value(brief, "product_name", "display_name", "product")},
            "query_strings": ["official customs pre filing requirements <destination country> <transport mode>", "public port carrier route guidance <departure country> <destination country> <cargo condition>"],
            "source_entry_ids": [],
            "required_source_priority": ["primary_official", "commercial_reference"],
            "must_open_source": True,
            "reject_if_only_snippet": True,
            "not_evidence": True,
            "allowed_output": ALLOWED_OUTPUT,
            "expected_observation_fields": ["source_name", "url", "date", "route_or_node", "cargo_condition", "limitations"],
            "expected_matrix_sheet": "运输方式、路线、港口与申报节点",
            "fallback_status": "logistics_lane_pack_missing_manual_plan_only",
            "handoff_target_skill": "logistics_skill",
            "blocked_outputs": BOUNDARY_BLOCKED_FACTS,
            "boundary_note": NOT_EVIDENCE_NOTE,
        })
    if export_country and export_country not in {"China", "Vietnam"}:
        steps.append({
            "query_plan_id": "qp_manual_export_pack_gap",
            "pack_id": None,
            "template_id": "manual_export_source_pack_gap",
            "query_group_id": "export_pack_gap",
            "purpose": f"出口申报国 {export_country} 暂无内置出口国 Source Pack，先生成人工计划入口清单。",
            "inputs_used": {"export_declaration_country": export_country, "target_country_or_region": target, "product_name": _brief_value(brief, "product_name", "display_name", "product")},
            "query_strings": [f"{export_country} official customs export requirements <product/HS>", f"{export_country} export control official list <product/HS>"],
            "source_entry_ids": [],
            "required_source_priority": ["primary_official"],
            "must_open_source": True,
            "reject_if_only_snippet": True,
            "not_evidence": True,
            "allowed_output": ALLOWED_OUTPUT,
            "expected_observation_fields": ["source_name", "url", "date", "applicability", "limitations"],
            "expected_matrix_sheet": "信息来源与待确认事项",
            "fallback_status": "source_pack_missing_manual_plan_only",
            "handoff_target_skill": "export_country_requirements_skill",
            "blocked_outputs": BOUNDARY_BLOCKED_FACTS,
            "boundary_note": NOT_EVIDENCE_NOTE,
        })
    return steps


def build_query_plan(brief_payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    brief = _maybe_brief_from_graph(brief_payload)
    packs, entries, templates, obs_map, rules = _registry_maps(registry)
    registry_issues = validate_registry(registry)
    selected_pack_ids, warnings, route_notes = _select_pack_ids(brief, registry)
    tags = _brief_product_tags(brief)
    if registry_issues:
        warnings.extend({"code": item["code"], "message": f"Registry self-check: {item['message']} ({item['path']})"} for item in registry_issues)

    selected_packs: list[dict[str, Any]] = []
    query_plan: list[dict[str, Any]] = []

    for pack_id in selected_pack_ids:
        pack = packs[pack_id]
        selected_packs.append({
            "pack_id": pack_id,
            "display_name": pack.get("display_name"),
            "pack_type": pack.get("pack_type"),
            "trade_role": pack.get("trade_role"),
            "jurisdiction_name": pack.get("jurisdiction_name"),
            "fact_domains_supported": pack.get("fact_domains_supported", []),
            "pack_boundary_note": pack.get("pack_boundary_note"),
            "not_evidence": True,
            "allowed_output": ALLOWED_OUTPUT,
            "blocked_outputs": pack.get("blocked_outputs", []),
        })
        for template_id in _str_list(pack.get("query_template_ids")):
            template = templates.get(template_id)
            if not template:
                continue
            should_run, skip_reason = _template_should_run(template, brief, pack_id)
            if not should_run:
                continue
            inputs = _inputs_used_for_template(template, brief)
            query_strings = [_fill_blueprint(item, inputs) for item in _str_list(template.get("query_blueprints"))]
            step = {
                "query_plan_id": f"qp_{len(query_plan)+1:03d}_{template_id}",
                "pack_id": pack_id,
                "template_id": template_id,
                "query_group_id": template.get("query_group_id"),
                "purpose": template.get("purpose"),
                "inputs_used": inputs,
                "query_strings": query_strings,
                "source_entry_ids": template.get("source_entry_scope", []),
                "required_source_priority": template.get("must_open_source_authority_levels", []),
                "must_open_source": True,
                "reject_if_only_snippet": True,
                "not_evidence": True,
                "allowed_output": ALLOWED_OUTPUT,
                "expected_observation_fields": template.get("expected_observation_fields", []),
                "expected_matrix_sheet": template.get("expected_matrix_sheet"),
                "fallback_status": template.get("fallback_status"),
                "handoff_target_skill": template.get("handoff_target_skill"),
                "blocked_outputs": _dedupe(_str_list(pack.get("blocked_outputs")) + BOUNDARY_BLOCKED_FACTS),
                "boundary_note": NOT_EVIDENCE_NOTE,
            }
            query_plan.append(step)

    query_plan.extend(_manual_gap_steps(brief, selected_pack_ids, query_plan))

    missing_required: list[str] = []
    if not _brief_value(brief, "target_country_or_region", "destination_country_or_region"):
        missing_required.append("target_country_or_region")
    if not _brief_value(brief, "product_name", "display_name", "product"):
        missing_required.append("product_name")
    if not _brief_value(brief, "export_declaration_country", "default_export_declaration_country"):
        warnings.append({"code": "market_source_plan_export_country_visible_default_needed", "message": "出口申报国未设置；未来 UI 应显示默认出口国并允许用户改，不从原产地自动推断。"})
    if not _brief_value(brief, "origin_country_or_region", "origin_country", "production_country"):
        warnings.append({"code": "market_source_plan_origin_country_unknown", "message": "原产国/制造来源未知；税费、COO、贸易救济和标签查询只能保留原产地缺口。"})
    if not _brief_value(brief, "departure_node"):
        warnings.append({"code": "market_source_plan_departure_node_unknown", "message": "实际起运地/港口/机场未知；物流计划不得猜默认港口。"})

    return {
        "ok": not registry_issues and not missing_required,
        "route": ROUTE,
        "execution_level": EXECUTION_LEVEL,
        "not_evidence": True,
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "allowed_output": ALLOWED_OUTPUT,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "registry": {
            "path": "shared/source_packs/product_market_seed_packs.json",
            "version": registry.get("version"),
            "boundary_note": registry.get("execution_boundary", {}).get("boundary_note"),
        },
        "brief_summary": {
            "product_name": _brief_value(brief, "product_name", "display_name", "product"),
            "target_country_or_region": _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region")),
            "export_declaration_country": _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country")),
            "origin_country_or_region": _country(_brief_value(brief, "origin_country_or_region", "origin_country", "production_country")),
            "departure_country_or_region": _country(_brief_value(brief, "departure_country_or_region", "departure_country")),
            "departure_node": _brief_value(brief, "departure_node"),
            "destination_node": _brief_value(brief, "destination_node"),
            "candidate_hs_hts": _brief_value(brief, "candidate_hs_hts", "candidate_hs", "candidate_hts"),
            "product_trigger_tags": tags,
            "roles_separated": True,
        },
        "selected_pack_ids": selected_pack_ids,
        "selected_packs": selected_packs,
        "route_notes": route_notes,
        "query_plan": query_plan,
        "warnings": warnings,
        "missing_required_fields": missing_required,
        "blocked_facts": BOUNDARY_BLOCKED_FACTS,
        "guardrails": [
            "source_plan_only",
            "not_evidence",
            "must_open_source",
            "reject_if_only_snippet",
            "Source Pack / QueryTemplate / Search snippet 不能直接生成 EvidenceCard 或 MatrixRow",
            "没有真实打开来源时，不输出税率、认证、物流时效、趋势、价格或市场判断",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Brief JSON or ProductMarketAnalysisGraph JSON")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Source Pack registry JSON")
    parser.add_argument("--format", choices=["json"], default="json")
    parser.add_argument("--check-registry", action="store_true", help="Only validate the Source Pack registry")
    args = parser.parse_args()

    registry_path = Path(args.registry)
    registry = _load_json(registry_path)
    if args.check_registry:
        issues = validate_registry(registry)
        print(json.dumps({"ok": not issues, "issue_count": len(issues), "issues": issues}, ensure_ascii=False, indent=2))
        return 0 if not issues else 1

    if not args.input:
        parser.error("--input is required unless --check-registry is used")
    brief = _load_json(Path(args.input))
    result = build_query_plan(brief, registry)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
