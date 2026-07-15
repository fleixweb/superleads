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

Inquiry version: 询盘待办, 来信联系人, 询盘信息摘要, 待补充信息, 来源说明. It is not a standard development list and does not claim buyer verification.

## Export rules

- `needs_correction` blocks formal standard and full export.
- 初筛客户名单 may include weak evidence but must show status.
- 标准开发名单 must include source links and contact status.
- 完整核查版 must include check notes.
- Do not expose internal artifact names as user-facing sheet names.
- A user-provided source is displayed as a business label such as `用户提供文件：目录.pdf（第 3 页）` or `用户提供文件：客户名单.xlsx（工作表 Contacts，A2:F2）`, not as a local path, `file:` URI, or artifact hash.
- Keep `hold_no_source` and `hold_inferred` contact values out of all sheets, source notes, warnings, and Manifest data.
- `user_business_dataset` contacts display `用户提供文件：<文件名>（定位）`; `correspondence_export` contacts display `用户提供沟通记录：<文件名>（定位）`. Both remain 建议核查后使用, never 可直接使用. Do not expose material roles, artifact hashes, local paths, or raw sensitive chat text.
- Inquiry output shows `邮件来信（日期）` or a user-provided correspondence label. It does not expose message/thread IDs, mailbox references, hashes, full mail body, internal review/audit terminology, or hold contacts. Incoming contacts are 来信联系人/待核验 unless independent evidence upgrades them.
- Standard and full customer and contact sheets include only current positive
  Entities marked `符合本次方向`. `需确认`, `不符合本次方向`, and `仅作参考` never
  appear as recommended customers or in contact summaries. Initial output may
  show them separately with these business labels only; do not expose
  TargetingContract, ScopeDecision, Claim, rule IDs, or internal review terms.
- Unknown direction, unresolved direction, and sample-first work export only
  initial direction samples. Never expose internal markers/classifications or
  present those samples as standard customers.
- A formal single-company analysis must export only its user-specified target
  as `单公司分析结果`; a formal existing-table enrichment must export only bound
  spreadsheet rows as `原表补全结果`. Neither may display `符合本次方向` unless a
  separate current development contract was completed.
