#!/usr/bin/env python3
"""Regression coverage for complete deep-verification delivery signals."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from html import unescape
from zipfile import ZipFile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_workbook import (
    build_initial_sheets,
    public_enrichment_empty_sheet_statuses,
    write_csv_sheets,
    write_xlsx_sheets,
)


FIXTURE = ROOT / "evals" / "fixtures" / "pass_default_discovery_candidate_pool.json"


class DeepVerifyCompletenessTest(unittest.TestCase):
    def test_empty_signal_sheet_reports_status_not_recorded_in_csv_and_xlsx(self) -> None:
        sheets = {"社媒与公开职业线索": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            write_csv_sheets(sheets, output)
            with (output / "社媒与公开职业线索.csv").open(encoding="utf-8-sig", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))

            write_xlsx_sheets(sheets, output, "signals.xlsx")
            with ZipFile(output / "signals.xlsx") as workbook:
                xlsx_sheet = unescape(workbook.read("xl/worksheets/sheet1.xml").decode("utf-8"))

        self.assertEqual([{"说明": "状态未记录"}], csv_rows)
        self.assertIn("状态未记录", xlsx_sheet)

    def test_empty_graph_fact_sheets_report_no_records_across_all_modes(self) -> None:
        fact_sheets_by_mode = {
            "initial": (
                "发现候选池",
                "联系方式汇总",
                "官网与来源链接",
                "搜索覆盖与收敛",
                "待核查事项",
                "已排除客户",
                "风险与说明",
            ),
            "standard": (
                "客户信息总表",
                "联系方式汇总",
                "公开信息与待核查事项",
                "官网与来源链接",
                "待核查事项",
                "风险与说明",
            ),
            "full": (
                "开发需求",
                "关键词与搜索思路",
                "发现候选池",
                "客户信息总表",
                "联系方式汇总",
                "公开信息与待核查事项",
                "官网与来源链接",
                "待核查事项",
                "已排除客户",
                "检查说明",
            ),
            "inquiry": (
                "询盘待办",
                "来信联系人",
                "询盘信息摘要",
                "待补充信息",
                "来源说明",
            ),
            "background": (
                "客户一眼看懂",
                "客户、品牌与关联方",
                "公开业务信号与待核验事项",
                "公开联系入口与关联依据",
                "待核验事项与来源限制",
                "信息从哪里来",
                "疑似进出口记录（第三方聚合，待核实）",
            ),
        }
        sheets = {
            sheet: []
            for mode_sheets in fact_sheets_by_mode.values()
            for sheet in mode_sheets
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            write_csv_sheets(sheets, output)
            for mode, mode_sheets in fact_sheets_by_mode.items():
                for sheet in mode_sheets:
                    with self.subTest(format="csv", mode=mode, sheet=sheet):
                        with (output / f"{sheet}.csv").open(encoding="utf-8-sig", newline="") as handle:
                            rows = list(csv.DictReader(handle))
                        self.assertEqual([{"说明": "本轮无此类记录"}], rows)
                        self.assertNotIn("状态未记录", rows[0]["说明"])

            representative_sheets = {
                mode_sheets[0]: []
                for mode_sheets in fact_sheets_by_mode.values()
            }
            write_xlsx_sheets(representative_sheets, output, "fact-sheets.xlsx")
            with ZipFile(output / "fact-sheets.xlsx") as workbook:
                xlsx_text = "\n".join(
                    unescape(workbook.read(name).decode("utf-8"))
                    for name in workbook.namelist()
                    if name.startswith("xl/worksheets/sheet")
                )

        self.assertIn("本轮无此类记录", xlsx_text)
        self.assertNotIn("状态未记录", xlsx_text)

    def test_recorded_signal_states_remain_distinct_in_csv_and_xlsx(self) -> None:
        graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for candidate in graph["candidates"]:
            summary = candidate["signal_summary"]
            summary["social_company"]["collection_status"] = "not_searched"
            summary["social_person"]["collection_status"] = "not_searched"
            summary["map_listing"]["collection_status"] = "searched_not_found"
            summary["trade_record"]["collection_status"] = "details_restricted"

        sheets = build_initial_sheets(graph, {"issues": []})
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            write_csv_sheets(sheets, output)
            social_csv = (output / "社媒与公开职业线索.csv").read_text(encoding="utf-8-sig")
            map_csv = (output / "地图与经营地址.csv").read_text(encoding="utf-8-sig")
            trade_csv = (output / "第三方贸易摘要.csv").read_text(encoding="utf-8-sig")

            write_xlsx_sheets(sheets, output, "signals.xlsx")
            with ZipFile(output / "signals.xlsx") as workbook:
                xlsx_text = "\n".join(
                    unescape(workbook.read(name).decode("utf-8"))
                    for name in workbook.namelist()
                    if name.startswith("xl/worksheets/sheet")
                )

        for value in ("本轮未检索", "已检索未见", "来源受限"):
            with self.subTest(value=value):
                self.assertIn(value, social_csv + map_csv + trade_csv)
                self.assertIn(value, xlsx_text)

    def test_empty_signal_sheets_use_recorded_collection_statuses(self) -> None:
        graph = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for candidate in graph["candidates"]:
            summary = candidate["signal_summary"]
            summary["social_company"]["collection_status"] = "not_searched"
            summary["social_person"]["collection_status"] = "not_searched"
            summary["map_listing"]["collection_status"] = "searched_not_found"
            summary["trade_record"]["collection_status"] = "details_restricted"
        sheets = {
            "社媒与公开职业线索": [],
            "地图与经营地址": [],
            "第三方贸易摘要": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            statuses = public_enrichment_empty_sheet_statuses(graph)
            write_csv_sheets(sheets, output, empty_sheet_statuses=statuses)
            csv_values = {}
            for sheet in sheets:
                with (output / f"{sheet}.csv").open(encoding="utf-8-sig", newline="") as handle:
                    csv_values[sheet] = list(csv.DictReader(handle))[0]["说明"]

            write_xlsx_sheets(sheets, output, "signals.xlsx", empty_sheet_statuses=statuses)
            with ZipFile(output / "signals.xlsx") as workbook:
                xlsx_values = {
                    sheet: unescape(workbook.read(f"xl/worksheets/sheet{index}.xml").decode("utf-8"))
                    for index, sheet in enumerate(sheets, start=1)
                }

        self.assertEqual("本轮未检索", csv_values["社媒与公开职业线索"])
        self.assertEqual("已检索未见", csv_values["地图与经营地址"])
        self.assertEqual("来源受限", csv_values["第三方贸易摘要"])
        for sheet, expected in csv_values.items():
            with self.subTest(sheet=sheet):
                self.assertIn(expected, xlsx_values[sheet])


if __name__ == "__main__":
    unittest.main()
