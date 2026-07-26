#!/usr/bin/env python3
"""Export ProductMarketAnalysisGraph as a safe CSV/Markdown workbook.

The exporter is deliberately boring: it does not research, complete, classify,
price, route, or rate anything.  It only moves already-reviewed
matrix_rows.user_visible_cells plus safe Gap/Conflict/Source notes into
human-readable tables.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _superleads_common import has_text, is_safe_public_http_url
from audit_product_market_analysis import audit_graph
from validate_product_market_analysis import _looks_like_internal_leak, ensure_list, load_market_fixture

SHEET_COLUMNS: dict[str, list[str]] = {
    "市场事实总览": [
        "样本ID", "产品名称", "产品版本/型号", "目的国/地区", "原产/制造来源", "出口申报国",
        "实际起运地", "关键已核实", "关键缺口", "总体状态", "观察日期", "备注",
    ],
    "产品档案与触发项": [
        "样本ID", "属性族", "属性", "当前值", "状态", "触发的核验路径", "来源/依据", "缺口/下一步",
    ],
    "长期需求与搜索趋势": [
        "样本ID", "关键词/Topic", "语言/同义词", "国家/地区", "时间范围", "搜索类型/类目",
        "趋势状态", "指标口径", "数据日期", "状态", "来源/依据", "限制说明",
    ],
    "公开市场资料与行业信息": [
        "样本ID", "来源名称", "来源类型", "指标或主题", "可见内容", "时间范围", "地区",
        "状态", "来源URL/文件", "限制说明",
    ],
    "线上市场与价格参考": [
        "样本ID", "渠道/平台", "产品/规格", "价格", "币种", "税/运费/促销状态",
        "观察日期", "状态", "来源URL/文件", "限制说明",
    ],
    "季节、节日与销售窗口": [
        "样本ID", "节点/窗口", "日期/周期", "国家/地区", "适用条件", "影响口径",
        "状态", "来源/依据", "限制说明",
    ],
    "产品准入与合规要求": [
        "样本ID", "要求类别", "要求名称", "适用条件", "当前证据", "状态",
        "官方/优先来源", "待补材料", "禁止升级",
    ],
    "进口税费": [
        "样本ID", "目的国", "候选 HS/HTS", "税号描述", "税种", "税率/金额",
        "适用条件", "计算税基", "状态", "来源/依据", "缺口/下一步",
    ],
    "出口国要求": [
        "样本ID", "出口申报国", "要求类别", "要求名称", "适用条件", "当前证据",
        "状态", "来源/依据", "缺口/下一步",
    ],
    "运输方式、路线、港口与申报节点": [
        "样本ID", "运输方式", "起运节点", "目的节点", "适用条件", "时间口径",
        "法定预申报", "操作截点", "状态", "来源/依据", "缺口/下一步",
    ],
    "近期外部因素": [
        "样本ID", "因素类型", "因素名称", "地区", "时间", "可能影响对象",
        "状态", "来源/依据", "限制说明",
    ],
    "信息来源与待确认事项": [
        "样本ID", "来源ID", "来源名称", "来源类型", "URL/文件名", "观察日期",
        "支持字段", "状态", "待确认事项", "用户可见备注",
    ],
}

SHEET_ORDER = list(SHEET_COLUMNS)

STATUS_LABELS = {
    "verified": "已核实",
    "derived_calculation": "派生计算",
    "candidate": "候选",
    "preliminary_reference": "初步参考",
    "business_confirmation_required": "待业务确认",
    "technical_docs_required": "待技术资料确认",
    "physical_verification_required": "待实物核验",
    "professional_confirmation_required": "待专业确认",
    "source_restricted": "来源受限",
    "not_executed": "未执行",
    "not_applicable": "不适用",
    "not_provided": "未提供",
    "conflict_pending_review": "有冲突待复核",
}

BLOCKED_ACCESS = {"blocked", "login_wall", "login_required", "forbidden", "inaccessible", "not_accessed"}


def _status_label(value: Any) -> str:
    return STATUS_LABELS.get(str(value), str(value or "未提供"))


def _stringify(value: Any) -> str:
    if value is None:
        return "未提供"
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_stringify(item) for item in value if item is not None and _stringify(item) != "未提供"]
        return "；".join(parts) if parts else "未提供"
    if isinstance(value, dict):
        parts = [f"{key}：{_stringify(val)}" for key, val in value.items() if val is not None]
        return "；".join(parts) if parts else "未提供"
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    return text if text else "未提供"


def _safe_url(value: Any) -> str:
    url = _stringify(value)
    if url == "未提供":
        return "未提供"
    return url if is_safe_public_http_url(url) and not _looks_like_internal_leak(url) else "来源不适合导出"


def _safe_cell(value: Any) -> str:
    text = _stringify(value)
    return "用户可见内容已隐藏" if _looks_like_internal_leak(text) else text


def _first_sample_id(matrix_rows: list[dict[str, Any]]) -> str:
    for row in matrix_rows:
        cells = row.get("user_visible_cells")
        if isinstance(cells, dict) and has_text(cells.get("样本ID")):
            return _safe_cell(cells.get("样本ID"))
    return "未提供"


def _observation_by_source(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for obs in ensure_list(graph, "observations"):
        if isinstance(obs, dict) and has_text(obs.get("source_id")):
            result.setdefault(str(obs["source_id"]), []).append(obs)
    return result


def _source_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    observations = _observation_by_source(graph)
    for idx, source in enumerate(ensure_list(graph, "sources"), start=1):
        if not isinstance(source, dict):
            continue
        source_observations = observations.get(str(source.get("source_id")), [])
        opened = any(obs.get("access_status") == "opened" for obs in source_observations if isinstance(obs, dict))
        restricted = any(str(obs.get("access_status") or "") in BLOCKED_ACCESS for obs in source_observations if isinstance(obs, dict))
        first_obs = next((obs for obs in source_observations if isinstance(obs, dict)), {})
        title = first_obs.get("title") if isinstance(first_obs, dict) else None
        observed_at = first_obs.get("observed_at") if isinstance(first_obs, dict) else None
        url = _safe_url(source.get("final_url") or source.get("canonical_url"))
        status = "来源受限" if restricted else ("已打开" if opened else "已记录")
        rows.append({
            "条目": _safe_cell(title or f"公开来源 S{idx}"),
            "样本ID": sample_id,
            "来源ID": f"S{idx}",
            "来源名称": _safe_cell(title or source.get("publisher_relation") or source.get("medium") or "公开来源"),
            "来源类型": _safe_cell(source.get("medium") or "公开来源"),
            "URL/文件名": url,
            "观察日期": _safe_cell(observed_at or "日期未见"),
            "支持字段": "来源本身仅作可追溯入口；具体支持字段以各矩阵行为准",
            "状态": status,
            "待确认事项": "无额外事项" if opened and not restricted else "需打开或复核原始来源",
            "用户可见备注": "不含本地路径、哈希或内部对象 ID",
        })
    return rows


def _gap_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, gap in enumerate(ensure_list(graph, "gaps"), start=1):
        if not isinstance(gap, dict):
            continue
        rows.append({
            "条目": _safe_cell(gap.get("field_name") or gap.get("missing_item") or f"待确认事项 G{idx}"),
            "样本ID": sample_id,
            "来源ID": f"G{idx}",
            "来源名称": _safe_cell(gap.get("missing_item") or gap.get("field_name") or "待确认事项"),
            "来源类型": "待确认事项",
            "URL/文件名": "用户/供应链/专业方待提供",
            "观察日期": "日期未见",
            "支持字段": _safe_cell(" / ".join(str(item) for item in (gap.get("field_domain"), gap.get("field_name")) if has_text(item))),
            "状态": _status_label(gap.get("status")),
            "待确认事项": _safe_cell(gap.get("user_visible_note") or gap.get("missing_item") or "待确认"),
            "用户可见备注": _safe_cell(gap.get("requested_from") or "需补材料后复核"),
        })
    return rows


def _conflict_rows(graph: dict[str, Any], sample_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, conflict in enumerate(ensure_list(graph, "conflicts"), start=1):
        if not isinstance(conflict, dict):
            continue
        rows.append({
            "条目": _safe_cell(conflict.get("field_name") or f"冲突待复核 C{idx}"),
            "样本ID": sample_id,
            "来源ID": f"C{idx}",
            "来源名称": _safe_cell(conflict.get("field_name") or "来源冲突"),
            "来源类型": "冲突待复核",
            "URL/文件名": "见已打开来源；需人工复核",
            "观察日期": "日期未见",
            "支持字段": _safe_cell(" / ".join(str(item) for item in (conflict.get("field_domain"), conflict.get("field_name")) if has_text(item))),
            "状态": _status_label(conflict.get("status")),
            "待确认事项": _safe_cell(conflict.get("summary") or "来源之间不一致，需复核"),
            "用户可见备注": "保留冲突，不强行合并为结论",
        })
    return rows


def build_sheets(graph: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    sheets: dict[str, list[dict[str, str]]] = {sheet: [] for sheet in SHEET_ORDER}
    matrix_rows = [row for row in ensure_list(graph, "matrix_rows") if isinstance(row, dict)]
    sample_id = _first_sample_id(matrix_rows)

    for row in matrix_rows:
        sheet_name = str(row.get("sheet_name") or "")
        if sheet_name not in sheets:
            continue
        cells = row.get("user_visible_cells")
        visible_cells = cells if isinstance(cells, dict) else {}
        exported: dict[str, str] = {"条目": _safe_cell(row.get("row_topic") or "未提供"), "状态": _status_label(row.get("status"))}
        for key, value in visible_cells.items():
            if not has_text(key):
                continue
            safe_key = _safe_cell(key)
            if safe_key == "用户可见内容已隐藏":
                continue
            exported[safe_key] = _safe_cell(value)
        if "样本ID" in SHEET_COLUMNS[sheet_name] and not has_text(exported.get("样本ID")) and sample_id != "未提供":
            exported["样本ID"] = sample_id
        sheets[sheet_name].append(exported)

    # The final sheet is explicitly allowed to include safe Source / Gap /
    # Conflict fields.  These rows do not introduce market facts; they expose
    # where the matrix came from and what remains to be checked.
    sheets["信息来源与待确认事项"].extend(_source_rows(graph, sample_id))
    sheets["信息来源与待确认事项"].extend(_gap_rows(graph, sample_id))
    sheets["信息来源与待确认事项"].extend(_conflict_rows(graph, sample_id))
    return sheets


def _headers_for_sheet(sheet_name: str, rows: list[dict[str, str]]) -> list[str]:
    base = ["条目"]
    for col in SHEET_COLUMNS[sheet_name]:
        if col not in base:
            base.append(col)
    if "状态" not in base:
        base.insert(1, "状态")
    for row in rows:
        for key in row:
            if key not in base:
                base.append(key)
    return base


def _safe_filename(index: int, sheet_name: str) -> str:
    return f"{index:02d}-{sheet_name}.csv"


def write_csv_sheets(sheets: dict[str, list[dict[str, str]]], output_dir: Path) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    for index, sheet_name in enumerate(SHEET_ORDER, start=1):
        rows = sheets.get(sheet_name, [])
        headers = _headers_for_sheet(sheet_name, rows)
        filename = _safe_filename(index, sheet_name)
        path = output_dir / filename
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({header: row.get(header, "未提供") for header in headers})
        generated.append({"sheet_name": sheet_name, "filename": filename, "row_count": len(rows)})
    return generated


def _md_escape(value: Any) -> str:
    text = _safe_cell(value)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def markdown_report(sheets: dict[str, list[dict[str, str]]]) -> str:
    lines: list[str] = [
        "# 产品出海市场分析",
        "",
        "本报告只搬运已审核矩阵行和安全的来源/待确认字段；未执行、待确认和冲突项会保留显示。",
        "",
    ]
    for sheet_name in SHEET_ORDER:
        rows = sheets.get(sheet_name, [])
        headers = _headers_for_sheet(sheet_name, rows)
        lines.append(f"## {sheet_name}")
        lines.append("")
        if not rows:
            lines.append("本表暂无矩阵行。")
            lines.append("")
            continue
        lines.append("| " + " | ".join(_md_escape(header) for header in headers) + " |")
        lines.append("| " + " | ".join("---" for _ in headers) + " |")
        for row in rows:
            lines.append("| " + " | ".join(_md_escape(row.get(header, "未提供")) for header in headers) + " |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _scan_exported_files(files: list[Path]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _looks_like_internal_leak(line):
                issues.append({
                    "severity": "critical",
                    "code": "market_export_internal_leak",
                    "message": "Exported file leaks local path, hash, tokenized URL, or internal ID",
                    "path": f"{path.name}:{line_no}",
                })
    return issues


def export_graph(
    graph: dict[str, Any],
    output_dir: Path,
    markdown_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    audit = audit_graph(graph)
    if not audit.get("ok"):
        return {
            "ok": False,
            "stage": "audit",
            "audit": audit,
            "generated_files": [],
            "issue_count": audit.get("issue_count", 0),
            "issues": audit.get("issues", []),
        }

    sheets = build_sheets(graph)
    generated = write_csv_sheets(sheets, output_dir)
    written_paths = [output_dir / item["filename"] for item in generated]

    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown_report(sheets), encoding="utf-8")
        generated.append({"sheet_name": "Markdown 报告", "filename": markdown_path.name, "row_count": None})
        written_paths.append(markdown_path)

    manifest: dict[str, Any] = {
        "ok": True,
        "route": "product_outbound_market_analysis",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "delivery_status": audit.get("delivery_status"),
        "audit_status": audit.get("audit_status"),
        "limitation_count": audit.get("limitation_count"),
        "files": generated,
        "notes": [
            "CSV/Markdown 只搬运已审核用户可见矩阵、来源、缺口和冲突字段。",
            "导出器不补税率、不猜港口、不生成趋势、价格、认证或物流结论。",
        ],
    }

    if manifest_path is not None:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        written_paths.append(manifest_path)

    leak_issues = _scan_exported_files(written_paths)
    if leak_issues:
        return {
            "ok": False,
            "stage": "post_export_scan",
            "audit": audit,
            "generated_files": generated,
            "issue_count": len(leak_issues),
            "issues": leak_issues,
        }

    return {
        "ok": True,
        "stage": "export",
        "delivery_status": audit.get("delivery_status"),
        "audit_status": audit.get("audit_status"),
        "limitation_count": audit.get("limitation_count"),
        "generated_files": generated,
        "issue_count": 0,
        "issues": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", help="ProductMarketAnalysisGraph JSON fixture")
    parser.add_argument("--output-dir", required=True, help="Directory for 12 CSV files")
    parser.add_argument("--format", choices=["csv"], default="csv")
    parser.add_argument("--markdown", help="Optional Markdown report path")
    parser.add_argument("--manifest", help="Optional manifest JSON path")
    args = parser.parse_args()

    try:
        graph = load_market_fixture(Path(args.graph))
    except Exception as exc:
        result = {
            "ok": False,
            "stage": "load",
            "issue_count": 1,
            "issues": [{
                "severity": "critical",
                "code": "market_fixture_load_failed",
                "message": f"Could not load market fixture: {exc}",
                "path": "graph",
            }],
            "generated_files": [],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    result = export_graph(
        graph,
        Path(args.output_dir),
        Path(args.markdown) if args.markdown else None,
        Path(args.manifest) if args.manifest else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
