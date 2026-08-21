#!/usr/bin/env python3
"""Smoke-check that formal Superleads Markdown delivery uses the unified exporter.

This is not a live research eval.  It catches the failure mode where an Agent
claims to "formally export" a Superleads report but hand-renders raw
``export_workbook.py`` sheets, causing workbook signal-status columns such as
``已观察`` to be mistaken for the user-facing ``依据状态``.

For real-business UAT, pass ``--claimed-graph`` and ``--claimed-markdown``.
That fixed gate re-runs ``export_superleads_markdown.py`` from the claimed
graph and requires the claimed Markdown path to match byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from audit_delivery import audit_graph as audit_lead_graph
from export_workbook import build_sheets as build_lead_sheets


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "shared" / "references" / "default-discovery-reference.example.json"
BACKGROUND_FIXTURE = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"
try:
    DEFAULT_PLUGIN_VERSION = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")).get("version", "0.1.4")
except Exception:  # pragma: no cover - defensive fallback for partial checkouts
    DEFAULT_PLUGIN_VERSION = "0.1.4"
DEFAULT_CACHE_ROOT = Path.home() / ".codex" / "plugins" / "cache" / "fleix" / "superleads" / str(DEFAULT_PLUGIN_VERSION)
SKILL_FILE_SNIPPETS = {
    "skills/using-superleads/SKILL.md": (
        "using-superleads-formal-delivery.md",
    ),
    "shared/internal-stages/exporting-lead-workbooks.md": (
        "export_superleads_markdown.py",
        "Do not hand-render Markdown",
        "Do not manually",
        "saved graph",
        "JSON path",
        "research draft",
        "claimed Markdown path",
        "customer_background_research",
        "发现候选池样表",
        "依据状态",
        "已观察；来源受限",
    ),
    "skills/researching-customer-background/SKILL.md": (
        "export_superleads_markdown.py",
        "customer_background_research",
        "graph JSON",
        "Markdown exporter",
        "不要声称",
    ),
}
REFERENCE_FILE_SNIPPETS = {
    "shared/references/using-superleads-formal-delivery.md": (
        "export_superleads_markdown.py",
        "Do not hand-render Markdown",
        "Do not manually",
        "saved graph",
        "JSON path",
        "research draft",
        "claimed Markdown path",
        "发现候选池样表",
        "依据状态",
        "已观察；来源受限",
    ),
}
UAT_INTERNAL_BASIS_STATUS_SAMPLE = ROOT / "evals" / "user_visible_outputs" / "fail_bulk_customer_real_uat_internal_basis_status.md"


def _issue(code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def claimed_path_attestation(
    *,
    graph_arg: str,
    markdown_arg: str,
    route: str,
    graph: Path,
    markdown: Path,
    issues: list[dict[str, str]],
) -> dict[str, Any]:
    """Describe the claimed-path result without exposing the fresh temp export."""
    return {
        "graph": graph_arg,
        "markdown": markdown_arg,
        "requested_route": route,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "graph_sha256": _sha256_file(graph),
        "markdown_sha256": _sha256_file(markdown),
    }


def check_skill_instructions(cache_root: Path, *, skip_cache: bool) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rel, required_snippets in SKILL_FILE_SNIPPETS.items():
        source = ROOT / rel
        if not source.exists():
            issues.append(_issue("formal_markdown_skill_source_missing", f"missing source skill: {rel}", rel))
            continue
        source_text = _read(source)
        for snippet in required_snippets:
            if snippet not in source_text:
                issues.append(_issue("formal_markdown_skill_instruction_missing", f"source skill lacks required snippet: {snippet}", rel))
        if skip_cache:
            continue
        cached = cache_root / rel
        if not cached.exists():
            issues.append(_issue("formal_markdown_plugin_cache_missing", f"missing cached skill: {cached}", str(cached)))
            continue
        cached_text = _read(cached)
        if cached_text != source_text:
            issues.append(_issue("formal_markdown_plugin_cache_stale", f"cached skill differs from repo source: {rel}", str(cached)))
        for snippet in required_snippets:
            if snippet not in cached_text:
                issues.append(_issue("formal_markdown_plugin_cache_instruction_missing", f"cached skill lacks required snippet: {snippet}", str(cached)))
    return issues


def check_reference_instructions(cache_root: Path, *, skip_cache: bool) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rel, required_snippets in REFERENCE_FILE_SNIPPETS.items():
        source = ROOT / rel
        if not source.exists():
            issues.append(_issue("formal_markdown_reference_source_missing", f"missing source reference: {rel}", rel))
            continue
        source_text = _read(source)
        for snippet in required_snippets:
            if snippet not in source_text:
                issues.append(_issue("formal_markdown_reference_instruction_missing", f"source reference lacks required snippet: {snippet}", rel))
        if skip_cache:
            continue
        cached = cache_root / rel
        if not cached.exists():
            issues.append(_issue("formal_markdown_plugin_cache_reference_missing", f"missing cached reference: {cached}", str(cached)))
            continue
        cached_text = _read(cached)
        if cached_text != source_text:
            issues.append(_issue("formal_markdown_plugin_cache_reference_stale", f"cached reference differs from repo source: {rel}", str(cached)))
        for snippet in required_snippets:
            if snippet not in cached_text:
                issues.append(_issue("formal_markdown_plugin_cache_reference_instruction_missing", f"cached reference lacks required snippet: {snippet}", str(cached)))
    return issues


def _run_export(fixture: Path, output: Path, *, route: str) -> tuple[dict[str, Any], str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_superleads_markdown.py"),
        str(fixture),
        "--route",
        route,
        "--output",
        str(output),
        "--format",
        "json",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        payload = {"ok": False, "issue_count": 1, "issues": [_issue("formal_markdown_export_output_not_json", proc.stdout)]}
    payload["returncode"] = proc.returncode
    payload["cmd"] = cmd
    text = output.read_text(encoding="utf-8") if output.exists() else ""
    return payload, text


def _line_containing(text: str, needle: str) -> str:
    for line in text.splitlines():
        if needle in line:
            return line
    return ""


def _markdown_table_rows(text: str, heading: str) -> list[str]:
    """Return only data rows from one named Markdown table."""
    marker = f"## {heading}"
    if marker not in text:
        return []
    section = text.split(marker, 1)[1].split("\n## ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return [line for line in rows if not set(line.replace("|", "").strip()) <= {"-", ":", " "} and "候选客户" not in line]


def _candidate_pool_rows(text: str) -> list[str]:
    return _markdown_table_rows(text, "发现候选池样表（候选池不是正式开发名单）")


def _candidate_pool_row_containing_all(rows: list[str], name: str, expected_parts: tuple[str, ...]) -> str:
    for line in rows:
        if name in line and all(part in line for part in expected_parts):
            return line
    return ""


def check_generated_markdown(fixture: Path) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    issues: list[dict[str, str]] = []
    graph = json.loads(fixture.read_text(encoding="utf-8"))
    audit = audit_lead_graph(graph) if isinstance(graph, dict) else {}
    delivery_status = audit.get("delivery_status")
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "formal-superleads-bulk.md"
        payload, text = _run_export(fixture, output, route="bulk_customer_development")
    if payload.get("returncode") != 0 or not payload.get("ok"):
        issues.append(_issue("formal_markdown_export_failed", "export_superleads_markdown.py did not produce a valid report"))
        return issues, payload, text
    required_text = ["# 批量客户开发"]
    if delivery_status == "standard_development_list":
        required_text.extend([
            "本次输出为标准开发名单",
            "## 客户信息总表",
            "| 公司名称 | 官网 | 国家/地区 | 客户类型 | 公开信息状态 |",
            "## 联系方式汇总",
            "## 公开信息与待核查事项",
            "## 官网与来源链接",
            "## 待核查事项",
            "## 风险与说明",
        ])
    else:
        required_text.extend([
            "发现候选池样表（候选池不是正式开发名单）",
            "| 分区 | 候选客户 |",
            "业务相关性",
            "依据状态",
            "联系方式汇总",
            "搜索覆盖与收敛",
            "已排除 / 仅作参考",
        ])
    for needle in required_text:
        if needle not in text:
            issues.append(_issue("formal_markdown_required_text_missing", f"generated Markdown missing: {needle}"))
    forbidden_headers = ["# Superleads 批量客户开发 Markdown 交付"]
    if delivery_status == "standard_development_list":
        forbidden_headers.append("发现候选池样表（候选池不是正式开发名单）")
    else:
        forbidden_headers.append("| 公司名称 | 国家/地区 | 官网/域名 |")
    for needle in forbidden_headers:
        if needle in text:
            issues.append(_issue("formal_markdown_raw_workbook_render_detected", f"generated Markdown looks like raw workbook sheet render: {needle}"))

    if delivery_status == "standard_development_list":
        standard_rows = _markdown_table_rows(text, "客户信息总表")
        expected_rows = build_lead_sheets(graph, audit, "standard").get("客户信息总表", [])
        for expected in expected_rows:
            if not isinstance(expected, dict):
                continue
            name = str(expected.get("公司名称") or "")
            status = str(expected.get("公开信息状态") or "")
            if name and not any(name in row and (not status or status in row) for row in standard_rows):
                issues.append(_issue("formal_markdown_standard_row_missing", "standard Markdown must render the verified customer-information row", name))
    else:
        row_expectations = {
            "HydraTrade Supplies": ("发现候选池样表（候选池不是正式开发名单）", ("公开信号已匹配当前范围", "直接相关", "已有明确依据")),
            "Northshore Drinkware Distributors": ("发现候选池样表（候选池不是正式开发名单）", ("待确认", "可能相关", "来源受限")),
            "Peak Bottle Co": ("发现候选池样表（候选池不是正式开发名单）", ("待确认", "信息不足", "来源受限")),
            "Summit Trading": ("发现候选池样表（候选池不是正式开发名单）", ("待确认", "主体待确认", "说法冲突待复核")),
            "Ironforge Manufacturing": ("已排除 / 仅作参考", ("已排除 / 仅作参考", "已排除 / 仅作参考", "已有明确依据")),
        }
        candidate_rows = _candidate_pool_rows(text)
        for name, (heading, expected_parts) in row_expectations.items():
            rows = _markdown_table_rows(text, heading)
            line = _candidate_pool_row_containing_all(rows, name, expected_parts)
            if not line:
                candidates = [candidate for candidate in rows if name in candidate]
                if not candidates:
                    issues.append(_issue("formal_markdown_expected_row_missing", f"missing row for {name}"))
                else:
                    for part in expected_parts:
                        if not any(part in candidate for candidate in candidates):
                            issues.append(_issue("formal_markdown_expected_row_status_missing", f"{name} row missing expected text: {part}", name))
        northshore = next((line for line in candidate_rows if "Northshore Drinkware Distributors" in line), "")
        if "已观察" in northshore:
            issues.append(_issue("formal_markdown_signal_status_used_as_basis", "Northshore row must not use 已观察 as 依据状态", "Northshore Drinkware Distributors"))
    return issues, payload, text


def check_customer_background_export_support() -> tuple[list[dict[str, str]], dict[str, Any]]:
    issues: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "formal-superleads-background.md"
        payload, text = _run_export(BACKGROUND_FIXTURE, output, route="customer_background_research")
    if payload.get("returncode") != 0 or not payload.get("ok"):
        issues.append(_issue(
            "formal_markdown_background_export_failed",
            "export_superleads_markdown.py must support customer_background_research",
            str(BACKGROUND_FIXTURE),
        ))
        return issues, payload
    for needle in ("# 单一客户背调", "公开联系入口与关联依据", "客户、品牌与关联方"):
        if needle not in text:
            issues.append(_issue("formal_markdown_background_required_text_missing", f"background Markdown missing: {needle}"))
    return issues, payload


def _read_claimed_markdown(path: Path, markdown_arg: str) -> tuple[str | None, dict[str, str] | None]:
    if not path.is_file():
        return None, _issue(
            "formal_markdown_claimed_markdown_not_readable",
            f"claimed Markdown report is not a readable UTF-8 file: {markdown_arg}",
            markdown_arg,
        )
    try:
        return _read(path), None
    except (OSError, UnicodeDecodeError):
        return None, _issue(
            "formal_markdown_claimed_markdown_not_readable",
            f"claimed Markdown report is not a readable UTF-8 file: {markdown_arg}",
            markdown_arg,
        )


def check_claimed_export_output(
    graph: Path,
    markdown: Path,
    *,
    graph_arg: str,
    markdown_arg: str,
    route: str,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not graph.exists():
        return [_issue("formal_markdown_claimed_graph_missing", f"claimed graph JSON does not exist: {graph_arg}", graph_arg)]
    if not graph.is_file():
        return [_issue(
            "formal_markdown_claimed_graph_not_readable",
            f"claimed graph JSON is not a readable file: {graph_arg}",
            graph_arg,
        )]
    if not markdown.exists():
        return [_issue("formal_markdown_claimed_markdown_missing", f"claimed Markdown report does not exist: {markdown_arg}", markdown_arg)]
    claimed_text, markdown_issue = _read_claimed_markdown(markdown, markdown_arg)
    if markdown_issue is not None:
        return [markdown_issue]
    with tempfile.TemporaryDirectory() as tmp:
        expected_path = Path(tmp) / "expected.md"
        payload, expected_text = _run_export(graph, expected_path, route=route)
    if payload.get("returncode") != 0 or not payload.get("ok"):
        issues.append(_issue(
            "formal_markdown_claimed_graph_export_failed",
            "claimed graph could not be exported by export_superleads_markdown.py",
            graph_arg,
        ))
        return issues
    if claimed_text != expected_text:
        issues.append(_issue(
            "formal_markdown_claimed_output_mismatch",
            "claimed Markdown path does not exactly match export_superleads_markdown.py output for the claimed graph",
            f"{markdown_arg} claimed_sha256={_sha256_text(claimed_text)} expected_sha256={_sha256_text(expected_text)}",
        ))
    return issues


def check_real_uat_regression_sample() -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not UAT_INTERNAL_BASIS_STATUS_SAMPLE.exists():
        return [_issue(
            "formal_markdown_real_uat_fixture_missing",
            f"missing real-UAT regression fixture: {UAT_INTERNAL_BASIS_STATUS_SAMPLE}",
            str(UAT_INTERNAL_BASIS_STATUS_SAMPLE),
        )]
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "validate_superleads_user_visible_output.py"),
        str(UAT_INTERNAL_BASIS_STATUS_SAMPLE),
        "--route",
        "bulk_customer_development",
        "--min-tables",
        "7",
        "--format",
        "json",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if proc.returncode == 0:
        issues.append(_issue(
            "formal_markdown_real_uat_internal_basis_status_not_blocked",
            "real-UAT hand-written report with 依据状态=已观察 unexpectedly passed",
            str(UAT_INTERNAL_BASIS_STATUS_SAMPLE),
        ))
        return issues
    if "user_visible_basis_status_internal_leak" not in proc.stdout:
        issues.append(_issue(
            "formal_markdown_real_uat_internal_basis_status_wrong_failure",
            "real-UAT regression did not fail with user_visible_basis_status_internal_leak",
            str(UAT_INTERNAL_BASIS_STATUS_SAMPLE),
        ))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--claimed-graph", help="Graph JSON path claimed by a real formal-call UAT run; pair with --claimed-markdown for the fixed UAT gate")
    parser.add_argument("--claimed-markdown", help="Markdown path claimed by a real formal-call UAT run; must exactly match a fresh exporter run from --claimed-graph")
    parser.add_argument("--claimed-route", choices=("auto", "bulk_customer_development", "customer_background_research", "product_outbound_market_analysis"), default="auto")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    issues = check_skill_instructions(args.cache_root, skip_cache=args.skip_cache)
    issues.extend(check_reference_instructions(args.cache_root, skip_cache=args.skip_cache))
    issues.extend(check_real_uat_regression_sample())
    markdown_issues, export_payload, text = check_generated_markdown(fixture)
    issues.extend(markdown_issues)
    background_issues, background_payload = check_customer_background_export_support()
    issues.extend(background_issues)
    claimed_attestation: dict[str, Any] | None = None
    if args.claimed_graph or args.claimed_markdown:
        if not (args.claimed_graph and args.claimed_markdown):
            issues.append(_issue("formal_markdown_claimed_pair_incomplete", "--claimed-graph and --claimed-markdown must be provided together"))
        else:
            claimed_graph_arg = args.claimed_graph
            claimed_markdown_arg = args.claimed_markdown
            claimed_graph_path = Path(claimed_graph_arg)
            claimed_markdown_path = Path(claimed_markdown_arg)
            claimed_graph = claimed_graph_path if claimed_graph_path.is_absolute() else ROOT / claimed_graph_path
            claimed_markdown = claimed_markdown_path if claimed_markdown_path.is_absolute() else ROOT / claimed_markdown_path
            claimed_issues = check_claimed_export_output(
                claimed_graph,
                claimed_markdown,
                graph_arg=claimed_graph_arg,
                markdown_arg=claimed_markdown_arg,
                route=args.claimed_route,
            )
            issues.extend(claimed_issues)
            claimed_attestation = claimed_path_attestation(
                graph_arg=claimed_graph_arg,
                markdown_arg=claimed_markdown_arg,
                route=args.claimed_route,
                graph=claimed_graph,
                markdown=claimed_markdown,
                issues=claimed_issues,
            )
    payload: dict[str, Any] = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "smoke_check": {
            "fixture": str(fixture),
            "cache_root": None if args.skip_cache else str(args.cache_root),
            "export": {
                "ok": bool(export_payload.get("ok")),
                "returncode": export_payload.get("returncode"),
                "route": export_payload.get("route"),
                "stage": export_payload.get("stage"),
                "issue_count": export_payload.get("issue_count"),
            },
            "background_export": {
                "ok": bool(background_payload.get("ok")),
                "returncode": background_payload.get("returncode"),
                "route": background_payload.get("route"),
                "stage": background_payload.get("stage"),
                "issue_count": background_payload.get("issue_count"),
            },
            "northshore_row": _line_containing(text, "Northshore Drinkware Distributors"),
        },
    }
    if claimed_attestation is not None:
        payload["claimed_path_attestation"] = claimed_attestation
    elif not (args.claimed_graph or args.claimed_markdown):
        payload.update(payload["smoke_check"])
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if payload["ok"]:
            print("formal Markdown delivery check passed")
            print(payload["smoke_check"]["northshore_row"])
        else:
            for issue in issues:
                print(f"{issue['code']}: {issue['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
