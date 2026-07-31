#!/usr/bin/env python3
"""Smoke-check that formal Superleads Markdown delivery uses the unified exporter.

This is not a live research eval.  It catches the failure mode where an Agent
claims to "formally export" a Superleads report but hand-renders raw
``export_workbook.py`` sheets, causing workbook signal-status columns such as
``已观察`` to be mistaken for the user-facing ``依据状态``.
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


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "shared" / "references" / "default-discovery-reference.example.json"
BACKGROUND_FIXTURE = ROOT / "evals" / "fixtures" / "pass_customer_background_chillys_markdown.json"
DEFAULT_CACHE_ROOT = Path.home() / ".codex" / "plugins" / "cache" / "fleix" / "superleads" / "0.1.3"
SKILL_FILE_SNIPPETS = {
    "skills/using-superleads/SKILL.md": (
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
    "skills/exporting-lead-workbooks/SKILL.md": (
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


def check_generated_markdown(fixture: Path) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    issues: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "formal-superleads-bulk.md"
        payload, text = _run_export(fixture, output, route="bulk_customer_development")
    if payload.get("returncode") != 0 or not payload.get("ok"):
        issues.append(_issue("formal_markdown_export_failed", "export_superleads_markdown.py did not produce a valid report"))
        return issues, payload, text
    required_text = [
        "# 批量客户开发",
        "发现候选池样表（候选池不是正式开发名单）",
        "| 分区 | 候选客户 |",
        "业务相关性",
        "依据状态",
        "联系方式汇总",
        "搜索覆盖与收敛",
        "已排除 / 仅作参考",
    ]
    for needle in required_text:
        if needle not in text:
            issues.append(_issue("formal_markdown_required_text_missing", f"generated Markdown missing: {needle}"))
    forbidden_headers = [
        "| 公司名称 | 国家/地区 | 官网/域名 |",
        "# Superleads 批量客户开发 Markdown 交付",
    ]
    for needle in forbidden_headers:
        if needle in text:
            issues.append(_issue("formal_markdown_raw_workbook_render_detected", f"generated Markdown looks like raw workbook sheet render: {needle}"))

    row_expectations = {
        "HydraTrade Supplies": ("可优先人工跟进", "直接相关", "已有明确依据"),
        "Northshore Drinkware Distributors": ("待确认", "可能相关", "来源受限"),
        "Peak Bottle Co": ("待确认", "信息不足", "来源受限"),
        "Summit Trading": ("待确认", "主体待确认", "说法冲突待复核"),
        "Ironforge Manufacturing": ("已排除 / 仅作参考", "已排除 / 仅作参考", "已有明确依据"),
    }
    for name, expected_parts in row_expectations.items():
        line = _line_containing(text, name)
        if not line:
            issues.append(_issue("formal_markdown_expected_row_missing", f"missing row for {name}"))
            continue
        for part in expected_parts:
            if part not in line:
                issues.append(_issue("formal_markdown_expected_row_status_missing", f"{name} row missing expected text: {part}", name))
    northshore = _line_containing(text, "Northshore Drinkware Distributors")
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
    for needle in ("# 单一客户背调", "怎么联系、先找谁", "客户、品牌与关联方"):
        if needle not in text:
            issues.append(_issue("formal_markdown_background_required_text_missing", f"background Markdown missing: {needle}"))
    return issues, payload


def check_claimed_export_output(graph: Path, markdown: Path, *, route: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not graph.exists():
        return [_issue("formal_markdown_claimed_graph_missing", f"claimed graph JSON does not exist: {graph}", str(graph))]
    if not markdown.exists():
        return [_issue("formal_markdown_claimed_markdown_missing", f"claimed Markdown report does not exist: {markdown}", str(markdown))]
    with tempfile.TemporaryDirectory() as tmp:
        expected_path = Path(tmp) / "expected.md"
        payload, expected_text = _run_export(graph, expected_path, route=route)
    if payload.get("returncode") != 0 or not payload.get("ok"):
        issues.append(_issue(
            "formal_markdown_claimed_graph_export_failed",
            "claimed graph could not be exported by export_superleads_markdown.py",
            str(graph),
        ))
        return issues
    claimed_text = _read(markdown)
    if claimed_text != expected_text:
        issues.append(_issue(
            "formal_markdown_claimed_output_mismatch",
            "claimed Markdown path does not exactly match export_superleads_markdown.py output for the claimed graph",
            f"{markdown} claimed_sha256={_sha256_text(claimed_text)} expected_sha256={_sha256_text(expected_text)}",
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
    parser.add_argument("--claimed-graph", type=Path, help="Optional graph JSON path claimed by a real formal-call UAT run")
    parser.add_argument("--claimed-markdown", type=Path, help="Optional Markdown path claimed by a real formal-call UAT run")
    parser.add_argument("--claimed-route", choices=("auto", "bulk_customer_development", "customer_background_research", "product_outbound_market_analysis"), default="auto")
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    issues = check_skill_instructions(args.cache_root, skip_cache=args.skip_cache)
    issues.extend(check_real_uat_regression_sample())
    markdown_issues, export_payload, text = check_generated_markdown(fixture)
    issues.extend(markdown_issues)
    background_issues, background_payload = check_customer_background_export_support()
    issues.extend(background_issues)
    if args.claimed_graph or args.claimed_markdown:
        if not (args.claimed_graph and args.claimed_markdown):
            issues.append(_issue("formal_markdown_claimed_pair_incomplete", "--claimed-graph and --claimed-markdown must be provided together"))
        else:
            claimed_graph = args.claimed_graph if args.claimed_graph.is_absolute() else ROOT / args.claimed_graph
            claimed_markdown = args.claimed_markdown if args.claimed_markdown.is_absolute() else ROOT / args.claimed_markdown
            issues.extend(check_claimed_export_output(claimed_graph, claimed_markdown, route=args.claimed_route))
    payload: dict[str, Any] = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
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
    }
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        if payload["ok"]:
            print("formal Markdown delivery check passed")
            print(payload["northshore_row"])
        else:
            for issue in issues:
                print(f"{issue['code']}: {issue['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
