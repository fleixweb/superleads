---
name: using-superleads
description: "Use for batch discovery of public overseas B2B customer information from product or keyword, target market, and customer type. Do not use for single-customer background research or product outbound market analysis."
---

# 批量发现公开客户信息

## Purpose

批量发现公开客户信息：基于产品或关键词、目标市场和客户类型，建立带来源状态、未知项与限制说明的候选池。不得用于单一客户背调或产品出海市场分析；独立的这两项必须分别从 `researching-customer-background` 和 `analyzing-product-outbound-market` 公开入口开始。

只交付带来源状态的候选池，不推荐客户、不判断采购意愿，也不把搜索摘要写成 Claim。不要在此入口替单一客户背调或产品市场分析创建独立报告、计划或研究图谱。

若同一次请求包含任意两个或以上明确业务目标，本入口保留批量发现子任务（如有），并创建一个父级组合任务；不得要求用户为了内部架构而拆成多次调用。组合父任务只协调已明确的子路线，不把批量发现入口改成单一客户背调或产品市场分析的独立入口。

## Required references

Read `../../shared/references/superleads-user-guidance.md` first for static first-use help and final user-delivery rules. Read `../../shared/references/user-intake.md` for intake modes and the bulk-discovery minimum research target. Read `../../shared/policies/tool-capability-policy.md` when tool availability affects deliverable level. For default discovery, read `../../shared/references/default-discovery-reference.md`; begin with `default-discovery-minimal-skeleton.example.json`, and open the complete reference only for status/contact/conflict boundaries. Before any formal bulk public-source route or real-business UAT, read `../../shared/references/using-superleads-formal-delivery.md`.

## Workflow

1. Before any business routing, run the pure mode classifier. `metadata` covers `@superleads`, help, current/installed-version questions, current-capability questions, and the feedback entry; it returns `operations: []` and never creates a Run/Brief, runs preflight, searches, opens sources, scans caches, exports, or validates. Keep `@superleads` and help on `static_help_response()` only. Read a version only from an explicitly supplied active plugin root's `.codex-plugin/plugin.json`; check a remote version only for an explicit update request through an injected callback, and report `本次未能确认远端版本` if it cannot be confirmed.
2. `material_triage` is the user-visible `资料初审` path for material-only PDF, Excel/CSV, or screenshot requests. It organizes only the provided material and pending checks; it creates no Run/Brief and does not begin public research. Otherwise, use `discovery_snapshot` for ordinary bounded batch discovery and `formal_research` only for explicit `正式开发名单` or `标准交付` intent.
3. Confirm this is a batch customer-discovery request: the user seeks customers, buyers, importers, lead lists, or prospect development by product/service or keywords plus at least one scope axis such as market, application, customer type, or existing table. A named single company, brand, domain, email, address, or material for background investigation with no second explicit business objective must stop here and use `researching-customer-background`. A product entering a target market for trends, price, compliance, tax, export, logistics, COO, or external factors with no second explicit business objective must stop here and use `analyzing-product-outbound-market`. When the same request has any two or more clear objectives, create the composite parent described below instead of making the user split the request.
4. Check the minimum batch-discovery target: product/service plus at least one scope axis. For existing-table enrichment, retain the user-provided spreadsheet and the rows/cells being supplemented. These results do not create a direction-matched customer list without the current development contract.
5. Create a Run Context only for `discovery_snapshot` or `formal_research`, with `run_id`, timestamp, task entry mode, platform, detected capabilities, requested output mode, evidence depth, and whether this run defaults to discovery-first or strict deep-check.
6. Run or emulate `scripts/preflight_capabilities.py --require-formal-research` before formal batch public-source research. It requires `search.web` plus one of `source.open`, `browser.render`, or `document.extract`. If the check is blocked, stop and tell the user: `本轮环境无法联网检索并打开可记录来源，不能完成 Superleads 正式客户开发研究。请切换到具备 Web Search 和来源打开能力的 Agent/环境后重试。若只需整理已有资料，可以继续，但那不是客户开发报告。` Do not offer a research plan or discovery candidate pool as a substitute delivery. In a Codex CLI session started with `codex --search`, inspect only the currently visible native `web_search` capability and write the controlled adapter report from actual operation results; do not assume another integration exists.
7. Before the formal validator in a real-business UAT, run `scripts/precheck_superleads_uat_input.py --route bulk_customer_development --graph <graph> --format json`. It checks only source-literal anchors, contact association, and enum values; it does not replace the formal validator. Fix reported structural input errors rather than rerunning the formal validator to discover the same issue.
8. For a real-business UAT, build the runtime package and initialize `scripts/measure_superleads_uat.py` in a UTC-named, durable `.plugin-eval/manual/uat-runs/` directory with `--runtime-package`. Record every gate's original result with `record-gate --artifact`, finish with `finalize`, then run `verify` against the completed bundle and a copied bundle. A `/tmp` run may retain a failed diagnostic record but can never establish a portable formal success. Record failed attempts with the prescribed failure class, stop active-time intervals around waits, and never describe a corrected run as first-pass success, compare Git status through hand-written text, or estimate unavailable token usage.
9. Route the batch request through `using-superleads` -> `scoping-lead-research` -> `writing-research-plans` -> `executing-research-plans` -> `verification-before-delivery` -> `exporting-lead-workbooks`. Discovery uses the planning, execution, contact, identity, and relevance guides internally as needed; it does not require every Candidate to have an Entity, Observation, ContactClaim, Claim, Assessment, Review, or Audit. Use the strict review/audit route only for an explicit formal verification, contact ownership verification, a contactable list, or a standard development list.

## 组合任务

本次请求包含任意两个或以上明确业务目标时，建立一个父级组合任务。批量发现只是其中一个可能的子任务；客户背调加市场分析、客户背调加表格补全、批量发现加公开联系人等组合也适用。先提取共享信息：指定公司、品牌、域名、地址、邮箱或社媒链接；产品、型号或品类；目标国家或地区；客户类型、资料范围和输出要求；以及哪一个子任务确实依赖另一个子任务的结果。

按用户明确目标建立独立子路线：

- 指定公司、品牌、域名、地址、邮箱或社媒链接对应客户背调子任务。
- 产品加目的国或地区对应产品市场分析子任务。
- 产品加客户范围对应批量客户发现子任务。
- 用户提供表格对应表格补全子任务；范围仅限该表及用户指定字段。
- 明确要求公开联系人对应公开联系人补充子任务；它只补充本次指定公司或候选范围内的公开关联信息。
- 明确要求导出对应最终导出子任务；它必须等待相关上游结果有当前 Run、已打开来源和合法交付前置条件后才可开始。

缺少产品或目的国等必要信息时，只把受影响的子任务标为“等待必要信息”。不得从公司主营业务、搜索摘要、其他子任务材料或模型记忆猜测补齐；其他可独立执行的子任务继续进行。不要因用户提及联系人、表格或导出而擅自创建对应子任务。

### 子任务边界与调度

独立子任务的查询组、不同来源页面、不同候选的公开联系人补充、不同资料文件整理和轻量结构检查可以分别规划。只有当前宿主实际提供并行工具能力时才可并行执行；不得伪造后台、流式进度或并行工具能力。没有这些能力时，在阶段边界给出简短、真实的父任务和子任务状态，不要假称正在后台处理。

下列工作必须串行：同一主体的身份合并、同一来源的冲突处理、Claim 或正式证据升级、存在明确数据依赖的子任务，以及最终审核、正式导出和组合报告汇总。市场准入分析缺少必要输入时不阻塞独立的客户背调；导出只等待其对应的上游子任务。

同一实际已打开来源可被多个子任务引用，但每个子任务必须各自记录用途、观察范围和证据边界。不得让一个子任务的来源自动升级为另一个子任务的事实：公司官网只支持公司业务、公开地址或公开联系人等公司事实；法规、海关、认证和监管来源只支持产品或市场准入事实。公司存在、进口记录、职位信息或市场准入要求均不能证明采购意向、买家身份或客户价值；搜索摘要仍只是线索。

### 组合任务状态与交付

若宿主支持中间状态，按阶段用非技术化短句显示父任务和各子任务的范围、已完成查询组、已发现候选或已打开来源数、已有明确依据、待确认、来源受限和本轮未执行数，以及“进行中”“等待必要信息”“已完成”“部分完成”“来源受限”或“无法执行”。若宿主不支持中间状态，最终交付提供同样的阶段摘要，但不得伪造实时进度或暴露内部技能名、Run ID、graph、Claim 或 Audit。

最终交付为一个父报告，依次说明本次范围与已执行子任务、客户公开背景结果、产品市场或准入结果、各子任务的来源受限/待确认/未执行项、来源与检查时间；需要时按既定规则仅追加一次更新提示。一个子任务因必要信息缺失、来源受限或能力不可用而无法完成时，交付其他已经完成的子任务，并说明该子任务的原因和用户可补充的公开信息。不得把组合结果写成客户值得开发、建议优先跟进、市场值得进入、该客户会采购该产品，或其他商业判断。

## 本次方向

For a new customer-development request, first respond in at most four short user-facing lines: `我理解你卖的是`、`本次优先找`、`本次不纳入`、`判断依据将重点看`. Keep the user's natural language in the current Brief; never display internal Claim, Candidate, ScopeDecision, or rule IDs. Ask at most one to three short questions only when the answer would reverse the customer direction. Do not ask again when the user already made it clear.

If a critical ambiguity remains, create a provisional direction and return at most three to five `方向样本，等待确认后再扩展为正式开发名单`. Do not create a standard list. Competitors, brands, manufacturers, and other references are search or market references by default, not automatic prospects.

Unknown direction and sample-first work produce only initial direction samples or a discovery candidate pool. Do not silently promote them to a standard list, and do not expose internal evidence markers, rule IDs, Claims, or audit terms to the user.

## Material intake

Classify user material before using it: published source copy, user business dataset, correspondence export, user-authored note, visual reference, connected inbound correspondence, or unknown. Product requirements belong in the Brief; pasted company/contact text is a clue, not a formal fact. If a file is ambiguous, use `user_business_dataset` or `unknown` and ask only whether it is an original public/other-party source or the user's own historical list/notes.

When the formal source-capability gate is blocked, user-provided materials may still be organized or checked against the user's stated question. Call this a `资料初审` and state that it does not replace public-source research. Do not search-plan, generate a candidate pool, or export it as a formal Superleads report in that state.

For an explicitly approved connected mailbox, capture only inbound mail within the requested folder/label and time/filter scope through `mail.read`. Route it to an Inquiry follow-up queue, not directly to a qualified lead or standard list. Never send, reply, mark read, move, delete, archive, or scan mail by default. Without `mail.read`, request an EML/PDF/mail export.

## Output

Return a concise Run Context and the next Superleads skill to use. Ask only for missing fields that block the minimum research target.

Only a terminal user delivery follows the footer rules in `../../shared/references/superleads-user-guidance.md`. Progress updates and standalone clarifications do not append the footer.

When the user asks to "直接给我看报告", "用 Markdown 表格", "在 ChatGPT app / Codex 里展示", or otherwise wants a chat-readable deliverable, route the reviewed graph to the unified Markdown delivery layer:

```bash
python3 scripts/export_superleads_markdown.py graph.json --route auto --output report.md --format json
```

This is mandatory for formal Markdown delivery. Do not hand-render Markdown from `export_workbook.py` sheets. Do not manually convert workbook/CSV rows into a substitute Markdown report, and do not relabel signal-status columns as `依据状态`. If the unified Markdown command cannot be run or fails validation, report that failure and stop instead of fabricating a report. A valid bulk customer development Markdown report starts with `# 批量客户开发` and contains `发现候选池样表（候选池不是正式开发名单）` with columns including `分区`, `业务相关性`, and `依据状态`.

For real-business research, a formal Markdown delivery requires a saved graph JSON path and a successful `export_superleads_markdown.py` JSON result. If you only have live search notes, source snippets, or a manually synthesized table, label it as a research draft / source-collection note, not as a formal Superleads delivery, and do not claim `ok=true` or `issue_count=0`. Build or repair the graph first, then run the exporter. Never write `依据状态` as internal public-signal labels such as `已观察`, `未检索`, `主体待确认`, `已观察；需确认`, or `已观察；来源受限`.

When reporting a formal run, the claimed Markdown path must be the exact file written by `export_superleads_markdown.py` for the claimed graph JSON. Do not post-process, rewrite, or replace that file with a manually edited report while still quoting the exporter's `ok=true` / `issue_count=0` result. If a user asks for verification, compare the claimed Markdown path against a fresh exporter run from the claimed graph.

This entry covers only batch customer discovery: show a candidate customer pool and pending checks. Redirect single-customer background research and product-market analysis to their own public entries before any research starts.

Do not expose internal graph, Claim, EvidenceCard, SearchLog, rule IDs, eval names, local paths, or artifact hashes in the user-facing report.

## Hard constraints

- Do not import old industry Skill defaults or assume ICP, country, company size, channel, or platform.
- Do not treat weak evidence as failure; plan to label it and keep the Candidate.
- Do not allow search snippets to become Claims later.
- Do not default to "筛剩少量推荐客户". Default output is a traceable candidate pool with public signals, unknowns, and coverage notes.
- Native `web_search` grants only initial search capability by default. Record source opening only after this session actually obtains an HTTP(S) URL, source identifier, verbatim source text, and locator; otherwise offer a research plan or initial leads. Do not install, configure, or rely on an external tool server.
- The native report controls only search and source opening. Keep separately available document extraction, page rendering, image inspection, or mail reading in their own host capability records; do not discard them because a native search report is present.
- When a native report is present, record every capability used for a source in that Run explicitly as available. An omitted rendering, document, image, or mail capability cannot be used to form a formal source record.
- In Codex CLI, a shell reader may separately open a public source only after a recorded successful read-only GET. Keep the host as Codex CLI and record the reader separately; do not describe a command name as the platform, or treat it as search capability. Never use it for logged-in, private, or restricted pages.
- When recording a platform, use one canonical host ID: lowercase ASCII letters, digits, and underscores only. This keeps hosts such as `hermes`, `claude`, and `workbuddy` portable while rejecting tool names, whitespace, uppercase, and hyphen variants. A public-source graph check rejects literal private and legacy numeric-IP forms without DNS resolution; the actual HTTP executor must still block non-global DNS results and redirect targets.
- Do not infer a product, application, role, exclusion, commercial model, or customer boundary from legacy skills or another Run.
