#!/usr/bin/env python3
"""Runtime error output must not expose implementation details."""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_product_market_collection_pipeline as pipeline


class PipelineErrorDisclosureTest(unittest.TestCase):
    def test_load_and_runtime_failures_use_neutral_messages(self) -> None:
        forbidden = (
            re.compile(r"(?i)\bjsonschema\b"),
            re.compile(r"(?i)\brequirements\.txt\b"),
            re.compile(r"(?i)\bpip(?:\s+install)?\b"),
            re.compile(r"解释器"),
            re.compile(r"(?i)\bvenv\b"),
            re.compile(r"(?i)\bPYTHONPATH\b"),
        )

        for failure_stage, patch_target in (("load", "load_market_fixture"), ("runtime", "build_pipeline_result")):
            with self.subTest(stage=failure_stage):
                stdout = io.StringIO()
                patchers = [
                    patch.object(pipeline, patch_target, side_effect=RuntimeError("jsonschema package missing")),
                    patch.object(pipeline, "_load_json_object", return_value={}),
                ]
                if failure_stage == "runtime":
                    patchers.append(patch.object(pipeline, "load_market_fixture", return_value={}))
                with (
                    patchers[0],
                    patchers[1],
                    patchers[2] if len(patchers) > 2 else contextlib.nullcontext(),
                    patch.object(
                        sys,
                        "argv",
                        [
                            "run_product_market_collection_pipeline.py",
                            "--graph",
                            "graph.json",
                            "--collection-input",
                            "collection.json",
                            "--output",
                            "merged.json",
                        ],
                    ),
                    contextlib.redirect_stdout(stdout),
                ):
                    return_code = pipeline.main()

                self.assertEqual(1, return_code)
                payload = json.loads(stdout.getvalue())
                self.assertFalse(payload["ok"])
                self.assertEqual(failure_stage, payload["stage"])
                rendered = stdout.getvalue()
                for pattern in forbidden:
                    self.assertIsNone(pattern.search(rendered), pattern.pattern)


if __name__ == "__main__":
    unittest.main()
