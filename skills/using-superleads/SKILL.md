---
name: using-superleads
description: "Use when the user wants to discover, qualify, enrich, organize, audit, or export overseas buyer leads for foreign trade from public or user-provided sources. Trigger for product-based overseas customer development, keyword-based prospecting, country or region lead research, importer/distributor/wholesaler/retailer/brand/OEM/end-user prospecting, public contact collection, customer list enrichment, company website analysis, trade fair/directory/PDF/social visible-source review, and evidence-backed sales lead workbook creation. Also use when the user explicitly says Superleads, superleads, 外贸客户开发, 海外客户开发, 找客户, 开发客户, 潜在客户, 客户名单, 补全客户表, 查联系方式, 找进口商, 找经销商, 找采购联系人, or similar."
---

# Using Superleads

## Purpose

Activate Superleads, identify the user's task entry, create Run Context, check tool capability, choose output level, and route to the next skill. Do not search, generate leads, write development advice, or export workbooks here.

## Required references

Read `../../shared/references/user-intake.md` for intake modes and minimum research targets. Read `../../shared/references/route-map.md` for routing. Read `../../shared/policies/tool-capability-policy.md` when tool availability affects deliverable level.

## Workflow

1. Identify the entry mode: single company, product plus scope, keywords, application/downstream field, country/customer type, existing table, competitor/seed, or source material list.
2. Check the minimum research target. For new customer development require product/service plus at least one scope axis. For single-company analysis, retain the current user's explicit company name, URL/domain, or material reference and bind the result to that Entity only. For existing-table enrichment, retain the user-provided spreadsheet and the rows/cells being supplemented. These two routes do not create a direction-matched customer list without the current development contract.
3. Create a Run Context with `run_id`, timestamp, task entry mode, platform, detected capabilities, requested output mode, and evidence depth.
4. Run or emulate `scripts/preflight_capabilities.py` when tools are uncertain. Record gaps and downgrade if source-opening or document extraction is unavailable. In a Codex CLI session started with `codex --search`, inspect only the currently visible native `web_search` capability and write the controlled adapter report from actual operation results; do not assume another integration exists.
5. Route to `scoping-lead-research` next unless the task is already a pure verification/export task.

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
samples. Do not silently promote them to a standard list, and do not expose
internal evidence markers, rule IDs, Claims, or audit terms to the user.

## Material intake

Classify user material before using it: published source copy, user business dataset, correspondence export, user-authored note, visual reference, connected inbound correspondence, or unknown. Product requirements belong in the Brief; pasted company/contact text is a clue, not a formal fact. If a file is ambiguous, use `user_business_dataset` or `unknown` and ask only whether it is an original public/other-party source or the user's own historical list/notes.

For an explicitly approved connected mailbox, capture only inbound mail within the requested folder/label and time/filter scope through `mail.read`. Route it to an Inquiry follow-up queue, not directly to a qualified lead or standard list. Never send, reply, mark read, move, delete, archive, or scan mail by default. Without `mail.read`, request an EML/PDF/mail export.

## Output

Return a concise Run Context and the next Superleads skill to use. Ask only for missing fields that block the minimum research target.

## Hard constraints

- Do not import old industry Skill defaults or assume ICP, country, company size, channel, or platform.
- Do not treat weak evidence as failure; plan to label it.
- Do not allow search snippets to become Claims later.
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
