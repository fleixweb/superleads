---
name: exporting-lead-workbooks
description: "Use when a Superleads discovery pool, deep check, or standard list needs workbook or CSV export."
---

# Exporting Lead Workbooks

## 内部阶段前置条件

父路线触发：verification-before-delivery：当前合法已验证 graph 与允许的输出模式。
不要直接调用；缺少上述上下文必须停止，不得虚构报告、工作簿或 Markdown 交付。用户在深度核验后单独提出 Excel、格式转换、工作表命名或重新导出时，仍是原交付链的续跑，不是新的表格任务。

## Purpose

Create user-facing workbook and Markdown outputs after verification. Default
customer-development output is a discovery candidate pool, not a recommended
customer shortlist. Select the artifact set from the audited `delivery_status`:
`initial_lead_list` keeps its existing candidate-pool behavior, while
`standard_development_list` must produce a 工作簿主产物 plus a Markdown 配套报告
from the same audited graph.

For the standard artifact set, invoke only the official commands:
`scripts/export_workbook.py <graph> --output-dir <session-artifact-dir> --mode standard --format auto --manifest <manifest>`
and `scripts/export_superleads_markdown.py <graph> --route bulk_customer_development --output <session-artifact-dir>/<report>.md --format json`.
The workbook is the primary operational deliverable; the Markdown file is its
readable companion. List both filenames and file types separately in the
terminal delivery. Do not change the standard workbook's six fixed sheets.

For spreadsheet export, use `--format auto` (or omit it) by default. It writes
XLSX when the workbook component is available and UTF-8-SIG CSV when it is not.
Use `--format xlsx` only when the user explicitly requires an XLSX file; an
explicit XLSX request must fail rather than silently producing CSV. Superleads
may use the current host's 宿主自带 runtime 解释器 when it is already exposed and
usable. It must not install missing dependencies at runtime, create a temporary
dependency directory, set `PYTHONPATH`, or search for an alternative runtime;
不得借用其他应用程序的 Python 环境、虚拟环境或解释器。 When the required script
path therefore cannot run, follow the no-script delivery path and mark
`本环境未运行确定性校验`. If core business-rule validation completed and only
the supplemental structure check did not run, use the accurate distinct
disclosure `本次已完成核心业务规则校验；补充结构检查未运行。` instead.

If the current legal validated graph, allowed output mode, validation, audit, or
exporter result is absent, do not use another skill, tool, script, or code to
make a substitute file. State the missing step, completed range, and continuation
option, then provide only a source-status 对话内工作表 when useful. It is not a
`标准开发名单`, and it must not use custom worksheet or column names to resemble a
formal workbook.

## Required references and script

Read `../../shared/references/output-schema.md` and
`../../shared/references/status-labels.md`, plus
`../../shared/references/superleads-user-guidance.md` for terminal user-delivery footer rules. Use
`../../shared/references/no-script-delivery-contract.md` as the single
no-script fallback contract; do not duplicate its checklist here. Use
`../../scripts/export_superleads_markdown.py` for the unified three-route
Markdown delivery layer. Use `../../scripts/export_workbook.py` for customer
development / customer-background XLSX or CSV export. Use
`../../scripts/export_product_market_workbook.py` for product outbound market
CSV plus optional Markdown export. For a default-discovery workbook,
`../../shared/references/default-discovery-reference.md` and its minimal
skeleton show the base initial sheet set; consult the complete reference only
for optional contact-status and conflict presentation.

Completed CSV/XLSX and chat-readable exports follow the shared footer rules only when presented as a terminal user delivery. Progress updates and standalone clarifications do not append the footer.

无脚本版式必须读取 `../../shared/references/bulk-customer-development-l1-template.md`
或 `../../shared/references/bulk-customer-development-l2-template.md`。进入 L2 前
优先确认 `session_artifact_dir` 或 `SUPERLEADS_SESSION_ARTIFACT_DIR` 指向已存在可写目录；
没有可用显式目录时回退到当前可写的工作区根目录。不得新建或使用 `work/`、`tmp/`、
`out/` 等运行期临时子目录；两级目录都不可用时才走对话内工作表。

## Sheet sets

Default discovery version: 发现候选池, 联系方式汇总, 官网与来源链接, 搜索覆盖与收敛, 待核查事项, 已排除客户, 风险与说明.

Standard development version: 客户信息总表, 联系方式汇总, 公开信息与待核查事项, 官网与来源链接, 待核查事项, 风险与说明.

Full review version: 开发需求, 关键词与搜索思路, 发现候选池, 客户信息总表, 联系方式汇总, 公开信息与待核查事项, 官网与来源链接, 待核查事项, 已排除客户, 检查说明.

`标准开发名单` only mechanically projects the user's pre-stated rules and
verified public information. It is not an AI recommendation, customer-value
ranking, or follow-up decision.

Inquiry version: 询盘待办, 来信联系人, 询盘信息摘要, 待补充信息, 来源说明. It is not a standard development list and does not claim buyer verification.

Customer background version: 客户一眼看懂, 客户、品牌与关联方, 公开业务信号与待核验事项, 公开联系入口与关联依据, 待核验事项与来源限制, 信息从哪里来. It describes public signals, public association evidence, open questions, and source limits only; it does not tell the user whom to contact, how to approach them, or what action to take. Use `--mode background` only for `customer_background_research` with output mode `客户背调报告`; it uses the current Brief scope projection, never creates a DeliveryManifest, and does not enter the formal audit chain.

## Markdown delivery

Use the unified Markdown delivery command when the user wants a readable report
inside a chat, Codex, or ChatGPT app:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route auto --output <session-artifact-dir>/report.md --format json
```

Explicit routes:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route bulk_customer_development --output <session-artifact-dir>/bulk-report.md --format json
python3 scripts/export_superleads_markdown.py graph.json --route customer_background_research --output <session-artifact-dir>/background-report.md --format json
python3 scripts/export_superleads_markdown.py graph.json --route product_outbound_market_analysis --output <session-artifact-dir>/market-report.md --format json
```

The Markdown command renders only already-audited workbook or matrix
projections. It runs the user-visible output contract before writing a file and
must not create facts, rank customers, recommend prices, decide market entry,
or turn candidate HS/HTS / COO / logistics lines into final conclusions.

For formal Markdown delivery, this command is required. Do not hand-render Markdown
from `export_workbook.py` sheets. Do not manually convert
`export_workbook.py` CSV/workbook sheets into Markdown, do not create a parallel
Markdown table from raw sheet columns, and do not treat public signal status
columns such as `业务/产品关联信号状态 = 已观察` as the user-facing `依据状态`. If the
command fails audit or user-visible validation, return the failure payload and
do not write a substitute report.

For real-business research, do not call a manually written table a formal
delivery. Formal Markdown delivery requires a saved graph JSON path and the
exporter's JSON payload with `ok=true`; otherwise the output is only a
research draft / source-collection note. Do not claim `issue_count=0` unless the
validator/exporter actually ran. Before exporting, repair any `依据状态` values
that still use internal public-signal labels such as `已观察`, `未检索`,
`主体待确认`, `已观察；需确认`, or `已观察；来源受限`; user-facing basis status must
use the Slice AE labels in `status-labels.md`.

The claimed Markdown path in the final answer must be the exact output path
written by `export_superleads_markdown.py` for the claimed graph JSON. Do not
post-process, rewrite, or substitute a manually edited report while reusing the
exporter's `ok=true` / `issue_count=0` payload. To check a real formal-call
result, run `check_superleads_formal_markdown_delivery.py --claimed-graph
graph.json --claimed-markdown report.md --claimed-route auto`.

Bulk customer development Markdown must be generated by
`export_superleads_markdown.py --route bulk_customer_development`. Its audited
delivery status determines the projection: `initial_lead_list` uses
`发现候选池样表（候选池不是正式开发名单）` with `分区`, `候选客户`, `业务相关性`,
`依据状态`, and `来源 / 来源状态`; `standard_development_list` uses the same
`客户信息总表`, `联系方式汇总`, `公开信息与待核查事项`, `官网与来源链接`,
`待核查事项`, and `风险与说明` projections as the standard workbook. Do not
apply the initial candidate-pool mapping to a standard list, and do not
hand-render either status from raw workbook/CSV fields.

Before relying on Skill instructions in a formal-call smoke test, run:

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json
```

For spreadsheet export, keep using:

```bash
python3 scripts/export_workbook.py graph.json --output-dir <session-artifact-dir> --mode initial --format csv
python3 scripts/export_workbook.py graph.json --output-dir <session-artifact-dir> --mode background --format csv
python3 scripts/export_product_market_workbook.py market-graph.json --output-dir <session-artifact-dir> --format csv --markdown <session-artifact-dir>/market-report.md --manifest manifest.json
```

## Export rules

- `needs_correction` blocks formal standard export.
- 发现候选池 may include weak evidence but must show relevance status,
  `分区`, `依据状态`, signal status, unknowns, and restrictions. For bulk
  customer development, use `发现候选池` with internal sections rather than a
  separate `初筛客户名单` output mode.
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
