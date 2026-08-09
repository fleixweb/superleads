---
name: using-superleads
description: "Use when users need overseas B2B customer discovery, public contact collection, lead-list enrichment, foreign-trade prospect research, single-customer background research, or product outbound market analysis intake/routing."
---

# Using Superleads

## Purpose

Activate Superleads, identify the user's task entry, create Run Context, decide whether this run is product outbound market analysis, default discovery, explicit deep verification, or customer background research, check tool capability, and route to the next skill. Do not search, generate leads, write development advice, or export workbooks here.

## Required references

Read `../../shared/references/user-intake.md` for intake modes and minimum research targets. Read `../../shared/references/route-map.md` for routing. For product outbound market analysis, read `../../shared/references/product-outbound-market-intake.md`. Read `../../shared/policies/tool-capability-policy.md` when tool availability affects deliverable level. For default discovery, read `../../shared/references/default-discovery-reference.md`; begin with `default-discovery-minimal-skeleton.example.json`, and open the complete reference only for status/contact/conflict boundaries.

## Workflow

1. Identify the entry mode: product outbound market analysis, a specified background-research subject, single company, product plus customer-development scope, keywords, application/downstream field, country/customer type, existing table, competitor/seed, or source material list.
   - If the core request is one product entering/exporting to a target country/region for trends, price references, compliance, import duties/taxes, export requirements, logistics, customs pre-filing, COO/proof of origin, or external factors, route to `analyzing-product-outbound-market`.
   - If the user asks for customers, buyers, importers, lead lists, or prospect development, keep the bulk customer-development route.
   - If the user names one company, brand, domain, email, address, Candidate, or user material and asks for background research, route to customer background research.
   - If the user asks for market analysis and then finding customers, split it into two stages and start with product outbound market analysis only.
   - If certification/compliance words describe the target customer attribute, such as `找需要 CE/UL 认证的进口商`, keep the bulk customer-development route. If the user asks whether the product needs CE/UL/SDS/UN38.3/COO, tariffs, labeling, customs documents, or market-access requirements for a destination, route to product outbound market analysis.
2. Check the minimum research target. For new customer development require product/service plus at least one scope axis. A user who names one company, brand, domain, address, email, Candidate, or user material and asks for customer background research follows `using-superleads` → `scoping-lead-research` → `researching-customer-background`; retain the original anchor without requiring pre-resolved Entity. For single-company analysis, retain the current user's explicit company name, URL/domain, or material reference and bind the result to that Entity only. For existing-table enrichment, retain the user-provided spreadsheet and the rows/cells being supplemented. These routes do not create a direction-matched customer list without the current development contract.
3. Create a Run Context with `run_id`, timestamp, task entry mode, platform, detected capabilities, requested output mode, evidence depth, and whether this run defaults to discovery-first or strict deep-check.
4. Run or emulate `scripts/preflight_capabilities.py --require-formal-research` before any formal public-source route. Formal customer development, customer background research, and product-market analysis require `search.web` plus one of `source.open`, `browser.render`, or `document.extract`. If the check is blocked, stop and tell the user: `本轮环境无法联网检索并打开可记录来源，不能完成 Superleads 正式外贸研究。请切换到具备 Web Search 和来源打开能力的 Agent/环境后重试。若只需整理已有资料，可以继续，但那不是市场分析或客户开发报告。` Do not offer a research plan or discovery candidate pool as a substitute delivery. In a Codex CLI session started with `codex --search`, inspect only the currently visible native `web_search` capability and write the controlled adapter report from actual operation results; do not assume another integration exists.
5. Route to the next skill unless the task is already a pure verification/export task. Product outbound market analysis routes to `analyzing-product-outbound-market` and uses `ProductMarketAnalysisGraph`, not Candidate/Lead/Claim/Assessment. The default customer-development route remains `using-superleads` → `scoping-lead-research` → `discovery` → `exporting-lead-workbooks`. A specified-object customer background request is a separate research-draft route, not default bulk discovery and not the current formal review/audit route. Do not route every “background check” into strict Review/Audit. Discovery uses the planning, execution, contact, and relevance guides internally as needed; it does not require every Candidate to have an Entity, Observation, ContactClaim, Claim, Assessment, Review, or Audit. Use the strict review/audit route only for an explicit formal verification, contact ownership verification, a contactable list, or a standard development list.

## 产品出海市场分析入口

When routing to product outbound market analysis, respond in user-facing Chinese with four short lines:

`我理解你要做的是：产品出海市场分析。`
`本轮对象：{产品/品类/候选 HS-HTS} → {目的国/地区}。`
`默认出口申报国/原产口径：{用户指定/中国默认}；缺型号、起运地、最终税号或技术文件时会保留为条件和待确认项，不会先要求补齐。`
`我会整理趋势、公开价格参考、准入/认证要求、税费、出口要求、物流和外部因素；不生成客户名单，也不判断是否值得进入。`

Ask at most three short questions only if the product identity or target country/region is missing. Do not ask for export/origin details as a first-pass blocker; if the user did not specify them, show the China default as visible and replaceable.

## 本次方向

For a new customer-development request, first respond in at most four short
user-facing lines: `我理解你卖的是`、`本次优先找`、`本次不纳入`、`判断依据将重点看`.
Keep the user's natural language in the current Brief; never display internal
Claim, Candidate, ScopeDecision, or rule IDs. Ask at most one to three short
questions only when the answer would reverse the customer direction. Do not
ask again when the user already made it clear.

If a critical ambiguity remains, create a provisional direction and return at
most three to five `方向样本，等待确认后再扩展为正式开发名单`. Do not create a
standard list. Competitors, brands, manufacturers, and other references are
search or market references by default, not automatic prospects.

Unknown direction and sample-first work produce only initial direction
samples or a discovery candidate pool. Do not silently promote them to a
standard list, and do not expose internal evidence markers, rule IDs,
Claims, or audit terms to the user.

## Material intake

Classify user material before using it: published source copy, user business dataset, correspondence export, user-authored note, visual reference, connected inbound correspondence, or unknown. Product requirements belong in the Brief; pasted company/contact text is a clue, not a formal fact. If a file is ambiguous, use `user_business_dataset` or `unknown` and ask only whether it is an original public/other-party source or the user's own historical list/notes.

When the formal source-capability gate is blocked, user-provided materials may
still be organized or checked against the user's stated question. Call this a
`资料初审` and state that it does not replace public-source research. Do not
search-plan, generate a candidate pool, or export it as a formal Superleads
report in that state.

For an explicitly approved connected mailbox, capture only inbound mail within the requested folder/label and time/filter scope through `mail.read`. Route it to an Inquiry follow-up queue, not directly to a qualified lead or standard list. Never send, reply, mark read, move, delete, archive, or scan mail by default. Without `mail.read`, request an EML/PDF/mail export.

## Output

Return a concise Run Context and the next Superleads skill to use. Ask only for
missing fields that block the minimum research target.

When the user asks to “直接给我看报告”, “用 Markdown 表格”, “在 ChatGPT app /
Codex 里展示”, or otherwise wants a chat-readable deliverable, route the
reviewed graph to the unified Markdown delivery layer:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route auto --output report.md --format json
```

This is mandatory for formal Markdown delivery. Do not hand-render Markdown
from `export_workbook.py` sheets. Do not manually convert workbook/CSV rows
into a substitute Markdown report, and do not relabel signal-status columns as
`依据状态`. If the unified Markdown command cannot be run or fails validation,
report that failure and stop instead of fabricating a report. A valid bulk
customer development Markdown report starts with `# 批量客户开发` and contains
`发现候选池样表（候选池不是正式开发名单）` with columns including `分区`,
`业务相关性`, and `依据状态`.

For real-business research, a formal Markdown delivery requires a saved graph
JSON path and a successful `export_superleads_markdown.py` JSON result. If you
only have live search notes, source snippets, or a manually synthesized table,
label it as a research draft / source-collection note, not as a formal
Superleads delivery, and do not claim `ok=true` or `issue_count=0`. Build or
repair the graph first, then run the exporter. Never write `依据状态` as internal
public-signal labels such as `已观察`, `未检索`, `主体待确认`, `已观察；需确认`,
or `已观察；来源受限`.

When reporting a formal run, the claimed Markdown path must be the exact file
written by `export_superleads_markdown.py` for the claimed graph JSON. Do not
post-process, rewrite, or replace that file with a manually edited report while
still quoting the exporter's `ok=true` / `issue_count=0` result. If a user asks
for verification, compare the claimed Markdown path against a fresh exporter
run from the claimed graph.

Keep the three user-visible routes separate:

- Bulk customer development shows a candidate customer pool and pending checks.
- Customer background research shows one specified object's background report.
- Product outbound market analysis shows a product market/access matrix and
  does not generate customer lists or market-entry recommendations.

Do not expose internal graph, Claim, EvidenceCard, SearchLog, rule IDs, eval
names, local paths, or artifact hashes in the user-facing report.

## Hard constraints

- Do not import old industry Skill defaults or assume ICP, country, company size, channel, or platform.
- Do not treat weak evidence as failure; plan to label it and keep the Candidate.
- Do not allow search snippets to become Claims later.
- Do not default to “筛剩少量推荐客户”. Default output is a traceable candidate pool with public signals, unknowns, and coverage notes.
- Native `web_search` grants only initial search capability by default. Record
  source opening only after this session actually obtains an HTTP(S) URL,
  source identifier, verbatim source text, and locator; otherwise offer a
  research plan or initial leads. Do not install, configure, or rely on an
  external tool server.
- The native report controls only search and source opening. Keep separately
  available document extraction, page rendering, image inspection, or mail
  reading in their own host capability records; do not discard them because a
  native search report is present.
- When a native report is present, record every capability used for a source
  in that Run explicitly as available. An omitted rendering, document, image,
  or mail capability cannot be used to form a formal source record.
- In Codex CLI, a shell reader may separately open a public source only after
  a recorded successful read-only GET. Keep the host as Codex CLI and record
  the reader separately; do not describe a command name as the platform, or
  treat it as search capability. Never use it for logged-in, private, or
  restricted pages.
- When recording a platform, use one canonical host ID: lowercase ASCII
  letters, digits, and underscores only. This keeps hosts such as `hermes`,
  `claude`, and `workbuddy` portable while rejecting tool names, whitespace,
  uppercase, and hyphen variants. A public-source graph check rejects literal
  private and legacy numeric-IP forms without DNS resolution; the actual HTTP
  executor must still block non-global DNS results and redirect targets.
- Do not infer a product, application, role, exclusion, commercial model, or
  customer boundary from legacy skills or another Run.
