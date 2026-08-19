#!/usr/bin/env python3
"""Regression coverage for public social, map, and trade enrichment."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_superleads_markdown import build_bulk_markdown
from export_workbook import build_initial_sheets
from check_superleads_formal_markdown_delivery import _candidate_pool_rows, check_generated_markdown
from _superleads_common import source_evidence_scope
from validate_research_graph import validate_graph


FIXTURE = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
REFERENCE_FIXTURE = ROOT / "shared" / "references" / "default-discovery-reference.example.json"
STANDARD_FIXTURE = ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json"


def _signal(status: str, collection_status: str, *, items: list[dict[str, object]] | None = None, notes: list[str] | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "status": status,
        "collection_status": collection_status,
    }
    if items is not None:
        result["items"] = items
    if notes is not None:
        result["notes"] = notes
    return result


def enriched_graph() -> dict[str, object]:
    graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
    graph["runs"][0]["capabilities"] = {
        "search.web": "available",
        "source.open": "available",
    }
    graph["plans"][0]["source_categories"] = [
        "website", "directory", "document", "social", "map", "trade_aggregator", "search_result",
    ]
    graph["plans"][0]["contact_collection_targets"] = [
        "email", "phone", "contact_form", "social_company", "social_person",
        "person_name", "job_title", "address", "map_phone", "public_trade_summary",
    ]
    graph["plans"][0]["candidate_enrichment_policy"] = {
        "apply_to": "all_output_scope_candidates",
        "max_queries_per_category_per_candidate": 2,
        "max_opens_per_category_per_candidate": 1,
        "same_run_url_dedupe": "canonical_or_final_url",
        "over_budget_status": "not_searched",
    }

    for candidate in graph["candidates"]:
        summary = candidate["signal_summary"]
        summary["social_company"] = _signal("not_searched", "not_searched", notes=["本轮未检索公司公开社媒页面"])
        summary["social_person"] = _signal("not_searched", "not_searched", notes=["本轮未检索公开职业联系人"])
        summary["map_listing"] = _signal("not_searched", "not_searched", notes=["本轮未检索公开地图页面"])
        summary["trade_record"]["collection_status"] = "not_searched"

    alpha = graph["candidates"][0]
    alpha["signal_summary"]["social_company"] = _signal("observed", "public_page_opened", items=[{
        "summary": "LinkedIn 公司页显示 Alpha Distributor。",
        "source_label": "Alpha Distributor LinkedIn 公司页",
        "source_url": "https://linkedin.example/company/alpha-distributor",
        "observed_at": "2026-08-16T00:00:00Z",
        "source_id": "src_alpha_social_001",
        "observation_id": "obs_alpha_social_001",
        "platform": "LinkedIn",
        "page_type": "company_page",
        "display_name": "Alpha Distributor",
        "association_basis": "Alpha Distributor",
        "subject_match_status": "name_domain_match",
        "cannot_conclude": "公司页不能证明采购意愿或采购权限。",
    }])
    alpha["signal_summary"]["social_person"] = _signal("observed", "public_page_opened", items=[{
        "summary": "公开职业页面显示 Jordan Lee 的 Sales Manager 职位。",
        "source_label": "Jordan Lee 公开职业页面",
        "source_url": "https://linkedin.example/in/jordan-lee",
        "observed_at": "2026-08-16T00:00:00Z",
        "source_id": "src_alpha_social_person_001",
        "observation_id": "obs_alpha_social_person_001",
        "platform": "LinkedIn",
        "page_type": "professional_person_page",
        "display_name": "Jordan Lee",
        "job_title": "Sales Manager",
        "association_basis": "Alpha Distributor",
        "subject_match_status": "name_domain_match",
        "cannot_conclude": "公开职位只是角色线索，不等于采购负责人或采购权限。",
    }])
    alpha["signal_summary"]["map_listing"] = _signal("observed", "public_page_opened", items=[{
        "summary": "地图商户页显示 Alpha Distributor 的公开地址和电话。",
        "source_label": "Alpha Distributor Google Maps 商户页",
        "source_url": "https://maps.example/place/alpha-distributor",
        "observed_at": "2026-08-16T00:00:00Z",
        "source_id": "src_alpha_map_001",
        "observation_id": "obs_alpha_map_001",
        "platform": "Google Maps",
        "page_type": "map_listing",
        "display_name": "Alpha Distributor",
        "address": "10 Example Road, Region Q",
        "public_phone": "+1 555 0100",
        "business_scene": "Distributor warehouse",
        "association_basis": "Alpha Distributor",
        "subject_match_status": "name_exact_address_match",
        "cannot_conclude": "地图地址或电话不能证明法律主体或采购部门归属。",
    }])
    alpha["signal_summary"]["trade_record"] = _signal("not_observed", "search_summary_visible", items=[{
        "summary": "搜索摘要可见 importer 和 sample product 字段，详情未打开。",
        "source_label": "第三方贸易数据聚合站搜索摘要",
        "source_url": "https://trade.example/company/alpha-distributor",
        "observed_at": "2026-08-16T00:00:00Z",
        "platform": "第三方贸易数据聚合站",
        "page_type": "trade_aggregator_summary",
        "subject_match_status": "name_exact_address_match",
        "cannot_conclude": "不能推出完整采购量、采购金额、采购周期、从中国采购事实或未来订单。",
    }], notes=["搜索摘要可见，详情未打开，不能当成官方海关记录。"])
    alpha["public_trade_summaries"] = [{
        "summary_id": "trade_alpha_001",
        "collection_status": "search_summary_visible",
        "search_log_id": "search_trade_alpha_001",
        "subject_match_status": "name_exact_address_match",
        "association_basis": "Alpha Distributor",
        "aggregator_source_name": "第三方贸易数据聚合站",
        "aggregator_source_url": "https://trade.example/company/alpha-distributor",
        "direction": "import",
        "counterparty_name": "公开摘要可见，待核实",
        "record_date": "2025-11",
        "product_or_hs": "sample product",
        "origin_or_destination": "Region Q",
        "observed_at": "2026-08-16T00:00:00Z",
        "cannot_conclude": "不能推出完整采购量、采购金额、采购周期、采购意愿或从中国采购事实。",
        "next_step_for_user": "详情页受限时请用自己的贸易数据渠道按上述字段核实。",
    }]

    beta = graph["candidates"][1]
    beta["signal_summary"]["social_company"] = _signal("source_restricted", "details_restricted", notes=["来源受限：LinkedIn 页面需要登录"])
    beta["signal_summary"]["map_listing"] = _signal("not_observed", "searched_not_found", notes=["已检索 Beta Industrial Supplies 公开地图页面，未见可可靠关联商户"])
    beta["signal_summary"]["trade_record"]["collection_status"] = "details_restricted"
    graph["candidates"][3]["signal_summary"]["trade_record"]["collection_status"] = "identity_pending"
    graph["candidates"][0]["search_log_ids"].append("search_trade_alpha_001")

    graph["search_logs"].append({
        "search_log_id": "search_trade_alpha_001",
        "run_id": "run_discovery_001",
        "brief_id": "brief_discovery_001",
        "plan_id": "plan_discovery_001",
        "query_group_id": "region_q_distributor",
        "queried_at": "2026-08-16T00:00:00Z",
        "capability": "search.web",
        "concrete_tool": "fixture_search",
        "query_text": "Alpha Distributor import records",
        "result_use": "candidate_seed_only",
        "result_refs": [{
            "candidate_id": "cand_alpha_001",
            "result_url": "https://trade.example/company/alpha-distributor",
            "result_locator": "rank=1",
            "visible_excerpt": "Alpha Distributor; import; 公开摘要可见，待核实; 2025-11; sample product; Region Q",
        }],
    })

    graph["sources"].extend([
        {
            "source_id": "src_alpha_social_001",
            "canonical_url": "https://linkedin.example/company/alpha-distributor",
            "final_url": "https://linkedin.example/company/alpha-distributor",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "social",
            "access_boundary": "public_no_login",
            "owner_hint": "Alpha Distributor",
        },
        {
            "source_id": "src_alpha_map_001",
            "canonical_url": "https://maps.example/place/alpha-distributor",
            "final_url": "https://maps.example/place/alpha-distributor",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "map",
            "access_boundary": "public_no_login",
            "owner_hint": "Alpha Distributor",
        },
        {
            "source_id": "src_alpha_social_person_001",
            "canonical_url": "https://linkedin.example/in/jordan-lee",
            "final_url": "https://linkedin.example/in/jordan-lee",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "social",
            "access_boundary": "public_no_login",
            "owner_hint": "Jordan Lee",
        },
    ])
    graph["observations"].extend([
        {
            "observation_id": "obs_alpha_social_001",
            "run_id": "run_discovery_001",
            "source_id": "src_alpha_social_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "ok",
            "raw_excerpt": "Alpha Distributor. Jordan Lee, Sales Manager.",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "alpha_social_hash",
            "title": "Alpha Distributor LinkedIn page",
            "page_or_dom_locator": "body",
        },
        {
            "observation_id": "obs_alpha_map_001",
            "run_id": "run_discovery_001",
            "source_id": "src_alpha_map_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "ok",
            "raw_excerpt": "Alpha Distributor. 10 Example Road, Region Q. +1 555 0100. Distributor warehouse.",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "alpha_map_hash",
            "title": "Alpha Distributor Google Maps",
            "page_or_dom_locator": "body",
        },
        {
            "observation_id": "obs_alpha_social_person_001",
            "run_id": "run_discovery_001",
            "source_id": "src_alpha_social_person_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "ok",
            "raw_excerpt": "Jordan Lee, Sales Manager at Alpha Distributor.",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "alpha_social_person_hash",
            "title": "Jordan Lee LinkedIn page",
            "page_or_dom_locator": "body",
        },
    ])
    return graph


def add_opened_trade_summary(graph: dict[str, object]) -> dict[str, object]:
    """Turn Alpha's visible trade snippet into one separately opened source."""
    alpha = graph["candidates"][0]
    record = alpha["public_trade_summaries"][0]
    record.update({
        "collection_status": "public_page_opened",
        "source_id": "src_alpha_trade_001",
        "observation_id": "obs_alpha_trade_001",
        "association_basis": "Alpha Distributor",
    })
    alpha["signal_summary"]["trade_record"] = _signal(
        "observed",
        "public_page_opened",
        notes=["公开贸易聚合页已打开；不是官方海关记录。"],
    )
    graph["sources"].append({
        "source_id": "src_alpha_trade_001",
        "canonical_url": "https://trade.example/company/alpha-distributor",
        "final_url": "https://trade.example/company/alpha-distributor",
        "publisher_relation": "third_party",
        "provenance": "discovered_public",
        "medium": "trade_aggregator",
        "access_boundary": "public_no_login",
        "owner_hint": "Alpha Distributor",
    })
    graph["observations"].append({
        "observation_id": "obs_alpha_trade_001",
        "run_id": "run_discovery_001",
        "source_id": "src_alpha_trade_001",
        "candidate_id": "cand_alpha_001",
        "entity_id": "ent_alpha_001",
        "capability": "source.open",
        "concrete_tool": "fixture",
        "observed_at": "2026-08-16T00:00:00Z",
        "access_status": "ok",
        "raw_excerpt": "Alpha Distributor import summary. 公开摘要可见，待核实. 2025-11. Sample product. Region Q.",
        "extraction_method": "fixture",
        "language": "en",
        "translation_status": "original",
        "content_hash": "alpha_trade_hash",
        "title": "Alpha Distributor trade aggregator summary",
        "page_or_dom_locator": "body",
    })
    return record


class PublicEnrichmentTest(unittest.TestCase):
    def test_formal_markdown_smoke_accepts_standard_workbook_projection(self) -> None:
        issues, payload, markdown = check_generated_markdown(STANDARD_FIXTURE)

        self.assertTrue(payload["ok"])
        self.assertEqual([], issues)
        self.assertIn("## 客户信息总表", markdown)
        self.assertIn("Example Buyer", markdown)
        self.assertNotIn("发现候选池样表（候选池不是正式开发名单）", markdown)

    def test_default_discovery_projects_social_map_and_trade_sections(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["brand_name"] = "Alpha Brand"
        issues = validate_graph(graph)
        self.assertEqual([], issues)

        sheets = build_initial_sheets(graph, {"issues": []})
        self.assertIn("社媒与公开职业线索", sheets)
        self.assertIn("地图与经营地址", sheets)
        self.assertIn("第三方贸易摘要", sheets)
        self.assertEqual("Alpha Brand", sheets["发现候选池"][0]["品牌名称"])
        social_row = sheets["社媒与公开职业线索"][0]
        map_row = sheets["地图与经营地址"][0]
        self.assertEqual("公开页面已打开", social_row["来源状态"])
        self.assertEqual("2026-08-16T00:00:00Z", social_row["观察时间"])
        self.assertIn("https://linkedin.example/", social_row["来源 / 链接"])
        self.assertEqual("公开页面已打开", map_row["来源状态"])
        self.assertIn("https://maps.example/", map_row["来源 / 链接"])
        trade_row = sheets["第三方贸易摘要"][0]
        self.assertEqual("名称与公开地址一致", trade_row["主体匹配状态"])

        markdown, export_issues = build_bulk_markdown(graph)
        self.assertEqual([], export_issues)
        self.assertIsNotNone(markdown)
        for expected in (
            "社媒与公开职业线索",
            "地图与经营地址",
            "第三方贸易摘要",
            "第三方贸易数据聚合站公开摘要，非官方海关记录",
            "品牌名称",
            "Alpha Brand",
            "公开职位只是角色线索，不等于采购负责人或采购权限。",
            "来源受限：该公开页面需要登录、验证码、付费访问、人工验证或当前 AI 无法正常读取。",
            "本轮未检索",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, markdown)

    def test_opened_social_or_map_item_requires_matching_opened_observation(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["signal_summary"]["social_company"]["items"][0]["observation_id"] = "obs_missing"
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_opened_observation_missing", codes)

    def test_opened_enrichment_item_url_must_match_bound_source(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["signal_summary"]["social_company"]["items"][0]["source_url"] = "https://unrelated.example/company"
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_source_url_mismatch", codes)

    def test_default_bulk_enrichment_cannot_be_skipped(self) -> None:
        graph = enriched_graph()
        del graph["plans"][0]["candidate_enrichment_policy"]
        for candidate in graph["candidates"]:
            for signal_key in ("social_company", "social_person", "map_listing"):
                del candidate["signal_summary"][signal_key]
            candidate["signal_summary"]["trade_record"].pop("collection_status", None)

        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_policy_missing", codes)
        self.assertIn("default_discovery_enrichment_signal_missing", codes)
        self.assertIn("default_discovery_enrichment_trade_collection_status_missing", codes)

    def test_search_summary_social_clue_cannot_export_unopened_person_or_contact(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["signal_summary"]["social_person"] = _signal(
            "not_observed",
            "search_summary_visible",
            items=[{
                "summary": "搜索摘要中可见社媒链接，页面未打开验证。",
                "source_label": "搜索结果链接",
                "source_url": "https://linkedin.example/in/jordan-lee",
                "display_name": "Jordan Lee",
                "job_title": "Purchasing Manager",
                "public_contact": "buyer@alpha.example",
            }],
        )

        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_search_summary_binding_missing", codes)
        self.assertIn("default_discovery_enrichment_search_summary_field_forbidden", codes)

        sheets = build_initial_sheets(graph, {"issues": []})
        row = next(item for item in sheets["社媒与公开职业线索"] if item["来源状态"] == "搜索摘要可见")
        self.assertEqual("未提供", row["页面名称 / 人员"])
        self.assertEqual("未提供", row["公开职位或部门"])
        self.assertEqual("未提供", row["公开联系入口"])

    def test_public_company_social_pages_use_the_same_public_open_contract(self) -> None:
        for platform, url in (
            ("LinkedIn", "https://linkedin.example/company/alpha-distributor"),
            ("Facebook", "https://facebook.example/alpha-distributor"),
            ("Instagram", "https://instagram.example/alpha-distributor"),
            ("X", "https://x.example/alpha-distributor"),
            ("YouTube", "https://youtube.example/@alpha-distributor"),
        ):
            with self.subTest(platform=platform):
                graph = enriched_graph()
                item = graph["candidates"][0]["signal_summary"]["social_company"]["items"][0]
                source = next(source for source in graph["sources"] if source["source_id"] == item["source_id"])
                source["canonical_url"] = url
                source["final_url"] = url
                item["platform"] = platform
                item["source_url"] = url
                self.assertEqual([], validate_graph(graph))

    def test_trade_search_summary_fields_must_be_visible_in_its_same_run_search_log(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["public_trade_summaries"][0]["product_or_hs"] = "unseen HS 9999"
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_trade_summary_value_not_in_search_excerpt", codes)

    def test_opened_social_map_items_require_public_tool_excerpt_and_confirmed_association(self) -> None:
        graph = enriched_graph()
        item = graph["candidates"][0]["signal_summary"]["social_company"]["items"][0]
        item.pop("source_url")
        item["subject_match_status"] = "name_only"
        source = next(source for source in graph["sources"] if source["source_id"] == item["source_id"])
        source["provenance"] = "tool_enriched"
        source["access_boundary"] = "paid_api"
        observation = next(observation for observation in graph["observations"] if observation["observation_id"] == item["observation_id"])
        observation["capability"] = "social.visible.read"
        observation["raw_excerpt"] = "Unrelated business page."

        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_source_url_missing", codes)
        self.assertIn("default_discovery_enrichment_source_not_public", codes)
        self.assertIn("default_discovery_enrichment_capability_not_allowed", codes)
        self.assertIn("default_discovery_enrichment_value_not_in_excerpt", codes)
        self.assertIn("default_discovery_enrichment_identity_pending_required", codes)

    def test_trade_rows_are_non_official_and_restricted_records_keep_next_step(self) -> None:
        graph = enriched_graph()
        alpha = graph["candidates"][0]
        alpha["signal_summary"]["trade_record"] = _signal(
            "source_restricted",
            "details_restricted",
            notes=["来源受限：第三方贸易详情页需要登录或付费"],
        )
        record = alpha["public_trade_summaries"][0]
        record["collection_status"] = "details_restricted"
        record["next_step_for_user"] = "请按记录日期和产品词手动核实。"

        sheets = build_initial_sheets(graph, {"issues": []})
        trade_row = sheets["第三方贸易摘要"][0]
        self.assertIn("第三方贸易数据聚合站公开摘要，非官方海关记录", trade_row["不能推出的内容"])
        pending = next(item for item in sheets["待核查事项"] if item.get("类型") == "第三方贸易摘要")
        self.assertIn("请按记录日期和产品词手动核实。", pending["建议动作"])

    def test_trade_aggregator_sources_cannot_support_formal_claims_or_contacts(self) -> None:
        source = {
            "source_id": "src_trade_scope_001",
            "canonical_url": "https://trade.example/company/alpha",
            "final_url": "https://trade.example/company/alpha",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "trade_aggregator",
            "access_boundary": "public_no_login",
        }
        observation = {"raw_excerpt": "Alpha trade summary."}
        for purpose in ("formal_claim", "assessment_basis", "contact_ready", "contact_with_source_note"):
            with self.subTest(purpose=purpose):
                allowed, reason = source_evidence_scope(source, observation, purpose)
                self.assertFalse(allowed)
                self.assertEqual(f"trade_aggregator_not_allowed_for_{purpose}", reason)

    def test_opened_trade_summary_requires_current_run_and_matching_source_url(self) -> None:
        graph = enriched_graph()
        record = add_opened_trade_summary(graph)
        graph["observations"][-1]["run_id"] = "run_other_001"
        record["aggregator_source_url"] = "https://unrelated.example/trade"
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_trade_summary_observation_run_mismatch", codes)
        self.assertIn("default_discovery_trade_summary_source_url_mismatch", codes)

    def test_opened_social_association_basis_must_be_visible_and_identify_candidate(self) -> None:
        graph = enriched_graph()
        item = graph["candidates"][0]["signal_summary"]["social_person"]["items"][0]
        item["association_basis"] = "Unrelated Distributor"

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_enrichment_association_basis_not_in_excerpt", codes)
        self.assertIn("default_discovery_enrichment_association_not_candidate_identity", codes)

    def test_identity_pending_trade_parent_cannot_hide_opened_trade_record(self) -> None:
        graph = enriched_graph()
        add_opened_trade_summary(graph)
        graph["candidates"][0]["signal_summary"]["trade_record"] = _signal(
            "identity_pending",
            "identity_pending",
            notes=["主体待确认，不能将同名贸易记录绑定到当前候选。"],
        )

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_trade_signal_state_mismatch", codes)

    def test_opened_trade_summary_requires_a_third_party_aggregator_source(self) -> None:
        graph = enriched_graph()
        record = add_opened_trade_summary(graph)
        source = next(source for source in graph["sources"] if source["source_id"] == record["source_id"])
        source["publisher_relation"] = "first_party"

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_trade_summary_source_not_third_party", codes)

    def test_opened_trade_summary_association_must_be_visible_and_identify_candidate(self) -> None:
        graph = enriched_graph()
        record = add_opened_trade_summary(graph)
        record["association_basis"] = "Unrelated Distributor"

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_trade_summary_association_basis_not_in_excerpt", codes)
        self.assertIn("default_discovery_trade_summary_association_not_candidate_identity", codes)

    def test_trade_search_summary_association_must_be_visible_and_identify_candidate(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["public_trade_summaries"][0]["association_basis"] = "Unrelated Distributor"

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_trade_summary_association_basis_not_in_excerpt", codes)
        self.assertIn("default_discovery_trade_summary_association_not_candidate_identity", codes)

    def test_restricted_trade_parent_state_remains_visible_with_search_summary_child(self) -> None:
        graph = enriched_graph()
        graph["candidates"][0]["signal_summary"]["trade_record"] = _signal(
            "source_restricted",
            "details_restricted",
            notes=["来源受限：第三方贸易详情页需要登录或付费"],
        )
        self.assertEqual([], validate_graph(graph))

        sheets = build_initial_sheets(graph, {"issues": []})
        trade_row = next(row for row in sheets["第三方贸易摘要"] if row["公司名称"] == "Alpha Distributor")
        pending = next(row for row in sheets["待核查事项"] if row["类型"] == "第三方贸易摘要" and "来源受限" in row["原因"])

        self.assertIn("来源受限", trade_row["状态"])
        self.assertIn("第三方贸易数据详情页需要登录、付费或无法正常打开", pending["建议动作"])

    def test_trade_aggregator_contact_lead_is_not_exported_as_a_public_contact(self) -> None:
        graph = enriched_graph()
        graph["sources"].append({
            "source_id": "src_trade_contact_001",
            "canonical_url": "https://trade.example/company/alpha/contact",
            "final_url": "https://trade.example/company/alpha/contact",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "trade_aggregator",
            "access_boundary": "public_no_login",
        })
        graph["observations"].append({
            "observation_id": "obs_trade_contact_001",
            "run_id": "run_discovery_001",
            "source_id": "src_trade_contact_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "ok",
            "raw_excerpt": "buyer@trade.example",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "trade_contact_hash",
            "title": "Trade contact clue",
            "page_or_dom_locator": "body",
        })
        graph.setdefault("contact_points", []).append({
            "contact_id": "contact_trade_001",
            "contact_type": "email",
            "normalized_value": "buyer@trade.example",
            "source_literal": "buyer@trade.example",
            "source_observation_id": "obs_trade_contact_001",
        })
        graph.setdefault("unassigned_contact_leads", []).append({
            "unassigned_contact_lead_id": "lead_trade_001",
            "contact_id": "contact_trade_001",
            "reason": "第三方贸易页仅显示无归属联系线索。",
            "suggested_manual_check": "请用户手动核对公司公开联系页。",
        })

        codes = {issue["code"] for issue in validate_graph(graph)}
        sheets = build_initial_sheets(graph, {"issues": []})
        exported_values = {row["联系方式"] for row in sheets["联系方式汇总"]}

        self.assertIn("trade_aggregator_contact_point_forbidden", codes)
        self.assertIn("trade_aggregator_contact_lead_forbidden", codes)
        self.assertNotIn("buyer@trade.example", exported_values)

    def test_enrichment_open_dedup_uses_both_canonical_and_final_urls(self) -> None:
        graph = enriched_graph()
        graph["sources"].append({
            "source_id": "src_alpha_social_redirect_001",
            "canonical_url": "https://linkedin.example/company/alpha-distributor",
            "final_url": "https://linkedin.example/company/alpha-distributor/about",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "social",
            "access_boundary": "public_no_login",
            "owner_hint": "Alpha Distributor",
        })
        graph["observations"].append({
            "observation_id": "obs_alpha_social_redirect_001",
            "run_id": "run_discovery_001",
            "source_id": "src_alpha_social_redirect_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "ok",
            "raw_excerpt": "Alpha Distributor.",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "alpha_social_redirect_hash",
            "title": "Alpha Distributor redirect",
            "page_or_dom_locator": "body",
        })
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_open_url_reused", codes)

    def test_enrichment_open_dedup_stops_after_a_restricted_attempt(self) -> None:
        graph = enriched_graph()
        graph["sources"].append({
            "source_id": "src_alpha_social_login_retry_001",
            "canonical_url": "https://linkedin.example/company/alpha-distributor",
            "final_url": "https://linkedin.example/company/alpha-distributor",
            "publisher_relation": "third_party",
            "provenance": "discovered_public",
            "medium": "social",
            "access_boundary": "public_no_login",
            "owner_hint": "Alpha Distributor",
        })
        graph["observations"].append({
            "observation_id": "obs_alpha_social_login_retry_001",
            "run_id": "run_discovery_001",
            "source_id": "src_alpha_social_login_retry_001",
            "candidate_id": "cand_alpha_001",
            "entity_id": "ent_alpha_001",
            "capability": "source.open",
            "concrete_tool": "fixture",
            "observed_at": "2026-08-16T00:00:00Z",
            "access_status": "login_required",
            "raw_excerpt": "Access requires login.",
            "extraction_method": "fixture",
            "language": "en",
            "translation_status": "original",
            "content_hash": "alpha_social_login_retry_hash",
            "title": "Alpha Distributor sign in",
            "page_or_dom_locator": "body",
        })

        codes = {issue["code"] for issue in validate_graph(graph)}

        self.assertIn("default_discovery_enrichment_open_url_reused", codes)

    def test_user_provided_enrichment_without_confirmed_association_stays_pending(self) -> None:
        graph = enriched_graph()
        gamma = graph["candidates"][2]
        gamma["signal_summary"]["social_company"] = _signal(
            "observed",
            "user_provided_material",
            items=[{
                "summary": "用户提供截图显示公开公司页名称。",
                "source_label": "用户提供资料",
                "observed_at": "2026-08-16T00:00:00Z",
                "platform": "Facebook",
                "page_type": "company_page",
                "display_name": "Gamma Packaging",
                "association_basis": "截图中的公司名称尚未与候选主体核对",
                "cannot_conclude": "用户提供资料不等于当前 AI 独立检索结果。",
            }],
        )
        codes = {issue["code"] for issue in validate_graph(graph)}
        self.assertIn("default_discovery_enrichment_status_mismatch", codes)

    def test_same_name_map_or_trade_clue_remains_identity_pending(self) -> None:
        graph = enriched_graph()
        delta = graph["candidates"][3]
        delta["signal_summary"]["map_listing"] = _signal("identity_pending", "identity_pending", notes=["同名地图商户地址不一致，不能自动合并"])
        delta["public_trade_summaries"] = [{
            "summary_id": "trade_delta_001",
            "collection_status": "identity_pending",
            "subject_match_status": "name_only",
            "aggregator_source_name": "第三方贸易数据聚合站",
            "aggregator_source_url": "https://trade.example/company/delta",
            "observed_at": "2026-08-16T00:00:00Z",
            "cannot_conclude": "同名记录不能自动绑定到候选公司。",
            "next_step_for_user": "核对地址、域名和注册主体后再判断。",
        }]
        issues = validate_graph(graph)
        self.assertEqual([], issues)
        markdown, export_issues = build_bulk_markdown(graph)
        self.assertEqual([], export_issues)
        self.assertIn("疑似，主体待确认", markdown)

    def test_restricted_and_user_provided_enrichment_states_remain_explicit(self) -> None:
        graph = enriched_graph()
        beta = graph["candidates"][1]
        beta["signal_summary"]["social_company"] = _signal(
            "source_restricted",
            "details_restricted",
            notes=["来源受限：公开社媒页面出现验证码"],
        )
        beta["signal_summary"]["map_listing"] = _signal(
            "source_restricted",
            "details_restricted",
            notes=["来源受限：地图页面可访问，但动态内容无法读取"],
        )
        beta["signal_summary"]["trade_record"] = _signal(
            "source_restricted",
            "details_restricted",
            notes=["来源受限：第三方贸易详情页需要登录或付费"],
        )
        gamma = graph["candidates"][2]
        gamma["signal_summary"]["social_company"] = _signal(
            "identity_pending",
            "user_provided_material",
            items=[{
                "summary": "用户提供截图显示公开公司页名称。",
                "source_label": "用户提供资料",
                "observed_at": "2026-08-16T00:00:00Z",
                "platform": "Facebook",
                "page_type": "company_page",
                "display_name": "Gamma Packaging",
                "association_basis": "用户提供截图中的公司名称仍待与候选主体核对",
                "cannot_conclude": "用户提供资料不等于当前 AI 独立检索结果。",
            }],
        )

        issues = validate_graph(graph)
        self.assertEqual([], issues)
        markdown, export_issues = build_bulk_markdown(graph)
        self.assertEqual([], export_issues)
        for expected in (
            "来源受限：该公开页面需要登录、验证码、付费访问、人工验证或当前 AI 无法正常读取。",
            "来源受限：页面可以访问，但当前 AI 无法自动读取其中的动态内容。",
            "来源受限：第三方贸易数据详情页需要登录、付费或无法正常打开。",
            "用户提供资料",
            "用户提供资料不等于当前 AI 独立检索结果。",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, markdown)

    def test_formal_markdown_smoke_finds_excluded_candidate_after_enrichment_sections(self) -> None:
        issues, _, _ = check_generated_markdown(REFERENCE_FIXTURE)
        self.assertEqual([], issues)

    def test_formal_markdown_smoke_reads_candidate_statuses_only_from_candidate_pool_table(self) -> None:
        markdown = """## 发现候选池样表（候选池不是正式开发名单）

| 分区 | 候选客户 | 依据状态 |
| --- | --- | --- |
| 待确认 | Example Importer | 来源受限 |

## 社媒与公开职业线索

| 公司名称 | 来源状态 |
| --- | --- |
| Example Importer | 已有明确依据 |
"""
        rows = _candidate_pool_rows(markdown)
        self.assertEqual(["| 待确认 | Example Importer | 来源受限 |"], rows)


if __name__ == "__main__":
    unittest.main()
