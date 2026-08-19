#!/usr/bin/env python3
"""Regression coverage for side-effect-free Superleads intake modes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from route_superleads_intake import classify, norm
from superleads_task_modes import (
    LATEST_VERSION_UNCONFIRMED,
    check_latest_version,
    classify_task_mode,
    is_explicit_update_request,
    normalize_remote_version,
    read_active_plugin_version,
)


class SuperleadsTaskModesTest(unittest.TestCase):
    PUBLIC_NEXT_SKILLS = {
        None,
        "using-superleads",
        "researching-customer-background",
        "analyzing-product-outbound-market",
    }

    def test_router_never_returns_an_unregistered_internal_skill(self) -> None:
        cases = (
            "帮我找德国的工业传感器进口商",
            "我上传了客户表，请补全官网",
            "请核查这批候选的公开联系人",
            "把已经核验的结果导出 Excel",
            "请保存这轮反馈",
            "调查 ABC GmbH，并整理我上传的客户表",
        )
        for text in cases:
            with self.subTest(text=text):
                response = classify(
                    text,
                    current_result_valid="导出" in text,
                    current_run_id="run-1" if "反馈" in text else None,
                )
                self.assertIn(response.get("next_skill"), self.PUBLIC_NEXT_SKILLS)

    def test_metadata_prompts_are_side_effect_free_before_business_routing(self) -> None:
        callbacks: list[str] = []

        def denied_callback() -> None:
            callbacks.append("called")
            raise AssertionError("metadata must not invoke operational callbacks")

        for text in (
            "Superleads 当前版本是什么？",
            "已安装的 Superleads 版本是多少？",
            "Superleads 当前能力是什么？",
            "Superleads 的反馈入口在哪里？",
            "What is the current Superleads version?",
            "What version of Superleads is installed?",
            "What is the latest Superleads version?",
            "What are the current Superleads capabilities?",
            "Where can I send Superleads feedback?",
            "@",
            "@superleads",
            "Superleads help",
        ):
            with self.subTest(text=text):
                response = classify(
                    text,
                    preflight_callback=denied_callback,
                    network_callback=denied_callback,
                    cache_scan_callback=denied_callback,
                    fetch_latest_version=denied_callback,
                )
                self.assertEqual("metadata", response["interaction_mode"])
                self.assertEqual([], response["operations"])

        self.assertEqual([], callbacks)

    def test_only_explicit_update_requests_may_call_the_injected_fetch(self) -> None:
        for text in (
            "请检查更新",
            "请查看 Superleads 最新版本",
            "check latest version",
            "Please check the latest Superleads version",
        ):
            with self.subTest(text=text):
                calls: list[str] = []

                def fetch() -> str:
                    calls.append("fetch")
                    return "1.2.4"

                response = classify(text, fetch_latest_version=fetch, session_cache={})

                self.assertEqual("metadata", response["interaction_mode"])
                self.assertEqual([], response["operations"])
                self.assertEqual(["fetch"], calls)
                self.assertIn("1.2.4", "\n".join(response["response_lines"]))

    def test_mode_classifier_covers_metadata_material_discovery_and_formal_intent(self) -> None:
        cases = {
            "How to use Superleads?": "metadata",
            "请初审我上传的客户名单.xlsx": "material_triage",
            "请初审这张竞争对手截图.png": "material_triage",
            "请初审附件中的 PDF": "material_triage",
            "帮我找德国的工业传感器进口商": "discovery_snapshot",
            "调查 example.com 这家公司背景": "discovery_snapshot",
            "分析中国出口保温杯到越南的市场": "discovery_snapshot",
            "给我一份德国工业传感器的正式开发名单": "formal_research",
            "保温杯出口越南的完整报告": "formal_research",
            "对 example.com 做深度背调": "formal_research",
            "联系人归属核验": "formal_research",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(expected, classify_task_mode(text))

    def test_material_only_intake_stays_at_user_visible_triage(self) -> None:
        for text in (
            "请初审我上传的客户名单.xlsx",
            "请初审这张竞争对手截图.png",
            "请初审附件中的 PDF",
        ):
            with self.subTest(text=text):
                response = classify(text)
                self.assertEqual("material_triage", response["interaction_mode"])
                self.assertEqual("material_triage", response["route"])
                self.assertEqual([], response["operations"])
        self.assertIn("资料初审", "\n".join(response["response_lines"]))

    def test_explicit_filename_material_requests_stay_in_triage_without_research(self) -> None:
        for text in (
            "请整理这份报价单.pdf",
            "请读取这张客户截图.png",
            "Please summarize this customer-list.xlsx",
        ):
            with self.subTest(text=text):
                response = classify(text)
                self.assertEqual("material_triage", response["interaction_mode"])
                self.assertEqual([], response["operations"])

    def test_capability_and_feedback_metadata_do_not_read_the_active_manifest(self) -> None:
        with patch("superleads_task_modes.read_active_plugin_version") as read_version:
            capability = classify("Superleads 当前有什么能力？", active_root="/unused")
            feedback = classify("Superleads 怎么反馈？", active_root="/unused")

        self.assertEqual("metadata", capability["interaction_mode"])
        self.assertEqual("metadata", feedback["interaction_mode"])
        read_version.assert_not_called()

    def test_status_and_export_help_are_fast_metadata_without_operations(self) -> None:
        for text in ("Superleads 当前状态是什么", "How do I export?"):
            with self.subTest(text=text):
                response = classify(text)
                self.assertEqual("metadata", response["interaction_mode"])
                self.assertEqual([], response["operations"])

    def test_one_object_contact_request_uses_single_object_route(self) -> None:
        response = classify("只找这家公司的公开邮箱 example.com")

        self.assertEqual("single_object_contact", response["route"])
        self.assertEqual("researching-customer-background", response["next_skill"])
        self.assertFalse(response["split_customer_development"])

    def test_export_request_does_not_become_table_enrichment(self) -> None:
        blocked = classify("把已经核验的结果导出 Excel")
        allowed = classify("把已经核验的结果导出 Excel", current_result_valid=True)

        self.assertEqual("export_requires_current_result", blocked["route"])
        self.assertNotEqual("existing_table_enrichment", blocked["route"])
        self.assertEqual("export_delivery", allowed["route"])
        self.assertEqual("using-superleads", allowed["next_skill"])
        self.assertEqual(
            "shared/internal-stages/exporting-lead-workbooks.md",
            allowed["next_stage_reference"],
        )

    def test_candidate_correction_stays_in_current_run_without_persistent_save(self) -> None:
        response = classify("这个候选不符合要求", current_run_id="run-1")

        self.assertEqual("current_run_feedback_correction", response["route"])
        self.assertEqual("current_run", response["feedback_scope"])
        self.assertEqual("current_run_correction", response["feedback_action"])
        self.assertEqual(
            "shared/internal-stages/learning-from-feedback.md",
            response["next_stage_reference"],
        )

    def test_product_market_document_requirements_are_not_material_triage(self) -> None:
        response = classify("48V锂电池到沙特要 SABER 吗，清关还要什么文件")

        self.assertEqual("discovery_snapshot", response["interaction_mode"])
        self.assertEqual("product_outbound_market_analysis", response["route"])

    def test_unambiguous_bulk_request_uses_ten_candidate_fast_snapshot(self) -> None:
        response = classify("帮我找丹麦做巡演音响的进口商")

        self.assertEqual("bulk_customer_development", response["route"])
        self.assertEqual("discovery_snapshot", response["task_mode"])
        self.assertEqual([], response["missing_fields"])
        self.assertEqual("fast_candidate_pool", response["delivery_mode"])
        self.assertEqual(10, response["first_batch_candidate_target"])
        self.assertEqual(10, response["max_candidates_per_group"])
        self.assertFalse(response["include_social"])
        self.assertFalse(response["include_maps"])
        self.assertFalse(response["include_trade_records"])
        self.assertTrue(response["ask_expansion_after_first_batch"])
        self.assertIn("30", "\n".join(response["response_lines"]))
        self.assertIn("50", "\n".join(response["response_lines"]))
        self.assertIn("100", "\n".join(response["response_lines"]))
        self.assertIn("直接说数量", "\n".join(response["response_lines"]))
        self.assertIn("补社媒 / 地图 / 贸易记录信号（较快", "\n".join(response["response_lines"]))
        self.assertIn("深度核验 → 标准开发名单（较慢", "\n".join(response["response_lines"]))

    def test_part_number_country_and_customer_type_is_an_unambiguous_bulk_request(self) -> None:
        response = classify("13185402+爱尔兰经销商")

        self.assertEqual("bulk_customer_development", response["route"])
        self.assertEqual("using-superleads", response["next_skill"])
        self.assertEqual([], response["missing_fields"])
        self.assertEqual("part_number", response["product_anchor_type"])
        self.assertEqual("13185402", response["product_anchor"])
        self.assertIn("公开检索核对产品身份", "\n".join(response["response_lines"]))

    def test_country_and_customer_type_without_action_still_routes_to_bulk_with_product_missing(self) -> None:
        response = classify("爱尔兰经销商")

        self.assertEqual("bulk_customer_development", response["route"])
        self.assertEqual(["product_or_scope"], response["missing_fields"])

    def test_phone_date_and_secret_like_tokens_are_not_part_number_anchors(self) -> None:
        for text in (
            "13800138000+爱尔兰经销商",
            "20260817+爱尔兰经销商",
            "sk-abcdef1234567890+爱尔兰经销商",
            "v0.2.0+爱尔兰经销商",
            "192.168.1.10+爱尔兰经销商",
            "550e8400-e29b-41d4-a716-446655440000+爱尔兰经销商",
            "AKIAIOSFODNN7EXAMPLE+爱尔兰经销商",
            "ghp_1234567890abcdef+爱尔兰经销商",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("bulk_customer_development", response["route"])
                self.assertEqual(["product_or_scope"], response["missing_fields"])
                self.assertNotIn("product_anchor_type", response)
                self.assertNotIn("product_anchor", response)

    def test_normalization_does_not_rewrite_plus_inside_email_or_url(self) -> None:
        self.assertEqual("sales+eu@example.com", norm("sales+eu@example.com"))
        self.assertEqual("https://example.com/?q=a+b", norm("https://example.com/?q=a+b"))

    def test_customer_in_a_market_question_does_not_create_a_batch_subtask(self) -> None:
        response = classify("客户问我要 SDS 和 UN38.3，美国那边到底要不要")

        self.assertEqual("product_outbound_market_analysis", response["route"])
        self.assertEqual(["product_identity"], response["missing_fields"])

    def test_open_ended_product_phrases_count_as_explicit_bulk_scope(self) -> None:
        for text in (
            "找德国工业阀门进口商",
            "找爱尔兰农业拖拉机经销商",
            "找美国太阳能逆变器分销商",
            "找法国医疗耗材批发商",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("bulk_customer_development", response["route"])
                self.assertEqual([], response["missing_fields"])

    def test_business_phrase_latest_version_does_not_become_metadata(self) -> None:
        response = classify("找德国最新版本工业阀门经销商")

        self.assertEqual("bulk_customer_development", response["route"])
        self.assertEqual([], response["missing_fields"])

    def test_additional_sensitive_or_non_product_tokens_are_not_part_number_anchors(self) -> None:
        for text in (
            "17/08/2026+爱尔兰经销商",
            "2026-08-17T10:30+爱尔兰经销商",
            "version-20260817+爱尔兰经销商",
            "API key 1234567890abcdef+爱尔兰经销商",
            "token 1234567890abcdef+爱尔兰经销商",
            "871234567+爱尔兰经销商",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("bulk_customer_development", response["route"])
                self.assertEqual(["product_or_scope"], response["missing_fields"])
                self.assertNotIn("product_anchor", response)

    def test_business_routes_are_preserved_under_discovery_snapshot(self) -> None:
        cases = {
            "帮我找德国的工业传感器进口商": "bulk_customer_development",
            "调查 example.com 这家公司背景": "customer_background_research",
            "分析中国出口保温杯到越南的市场": "product_outbound_market_analysis",
        }
        for text, expected_route in cases.items():
            with self.subTest(text=text):
                response = classify(text)
                self.assertEqual("discovery_snapshot", response["interaction_mode"])
                self.assertEqual(expected_route, response["route"])

    def test_composite_business_request_returns_parent_and_isolated_subtasks(self) -> None:
        response = classify("调查 ABC GmbH，并分析保温杯出口德国的准入要求")

        self.assertEqual("composite_superleads_task", response["route"])
        self.assertEqual(
            ["customer_background_research", "product_outbound_market_analysis"],
            [item["route"] for item in response["subtasks"]],
        )
        self.assertFalse(response["split_customer_development"])

    def test_background_and_uploaded_table_stay_as_two_isolated_subtasks(self) -> None:
        response = classify("调查 ABC GmbH，并整理我上传的客户表")

        self.assertEqual("composite_superleads_task", response["route"])
        self.assertEqual(
            ["customer_background_research", "existing_table_enrichment"],
            [item["route"] for item in response["subtasks"]],
        )
        self.assertNotIn("bulk_customer_development", response["route_order"])

    def test_contact_scope_is_independent_for_a_single_company_request(self) -> None:
        response = classify("调查 ABC GmbH，并核查公开联系人")

        contact = next(item for item in response["subtasks"] if item["route"] == "contact_supplement")
        self.assertEqual([], contact["dependencies"])

    def test_table_contact_and_export_requests_are_detected_in_chinese_and_english(self) -> None:
        cases = (
            ("我上传了客户表，请核查公开联系人并导出", {"existing_table_enrichment", "contact_supplement", "export_delivery"}),
            ("Please enrich the attached client list, verify public contacts, and export it", {"existing_table_enrichment", "contact_supplement", "export_delivery"}),
        )
        for text, expected_routes in cases:
            with self.subTest(text=text):
                response = classify(text)
                self.assertEqual("composite_superleads_task", response["route"])
                self.assertEqual(expected_routes, {item["route"] for item in response["subtasks"]})

    def test_english_background_and_market_request_is_a_localized_composite(self) -> None:
        response = classify("Run a background check on ABC GmbH and analyze tariffs for mugs exported to Germany")

        self.assertEqual("composite_superleads_task", response["route"])
        self.assertEqual("en", response["language"])
        self.assertEqual("Scope and subtask status", response["parent_title"])
        self.assertEqual(
            ["customer_background_research", "product_outbound_market_analysis"],
            [item["route"] for item in response["subtasks"]],
        )
        self.assertNotIn("本次包含", "\n".join(response["response_lines"]))
        self.assertIn("Planning the public-information scope", "\n".join(response["response_lines"]))

    def test_composite_market_subtask_preserves_requested_module_scope(self) -> None:
        response = classify("调查 ABC GmbH，并查保温杯出口德国的关税")

        self.assertEqual("composite_superleads_task", response["route"])
        self.assertEqual(["import_tax"], response["analysis_modules_requested"])
        market = next(item for item in response["subtasks"] if item["route"] == "product_outbound_market_analysis")
        self.assertEqual(["import_tax"], market["analysis_modules_requested"])

    def test_customer_compliance_attribute_does_not_create_market_subtask(self) -> None:
        for text in (
            "帮我找需要 CE 认证的欧洲进口商",
            "找美国需要UL认证的进口商",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("bulk_customer_development", response["route"])
                self.assertEqual("using-superleads", response["next_skill"])
                self.assertEqual(
                    "shared/internal-stages/scoping-lead-research.md",
                    response["next_stage_reference"],
                )
                self.assertEqual([], response["secondary_routes"])
                self.assertNotIn("subtasks", response)

    def test_explicit_formal_intent_keeps_business_route(self) -> None:
        response = classify("给我一份德国工业传感器的正式开发名单")

        self.assertEqual("formal_research", response["interaction_mode"])
        self.assertEqual("bulk_customer_development", response["route"])
        self.assertEqual("formal_research", response["task_mode"])
        self.assertEqual("formal_report", response["delivery_mode"])
        self.assertNotIn("first_batch_candidate_target", response)
        self.assertNotIn("ask_expansion_after_first_batch", response)

    def test_english_explicit_formal_report_uses_formal_research_mode(self) -> None:
        response = classify("Give me a full report about example.com")

        self.assertEqual("formal_research", response["interaction_mode"])
        self.assertEqual("customer_background_research", response["route"])

    def test_single_market_module_does_not_expand_to_a_complete_report(self) -> None:
        response = classify("查中国出口保温杯到越南的关税")

        self.assertEqual("product_outbound_market_analysis", response["route"])
        self.assertEqual(["import_tax"], response["analysis_modules_requested"])
        text = "\n".join(response["response_lines"])
        self.assertIn("本轮范围：税费", text)
        self.assertIn("本轮未执行", text)
        self.assertNotIn("我会整理趋势、公开价格参考、准入、税费、出口要求、物流和外部因素", text)

    def test_english_tariff_request_uses_product_market_route(self) -> None:
        response = classify("Analyze the tariff for exporting kettles to the United States")

        self.assertEqual("product_outbound_market_analysis", response["route"])
        self.assertEqual(["import_tax"], response["analysis_modules_requested"])

    def test_explicit_complete_market_analysis_uses_all_modules(self) -> None:
        response = classify("做一份中国出口保温杯到越南的完整市场分析")

        self.assertEqual("formal_research", response["interaction_mode"])
        self.assertEqual("product_outbound_market_analysis", response["route"])
        self.assertEqual(
            [
                "market_trends",
                "public_price",
                "market_access",
                "import_tax",
                "export_requirements",
                "logistics",
                "external_factors",
            ],
            response["analysis_modules_requested"],
        )
        self.assertIn("完整市场分析", "\n".join(response["response_lines"]))

    def test_complete_market_report_requests_keep_market_route_and_formal_mode(self) -> None:
        for text in (
            "做中国保温杯出口越南的完整报告",
            "Give me a complete analysis of exporting mugs to Vietnam",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("formal_research", response["interaction_mode"])
                self.assertEqual("product_outbound_market_analysis", response["route"])

    def test_table_enrichment_or_export_intent_is_not_material_triage(self) -> None:
        for text in (
            "我上传了 Excel，请补全官网",
            "请把上传的 CSV 补全公开邮箱并导出",
            "I uploaded an Excel; enrich the company websites",
        ):
            with self.subTest(text=text):
                response = classify(text)

                self.assertEqual("discovery_snapshot", response["interaction_mode"])
                if "导出" in text:
                    self.assertEqual("composite_superleads_task", response["route"])
                    self.assertEqual(
                        ["existing_table_enrichment", "export_delivery"],
                        [item["route"] for item in response["subtasks"]],
                    )
                else:
                    self.assertEqual("existing_table_enrichment", response["route"])

    def test_ambiguous_market_request_asks_for_scope_without_promising_full_coverage(self) -> None:
        response = classify("分析中国出口保温杯到越南的市场")

        self.assertEqual("product_outbound_market_analysis", response["route"])
        self.assertEqual([], response["analysis_modules_requested"])
        text = "\n".join(response["response_lines"])
        self.assertIn("请说明本轮想了解", text)
        self.assertNotIn("我会整理趋势、公开价格参考、准入、税费、出口要求、物流和外部因素", text)

    def test_version_reader_uses_only_the_explicit_active_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active_root = root / "active"
            manifest = active_root / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"version": "1.2.3"}), encoding="utf-8")

            installed_cache = root / "installed-cache" / ".codex-plugin" / "plugin.json"
            installed_cache.parent.mkdir(parents=True)
            installed_cache.write_text(json.dumps({"version": "9.9.9"}), encoding="utf-8")

            self.assertEqual("1.2.3", read_active_plugin_version(active_root))
            self.assertIsNone(read_active_plugin_version(root / "missing"))

    def test_explicit_update_returns_structured_release_result_and_reuses_host_cache(self) -> None:
        cache: dict[str, object] = {}
        calls: list[bool] = []

        result = check_latest_version(
            lambda: calls.append(True) or {
                "version": "0.2.0",
                "source_kind": "github_release",
                "source_url": "https://github.com/fleixweb/superleads/releases/tag/v0.2.0",
            },
            cache,
            local_version="0.1.20",
            checked_at="2026-08-16T00:00:00Z",
        )

        self.assertEqual("update_available", result["status"])
        self.assertEqual("0.1.20", result["local_version"])
        self.assertEqual("0.2.0", result["remote_version"])
        self.assertEqual("github_release", result["source_kind"])
        self.assertTrue(result["stable"])
        self.assertEqual(1, len(calls))
        self.assertEqual(result, check_latest_version(None, cache, local_version="0.1.20"))

    def test_branch_manifest_is_repository_version_not_latest_stable(self) -> None:
        result = normalize_remote_version({"version": "0.2.0", "branch": "master"})

        self.assertEqual("repository_version", result["source_kind"])
        self.assertFalse(result["stable"])

    def test_branch_manifest_cannot_claim_a_stable_release(self) -> None:
        result = normalize_remote_version({
            "version": "0.2.0",
            "branch": "master",
            "source_kind": "github_release",
        })

        self.assertEqual("repository_version", result["source_kind"])
        self.assertFalse(result["stable"])

    def test_github_release_payload_with_tag_name_remains_a_stable_release(self) -> None:
        result = normalize_remote_version({
            "version": "0.2.0",
            "tag_name": "v0.2.0",
            "html_url": "https://github.com/fleixweb/superleads/releases/tag/v0.2.0",
        })

        self.assertEqual("github_release", result["source_kind"])
        self.assertTrue(result["stable"])

    def test_explicit_update_recognizes_command_and_github_version_requests(self) -> None:
        for text in (
            "@superleads update",
            "请检查 Superleads 的 GitHub 最新版本",
            "check the latest GitHub version of Superleads",
        ):
            with self.subTest(text=text):
                self.assertTrue(is_explicit_update_request(text))

    def test_failed_or_missing_explicit_check_is_structured_and_localized_by_caller(self) -> None:
        failed = check_latest_version(
            lambda: (_ for _ in ()).throw(RuntimeError("offline")),
            {},
            local_version="0.1.20",
            checked_at="2026-08-16T00:00:00Z",
        )
        not_checked = check_latest_version(None, None, local_version="0.1.20")

        self.assertEqual("check_failed", failed["status"])
        self.assertIsNone(failed["remote_version"])
        self.assertEqual("not_checked", not_checked["status"])
        self.assertEqual(LATEST_VERSION_UNCONFIRMED, failed["message_zh"])

    def test_cached_remote_result_is_recomputed_for_the_current_local_version(self) -> None:
        cache: dict[str, object] = {}
        first = check_latest_version(
            lambda: {"version": "0.2.0", "source_kind": "github_release"},
            cache,
            local_version="0.1.20",
        )
        second = check_latest_version(None, cache, local_version="0.3.0")

        self.assertEqual("update_available", first["status"])
        self.assertEqual("0.3.0", second["local_version"])
        self.assertEqual("up_to_date", second["status"])
        self.assertEqual("host_session_cache", second["cache_marker"])


if __name__ == "__main__":
    unittest.main()
