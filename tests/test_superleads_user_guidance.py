#!/usr/bin/env python3
"""Regression coverage for static Superleads first-use guidance."""
from __future__ import annotations

import os
import re
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import mock_open, patch
from urllib import request as urllib_request


ROOT = Path(__file__).resolve().parents[1]
GUIDANCE_REFERENCE = ROOT / "shared" / "references" / "superleads-user-guidance.md"
PUBLIC_BATCH_SKILL = ROOT / "skills" / "using-superleads" / "SKILL.md"
PUBLIC_BATCH_AGENT = ROOT / "skills" / "using-superleads" / "agents" / "openai.yaml"
MODEL_CONTROL_START = "<!-- superleads-model-control:start -->"
MODEL_CONTROL_END = "<!-- superleads-model-control:end -->"
USER_VISIBLE_GUIDE_START = "<!-- superleads-user-visible-guide:start -->"
USER_VISIBLE_GUIDE_END = "<!-- superleads-user-visible-guide:end -->"
sys.path.insert(0, str(ROOT / "scripts"))

import superleads_user_guidance
from validate_superleads_user_visible_output import validate as validate_user_visible_output


class SuperleadsUserGuidanceTest(unittest.TestCase):
    def test_public_batch_entry_declares_bare_activation_before_research_references(self) -> None:
        skill = PUBLIC_BATCH_SKILL.read_text(encoding="utf-8")
        agent = PUBLIC_BATCH_AGENT.read_text(encoding="utf-8")

        self.assertLess(skill.index("## 裸启动"), skill.index("## 执行边界"))
        self.assertIn("不要调用 shell", skill)
        # Both static guides are intentionally inlined to avoid a high-latency
        # host tool round trip; do not reintroduce a byte budget that forces a
        # reference read back into either path.
        self.assertIn("## 详细帮助", skill)
        self.assertIn("bare @ activation", agent)

    def test_static_help_recognizes_supported_prompts(self) -> None:
        for text, language in (
            ("@superleads", "zh"),
            ("你能干嘛？", "zh"),
            ("Superleads 能做什么？", "zh"),
            ("Superleads 怎么用？", "zh"),
            ("新手入门", "zh"),
            ("What can you do?", "en"),
            ("What can Superleads do?", "en"),
            ("How to use Superleads?", "en"),
            ("Superleads help", "en"),
        ):
            with self.subTest(text=text):
                response = superleads_user_guidance.static_help_response(text)
                self.assertIsNotNone(response)
                self.assertEqual("first_use_guide", response["route"])
                expected_contract = "static_compact_help" if text in {"@superleads"} else "static_first_use_help"
                if expected_contract == "static_compact_help":
                    self.assertIsNone(response["next_skill"])
                else:
                    self.assertEqual("using-superleads", response["next_skill"])
                self.assertEqual(expected_contract, response["response_contract"])
                self.assertEqual(language, response["language"])
                self.assertEqual("metadata", response["interaction_mode"])
                expected_reference = None if expected_contract == "static_compact_help" else "shared/references/superleads-user-guidance.md"
                self.assertEqual(expected_reference, response["guidance_reference"])
                self.assertEqual([], response["operations"])
                self.assertTrue(response["response_lines"])

    def test_empty_input_returns_the_zh_bare_help_block(self) -> None:
        for text in ("", "   "):
            with self.subTest(text=repr(text)):
                response = superleads_user_guidance.static_help_response(text)
                self.assertIsNotNone(response)
                self.assertEqual("zh", response["language"])
                self.assertEqual("static_compact_help", response["response_contract"])
                self.assertIn("批量开发客户", "\n".join(response["response_lines"]))

    def test_static_help_does_not_intercept_real_tasks(self) -> None:
        for text in (
            "帮我开发美国保温杯客户",
            "调查 Chilly's Bottles 的背景",
            "Analyze the US market for electric kettles",
        ):
            with self.subTest(text=text):
                self.assertIsNone(superleads_user_guidance.static_help_response(text))

    def test_static_help_returns_a_compact_user_visible_guide(self) -> None:
        response = superleads_user_guidance.static_help_response("@superleads")
        self.assertIsNotNone(response)
        guide = "\n".join(response["response_lines"])

        for expected in (
            "批量开发客户",
            "单一客户背调",
            "目标市场分析",
            "Superleads 支持",
            "https://github.com/fleixweb/superleads/issues",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)
        self.assertNotIn("更多用法", guide)
        self.assertTrue(guide.rstrip().endswith("请勿提交密码、API Key 或未经脱敏的客户敏感资料。"))

    def test_bare_skill_inlines_exact_compact_guidance_in_both_languages(self) -> None:
        skill = PUBLIC_BATCH_SKILL.read_text(encoding="utf-8")

        for language in ("zh", "en"):
            with self.subTest(language=language):
                start = f"<!-- superleads-user-visible-guide:{language}:start -->"
                end = f"<!-- superleads-user-visible-guide:{language}:end -->"
                self.assertIn(start, skill)
                self.assertIn(end, skill)
                marked_section = skill.split(start, 1)[1].split(end, 1)[0]
                code_block = re.fullmatch(r"\s*```markdown\n(.*?)\n```\s*", marked_section, re.DOTALL)
                self.assertIsNotNone(code_block)
                inline = code_block.group(1)
                self.assertNotIn("<!--", inline)
                self.assertNotIn("-->", inline)
                rendered = "\n".join(superleads_user_guidance._compact_guide_lines(language))
                self.assertEqual(rendered, inline)

    def test_detailed_help_skill_inlines_exact_full_guidance_in_both_languages(self) -> None:
        skill = PUBLIC_BATCH_SKILL.read_text(encoding="utf-8")
        detailed_help = skill.split("## 详细帮助", 1)[1].split("## 路由", 1)[0]

        for language in ("zh", "en"):
            with self.subTest(language=language):
                rendered = "\n".join(superleads_user_guidance._guide_lines(language))
                self.assertIn(f"```markdown\n{rendered}\n```", detailed_help)
                self.assertNotIn("<!--", rendered)
                self.assertNotIn("-->", rendered)
                self.assertIn("更多用法" if language == "zh" else "More ways to use Superleads", rendered)

    def test_detailed_help_projection_check_detects_content_model_drift(self) -> None:
        skill = PUBLIC_BATCH_SKILL.read_text(encoding="utf-8")
        detailed_help = skill.split("## 详细帮助", 1)[1].split("## 路由", 1)[0]
        inline = "\n".join(superleads_user_guidance._guide_lines("zh"))
        self.assertIn(f"```markdown\n{inline}\n```", detailed_help)

        with patch.dict(
            superleads_user_guidance._GUIDE_CONTENT["zh"],
            {"more_items": ("用于证明一致性测试会拦住内容漂移。",)},
        ):
            drifted = "\n".join(superleads_user_guidance._guide_lines("zh"))
        self.assertNotEqual(inline, drifted)
        self.assertNotIn(f"```markdown\n{drifted}\n```", detailed_help)

    def test_bare_skill_path_needs_no_script_or_reference_read(self) -> None:
        skill = PUBLIC_BATCH_SKILL.read_text(encoding="utf-8")
        bare_section = skill.split("## 裸启动", 1)[1].split("## 详细帮助", 1)[0]

        self.assertIn("逐字返回下方对应代码块内的全部内容", bare_section)
        self.assertNotRegex(bare_section, r"scripts/[^\s`]+\.py")
        self.assertNotIn("../../shared/references/", bare_section)

    def test_detailed_help_is_opt_in(self) -> None:
        response = superleads_user_guidance.static_help_response("你能干嘛？")
        self.assertIsNotNone(response)
        self.assertEqual("static_first_use_help", response["response_contract"])
        self.assertEqual("using-superleads", response["next_skill"])
        guide = "\n".join(response["response_lines"])
        self.assertIn("更多用法", guide)
        self.assertIn("产品关键词 + 目标市场 + 客户类型", guide)

    def test_bare_at_alias_is_the_minimal_static_path(self) -> None:
        response = superleads_user_guidance.static_help_response("@")
        self.assertIsNotNone(response)
        self.assertEqual("static_compact_help", response["response_contract"])
        self.assertIsNone(response["next_skill"])
        self.assertTrue(response["fast_path"])
        self.assertLess(response["elapsed_seconds"], 0.25)
        self.assertEqual([], response["operations"])

    def test_english_static_help_returns_english_user_visible_guide(self) -> None:
        response = superleads_user_guidance.static_help_response("What can Superleads do?")
        self.assertIsNotNone(response)
        guide = "\n".join(response["response_lines"])

        for expected in (
            "Batch customer development",
            "Single-customer background research",
            "Target market analysis",
            "More ways to use Superleads",
            "Superleads Support",
            "https://github.com/fleixweb/superleads/issues",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, guide)
        self.assertNotIn("## 批量开发客户", guide)

    def test_footer_is_idempotent_and_contains_support_and_safety(self) -> None:
        footer_once = superleads_user_guidance.append_final_footer("交付内容")
        footer_twice = superleads_user_guidance.append_final_footer(footer_once)

        self.assertEqual(footer_once, footer_twice)
        self.assertTrue(superleads_user_guidance.has_exactly_one_final_footer(footer_twice))
        self.assertIn("https://github.com/fleixweb/superleads/issues", footer_twice)
        self.assertIn("小红书搜索 Fleixweb", footer_twice)
        self.assertNotIn("<!--", footer_twice)
        self.assertNotIn("-->", footer_twice)

    def test_chinese_footer_uses_an_explicit_markdown_link_boundary(self) -> None:
        footer = superleads_user_guidance._canonical_footer("zh")
        expected = (
            "欢迎通过 [GitHub Issues](https://github.com/fleixweb/superleads/issues) 反馈，"
            "或在小红书搜索 Fleixweb 联系 Fleix。"
        )

        self.assertIn(expected, footer)
        self.assertNotIn("GitHub Issues（https://", footer)
        link = re.search(r"\[([^]]+)]\((https://[^)]+)\)", footer)
        self.assertIsNotNone(link)
        self.assertEqual("GitHub Issues", link.group(1))
        self.assertEqual("https://github.com/fleixweb/superleads/issues", link.group(2))
        self.assertTrue(footer[link.end() :].startswith(" 反馈，或在小红书搜索 Fleixweb 联系 Fleix。"))

    def test_user_visible_prose_has_no_bare_url_next_to_fullwidth_punctuation(self) -> None:
        roots = (
            ROOT / "scripts",
            ROOT / "skills",
            ROOT / "shared",
            ROOT / "evals" / "user_visible_outputs",
            ROOT / "docs" / "superpowers" / "specs",
        )
        unsafe = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'*+,;=%-]+[）。，、；：！？]")
        failures: list[str] = []

        for root in roots:
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".py", ".json", ".yaml", ".yml"}:
                    if unsafe.search(path.read_text(encoding="utf-8")):
                        failures.append(str(path.relative_to(ROOT)))

        self.assertEqual([], failures)

    def test_english_footer_is_localized_without_changing_its_meaning(self) -> None:
        footer = superleads_user_guidance.append_final_footer("Delivery", language="en")

        self.assertIn("## Superleads Support", footer)
        self.assertIn("https://github.com/fleixweb/superleads/issues", footer)
        self.assertIn("search Xiaohongshu for Fleixweb", footer)
        self.assertIn("Do not submit passwords, API keys, or customer sensitive data that has not been de-identified.", footer)
        self.assertNotIn("## Superleads 支持", footer)
        self.assertTrue(superleads_user_guidance.has_exactly_one_final_footer(footer))

    def test_static_guidance_never_reads_files_or_network(self) -> None:
        guide = GUIDANCE_REFERENCE.read_text(encoding="utf-8")
        file_open = mock_open(read_data=guide)
        with (
            patch("builtins.open", file_open),
            patch("socket.create_connection") as create_connection,
            patch.object(urllib_request, "urlopen") as urlopen,
        ):
            response = superleads_user_guidance.static_help_response("你能干嘛？")
            completed = superleads_user_guidance.append_final_footer("交付内容")
            self.assertTrue(superleads_user_guidance.has_exactly_one_final_footer(completed))

        self.assertEqual("first_use_guide", response["route"])
        file_open.assert_not_called()
        create_connection.assert_not_called()
        urlopen.assert_not_called()

    def test_footer_works_after_the_current_directory_changes(self) -> None:
        original_directory = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as directory:
                os.chdir(directory)
                try:
                    completed = superleads_user_guidance.append_final_footer("交付内容")
                except FileNotFoundError as error:
                    self.fail(f"terminal footer must not depend on the current directory: {error}")
        finally:
            os.chdir(original_directory)

        self.assertTrue(superleads_user_guidance.has_exactly_one_final_footer(completed))

    def test_footer_rejects_legacy_comments_incomplete_or_nonterminal_content(self) -> None:
        marker = superleads_user_guidance.SUPPORT_FOOTER_MARKER
        for text in (
            "交付内容\n\n" + marker,
            "交付内容\n\n" + marker + "\n\n---\nSuperleads 支持",
            superleads_user_guidance.append_final_footer("交付内容") + "\n额外内容",
        ):
            with self.subTest(text=text):
                self.assertFalse(superleads_user_guidance.has_exactly_one_final_footer(text))
                with self.assertRaises(ValueError):
                    superleads_user_guidance.append_final_footer(text)

    def test_progress_and_standalone_clarification_do_not_carry_a_footer(self) -> None:
        for text in (
            "正在整理公开来源，请稍候。",
            "请确认目标市场是德国还是整个欧盟。",
        ):
            with self.subTest(text=text):
                self.assertNotIn(superleads_user_guidance.SUPPORT_FOOTER_MARKER, text)
                self.assertFalse(superleads_user_guidance.has_exactly_one_final_footer(text))

    def test_user_visible_validator_requires_one_terminal_footer(self) -> None:
        report = (ROOT / "evals" / "user_visible_outputs" / "bulk_customer_development_us_generator_aftermarket.md").read_text(encoding="utf-8")
        completed = superleads_user_guidance.append_final_footer(report)
        footer = superleads_user_guidance._canonical_footer("zh")
        footer_index = completed.index(footer)
        missing = completed[:footer_index].rstrip() + "\n"
        duplicated = completed + "\n" + completed[footer_index:]

        missing_codes = {
            issue["code"]
            for issue in validate_user_visible_output(missing, "bulk_customer_development", min_tables=7)
        }
        duplicated_codes = {
            issue["code"]
            for issue in validate_user_visible_output(duplicated, "bulk_customer_development", min_tables=7)
        }
        self.assertIn("user_visible_support_footer_missing", missing_codes)
        self.assertIn("user_visible_support_footer_duplicated", duplicated_codes)

    def test_user_visible_validator_rejects_html_comment_delimiters(self) -> None:
        terminal_report = (ROOT / "evals" / "user_visible_outputs" / "bulk_customer_development_us_generator_aftermarket.md").read_text(encoding="utf-8")
        bare_guide = "# Superleads\n\n<!-- internal guide delimiter\n\n开始使用"

        for text, route, min_tables in (
            (bare_guide, "product_outbound_market_analysis", 0),
            (terminal_report + "\ninternal footer delimiter -->\n", "bulk_customer_development", 7),
        ):
            with self.subTest(route=route):
                codes = {
                    issue["code"]
                    for issue in validate_user_visible_output(text, route, min_tables=min_tables)
                }
                self.assertIn("user_visible_html_comment", codes)

    def test_shared_reference_assigns_bare_copy_to_skill_and_rendering_to_python(self) -> None:
        reference = GUIDANCE_REFERENCE.read_text(encoding="utf-8")
        source = (ROOT / "scripts" / "superleads_user_guidance.py").read_text(encoding="utf-8")

        self.assertIn("唯一业务内容模型", reference)
        self.assertIn("程序化渲染", reference)
        self.assertNotIn("裸启动正文归", reference)
        self.assertNotIn("static_help_response()", reference)
        self.assertIn("静态引导", reference)
        self.assertIn("append_final_footer()", reference)
        self.assertNotIn("## Superleads 支持", reference)
        self.assertNotIn("https://github.com/fleixweb/superleads/issues", reference)
        self.assertIn("_GUIDE_CONTENT", source)
        self.assertIn("Batch customer development", source)
        self.assertIn("批量开发客户", source)

    def test_internal_stage_references_cannot_be_used_as_a_capability_list(self) -> None:
        paths = (
            ROOT / "shared" / "references" / "route-map.md",
            ROOT / "shared" / "references" / "batch-discovery-execution.md",
            PUBLIC_BATCH_SKILL,
        )
        paragraphs = []
        for path in paths:
            paragraphs.extend(
                paragraph
                for paragraph in path.read_text(encoding="utf-8").split("\n\n")
                if "shared/internal-stages/" in paragraph
            )

        self.assertEqual(4, len(paragraphs))
        for paragraph in paragraphs:
            with self.subTest(paragraph=paragraph):
                self.assertIn("不得枚举", paragraph)
                self.assertIn("用户可见的功能清单", paragraph)
                self.assertRegex(paragraph, r"帮助|能力类问题")

    def test_python_uses_one_structured_content_model_without_file_reads(self) -> None:
        source = (ROOT / "scripts" / "superleads_user_guidance.py").read_text(encoding="utf-8")
        self.assertIn("superleads-user-guidance.md", source)
        self.assertIn("_GUIDE_CONTENT", source)
        self.assertNotIn("open(GUIDANCE_REFERENCE", source)

    def test_final_delivery_skills_reference_the_shared_guidance(self) -> None:
        required_terminal_rules = {
            ROOT / "skills" / "using-superleads" / "SKILL.md": "终局交付才附",
            ROOT / "skills" / "analyzing-product-outbound-market" / "SKILL.md": "终局能力受限说明",
            ROOT / "skills" / "researching-customer-background" / "SKILL.md": "final customer background report follows those rules",
            ROOT / "shared" / "internal-stages" / "exporting-lead-workbooks.md": "Completed CSV/XLSX and chat-readable exports follow the shared footer rules",
            ROOT / "shared" / "internal-stages" / "collecting-contact-intelligence.md": "final public-contact check follows those rules",
        }
        for path, required_rule in required_terminal_rules.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertIn("../../shared/references/superleads-user-guidance.md", text)
                if path == PUBLIC_BATCH_SKILL:
                    self.assertEqual(4, text.count("https://github.com/fleixweb/superleads/issues"))
                else:
                    self.assertNotIn("https://github.com/fleixweb/superleads/issues", text)
                self.assertIn(required_rule, text)
                self.assertTrue(
                    "standalone clarifications do not append the footer" in text
                    or ("进度" in text and "澄清" in text and "不附" in text)
                )

    def test_exposed_prompt_uses_the_three_user_business_entries(self) -> None:
        agent = (ROOT / "skills" / "using-superleads" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        plugin = (ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        for label in ("批量开发客户", "单一客户背调", "目标市场分析"):
            self.assertIn(label, agent + plugin)

    def test_guidance_has_no_side_effects(self) -> None:
        self.assertEqual([], superleads_user_guidance.guidance_side_effects())


if __name__ == "__main__":
    unittest.main()
