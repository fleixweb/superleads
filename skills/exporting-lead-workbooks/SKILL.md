---
name: exporting-lead-workbooks
description: "Export Superleads lead research into user-facing XLSX or UTF-8-SIG CSV workbooks with Chinese business sheet names, contact status labels, source links, development suggestions, pending checks, risks, and full-review sheets when requested. Use only after verification gates."
---

# Exporting Lead Workbooks

## Purpose

Create user-facing workbook outputs after verification. Prefer XLSX when available and fall back to UTF-8-SIG CSV files.

## Required references and script

Read `../../shared/references/output-schema.md` and `../../shared/references/status-labels.md`. Use `../../scripts/export_workbook.py` for deterministic export.

## Sheet sets

Default development version: 客户信息总表, 联系方式汇总, 开发建议, 官网与来源链接, 待核查事项, 风险与说明.

Full review version: 开发需求, 关键词与搜索思路, 初筛客户名单, 客户信息总表, 联系方式汇总, 开发建议, 官网与来源链接, 待核查事项, 已排除客户, 检查说明.

## Export rules

- `needs_correction` blocks formal standard and full export.
- 初筛客户名单 may include weak evidence but must show status.
- 标准开发名单 must include source links and contact status.
- 完整核查版 must include check notes.
- Do not expose internal artifact names as user-facing sheet names.
