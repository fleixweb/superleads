#!/usr/bin/env python3
"""Regression coverage for the product-market evidence compiler."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evals" / "fixtures"
COMPILER = ROOT / "scripts" / "compile_product_market_evidence.py"
VALIDATOR = ROOT / "scripts" / "validate_product_market_analysis.py"


def materialize_fixture(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "extends" not in payload:
        return payload
    sys.path.insert(0, str(ROOT / "evals"))
    from run_evals import _load_fixture_graph  # type: ignore[import-not-found]

    return _load_fixture_graph(path)


class ProductMarketEvidenceCompilerTest(unittest.TestCase):
    maxDiff = None

    def _compile(self, graph: dict[str, object], notes: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            graph_path = tmp_path / "graph.json"
            notes_path = tmp_path / "notes.json"
            output_path = tmp_path / "compiled.json"
            graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
            notes_path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(COMPILER), "--graph", str(graph_path), "--notes", str(notes_path), "--output", str(output_path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            result.output_path = output_path  # type: ignore[attr-defined]
            result.compiled_graph = json.loads(output_path.read_text(encoding="utf-8")) if output_path.exists() else None  # type: ignore[attr-defined]
            return result

    def test_compiles_opened_observation_and_preserves_known_product_attribute(self) -> None:
        graph = materialize_fixture(FIXTURES / "market_pass_xingheng_minimum_boundary.json")
        notes = {
            "product_attributes": [
                {
                    "attribute_name": "额定功率",
                    "value": "1500",
                    "unit": "W",
                    "status": "preliminary_reference",
                    "trigger_paths": ["产品规格核验"],
                }
            ],
            "evidence_notes": [
                {
                    "evidence_note_id": "note-xh-opened-voltage",
                    "observation_id": "observation-xh-product-spec",
                    "field_domain": "产品属性",
                    "field_name": "公开额定电压",
                    "current_value": "48 V",
                    "status": "preliminary_reference",
                    "source_excerpt_quote": "48 V",
                    "applicability_scope": "仅限已打开的 Xing Heng 产品页，不扩大到其它型号。",
                    "supports": ["页面原文包含 48 V。"],
                    "does_not_support": ["不能作为最终目的国合规结论。"],
                    "boundary_rule_ids": ["EB-LB-02"],
                    "row": {
                        "sheet_name": "产品档案与触发项",
                        "row_topic": "公开规格摘录：额定电压",
                        "user_visible_cells": {
                            "属性": "额定电压",
                            "当前值": "48 V",
                            "依据说明": "来自本轮已打开产品页。",
                            "不能推出什么": "不能作为最终目的国合规结论。",
                        },
                    },
                }
            ],
        }

        result = self._compile(graph, notes)

        self.assertEqual(result.returncode, 0, result.stdout)
        compiled = result.compiled_graph  # type: ignore[attr-defined]
        self.assertIsInstance(compiled, dict)
        self.assertIn(
            {"attribute_name": "额定功率", "value": "1500", "unit": "W"},
            [
                {key: item.get(key) for key in ("attribute_name", "value", "unit")}
                for item in compiled["attributes"]
            ],
        )
        self.assertIn("card-note-xh-opened-voltage", {item["evidence_card_id"] for item in compiled["evidence_cards"]})
        self.assertIn("row-note-xh-opened-voltage", {item["matrix_row_id"] for item in compiled["matrix_rows"]})

        with tempfile.TemporaryDirectory() as tmp:
            compiled_path = Path(tmp) / "compiled.json"
            compiled_path.write_text(json.dumps(compiled, ensure_ascii=False, indent=2), encoding="utf-8")
            validation = subprocess.run(
                [sys.executable, str(VALIDATOR), str(compiled_path)],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        self.assertEqual(validation.returncode, 0, validation.stdout)

    def test_rejects_evidence_note_for_unopened_observation(self) -> None:
        graph = materialize_fixture(FIXTURES / "market_pass_origin_proof_unable_to_verify_source_limited.json")
        notes = {
            "evidence_notes": [
                {
                    "evidence_note_id": "note-unopened-origin",
                    "observation_id": "observation-us-origin-proof-not-opened",
                    "field_domain": "origin_proof_requirement",
                    "field_name": "COO 要求",
                    "current_value": "未核实",
                    "status": "source_restricted",
                    "source_excerpt_quote": "规则",
                    "applicability_scope": "United States",
                    "supports": [],
                    "does_not_support": ["未打开来源不能形成目标国规则结论。"],
                    "boundary_rule_ids": ["EB-ORIGIN-01"],
                    "row": {
                        "sheet_name": "产品准入与合规要求",
                        "row_topic": "COO 要求",
                        "user_visible_cells": {"规则结论": "本轮未核实"},
                    },
                }
            ]
        }

        result = self._compile(graph, notes)

        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("market_evidence_compiler_observation_not_opened", result.stdout)


if __name__ == "__main__":
    unittest.main()
