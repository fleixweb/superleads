#!/usr/bin/env python3
"""Regression coverage for evidence-only user-visible delivery wording."""
from __future__ import annotations

import json
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_delivery import audit_graph
from background_report import build_background_report_sheets, validate_background_report
import export_superleads_markdown as markdown_exporter
from export_superleads_markdown import (
    build_background_markdown,
    build_bulk_markdown,
    build_markdown,
    build_product_market_markdown,
)
from export_workbook import build_sheets
from _superleads_common import DETERMINISTIC_VALIDATION_DISCLOSURE, SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE
from superleads_execution_state import create_execution_state, record_candidate
from superleads_user_guidance import append_final_footer
from validate_superleads_user_visible_output import (
    GENERIC_INTERNAL_LANGUAGE,
    INTERNAL_RUNTIME_PATTERNS,
    parse_args,
    validate,
)


STANDARD_FIXTURE = ROOT / "evals" / "fixtures" / "pass_geography_searchlog_standard.json"
BULK_FIXTURE = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"
BACKGROUND_FIXTURE = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"
MARKET_FIXTURE = ROOT / "evals" / "fixtures" / "market_pass_xingheng_minimum_boundary.json"

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
    def test_visible_validator_cli_accepts_standard_bulk_delivery_status(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "validate_superleads_user_visible_output.py",
                "report.md",
                "--route",
                "bulk_customer_development",
                "--delivery-status",
                "standard_development_list",
            ],
        ):
            args = parse_args()

        self.assertEqual("standard_development_list", args.delivery_status)

    def test_standard_bulk_markdown_uses_the_standard_workbook_projection(self) -> None:
        markdown, issues, route, delivery_status = build_markdown(STANDARD_FIXTURE, "bulk_customer_development")

        self.assertEqual("bulk_customer_development", route)
        self.assertEqual("standard_development_list", delivery_status)
        self.assertEqual([], issues)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("本次输出为标准开发名单", markdown)
        self.assertIn("## 客户信息总表", markdown)
        self.assertIn("| 公司名称 | 官网 | 国家/地区 | 客户类型 | 公开信息状态 |", markdown)
        self.assertIn("| Example Buyer | https://example.com | Exampleland |", markdown)
        self.assertIn("## 公开信息与待核查事项", markdown)
        self.assertIn("## 联系方式汇总", markdown)
        self.assertNotIn("本次输出是发现候选池", markdown)
        self.assertNotIn("发现候选池样表（候选池不是正式开发名单）", markdown)

        rendered = append_final_footer(markdown)
        self.assertIn("## 下一步可选\n\n- 当前环境可继续在对话内输出表格", rendered)
        self.assertIn("- 补充待确认项的公开核验或补公开信号", rendered)
        self.assertIn("- 换搜索组合再找一批（换产品词 / 换客户类型，国家不变）", rendered)
        self.assertIn("- 选 1 家做单一客户背调", rendered)
        self.assertLess(rendered.index("## 下一步可选"), rendered.index("## Superleads 支持"))

    def test_standard_bulk_markdown_shows_file_export_only_when_the_host_recorded_it(self) -> None:
        graph = _load(STANDARD_FIXTURE)
        audit = audit_graph(graph, requested_delivery_status="standard_development_list")
        self.assertTrue(audit["ok"])
        execution_state = create_execution_state(
            "run-standard-file-menu",
            query_groups=[],
            budget={},
            task_mode="formal_research",
            route="bulk_customer_development",
        )
        execution_state["capabilities"] = {"file.write": "available"}
        graph["runs"][-1]["execution_state"] = execution_state

        markdown, issues = markdown_exporter._build_standard_bulk_markdown(graph, audit)

        self.assertEqual([], issues)
        self.assertIn("- 换格式重新导出 / 重命名工作簿（标准交付已包含表格文件）", markdown)
        self.assertNotIn("当前环境可继续在对话内输出表格", markdown)

    def test_visible_validator_rejects_unavailable_part_or_import_role_as_l2_disqualification(self) -> None:
        markdown, issues, delivery_status = build_bulk_markdown(_load(STANDARD_FIXTURE))

        self.assertEqual([], issues)
        self.assertEqual("standard_development_list", delivery_status)
        assert markdown is not None
        issues = validate(
            append_final_footer(
                markdown + "\n因官网未出现精确料号且无公开进口身份，Example Importer 不合格，不进入名单。\n"
            ),
            "bulk_customer_development",
            min_tables=6,
            delivery_status=delivery_status,
        )

        self.assertIn(
            "bulk_l2_unavailable_requirement_as_disqualification",
            {issue["code"] for issue in issues},
        )

    def test_visible_validator_allows_pending_part_or_import_role_explanation(self) -> None:
        markdown, issues, delivery_status = build_bulk_markdown(_load(STANDARD_FIXTURE))

        self.assertEqual([], issues)
        self.assertEqual("standard_development_list", delivery_status)
        assert markdown is not None
        issues = validate(
            append_final_footer(
                markdown
                + "\n官网未列精确料号、未公开进口身份属于首次接洽时核实项，不代表候选不合格，不得因此排除或不纳入名单。\n"
            ),
            "bulk_customer_development",
            min_tables=6,
            delivery_status=delivery_status,
        )

        self.assertNotIn(
            "bulk_l2_unavailable_requirement_as_disqualification",
            {issue["code"] for issue in issues},
        )

    def test_standard_list_claim_requires_canonical_structure_without_caller_status(self) -> None:
        text = "\n".join(
            (
                "# 批量客户开发",
                "",
                "本次输出为标准开发名单。",
                "",
                "## 概览",
                "## 标准开发名单",
                "## 待确认名单",
                "## 产品核验",
                "## 来源说明",
            )
        )

        issues = validate(text, "bulk_customer_development", min_tables=0)
        codes = {issue["code"] for issue in issues}
        missing = {
            issue["value"]
            for issue in issues
            if issue["code"] == "user_visible_missing_required_text"
        }

        self.assertIn("user_visible_standard_list_noncanonical_structure", codes)
        self.assertTrue({"客户信息总表", "联系方式汇总", "官网与来源链接"}.issubset(missing))

    def test_standard_list_claim_without_custom_headings_still_reports_missing_structure(self) -> None:
        text = "\n".join(
            (
                "# 批量客户开发",
                "",
                "本次输出为标准开发名单。",
                "",
                "## 已核验主体",
                "",
                "| 公司名称 | 国家/地区 |",
                "|---|---|",
                "| Example Importer | 爱尔兰 |",
            )
        )

        codes = {issue["code"] for issue in validate(text, "bulk_customer_development", min_tables=0)}

        self.assertIn("user_visible_standard_list_structure_missing", codes)

    def test_standard_bulk_graph_can_render_the_initial_candidate_pool_view(self) -> None:
        markdown, issues, route, delivery_status = build_markdown(
            STANDARD_FIXTURE,
            "bulk_customer_development",
            requested_delivery_status="initial_lead_list",
        )

        self.assertEqual("bulk_customer_development", route)
        self.assertEqual("initial_lead_list", delivery_status)
        self.assertEqual([], issues)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("发现候选池样表（候选池不是正式开发名单）", markdown)
        self.assertIn("## 搜索覆盖与收敛", markdown)
        self.assertNotIn("## 客户信息总表", markdown)
        self.assertNotIn("本次输出为标准开发名单", markdown)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, markdown)

    def test_initial_bulk_graph_rejects_standard_delivery_override(self) -> None:
        markdown, issues, route, delivery_status = build_markdown(
            BULK_FIXTURE,
            "bulk_customer_development",
            requested_delivery_status="standard_development_list",
        )

        self.assertEqual("bulk_customer_development", route)
        self.assertIsNone(markdown)
        self.assertIsNone(delivery_status)
        self.assertIn("markdown_delivery_status_not_allowed", {item["code"] for item in issues})

    def test_non_bulk_builders_return_no_bulk_delivery_status(self) -> None:
        background_markdown, background_issues, background_status = build_background_markdown(_load(BACKGROUND_FIXTURE))
        market_markdown, market_issues, market_status = build_product_market_markdown(_load(MARKET_FIXTURE))

        self.assertIsNotNone(background_markdown)
        self.assertEqual([], background_issues)
        self.assertIsNone(background_status)
        self.assertIsNotNone(market_markdown)
        self.assertEqual([], market_issues)
        self.assertIsNone(market_status)

    def test_exporter_passes_audited_status_without_sniffing_standard_template_text(self) -> None:
        original_builder = markdown_exporter._build_standard_bulk_markdown

        def render_without_status_sentence(graph, audit):
            text, issues = original_builder(graph, audit)
            return text.replace("本次输出为标准开发名单", "本次交付采用已核验名单口径"), issues

        stdout = StringIO()
        with (
            patch.object(markdown_exporter, "_build_standard_bulk_markdown", side_effect=render_without_status_sentence),
            patch.object(markdown_exporter, "validate_user_visible_markdown", return_value=[]) as validator,
            patch.object(
                sys,
                "argv",
                [
                    "export_superleads_markdown.py",
                    str(STANDARD_FIXTURE),
                    "--route",
                    "bulk_customer_development",
                    "--format",
                    "json",
                ],
            ),
            redirect_stdout(stdout),
        ):
            return_code = markdown_exporter.main()

        self.assertEqual(0, return_code)
        self.assertEqual("standard_development_list", validator.call_args.kwargs["delivery_status"])
        self.assertEqual(6, validator.call_args.kwargs["min_tables"])

    def test_exporter_cli_accepts_downward_delivery_status_override(self) -> None:
        stdout = StringIO()
        with (
            patch.object(
                sys,
                "argv",
                [
                    "export_superleads_markdown.py",
                    str(STANDARD_FIXTURE),
                    "--route",
                    "bulk_customer_development",
                    "--delivery-status",
                    "initial_lead_list",
                    "--format",
                    "json",
                ],
            ),
            redirect_stdout(stdout),
        ):
            return_code = markdown_exporter.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, return_code)
        self.assertTrue(payload["ok"])
        self.assertEqual("initial_lead_list", payload["delivery_status"])
        self.assertGreaterEqual(payload["table_count"], 10)

    def test_exporter_cli_rejects_upward_delivery_status_override(self) -> None:
        stdout = StringIO()
        with (
            patch.object(
                sys,
                "argv",
                [
                    "export_superleads_markdown.py",
                    str(BULK_FIXTURE),
                    "--route",
                    "bulk_customer_development",
                    "--delivery-status",
                    "standard_development_list",
                    "--format",
                    "json",
                ],
            ),
            redirect_stdout(stdout),
        ):
            return_code = markdown_exporter.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(1, return_code)
        self.assertFalse(payload["ok"])
        self.assertIn("markdown_delivery_status_not_allowed", {item["code"] for item in payload["issues"]})

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
        markdown, issues, delivery_status = build_bulk_markdown(_load(BULK_FIXTURE))

        self.assertEqual([], issues)
        self.assertEqual("initial_lead_list", delivery_status)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("公开信号已匹配当前范围", markdown)
        self.assertNotIn("可优先人工跟进", markdown)
        for wording in FORBIDDEN_DECISION_WORDING:
            self.assertNotIn(wording, markdown)

    def test_bulk_markdown_does_not_expose_internal_query_group_ids(self) -> None:
        markdown, issues, delivery_status = build_bulk_markdown(_load(BULK_FIXTURE))

        self.assertEqual([], issues)
        self.assertEqual("initial_lead_list", delivery_status)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertNotIn("region_q_distributor", markdown)
        self.assertNotIn("region_r_directory", markdown)

    def test_bulk_markdown_renders_search_combinations_and_a_nonblocking_next_step_menu(self) -> None:
        graph = _load(BULK_FIXTURE)
        execution_state = create_execution_state(
            "run-menu-internal-only",
            query_groups=[
                {
                    "group_id": "importer-combination-internal-only",
                    "execution_order": "independent",
                    "status": "completed",
                    "search_combination": {
                        "product_term": "sample product",
                        "market": "Region Q",
                        "customer_type": "经销商",
                    },
                }
            ],
            budget={"query_group_limit": 1},
            uncovered_combination_hints=["已观察到的本地术语 + Region Q + 维修厂"],
        )
        for index in range(10):
            self.assertTrue(record_candidate(execution_state, query_group_id="importer-combination-internal-only", candidate_id=f"candidate-{index}")["recorded"])
        graph["runs"][-1]["execution_state"] = execution_state

        markdown, issues, delivery_status = build_bulk_markdown(graph)

        self.assertEqual([], issues)
        self.assertEqual("initial_lead_list", delivery_status)
        self.assertIsNotNone(markdown)
        assert markdown is not None
        self.assertIn("## 本轮搜索组合", markdown)
        self.assertIn("| 产品词 | 国家/市场 | 客户类型 | 新增主体 |", markdown)
        self.assertIn("已观察到的本地术语 + Region Q + 维修厂", markdown)
        self.assertIn("## 下一步可选", markdown)
        self.assertIn("继续扩展（可指定 30 / 50 / 100 家，或直接说数量）", markdown)
        self.assertIn("对上述名单做深度核验 → 标准开发名单（含社媒 / 地图 / 贸易记录 + 联系人归属核验；交付表格文件 + 配套报告；较慢；产量降、耗时增", markdown)
        self.assertIn("只补社媒 / 地图 / 贸易记录信号（不做主体与联系人核验；较快，仍属候选池，不升级为已验证）", markdown)
        self.assertIn("\n- 已观察到的本地术语 + Region Q + 维修厂", markdown)
        self.assertIn("\n- 继续扩展（可指定 30 / 50 / 100 家，或直接说数量）", markdown)
        self.assertNotIn("\n· ", markdown)
        self.assertNotIn("importer-combination-internal-only", markdown)
        self.assertNotIn("run-menu-internal-only", markdown)
        self.assertLess(markdown.index("## 本轮搜索组合"), markdown.index("## 下一步可选"))

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

        markdown, markdown_issues, delivery_status = build_background_markdown(graph)
        self.assertEqual([], markdown_issues)
        self.assertIsNone(delivery_status)
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

        markdown, markdown_issues, delivery_status = build_background_markdown(graph)
        self.assertEqual([], markdown_issues)
        self.assertIsNone(delivery_status)
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
        markdown, issues, delivery_status = build_bulk_markdown(_load(BULK_FIXTURE))
        self.assertEqual([], issues)
        self.assertEqual("initial_lead_list", delivery_status)
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

    def test_visible_validator_blocks_runtime_technical_details(self) -> None:
        expected = {
            "jsonschema",
            "openpyxl",
            "python3",
            "python.exe",
            "pip install",
            "venv",
            "Traceback",
            "ImportError",
            "ModuleNotFoundError",
            "模块名",
            "preflight_capabilities.py",
            "PYTHONPATH",
            "工作区目录",
        }
        self.assertTrue(expected.issubset(GENERIC_INTERNAL_LANGUAGE))
        self.assertTrue({".py", "预检", "适配器", "模块", "python", "interpreter", "解释器", "依赖", "依赖缺失", "referencing"}.isdisjoint(GENERIC_INTERNAL_LANGUAGE))
        self.assertGreaterEqual(len(INTERNAL_RUNTIME_PATTERNS), 5)

        issues = validate(
            "当前系统 Python 缺少它依赖的 jsonschema。",
            "product_outbound_market_analysis",
            min_tables=0,
        )
        self.assertIn(
            ("user_visible_internal_language", "jsonschema"),
            {(item["code"], item.get("value")) for item in issues},
        )

        for text, phrase in (
            ("preflight_capabilities.py 对当前能力进行了预检。", "preflight_capabilities.py"),
            ("我会通过 PYTHONPATH 重试当前校验。", "PYTHONPATH"),
            ("The runtime path is unavailable for this export.", "runtime dependency operation"),
            ("当前环境缺少依赖，暂时不能完成导出。", "runtime dependency operation"),
            ("This module is unavailable in the current runtime.", "runtime dependency operation"),
            ("A package import failed during validation.", "runtime import context"),
            ("Python interpreter is unavailable for validation.", "runtime interpreter context"),
            ("当前 Python 解释器不可用。", "runtime interpreter context"),
        ):
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertIn(
                    ("user_visible_internal_language", phrase),
                    {(item["code"], item.get("value")) for item in issues},
                )

        for text in (
            "能力预检脚本给出了受限结果。",
            "适配器报告显示该操作不可用。",
            "不要重试同一失败适配器。",
            "scripts/validate_report.py 需要在内部路径运行。",
        ):
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertIn("user_visible_internal_language", {item["code"] for item in issues})

        for text in (
            "本轮分析中国出口电源适配器到越南的公开价格。",
            "候选客户官网为 example.com.py 的巴拉圭进口商。",
            "越南要求装运前预检报告。",
            "本轮分析电源适配器的公开价格；候选官网为 example.com.py；越南的装运前预检报告仍待确认。",
            "本轮确认进口商角色、import duty、包装材料和纸浆进口公开信息。",
            "Company provides translation and interpreter services.",
            "当前市场依赖进口，本地产能有限。",
        ):
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn("user_visible_internal_language", {item["code"] for item in issues})

    def test_visible_validator_allows_foreign_trade_terms_that_resemble_runtime_words(self) -> None:
        allowed_samples = (
            "客户类型：光伏模块安装商与分销商。",
            "主营太阳能模块进口与安装。",
            "该公司提供模块化厂房安装服务。",
            "产品含 LED 模块，安装于户外广告牌。",
            "公开信息：电池模块安装线已投产。",
            "客户为空调安装商，业务依赖进口压缩机。",
            "官网称设备安装需要依赖其认证团队。",
            "Public page mentions PV module import from China.",
            "Business: solar module import and distribution.",
            "Customer type: solar module importer and distributor.",
            "Company provides translation and interpreter services.",
            "Battery pack dependency on imported cells is noted.",
            "该市场原纸依赖进口，本地产能有限。",
            "主营包装材料，含 import duty 说明。",
            "德国工业传感器进口商，官网列出安装指南。",
            "逆变器模块安装商为工商业屋顶项目提供服务。",
            "LED 显示屏模块安装与售后维护由当地团队负责。",
            "该经销商进口冷却模块并提供现场安装。",
            "HVAC equipment imports depend on seasonal demand.",
            "The distributor handles power module imports and local installation.",
            "Solar panel mounting system installer and module distributor.",
            "Modular cleanroom installation is the company's core service.",
            "Dependence on imported copper remains high.",
            "目标客户是储能电池包组装商与模块供应商。",
            "官网提供泵站安装手册及进口备件目录。",
            "Paper packaging importer relies on certified pulp suppliers.",
            "Conference interpreter services are listed under business support.",
            "模块安装已完成。当前环境温度为 25°C。",
            "The module installation is complete. The runtime is eight hours.",
        )
        for text in allowed_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_visible_validator_continues_blocking_runtime_leakage(self) -> None:
        blocked_samples = (
            "当前交付为\"发现候选池\"，本环境因缺少 jsonschema 依赖，未能完成完整确定性校验。",
            "当前校验环境缺少隔离依赖，我会在临时隔离环境补齐后再运行最终检查，不改动你的项目文件。",
            "请先执行 pip install -r requirements.txt",
            "[下载标准开发名单](C:/Users/Lenovo/Documents/Codex/outputs/名单.md)",
            "报告已写入 file:///home/u/out/report.md",
        )
        for text in blocked_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_visible_validator_keeps_runtime_leakage_blocked_after_anchor_narrowing(self) -> None:
        blocked_samples = (
            "本环境因缺少 jsonschema 依赖，未能完成完整确定性校验。",
            "当前校验环境缺少隔离依赖，我会在临时隔离环境补齐后再运行最终检查。",
            "请先执行 pip install -r requirements.txt",
            "本环境缺少必要依赖，未能生成工作簿。",
            "运行环境缺少组件，无法完成导出。",
            "由于依赖问题，本次未能完成校验。",
            "未安装 openpyxl，改为输出 CSV。",
            "Python 运行时不可用，已降级交付。",
            "校验脚本所需模块不可用。",
            "当前环境缺少校验依赖。",
            "需要先补齐运行时依赖。",
            "ModuleNotFoundError: No module named x",
            "设置 PYTHONPATH 后重试",
        )
        for text in blocked_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_visible_validator_allows_trade_language_after_runtime_anchor_narrowing(self) -> None:
        allowed_samples = (
            "设备运行环境温度 -20~50℃，安装简便。",
            "产品运行环境要求洁净，需配套模块化机柜。",
            "该产业依赖环境政策支持，本地缺少配套产能。",
            "随机附安装包与备用模块。",
            "官网标注安装包内含固定件与密封模块。",
            "计量校验证书由第三方出具，含安装位置说明。",
            "出口前需完成环境与安全校验，设备安装后验收。",
            "工作环境粉尘大，客户依赖进口滤芯。",
        )
        for text in allowed_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_visible_validator_allows_environmental_trade_language_and_canonical_disclosures(self) -> None:
        allowed_samples = (
            "该公司通过 ISO 14001 环境管理体系认证，提供设备安装服务。",
            "产品符合欧盟环境法规，包装模块可回收。",
            "官网提到环境友好型模块化冷库安装方案。",
            "出口需提供环境影响评估与安装验收报告。",
            "公开资料显示其洁净室环境下完成模块安装。",
            "该工厂环境温控依赖进口机组。",
            "第三方校验机构出具了模块化产线安装报告。",
            "客户类型：光伏模块安装商与分销商。",
            "主营太阳能模块进口与安装。",
            "该公司提供模块化厂房安装服务。",
            "产品含 LED 模块，安装于户外广告牌。",
            "公开信息：电池模块安装线已投产。",
            "客户为空调安装商，业务依赖进口压缩机。",
            "官网称设备安装需要依赖其认证团队。",
            "该市场原纸依赖进口，本地产能有限。",
            "德国工业传感器进口商，官网列出安装指南。",
            "Company provides translation and interpreter services.",
            "Battery pack dependency on imported cells is noted.",
            DETERMINISTIC_VALIDATION_DISCLOSURE,
            SCHEMA_PROFILE_UNAVAILABLE_DISCLOSURE,
        )
        for text in allowed_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_visible_validator_covers_additional_environmental_certification_language(self) -> None:
        allowed_samples = (
            "企业通过 RoHS 环保合规审核并提供检测报告。",
            "产品符合 REACH 要求，材料成分可追溯。",
            "计量校准证书已随设备资料一并提供。",
            "第三方检测报告列明噪声与能耗指标。",
            "工厂取得职业健康安全管理体系认证。",
            "包装材料满足可回收设计要求。",
            "供应商提供碳足迹核算与审计记录。",
            "设备出厂前完成电气安全检验。",
        )
        for text in allowed_samples:
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn(
                    "user_visible_internal_language",
                    {item["code"] for item in issues},
                )

    def test_terminal_dialog_rejects_runtime_recovery_path_and_missing_footer(self) -> None:
        text = (
            "[下载标准开发名单](C:/Users/Lenovo/Documents/Codex/越南巡演音响_标准开发名单.md)\n"
            "当前校验环境缺少隔离依赖，我会在临时隔离环境补齐后再运行最终检查。"
        )
        issues = validate(text, "bulk_customer_development", min_tables=0)
        codes = {item["code"] for item in issues}
        self.assertIn("user_visible_internal_language", codes)
        self.assertIn("user_visible_support_footer_missing", codes)
        self.assertTrue(any(item.get("value") == "local path" for item in issues))

    def test_visible_validator_reuses_common_local_path_detection_without_echoing_path(self) -> None:
        self.assertTrue({"file://", "/home/", "/tmp/"}.isdisjoint(GENERIC_INTERNAL_LANGUAGE))
        samples = (
            r"[Markdown 背调报告](C:\Users\Lenovo\Documents\bernard_background.md)",
            r"[Markdown 背调报告](C:\\Users\\Lenovo\\Documents\\bernard_background.md)",
            "/home/fleix/outputs/bernard_background.md",
            "/tmp/bernard_background.md",
            "file:///tmp/bernard_background.md",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                issues = validate(sample, "product_outbound_market_analysis", min_tables=0)
                internal = [item for item in issues if item["code"] == "user_visible_internal_language"]
                self.assertTrue(internal)
                self.assertTrue(all(item.get("value") == "local path" for item in internal))
                self.assertTrue(all(sample not in item.get("message", "") for item in internal))

    def test_visible_validator_blocks_host_directive_constructs_by_shape(self) -> None:
        for text in (
            ':codex-file-citation{path="C:__codex_directive_quoted_backslash__Users__codex_directive_quoted_backslash__Lenovo__codex_directive_quoted_backslash__Documents__codex_directive_quoted_backslash__bernard_background.xlsx" purpose="output"}',
            "报告已生成：__codex_directive_quoted_backslash__",
        ):
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertIn("user_visible_internal_language", {item["code"] for item in issues})

    def test_visible_validator_does_not_misclassify_normal_colons_links_or_values(self) -> None:
        for text in (
            "注意：本轮未取得新的公开来源。",
            "[Markdown 背调报告](bernard_background.md)",
            "![公司标志](bernard_logo.png)",
            "更新时间 11:37，比例 4.6/5。",
            "公开邮箱 sales.irl@apairltd.com 可作为联系入口。",
            "Status: pending public verification.",
        ):
            with self.subTest(text=text):
                issues = validate(text, "product_outbound_market_analysis", min_tables=0)
                self.assertNotIn("user_visible_internal_language", {item["code"] for item in issues})

    def test_visible_validator_allows_product_market_module_header(self) -> None:
        issues = validate(
            "| 模块 | 当前结果 | 状态 |\n| --- | --- | --- |",
            "product_outbound_market_analysis",
            min_tables=0,
        )
        self.assertNotIn("user_visible_internal_language", {item["code"] for item in issues})

    def test_visible_validator_blocks_coverage_overclaims_and_node_workarounds(self) -> None:
        for wording in (
            "我们已全部找到爱尔兰的目标公司。",
            "本轮实现全网覆盖，没有无遗漏问题。",
            "这份名单已覆盖全部目标主体，达到 100% 覆盖。",
            "我们列出了所有爱尔兰的农机零件公司。",
            "建议切换到爱尔兰节点后再搜索。",
            "请使用 VPN 或代理获得本地结果。",
        ):
            with self.subTest(wording=wording):
                issues = validate(wording, "bulk_customer_development", min_tables=0)
                self.assertIn("user_visible_coverage_overclaim", {item["code"] for item in issues})

        compliant = "本轮搜索组合有可见边界；新增组合与已有池重合度约 40%，接近当前公开检索可见范围。不要建议使用 VPN、代理或换节点。"
        issues = validate(compliant, "bulk_customer_development", min_tables=0)
        self.assertNotIn("user_visible_coverage_overclaim", {item["code"] for item in issues})
