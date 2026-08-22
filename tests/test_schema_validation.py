#!/usr/bin/env python3
"""Regression tests for local JSON Schema resolution across jsonschema versions."""
from __future__ import annotations

import copy
import importlib.abc
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from schema_validation import SchemaResolutionError, schema_validation_errors


class SchemaValidationTest(unittest.TestCase):
    def test_default_research_graph_fixture_resolves_local_and_cross_schema_refs(self) -> None:
        graph = json.loads((ROOT / "shared/references/default-discovery-reference.example.json").read_text(encoding="utf-8"))
        self.assertEqual([], schema_validation_errors(graph, ROOT / "shared/schemas/research-graph.schema.json"))

    def test_invalid_enum_is_reported_as_a_schema_error(self) -> None:
        graph = json.loads((ROOT / "shared/references/default-discovery-reference.example.json").read_text(encoding="utf-8"))
        invalid = copy.deepcopy(graph)
        invalid["candidates"][0]["discovery_method"] = "not-a-supported-method"
        errors = schema_validation_errors(invalid, ROOT / "shared/schemas/research-graph.schema.json")
        self.assertTrue(any("discovery_method" in error["path"] for error in errors))
        self.assertTrue(any(error["kind"] == "schema_validation_failed" for error in errors))

    def test_invalid_local_ref_fails_with_a_clear_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema_path = Path(directory) / "broken.schema.json"
            schema_path.write_text(json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "https://superleads.local/schemas/broken.schema.json",
                "$ref": "#/$defs/DoesNotExist",
            }), encoding="utf-8")
            with self.assertRaises(SchemaResolutionError) as raised:
                schema_validation_errors({}, schema_path)
        self.assertIn("#/$defs/DoesNotExist", str(raised.exception))

    def test_missing_schema_dependencies_use_a_stable_neutral_message(self) -> None:
        class MissingSchemaDependencies(importlib.abc.MetaPathFinder):
            def find_spec(self, name: str, path: object = None, target: object = None) -> object:
                if name.split(".")[0] in {"jsonschema", "referencing"}:
                    raise ImportError(f"No module named '{name}'")
                return None

        finder = MissingSchemaDependencies()
        cached_modules = {
            name: module
            for name, module in list(sys.modules.items())
            if name.split(".")[0] in {"jsonschema", "referencing"}
        }
        for name in cached_modules:
            sys.modules.pop(name)
        sys.meta_path.insert(0, finder)
        try:
            with self.assertRaises(SchemaResolutionError) as raised:
                schema_validation_errors({}, ROOT / "shared/schemas/run.schema.json")
        finally:
            sys.meta_path.remove(finder)
            sys.modules.update(cached_modules)

        message = str(raised.exception)
        self.assertEqual("补充形状校验档案不可用", message)
        for forbidden in ("jsonschema", "requirements.txt", "pip", "安装", "解释器", "venv", "PYTHONPATH"):
            self.assertNotIn(forbidden, message)

    def test_dependency_declaration_covers_schema_and_xlsx_runtime_dependencies(self) -> None:
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertRegex(requirements, r"(?m)^jsonschema(==|>=4\.18)")
        self.assertRegex(requirements, r"(?m)^referencing(==|>=0\.30)")
        self.assertRegex(requirements, r"(?m)^openpyxl(==|>=3\.1)")


if __name__ == "__main__":
    unittest.main()
