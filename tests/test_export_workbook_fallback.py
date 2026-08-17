#!/usr/bin/env python3
"""Regression coverage for dependency-free workbook delivery fallback."""
from __future__ import annotations

import builtins
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import export_workbook


class ExportWorkbookFallbackTest(unittest.TestCase):
    def test_auto_export_explains_csv_fallback_when_openpyxl_is_unavailable(self) -> None:
        fixture = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"
        original_import = builtins.__import__

        def missing_openpyxl(name: str, *args: object, **kwargs: object) -> object:
            if name == "openpyxl":
                raise ModuleNotFoundError("No module named 'openpyxl'")
            return original_import(name, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "export"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("builtins.__import__", side_effect=missing_openpyxl), patch.object(
                sys,
                "argv",
                [
                    "export_workbook.py",
                    str(fixture),
                    "--output-dir",
                    str(output),
                    "--mode",
                    "background",
                    "--format",
                    "auto",
                ],
            ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                result = export_workbook.main()

            self.assertEqual(0, result)
            payload = json.loads(stdout.getvalue())
            self.assertEqual("csv", payload["format"])
            self.assertIn("XLSX export unavailable", stderr.getvalue())
            self.assertIn("UTF-8-SIG CSV", stderr.getvalue())
            self.assertTrue(list(output.glob("*.csv")))
            self.assertFalse(list(output.glob("*.xlsx")))


if __name__ == "__main__":
    unittest.main()
