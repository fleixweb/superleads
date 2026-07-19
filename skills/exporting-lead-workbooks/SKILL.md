---
name: exporting-lead-workbooks
description: "Export Superleads lead research into user-facing XLSX or UTF-8-SIG CSV workbooks with Chinese business sheet names, contact status labels, source links, development suggestions, pending checks, and risks. Use only after verification gates."
---

# Exporting Lead Workbooks

## Purpose

Create user-facing workbook outputs after verification. Default output is a discovery candidate pool, not a recommended-customer shortlist. Prefer XLSX when available and fall back to UTF-8-SIG CSV files.

## Required references and script

Read `../../shared/references/output-schema.md` and `../../shared/references/status-labels.md`. Use `../../scripts/export_workbook.py` for deterministic export. For a default-discovery workbook, `../../shared/references/default-discovery-reference.md` and its minimal skeleton show the base initial sheet set; consult the complete reference only for optional contact-status and conflict presentation.

## Sheet sets

Default discovery version: 发现候选池, 联系方式汇总, 官网与来源链接, 搜索覆盖与收敛, 待核查事项, 已排除客户, 风险与说明.

Standard development version: 客户信息总表, 联系方式汇总, 开发建议, 官网与来源链接, 待核查事项, 风险与说明.

Full review version: 开发需求, 关键词与搜索思路, 发现候选池, 客户信息总表, 联系方式汇总, 开发建议, 官网与来源链接, 待核查事项, 已排除客户, 检查说明.

Inquiry version: 询盘待办, 来信联系人, 询盘信息摘要, 待补充信息, 来源说明. It is not a standard development list and does not claim buyer verification.

## Export rules

- `needs_correction` blocks formal standard export.
- 发现候选池 may include weak evidence but must show relevance status,
  signal status, unknowns, and restrictions.
- Candidate discovery and signal links are exported only when they are safe,
  credential-free public HTTP(S) URLs. Keep an available source label or
  restriction note when no safe link can be shown; never export or guess a
  URL with userinfo or sensitive query/fragment credential parameters
  (including SPA fragment-route query), a
  local/private/non-HTTP(S), or malformed URL. The 官网/域名 column may retain a
  plain public domain but never guesses a protocol or exports an unsafe URL.
- 标准开发名单 must include source links and contact status.
- This local deployment does not provide `full_review_package`.
- Do not expose internal artifact names as user-facing sheet names.
- A user-provided source is displayed as a business label such as `用户提供文件：目录.pdf（第 3 页）` or `用户提供文件：客户名单.xlsx（工作表 Contacts，A2:F2）`, not as a local path, `file:` URI, or artifact hash.
- Keep `hold_no_source` and `hold_inferred` contact values out of all sheets, source notes, warnings, and Manifest data.
- `user_business_dataset` contacts display `用户提供文件：<文件名>（定位）`; `correspondence_export` contacts display `用户提供沟通记录：<文件名>（定位）`. Both remain 建议核查后使用, never 可直接使用. Do not expose material roles, artifact hashes, local paths, or raw sensitive chat text.
- Inquiry output shows `邮件来信（日期）` or a user-provided correspondence label. It does not expose message/thread IDs, mailbox references, hashes, full mail body, internal review/audit terminology, or hold contacts. Incoming contacts are 来信联系人/待核验 unless independent evidence upgrades them.
- Standard customer and contact sheets include only current positive
  Entities marked `符合本次方向`. `需确认`, `不符合本次方向`, and `仅作参考` never
  appear as recommended customers or in contact summaries. Initial output may
  show them separately with these business labels only; do not expose
  TargetingContract, ScopeDecision, Claim, rule IDs, or internal review terms.
- Unknown direction, unresolved direction, and sample-first work export only
  initial direction samples. Never expose internal markers/classifications or
  present those samples as standard customers.
- Default discovery must not be named or described as 推荐客户, 正式合格名单,
  高质量客户名单, or purchase-probability output.
- A formal single-company analysis must export only its user-specified target
  as `单公司分析结果`; a formal existing-table enrichment must export only bound
  spreadsheet rows as `原表补全结果`. Neither may display `符合本次方向` unless a
  separate current development contract was completed.
