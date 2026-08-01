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
    "840": "United States",
    "u.s.": "United States",
    "u.s.a.": "United States",
    "america": "United States",
    "美国": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "cn": "China",
    "chn": "China",
    "156": "China",
    "china": "China",
    "prc": "China",
    "people's republic of china": "China",
    "peoples republic of china": "China",
    "中国": "China",
    "vn": "Vietnam",
    "vnm": "Vietnam",
    "704": "Vietnam",
    "vietnam": "Vietnam",
    "viet nam": "Vietnam",
    "越南": "Vietnam",
    "de": "Germany",
    "deu": "Germany",
    "276": "Germany",
    "germany": "Germany",
    "deutschland": "Germany",
    "德国": "Germany",
    "in": "India",
    "ind": "India",
    "356": "India",
    "india": "India",
    "印度": "India",
    "gb": "United Kingdom",
    "gbr": "United Kingdom",
    "uk": "United Kingdom",
    "826": "United Kingdom",
    "united kingdom": "United Kingdom",
    "great britain": "United Kingdom",
    "britain": "United Kingdom",
    "英国": "United Kingdom",
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

BRIEF_FIELD_ALIASES = {
    "product_name": [
        "product_name",
        "display_name",
        "product",
        "product_category",
        "category",
        "product_family",
        "product_description",
        "use_description",
        "用途描述",
        "产品",
        "品类",
    ],
    "target_country_or_region": [
        "target_country_or_region",
        "destination_country_or_region",
        "target_country",
        "destination_country",
        "target_market",
        "destination_market",
        "sales_country",
        "import_country",
        "目的国",
        "目标国家",
        "目标市场",
    ],
    "destination_country_or_region": [
        "destination_country_or_region",
        "target_country_or_region",
        "destination_country",
        "target_country",
        "target_market",
        "destination_market",
        "sales_country",
        "import_country",
        "目的国",
        "目标国家",
        "目标市场",
    ],
    "candidate_hs_hts": [
        "candidate_hs_hts",
        "candidate_hs",
        "candidate_hts",
        "hs_code",
        "hts_code",
        "htsus",
        "hts",
        "hs",
        "hs_or_hts",
        "hs_or_hts_candidates",
        "tariff_code",
        "commodity_code",
        "customs_code",
        "税号",
        "海关编码",
        "HTScode",
    ],
    "export_declaration_country": [
        "export_declaration_country",
        "default_export_declaration_country",
        "export_country",
        "出口国",
        "出口申报国",
    ],
    "origin_country_or_region": [
        "origin_country_or_region",
        "origin_country",
        "customs_origin_country",
        "customs_origin_country_or_region",
        "country_of_origin",
        "country_of_origin_or_region",
        "原产国",
        "原产地",
        "海关原产国",
    ],
    "manufacturing_country_clue": [
        "manufacturing_country_clue",
        "production_country",
        "manufacturing_country",
        "made_in_country",
        "coo_country",
        "制造来源",
        "生产国",
        "生产/制造来源",
    ],
    "departure_country_or_region": [
        "departure_country_or_region",
        "departure_country",
        "ship_from_country",
        "origin_shipping_country",
        "起运国",
        "发货国",
    ],
    "departure_node": [
        "departure_node",
        "departure_port",
        "origin_port",
        "ship_from_port",
        "loading_port",
        "port_of_loading",
        "起运港",
        "装运港",
    ],
    "destination_node": [
        "destination_node",
        "destination_port",
        "port_of_discharge",
        "delivery_city",
        "目的港",
        "目的城市",
    ],
    "model_or_sku": ["model_or_sku", "model", "sku", "version", "型号", "规格"],
    "manufacturer_or_brand": ["manufacturer_or_brand", "manufacturer", "brand", "maker", "品牌", "制造商"],
    "product_trigger_tags": ["product_trigger_tags", "trigger_tags", "tags"],
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


def _looks_like_unmapped_country_code(raw_value: Any, normalized_value: str | None) -> bool:
    raw = _norm(raw_value)
    if not raw or not normalized_value:
        return False
    compact = re.sub(r"[\s._-]+", "", raw)
    if not re.fullmatch(r"[A-Za-z]{2,3}|\d{3}", compact):
        return False
    return _country(raw) == raw


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
    candidates: list[str] = []
    seen: set[str] = set()
    for name in names:
        for candidate in [name, *BRIEF_FIELD_ALIASES.get(name, [])]:
            if candidate not in seen:
                seen.add(candidate)
                candidates.append(candidate)
    for name in candidates:
        if name in brief and brief[name] not in (None, ""):
            return brief[name]
    return None


def _candidate_hs_hts(brief: dict[str, Any]) -> str:
    return _norm(_brief_value(brief, "candidate_hs_hts", "candidate_hs", "candidate_hts"))


def _brief_origin_country(brief: dict[str, Any]) -> str | None:
    """Return only explicit customs-origin fields, not Made in/manufacturing clues."""
    return _country(_brief_value(brief, "origin_country_or_region", "origin_country"))


def _brief_manufacturing_country_clue(brief: dict[str, Any]) -> str | None:
    """Return production/Made-in clues that must not satisfy customs-origin gaps."""
    return _country(_brief_value(brief, "manufacturing_country_clue"))


def _brief_product_identity(brief: dict[str, Any]) -> str:
    product = _brief_value(brief, "product_name", "display_name", "product")
    if product is not None:
        return _norm(product)
    candidate_hs = _candidate_hs_hts(brief)
    if candidate_hs:
        return f"候选 HS/HTS {candidate_hs}"
    if _brief_value(brief, "product_source_urls", "source_urls", "user_files", "image_clue", "product_image"):
        return "用户提供的产品资料线索"
    return ""


def _brief_product_query_term(brief: dict[str, Any]) -> str:
    """Return a search-safe product term, separated from the user-facing identity label."""
    product = _brief_value(brief, "product_name", "display_name", "product")
    if product is not None:
        return _norm(product)
    candidate_hs = _candidate_hs_hts(brief)
    if candidate_hs:
        return candidate_hs
    return ""


def _brief_has_only_source_material_identity(brief: dict[str, Any]) -> bool:
    if _norm(_brief_value(brief, "product_name", "display_name", "product")):
        return False
    if _candidate_hs_hts(brief):
        return False
    return bool(_brief_value(brief, "product_source_urls", "source_urls", "user_files", "image_clue", "product_image"))


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
    raw_target = _brief_value(brief, "target_country_or_region", "destination_country_or_region")
    raw_export_country = _brief_value(brief, "export_declaration_country", "default_export_declaration_country")
    raw_departure_country = _brief_value(brief, "departure_country_or_region", "departure_country")
    target = _country(raw_target)
    export_country = _country(raw_export_country)
    origin_country = _brief_origin_country(brief)
    departure_country = _country(raw_departure_country)
    candidate_hs = _candidate_hs_hts(brief)
    requested_modules = set(_str_list(_brief_value(brief, "analysis_modules_requested", "modules_requested")))

    selected: list[str] = []
    warnings: list[dict[str, str]] = []
    route_notes: list[str] = []

    if target in COUNTRY_TO_PACK and "destination" in COUNTRY_TO_PACK[target]:
        selected.extend(COUNTRY_TO_PACK[target]["destination"])
        route_notes.append(f"target_country_or_region={target} -> destination/import/origin-proof/market-signal packs")
    elif target:
        if _looks_like_unmapped_country_code(raw_target, target):
            warnings.append({"code": "market_source_plan_country_code_unrecognized", "message": f"目标国家/地区 {raw_target} 看起来像国家代码但未完成规范化；需确认后再判断是否有内置目的国 Source Pack。"})
        warnings.append({"code": "market_source_pack_destination_missing", "message": f"目标国家/地区 {target} 暂无内置目的国 Source Pack；只能保留人工 Query Plan。"})
    else:
        warnings.append({"code": "market_source_plan_missing_target_country", "message": "缺少目标销售国家/地区；目的国准入、税费、COO 和市场信号查询只能停在计划缺口。"})

    if export_country in COUNTRY_TO_PACK and "export" in COUNTRY_TO_PACK[export_country]:
        selected.extend(COUNTRY_TO_PACK[export_country]["export"])
        route_notes.append(f"export_declaration_country={export_country} -> export-country pack")
    elif export_country:
        if _looks_like_unmapped_country_code(raw_export_country, export_country):
            warnings.append({"code": "market_source_plan_country_code_unrecognized", "message": f"出口申报国 {raw_export_country} 看起来像国家代码但未完成规范化；需确认后再判断是否有内置出口国 Source Pack。"})
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
            if pack_id.startswith("seed_us_") and target != "United States":
                continue
            if pack_id == "seed_market_signal_global_to_us" and target != "United States":
                continue
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
    country_slots = {
        "target_country_or_region",
        "destination_country_or_region",
        "export_declaration_country",
        "origin_country_or_region",
        "departure_country_or_region",
    }
    used: dict[str, Any] = {}
    for slot in _str_list(template.get("term_slots")) + _str_list(template.get("required_brief_fields")):
        key = aliases.get(slot, slot)
        if slot == "product_name":
            value = _brief_product_query_term(brief)
        elif key == "origin_country_or_region":
            value = _brief_origin_country(brief)
        else:
            value = _brief_value(brief, key, slot)
        if value is None and slot == "product_trigger_tags":
            value = _brief_product_tags(brief)
        if value is None and slot == "target_country_or_region":
            value = _country(_brief_value(brief, "destination_country_or_region"))
        if value is not None and (slot in country_slots or key in country_slots):
            value = _country(value)
        if value is not None:
            used[slot] = value
    # Always include these visible trade roles when known so the plan does not merge them.
    for key in ("target_country_or_region", "export_declaration_country", "origin_country_or_region", "departure_country_or_region", "departure_node", "destination_node", "candidate_hs_hts"):
        if key == "origin_country_or_region":
            value = _brief_origin_country(brief)
        else:
            value = _brief_value(brief, key)
        if key in country_slots:
            value = _country(value)
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


def _clean_query_string(query: str) -> str:
    """Normalize a planned query without inventing missing terms."""
    tokens = _norm(query).split(" ")
    deduped: list[str] = []
    for token in tokens:
        if deduped and token == deduped[-1]:
            continue
        deduped.append(token)
    return " ".join(deduped)


def _manual_authority_discovery_steps(brief: dict[str, Any]) -> list[dict[str, Any]]:
    """Open-world authority discovery plan for non-prelisted jurisdictions.

    This intentionally emits search/open tasks only.  It does not assume a
    regulator name, official domain, tariff rate, certificate, route, or legal
    conclusion for the target country.  The collector must later open sources
    and create AuthorityVerificationRecords before any determinate MatrixRow.
    """
    target = _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region"))
    if not target or target == "United States":
        return []

    product = _brief_product_query_term(brief) or "<product:待确认>"
    candidate_hs = _candidate_hs_hts(brief) or "<candidate_hs:待确认>"
    tags = set(_brief_product_tags(brief))
    requested = set(_str_list(_brief_value(brief, "analysis_modules_requested", "modules_requested")))
    steps: list[dict[str, Any]] = []

    def add(step_id: str, group: str, purpose: str, queries: list[str], domains: list[str], sheet: str, priority: list[str] | None = None) -> None:
        steps.append({
            "query_plan_id": f"qp_manual_authority_{step_id}",
            "pack_id": None,
            "template_id": f"manual_open_world_authority_{step_id}",
            "query_group_id": group,
            "purpose": purpose,
            "inputs_used": {
                "target_country_or_region": target,
                "product_name": product,
                "candidate_hs_hts": candidate_hs,
                "open_world_authority_discovery": True,
            },
            "query_strings": queries,
            "source_entry_ids": [],
            "required_source_priority": priority or ["primary_official", "official_portal", "official_gazette_or_legal_database"],
            "authority_discovery_model": {
                "open_world": True,
                "not_country_hardcoded": True,
                "must_verify_identity": True,
                "must_match_fact_domain": True,
                "must_match_jurisdiction": True,
                "must_record_authority_profile_before_claim": True,
                "fact_domains_to_verify": domains,
                "fallback_when_unverified": "candidate_needs_check_or_unable_to_verify",
            },
            "must_open_source": True,
            "reject_if_only_snippet": True,
            "not_evidence": True,
            "allowed_output": ALLOWED_OUTPUT,
            "expected_observation_fields": [
                "source_name",
                "url",
                "visible_institution_identity",
                "jurisdiction",
                "fact_domain_scope",
                "source_date_or_effective_date",
                "limitations",
            ],
            "expected_matrix_sheet": sheet,
            "fallback_status": "authority_discovery_plan_only",
            "handoff_target_skill": "analyzing-product-outbound-market",
            "blocked_outputs": BOUNDARY_BLOCKED_FACTS + [
                "official_requirement_claim_without_authority_verification",
                "domain_suffix_as_authority",
                "keyword_only_authority",
            ],
            "boundary_note": NOT_EVIDENCE_NOTE + " 开放世界国家/地区必须先核实机构身份、事实域、管辖范围和时效，再生成 AuthorityVerificationRecord。",
        })

    if requested & {"destination_compliance", "origin_proof_requirement"} or not requested:
        add(
            "destination_market_access",
            "authority_discovery_destination_compliance",
            f"为 {target} 发现产品准入、标签、包装、认证或许可主管来源；只形成权威来源候选，不形成要求结论。",
            [
                f"{target} official product safety market access {product}",
                f"{target} official labeling packaging requirements {product} {candidate_hs}",
                f"{target} official conformity certification import requirements {product}",
            ],
            ["certification_requirement", "destination_requirement"],
            "产品准入与合规要求",
        )
        add(
            "origin_proof",
            "authority_discovery_origin_proof",
            f"为 {target} 发现 COO / proof of origin / 原产地规则主管来源；只形成来源核实路径。",
            [
                f"{target} official certificate of origin proof of origin import rules {candidate_hs}",
                f"{target} customs rules of origin import proof {product}",
            ],
            ["origin_proof_requirement"],
            "产品准入与合规要求",
        )
    if requested & {"import_tax"} or not requested:
        add(
            "customs_tariff",
            "authority_discovery_import_tax",
            f"为 {target} 发现官方海关税则、关税、贸易救济查询入口；不输出税率。",
            [
                f"{target} official customs tariff lookup {candidate_hs}",
                f"{target} official import duty tariff schedule {product} {candidate_hs}",
                f"{target} official trade remedy additional duty {candidate_hs}",
            ],
            ["import_tax", "trade_remedy"],
            "进口税费",
        )
    if requested & {"logistics"} or not requested:
        add(
            "prefiling_logistics",
            "authority_discovery_logistics_prefiling",
            f"为 {target} 发现进口预申报、舱单、危险品/运输监管来源；不承诺路线或时效。",
            [
                f"{target} official customs advance manifest pre filing import cargo",
                f"{target} official dangerous goods transport requirements {product}",
            ],
            ["logistics_prefiling", "dangerous_goods_transport"],
            "运输方式、路线、港口与申报节点",
            ["primary_official", "port_or_transport_authority", "carrier_or_forwarder_reference_only"],
        )
    if tags & {"food", "fresh_produce", "plant_material", "tea", "flower"}:
        add(
            "food_agri_quarantine",
            "authority_discovery_inspection_quarantine",
            f"产品触发食品/农产品/植物材料路径；为 {target} 发现检验检疫或食品安全主管来源。",
            [
                f"{target} official food safety import requirements {product}",
                f"{target} official phytosanitary quarantine import requirements {product}",
                f"{target} official agriculture quarantine import permit {candidate_hs}",
            ],
            ["inspection_quarantine", "certification_requirement"],
            "产品准入与合规要求",
        )
    if tags & {"lithium_battery", "dangerous_goods", "battery_standalone", "chemical", "liquid"}:
        add(
            "dangerous_goods",
            "authority_discovery_dangerous_goods",
            f"产品触发危险品/化学品/锂电路径；为 {target} 发现运输和市场准入主管来源。",
            [
                f"{target} official lithium battery dangerous goods transport requirements {product}",
                f"{target} official hazardous materials import transport documentation {candidate_hs}",
            ],
            ["dangerous_goods_transport", "certification_requirement"],
            "产品准入与合规要求",
        )
    return steps


def _manual_gap_steps(brief: dict[str, Any], selected_pack_ids: list[str], templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    target = _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region"))
    export_country = _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country"))
    steps.extend(_manual_authority_discovery_steps(brief))
    if target and target != "United States":
        steps.append({
            "query_plan_id": "qp_manual_destination_pack_gap",
            "pack_id": None,
            "template_id": "manual_destination_source_pack_gap",
            "query_group_id": "destination_pack_gap",
            "purpose": f"目标国家/地区 {target} 暂无内置目的国 Source Pack，先生成人工计划入口清单。",
            "inputs_used": {"target_country_or_region": target, "product_name": _brief_product_identity(brief)},
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
    origin_country = _brief_origin_country(brief)
    departure_country = _country(_brief_value(brief, "departure_country_or_region", "departure_country"))
    if logistics_requested and not _transpacific_pack_applies(target, export_country, departure_country, origin_country):
        steps.append({
            "query_plan_id": "qp_manual_logistics_lane_pack_gap",
            "pack_id": None,
            "template_id": "manual_logistics_lane_pack_gap",
            "query_group_id": "logistics_pack_gap",
            "purpose": "当前起运国/目的国组合暂无可直接套用的物流 Source Pack，先生成人工物流来源计划。",
            "inputs_used": {"target_country_or_region": target, "export_declaration_country": export_country, "departure_country_or_region": departure_country, "origin_country_or_region": origin_country, "product_name": _brief_product_identity(brief)},
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
            "inputs_used": {"export_declaration_country": export_country, "target_country_or_region": target, "product_name": _brief_product_identity(brief)},
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
            query_strings = [_clean_query_string(_fill_blueprint(item, inputs)) for item in _str_list(template.get("query_blueprints"))]
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
    if not _brief_product_identity(brief):
        missing_required.append("product_name")
    elif not _norm(_brief_value(brief, "product_name", "display_name", "product")) and _candidate_hs_hts(brief):
        warnings.append({"code": "market_source_plan_product_identity_from_hs_hts", "message": "本轮以用户给出的候选 HS/HTS 作为产品身份线索启动；仍不能替代最终归类或 SKU 资料。"})
    elif _brief_has_only_source_material_identity(brief):
        warnings.append({"code": "market_source_plan_product_identity_from_source_material", "message": "产品身份仅来自 URL/文件/图片等用户材料线索；需先打开来源并提取产品名、品类或型号后，再形成有效检索词。当前含占位符的查询只作来源打开计划，不是向用户索取资料清单。"})
    if not _brief_value(brief, "export_declaration_country", "default_export_declaration_country"):
        warnings.append({"code": "market_source_plan_export_country_visible_default_needed", "message": "出口申报国未设置；未来 UI 应显示默认出口国并允许用户改，不从原产地自动推断。"})
    origin_country = _brief_origin_country(brief)
    manufacturing_country_clue = _brief_manufacturing_country_clue(brief)
    if not origin_country:
        warnings.append({"code": "market_source_plan_origin_country_unknown", "message": "原产国/制造来源未知；税费、COO、贸易救济和标签查询只能保留原产地缺口。"})
        if manufacturing_country_clue:
            warnings.append({"code": "market_source_plan_manufacturing_clue_not_origin_proof", "message": f"只看到 Made in/生产制造来源线索 {manufacturing_country_clue}；未作为海关原产国、出口申报国或 COO 证明使用。"})
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
            "product_name": _brief_product_identity(brief),
            "target_country_or_region": _country(_brief_value(brief, "target_country_or_region", "destination_country_or_region")),
            "export_declaration_country": _country(_brief_value(brief, "export_declaration_country", "default_export_declaration_country")),
            "origin_country_or_region": origin_country,
            "manufacturing_country_clue": manufacturing_country_clue,
            "departure_country_or_region": _country(_brief_value(brief, "departure_country_or_region", "departure_country")),
            "departure_node": _brief_value(brief, "departure_node"),
            "destination_node": _brief_value(brief, "destination_node"),
            "candidate_hs_hts": _candidate_hs_hts(brief),
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



def build_empty_collection_run(plan: dict[str, Any]) -> dict[str, Any]:
    """Create an empty, auditable collection-run shell from a Query Plan.

    This is Slice J glue: it does not search or open sources.  It only records
    which query-plan steps are ready to be executed and which guardrails must
    survive into SearchLog / Source / Observation collection.
    """
    return {
        "collection_run_id": "collection_run_manual_source_collection",
        "route": "product_outbound_market_analysis_source_collection",
        "source_plan_route": plan.get("route"),
        "source_plan_generated_at": plan.get("generated_at"),
        "execution_level": "collection_record_shell_only",
        "does_not_search_web": True,
        "does_not_open_sources": True,
        "not_evidence": True,
        "allowed_output": "collection_run_shell_only",
        "search_logs": [],
        "sources": [],
        "observations": [],
        "pending_query_plan_steps": [
            {
                "query_plan_id": step.get("query_plan_id"),
                "query_group_id": step.get("query_group_id"),
                "pack_id": step.get("pack_id"),
                "template_id": step.get("template_id"),
                "query_strings": step.get("query_strings", []),
                "must_open_source": True,
                "reject_if_only_snippet": True,
                "search_log_allowed_output": "search_log_or_source_locator_only",
                "observation_allowed_only_after_open_source": True,
                "not_evidence": True,
            }
            for step in _as_list(plan.get("query_plan"))
            if isinstance(step, dict)
        ],
        "guardrails": [
            "Query Plan 不能直接生成 EvidenceCard 或 MatrixRow",
            "SearchLog 只能记录查询和候选来源定位，不能写事实",
            "未打开来源不能生成 Observation",
            "Observation 必须引用已打开 Source，仍需再进入 EvidenceCard 互证",
        ],
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Brief JSON or ProductMarketAnalysisGraph JSON")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Source Pack registry JSON")
    parser.add_argument("--format", choices=["json"], default="json")
    parser.add_argument("--check-registry", action="store_true", help="Only validate the Source Pack registry")
    parser.add_argument("--emit-collection-run-shell", action="store_true", help="Also emit a SearchLog/Source/Observation collection-run shell without searching or opening sources")
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
    if args.emit_collection_run_shell:
        result = dict(result)
        result["collection_run_shell"] = build_empty_collection_run(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
