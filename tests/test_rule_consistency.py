"""Deterministic checks for shared rule ownership and no-script delivery semantics."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_superleads_rule_consistency import check_rule_consistency  # noqa: E402


class RuleConsistencyTest(unittest.TestCase):
    def test_no_script_contract_and_consumers_are_consistent(self) -> None:
        issues = check_rule_consistency(ROOT)
        self.assertEqual([], issues)

    def test_bulk_markdown_templates_are_packaged_authorities(self) -> None:
        l1 = ROOT / "shared" / "references" / "bulk-customer-development-l1-template.md"
        l2 = ROOT / "shared" / "references" / "bulk-customer-development-l2-template.md"
        ownership = (ROOT / "shared" / "references" / "rule-ownership.md").read_text(encoding="utf-8")

        self.assertTrue(l1.is_file())
        self.assertTrue(l2.is_file())
        self.assertIn("L1 用户可见 Markdown 版式", ownership)
        self.assertIn("bulk-customer-development-l1-template.md", ownership)
        self.assertIn("L2 用户可见 Markdown 版式", ownership)
        self.assertIn("bulk-customer-development-l2-template.md", ownership)

    def test_l2_template_matches_standard_exporter_contact_and_review_headers(self) -> None:
        template = (ROOT / "shared" / "references" / "bulk-customer-development-l2-template.md").read_text(encoding="utf-8")
        self.assertIn(
            "| 公司名称 | 联系方式类型 | 联系方式 | 原文 | 联系人 | 职位/部门 | 状态 | 来源上下文 | 归属证据 | 来源说明 | 来源链接 | 需人工核查说明 |",
            template,
        )
        self.assertIn(
            "| 说明 | 公司名称 | 公开信息状态 | 待核查事项 | 需人工核查 | 方向状态 |",
            template,
        )


if __name__ == "__main__":
    unittest.main()
