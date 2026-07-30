#!/usr/bin/env python3
"""Smoke-check that formal Superleads Markdown delivery uses the unified exporter.

This is not a live research eval.  It catches the failure mode where an Agent
claims to "formally export" a Superleads report but hand-renders raw
``export_workbook.py`` sheets, causing workbook signal-status columns such as
``已观察`` to be mistaken for the user-facing ``依据状态``.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "shared" / "references" / "default-discovery-reference.example.json"
DEFAULT_CACHE_ROOT = Path.home() / ".codex" / "plugins" / "cache" / "fleix" / "superleads" / "0.1.3"
SKILL_FILES = (
    "skills/using-superleads/SKILL.md",
    "skills/exporting-lead-workbooks/SKILL.md",
)
REQUIRED_SKILL_SNIPPETS = (
    "export_superleads_markdown.py",
    "Do not hand-render Markdown",
    "Do not manually",
    "发现候选池样表",
    "依据状态",
)


def _issue(code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_skill_instructions(cache_root: Path, *, skip_cache: bool) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for rel in SKILL_FILES:
        source = ROOT / rel
        if not source.exists():
            issues.append(_issue("formal_markdown_skill_source_missing", f"missing source skill: {rel}", rel))
            continue
        source_text = _read(source)
        for snippet in REQUIRED_SKILL_SNIPPETS:
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
        for snippet in REQUIRED_SKILL_SNIPPETS:
            if snippet not in cached_text:
                issues.append(_issue("formal_markdown_plugin_cache_instruction_missing", f"cached skill lacks required snippet: {snippet}", str(cached)))
    return issues


def _run_export(fixture: Path, output: Path) -> tuple[dict[str, Any], str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "export_superleads_markdown.py"),
        str(fixture),
        "--route",
        "bulk_customer_development",
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
        payload, text = _run_export(fixture, output)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--cache-root", type=Path, default=DEFAULT_CACHE_ROOT)
    parser.add_argument("--skip-cache", action="store_true")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    fixture = args.fixture if args.fixture.is_absolute() else ROOT / args.fixture
    issues = check_skill_instructions(args.cache_root, skip_cache=args.skip_cache)
    markdown_issues, export_payload, text = check_generated_markdown(fixture)
    issues.extend(markdown_issues)
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
