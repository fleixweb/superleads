#!/usr/bin/env python3
"""Regression tests for composite Superleads parent tasks."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from superleads_composite_tasks import (
    composite_status_summary,
    plan_composite_task,
    parent_progress_summary,
    register_subtask_source_use,
    render_composite_delivery,
    source_use_can_support,
)
from superleads_user_guidance import has_exactly_one_final_footer


class SuperleadsCompositeTaskTest(unittest.TestCase):
    def test_company_and_market_request_creates_two_independent_subtasks(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")

        self.assertEqual("composite", parent["route"])
        self.assertEqual(
            ["customer_background_research", "product_outbound_market_analysis"],
            [item["route"] for item in parent["subtasks"]],
        )
        self.assertTrue(all(item["status"] == "ready" for item in parent["subtasks"]))
        self.assertEqual("parallel_if_host_supported", parent["scheduling"]["execution_style"])

    def test_missing_market_inputs_do_not_block_background_subtask(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析出口市场准入")
        background, market = parent["subtasks"]

        self.assertEqual("ready", background["status"])
        self.assertEqual("waiting_for_required_input", market["status"])
        self.assertEqual({"product_identity", "target_country_or_region"}, set(market["missing_fields"]))

    def test_batch_and_explicit_contact_request_are_separate_subtasks(self) -> None:
        parent = plan_composite_task("找德国工业传感器进口商，并核查公开联系人")

        self.assertEqual(
            ["bulk_customer_development", "contact_supplement"],
            [item["route"] for item in parent["subtasks"]],
        )
        self.assertEqual(["bulk_customer_development"], parent["subtasks"][1]["dependencies"])

    def test_background_and_explicit_contact_request_makes_contact_depend_on_background(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并核查公开联系人")

        self.assertEqual(
            ["customer_background_research", "contact_supplement"],
            [item["route"] for item in parent["subtasks"]],
        )
        self.assertEqual(["customer_background_research"], parent["subtasks"][1]["dependencies"])

    def test_explicit_same_request_contact_scope_is_independent(self) -> None:
        parent = plan_composite_task(
            "调查 ABC GmbH，并核查公开联系人",
            {"has_background": True, "has_contact": True, "contact_scope": "same_request"},
        )

        contact = next(item for item in parent["subtasks"] if item["route"] == "contact_supplement")
        self.assertEqual([], contact["dependencies"])
        self.assertEqual("independent", contact["execution_order"])

    def test_table_contact_request_depends_on_the_supplied_table_only(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并补全我上传的客户表公开联系人")

        contact = next(item for item in parent["subtasks"] if item["route"] == "contact_supplement")
        self.assertEqual(["existing_table_enrichment"], contact["dependencies"])
        self.assertNotIn("customer_background_research", contact["dependencies"])

    def test_table_field_enrichment_does_not_imply_a_contact_subtask(self) -> None:
        parent = plan_composite_task("请把上传的客户表补全官网和公开邮箱")

        self.assertEqual(
            ["existing_table_enrichment"],
            [item["route"] for item in parent["subtasks"]],
        )

    def test_export_excludes_unready_subtasks_without_an_explicit_export_scope(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析出口市场准入，导出结果")

        export = next(item for item in parent["subtasks"] if item["route"] == "export_delivery")
        self.assertEqual(["customer_background_research"], export["dependencies"])

    def test_waiting_for_required_input_subtask_is_not_parallelizable(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析出口市场准入")

        self.assertEqual(["customer_background_research"], parent["scheduling"]["parallelizable"])

    def test_market_subtask_preserves_requested_analysis_modules(self) -> None:
        contexts = (
            {"analysis_modules_requested": ["tariff", "certification"]},
            {"requested_market_modules": ["public_price"]},
        )

        for context in contexts:
            with self.subTest(context=context):
                parent = plan_composite_task(
                    "市场分析",
                    {"has_market": True, "has_product": True, "has_country": True, **context},
                )

                self.assertEqual(
                    next(iter(context.values())),
                    parent["subtasks"][0]["analysis_modules_requested"],
                )

    def test_source_use_is_scoped_and_cannot_cross_promote_fact_domains(self) -> None:
        company_use = register_subtask_source_use(
            "background-1",
            "https://abc.example/about",
            "company_business",
            purpose="company background",
        )
        regulation_use = register_subtask_source_use(
            "market-1",
            "https://regulator.example/rules",
            "market_access",
            purpose="market access",
        )

        self.assertFalse(source_use_can_support(company_use, "market_access", "market-1"))
        self.assertFalse(source_use_can_support(regulation_use, "company_business", "background-1"))
        contact_use = register_subtask_source_use(
            "background-1",
            "https://abc.example/contact",
            "company_contact",
            purpose="public contact",
        )
        self.assertFalse(source_use_can_support(company_use, "company_contact", "background-1"))
        self.assertTrue(source_use_can_support(company_use, "company_business", "background-1"))
        self.assertTrue(source_use_can_support(contact_use, "company_contact", "background-1"))
        self.assertFalse(source_use_can_support(company_use, "company_business", "other-subtask"))
        self.assertFalse(source_use_can_support(company_use, "company_business"))

    def test_source_use_requires_matching_requesting_subtask_identity(self) -> None:
        source_use = register_subtask_source_use(
            "background-1",
            "https://abc.example/about",
            "company_business",
            purpose="company background",
        )

        self.assertFalse(source_use_can_support({**source_use, "subtask_id": ""}, "company_business", "background-1"))

    def test_source_use_requires_nonempty_subtask_id_and_purpose(self) -> None:
        invalid_arguments = (
            {"subtask_id": "   ", "purpose": "company background"},
            {"subtask_id": "background-1", "purpose": "\t"},
        )

        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    register_subtask_source_use(
                        arguments["subtask_id"],
                        "https://abc.example/about",
                        "company_business",
                        purpose=arguments["purpose"],
                    )

    def test_parent_status_without_recorded_subtask_states_is_explicit(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")

        status = composite_status_summary(parent, {})
        rendered = render_composite_delivery(parent, {})

        self.assertEqual("未记录状态", status["status"])
        self.assertEqual(0, status["recorded_subtask_count"])
        self.assertIn("状态：未记录状态", rendered)

    def test_parent_status_and_delivery_keep_partial_subtasks_separate(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")
        status = composite_status_summary(parent, {
            "customer_background_research": {"status": "completed", "opened_source_count": 2},
            "product_outbound_market_analysis": {"status": "source_restricted", "opened_source_count": 1},
        })
        rendered = render_composite_delivery(parent, {
            "customer_background_research": "公司公开背景结果",
            "product_outbound_market_analysis": "市场准入结果",
        })

        self.assertEqual("部分完成", status["status"])
        self.assertIn("客户公开背景核查", rendered)
        self.assertIn("产品市场准入信息整理", rendered)
        self.assertIn("市场准入结果", rendered)
        self.assertNotIn("值得开发", rendered)
        self.assertNotIn("采购意向", rendered)

    def test_parent_status_includes_recorded_per_subtask_coverage_counts(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")

        summary = composite_status_summary(parent, {
            "customer_background_research": {
                "status": "completed",
                "completed_query_group_count": 2,
                "candidate_count": 1,
                "opened_source_count": 3,
                "confirmed_count": 2,
                "pending_count": 1,
                "source_restricted_count": 0,
                "not_executed_count": 0,
            },
        })

        background = next(item for item in summary["subtasks"] if item["route"] == "customer_background_research")
        self.assertEqual(2, background["completed_query_group_count"])
        self.assertEqual(3, background["opened_source_count"])
        self.assertIsNone(next(item for item in summary["subtasks"] if item["route"] == "product_outbound_market_analysis")["status"])

        self.assertEqual(1, summary["completed_count"])
        self.assertEqual(0, summary["waiting_for_required_input_count"])
        self.assertEqual(0, summary["source_restricted_count"])

    def test_parent_progress_without_host_state_does_not_invent_counts(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析出口市场准入")

        progress = parent_progress_summary(parent, {})

        self.assertEqual("未记录状态", progress["status"])
        for item in progress["subtasks"]:
            self.assertIsNone(item["candidate_count"])
            self.assertIsNone(item["opened_source_count"])
            self.assertIsNone(item["confirmed_count"])
            self.assertIsNone(item["pending_count"])
            self.assertIsNone(item["source_restricted_count"])
            self.assertIsNone(item["not_executed_count"])

    def test_terminal_composite_delivery_rejects_commercial_judgment_and_adds_one_footer(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH，并分析保温杯出口德国的准入要求")

        for judgment in (
            "该客户值得开发，建议优先跟进。",
            "This is a high priority prospect. We recommend following up.",
            "This is a priority lead with a recommended follow-up.",
            "The market is worth entering and this company will purchase.",
            "This customer has high value and a high purchase likelihood; the market is attractive and suitable for entry.",
            "该客户价值很高，可能采购；这个市场很有吸引力，适合进入。",
            "This lead has high customer value and is a likely buyer; market attractiveness is high.",
            "客户价值很高，市场适合进入。",
        ):
            with self.subTest(judgment=judgment):
                with self.assertRaises(ValueError):
                    render_composite_delivery(parent, {
                        "customer_background_research": judgment,
                    })
        for boundary in (
            "公开资料不足，不判断采购可能性，也不判断客户价值。",
            "Superleads does not decide whether this market is attractive or suitable for entry.",
        ):
            with self.subTest(boundary=boundary):
                render_composite_delivery(parent, {"customer_background_research": boundary})
        rendered = render_composite_delivery(parent, {
            "customer_background_research": "公司公开背景结果",
            "product_outbound_market_analysis": "市场准入结果",
        })

        self.assertTrue(has_exactly_one_final_footer(rendered))

    def test_terminal_composite_delivery_rejects_internal_terms_and_paths(self) -> None:
        parent = plan_composite_task("调查 ABC GmbH")

        for internal_text in (
            "Run ID: run-123; Claim: customer_business.",
            "The graph passed the validator and audit rule ID 7.",
            "See subtask_id=background-1 at scripts/run.py and /tmp/report.json path.",
        ):
            with self.subTest(internal_text=internal_text):
                with self.assertRaises(ValueError):
                    render_composite_delivery(parent, {"customer_background_research": internal_text})

    def test_english_parent_uses_english_display_labels(self) -> None:
        parent = plan_composite_task(
            "Run a background check on ABC GmbH and analyze tariffs for mugs exported to Germany",
            {"has_background": True, "has_market": True, "has_product": True, "has_country": True, "language": "en"},
        )

        self.assertEqual(
            ["Customer public background", "Product market and access information"],
            [item["display_name"] for item in parent["subtasks"]],
        )
        self.assertEqual("Scope and subtask status", parent["parent_title"])

    def test_english_terminal_delivery_uses_english_title_status_and_footer(self) -> None:
        parent = plan_composite_task(
            "Run a background check on ABC GmbH and analyze tariffs for mugs exported to Germany",
            {"has_background": True, "has_market": True, "has_product": True, "has_country": True, "language": "en"},
        )

        rendered = render_composite_delivery(
            parent,
            {"customer_background_research": "Public background result."},
            {"product_outbound_market_analysis": {"status": "source_restricted"}},
        )

        self.assertIn("# Scope and subtask status", rendered)
        self.assertIn("## Customer public background", rendered)
        self.assertIn("Status: Source restricted", rendered)
        self.assertIn("## Superleads Support", rendered)
        self.assertNotIn("本次范围", rendered)

    def test_delivery_renders_every_declared_route_without_claiming_execution(self) -> None:
        parent = plan_composite_task(
            "组合请求",
            {
                "has_background": True,
                "has_market": True,
                "has_batch": True,
                "has_table": True,
                "has_contact": True,
                "has_export": True,
                "has_product": True,
                "has_country": True,
            },
        )

        rendered = render_composite_delivery(
            parent,
            {"customer_background_research": "公司公开背景结果"},
            {"contact_supplement": {"status": "source_restricted"}},
        )

        self.assertIn("# 本次范围与子任务状态", rendered)
        for heading in (
            "客户公开背景核查",
            "产品市场准入信息整理",
            "批量发现公开客户信息",
            "已有客户表补全",
            "公开联系人补充",
            "最终导出",
        ):
            self.assertIn(f"## {heading}", rendered)
        self.assertIn("状态：来源受限", rendered)
        self.assertIn("未提供本任务交付或状态。", rendered)
        self.assertNotIn("已执行子任务", rendered)
        self.assertNotIn("本轮未执行", rendered)


if __name__ == "__main__":
    unittest.main()
