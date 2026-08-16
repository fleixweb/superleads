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

from route_superleads_intake import classify
from superleads_task_modes import (
    LATEST_VERSION_UNCONFIRMED,
    check_latest_version,
    classify_task_mode,
    read_active_plugin_version,
)


class SuperleadsTaskModesTest(unittest.TestCase):
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

    def test_product_market_document_requirements_are_not_material_triage(self) -> None:
        response = classify("48V锂电池到沙特要 SABER 吗，清关还要什么文件")

        self.assertEqual("discovery_snapshot", response["interaction_mode"])
        self.assertEqual("product_outbound_market_analysis", response["route"])

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

    def test_explicit_formal_intent_keeps_business_route(self) -> None:
        response = classify("给我一份德国工业传感器的正式开发名单")

        self.assertEqual("formal_research", response["interaction_mode"])
        self.assertEqual("bulk_customer_development", response["route"])

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

    def test_explicit_update_check_is_injected_cached_and_fails_closed(self) -> None:
        calls: list[str] = []
        session_cache: dict[str, str] = {}

        def fetch() -> str:
            calls.append("fetch")
            return "1.2.4"

        self.assertEqual("1.2.4", check_latest_version(fetch, session_cache))
        self.assertEqual("1.2.4", check_latest_version(fetch, session_cache))
        self.assertEqual(["fetch"], calls)
        self.assertEqual(
            LATEST_VERSION_UNCONFIRMED,
            check_latest_version(lambda: (_ for _ in ()).throw(RuntimeError("offline")), {}),
        )


if __name__ == "__main__":
    unittest.main()
