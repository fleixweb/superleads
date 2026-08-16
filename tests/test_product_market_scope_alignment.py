#!/usr/bin/env python3
"""Keep intake module names aligned with market planning and delivery scope."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from plan_product_market_sources import DEFAULT_REGISTRY, _load_json, build_query_plan
from export_product_market_workbook import _market_scope_declaration, requested_market_modules, selected_sheet_order
from route_superleads_intake import classify


class ProductMarketScopeAlignmentTest(unittest.TestCase):
    def test_user_facing_market_access_scope_reaches_only_access_query_groups(self) -> None:
        intake = classify("分析中国出口保温杯到美国的准入要求")
        self.assertEqual(["market_access"], intake["analysis_modules_requested"])

        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "United States",
                "export_declaration_country": "China",
                "analysis_modules_requested": intake["analysis_modules_requested"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        query_groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("destination_compliance", query_groups)
        self.assertIn("origin_proof_requirement", query_groups)
        self.assertNotIn("import_tax", query_groups)
        self.assertNotIn("market_signal", query_groups)
        self.assertNotIn("logistics", query_groups)

    def test_user_facing_market_access_scope_selects_only_access_delivery_sheet(self) -> None:
        graph = {
            "runs": [{"brief_id": "brief-1"}],
            "briefs": [{
                "brief_id": "brief-1",
                "analysis_modules_requested": ["market_access"],
            }],
        }

        self.assertEqual({"destination_compliance"}, requested_market_modules(graph))
        sheets = selected_sheet_order(graph)
        self.assertIn("产品准入与合规要求", sheets)
        self.assertNotIn("进口税费", sheets)
        self.assertNotIn("运输方式、路线、港口与申报节点", sheets)

    def test_empty_scope_does_not_fall_back_to_a_complete_market_report(self) -> None:
        graph = {
            "runs": [{"brief_id": "brief-1"}],
            "briefs": [{"brief_id": "brief-1", "analysis_modules_requested": []}],
        }

        self.assertEqual(set(), requested_market_modules(graph))
        self.assertEqual(
            ["市场事实总览", "产品档案与触发项", "信息来源与待确认事项"],
            selected_sheet_order(graph),
        )
        declaration = "\n".join(_market_scope_declaration(graph))
        self.assertIn("本轮范围待确认", declaration)
        self.assertIn("本轮未执行：", declaration)

    def test_explicitly_empty_scope_keeps_source_planner_scope_pending(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "United States",
                "export_declaration_country": "China",
                "analysis_modules_requested": [],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        self.assertEqual([], plan["query_plan"])
        self.assertEqual([], plan["selected_pack_ids"])
        self.assertTrue(any(item["code"] == "market_source_plan_scope_pending" for item in plan["warnings"]))

    def test_tariff_only_scope_does_not_expand_to_origin_or_export_requirements(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "United States",
                "export_declaration_country": "China",
                "candidate_hs_hts": "9617.00",
                "analysis_modules_requested": ["import_tax"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        query_groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("import_tax", query_groups)
        self.assertNotIn("origin_proof_requirement", query_groups)
        self.assertNotIn("export_requirements", query_groups)
        self.assertNotIn("destination_compliance", query_groups)
        self.assertNotIn("seed_us_origin_proof_general", plan["selected_pack_ids"])
        self.assertNotIn("seed_cn_export_general", plan["selected_pack_ids"])

    def test_non_us_market_access_alias_gets_only_scoped_manual_queries(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "Vietnam",
                "export_declaration_country": "China",
                "analysis_modules_requested": ["market_access"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        query_groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("authority_discovery_destination_compliance", query_groups)
        self.assertIn("authority_discovery_origin_proof", query_groups)
        self.assertNotIn("authority_discovery_import_tax", query_groups)
        self.assertNotIn("authority_discovery_logistics_prefiling", query_groups)
        self.assertNotIn("destination_pack_gap", query_groups)

    def test_non_us_market_trends_alias_gets_only_scoped_manual_queries(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "Vietnam",
                "export_declaration_country": "China",
                "analysis_modules_requested": ["market_trends"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        query_groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("market_trends", query_groups)
        self.assertNotIn("authority_discovery_destination_compliance", query_groups)
        self.assertNotIn("authority_discovery_import_tax", query_groups)
        self.assertNotIn("destination_pack_gap", query_groups)

    def test_public_price_does_not_plan_market_trend_queries(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "Vietnam",
                "export_declaration_country": "China",
                "analysis_modules_requested": ["public_price"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("public_price", groups)
        self.assertNotIn("market_trends", groups)

    def test_market_trends_does_not_plan_public_price_queries(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "Vietnam",
                "export_declaration_country": "China",
                "analysis_modules_requested": ["market_trends"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("market_trends", groups)
        self.assertNotIn("public_price", groups)

    def test_non_us_external_factors_get_a_scoped_manual_query(self) -> None:
        plan = build_query_plan(
            {
                "product_name": "保温杯",
                "target_country_or_region": "Vietnam",
                "export_declaration_country": "China",
                "analysis_modules_requested": ["external_factors"],
            },
            _load_json(DEFAULT_REGISTRY),
        )

        groups = {step["query_group_id"] for step in plan["query_plan"]}
        self.assertIn("external_factors", groups)
        self.assertNotIn("market_signal", groups)


if __name__ == "__main__":
    unittest.main()
