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


if __name__ == "__main__":
    unittest.main()
