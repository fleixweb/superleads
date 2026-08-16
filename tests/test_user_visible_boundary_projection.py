#!/usr/bin/env python3
"""Regression coverage for evidence-only user-visible delivery wording."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_delivery import audit_graph
from background_report import build_background_report_sheets, validate_background_report
from export_superleads_markdown import build_background_markdown, build_bulk_markdown
from export_workbook import build_sheets
from superleads_user_guidance import append_final_footer
from validate_superleads_user_visible_output import validate


STANDARD_FIXTURE = ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json"
BULK_FIXTURE = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
BACKGROUND_FIXTURE = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"

FORBIDDEN_DECISION_WORDING = (
    "重点开发",
    "推荐跟进",
    "暂不建议",
    "开发建议",
    "值不值得继续跟",
    "建议继续跟进",
    "重点跟进",
    "建议优先联系",
    "继续跟进",
    "high priority prospect",
    "recommend contacting",
    "should follow up",
)


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class UserVisibleBoundaryProjectionTest(unittest.TestCase):
    def test_standard_workbook_csv_projection_uses_evidence_labels_and_mechanical_filter_disclosure(self) -> None:
        graph = _load(STANDARD_FIXTURE)
        audit = audit_graph(graph, requested_delivery_status="standard_development_list")
        self.assertTrue(audit["ok"])

        sheets = build_sheets(graph, audit, "standard")
        rendered = json.dumps(sheets, ensure_ascii=False)

        self.assertIn("公开信息与待核查事项", sheets)
        self.assertNotIn("开发建议", sheets)
        self.assertIn("公开信号已匹配当前范围", rendered)
        self.assertIn("按用户事先提供的规则和已核验公开信息机械筛选", rendered)
        self.assertIn("不代表 AI 推荐或价值判断", rendered)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, rendered)

    def test_bulk_markdown_uses_evidence_partition_not_follow_up_priority(self) -> None:
        markdown, issues = build_bulk_markdown(_load(BULK_FIXTURE))

        self.assertEqual([], issues)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("公开信号已匹配当前范围", markdown)
        self.assertNotIn("可优先人工跟进", markdown)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, markdown)

    def test_background_report_asks_about_verification_basis_without_follow_up_advice(self) -> None:
        graph = _load(BACKGROUND_FIXTURE)
        scope, issues = validate_background_report(graph)
        self.assertEqual([], issues)
        self.assertIsNotNone(scope)
        assert scope is not None

        sheets = build_background_report_sheets(scope)
        overview = json.dumps(sheets["客户一眼看懂"], ensure_ascii=False)
        self.assertIn("是否具备继续核验基础", overview)
        self.assertIn("公开联系入口与待确认事项", overview)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, overview)
        self.assertNotIn("现在能不能开始联系", overview)
        self.assertNotIn("可准备首轮沟通", overview)
        self.assertNotIn("可以从已核实的公开入口开始", overview)

        markdown, markdown_issues = build_background_markdown(graph)
        self.assertEqual([], markdown_issues)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("是否具备继续核验基础", markdown)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, markdown)

    def test_background_delivery_uses_evidence_sections_without_commercial_action_guidance(self) -> None:
        graph = _load(BACKGROUND_FIXTURE)
        scope, issues = validate_background_report(graph)
        self.assertEqual([], issues)
        assert scope is not None

        sheets = build_background_report_sheets(scope)
        rendered = json.dumps(sheets, ensure_ascii=False)
        self.assertIn("公开业务信号与待核验事项", sheets)
        self.assertIn("公开联系入口与关联依据", sheets)
        self.assertIn("待核验事项与来源限制", sheets)
        for wording in (
            "我们看到的业务机会",
            "建议怎么切入",
            "怎么联系、先找谁",
            "建议联系谁/哪里",
            "为什么先找这里",
            "联系时先问什么",
            "跟进前要注意什么",
            "建议动作",
        ):
            self.assertNotIn(wording, rendered)

        markdown, markdown_issues = build_background_markdown(graph)
        self.assertEqual([], markdown_issues)
        assert markdown is not None
        for wording in (
            "公开业务信号与可沟通角度",
            "可以怎么问",
            "怎么联系、先找谁",
            "建议联系谁/哪里",
            "为什么先找这里",
            "联系时先问什么",
            "跟进前要注意什么",
            "建议动作",
        ):
            self.assertNotIn(wording, markdown)

    def test_visible_validator_blocks_positive_commercial_language_but_allows_a_negated_boundary(self) -> None:
        markdown, issues = build_bulk_markdown(_load(BULK_FIXTURE))
        self.assertEqual([], issues)
        assert markdown is not None

        positive_issues = validate(
            append_final_footer(markdown + "\n重点开发：应立即联系。\n"),
            "bulk_customer_development",
            min_tables=10,
        )
        self.assertIn("user_visible_value_judgment", {item["code"] for item in positive_issues})

        for positive_wording in (
            "建议优先联系这家公司。",
            "可作为指定背调对象继续跟进。",
            "公开信息不足但仍推荐跟进。",
            "不是正式名单但推荐跟进。",
            "不判断采购意愿，但重点开发。",
            "不推荐跟进这家公司。",
            "不重点开发这家公司。",
            "不建议进入这个市场。",
            "This is a high priority prospect.",
            "We recommend contacting this company.",
            "You should follow up with this lead.",
            "We do not know buyer intent but recommend contacting this company.",
            "We do not recommend contacting this company.",
        ):
            with self.subTest(positive_wording=positive_wording):
                positive_issues = validate(
                    append_final_footer(markdown + "\n" + positive_wording + "\n"),
                    "bulk_customer_development",
                    min_tables=10,
                )
                self.assertIn("user_visible_value_judgment", {item["code"] for item in positive_issues})

        boundary_issues = validate(
            append_final_footer(markdown + "\nSuperleads 不替用户推荐跟进。\n"),
            "bulk_customer_development",
            min_tables=10,
        )
        self.assertNotIn("user_visible_value_judgment", {item["code"] for item in boundary_issues})

        market_boundary_issues = validate(
            append_final_footer(markdown + "\nSuperleads 不判断是否值得进入。\n"),
            "bulk_customer_development",
            min_tables=10,
        )
        self.assertNotIn("user_visible_value_judgment", {item["code"] for item in market_boundary_issues})

        for boundary in (
            "不做推荐客户排序，也不给采购概率。",
            "不能写成最佳路线或承诺交期。",
        ):
            with self.subTest(boundary=boundary):
                boundary_issues = validate(
                    append_final_footer(markdown + "\n" + boundary + "\n"),
                    "bulk_customer_development",
                    min_tables=10,
                )
                self.assertNotIn("user_visible_value_judgment", {item["code"] for item in boundary_issues})

        mixed_sentence_issues = validate(
            append_final_footer(markdown + "\n不猜采购意愿，重点开发应立即联系。\n"),
            "bulk_customer_development",
            min_tables=10,
        )
        self.assertIn("user_visible_value_judgment", {item["code"] for item in mixed_sentence_issues})
