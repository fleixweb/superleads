---
name: using-superleads
description: "Use when users need overseas B2B customer discovery, public contact collection, lead-list enrichment, or foreign-trade prospect research."
---

# Using Superleads

## Purpose

Activate Superleads, identify the user's task entry, create Run Context, decide whether this run is default discovery or explicit deep verification, check tool capability, and route to the next skill. Do not search, generate leads, write development advice, or export workbooks here.

## Required references

Read `../../shared/references/user-intake.md` for intake modes and minimum research targets. Read `../../shared/references/route-map.md` for routing. Read `../../shared/policies/tool-capability-policy.md` when tool availability affects deliverable level. For default discovery, read `../../shared/references/default-discovery-reference.md`; begin with `default-discovery-minimal-skeleton.example.json`, and open the complete reference only for status/contact/conflict boundaries.

## Workflow

1. Identify the entry mode: a specified background-research subject, single company, product plus scope, keywords, application/downstream field, country/customer type, existing table, competitor/seed, or source material list.
2. Check the minimum research target. For new customer development require product/service plus at least one scope axis. A user who names one company, brand, domain, address, email, Candidate, or user material and asks for customer background research follows `using-superleads` → `scoping-lead-research` → `researching-customer-background`; retain the original anchor without requiring pre-resolved Entity. For single-company analysis, retain the current user's explicit company name, URL/domain, or material reference and bind the result to that Entity only. For existing-table enrichment, retain the user-provided spreadsheet and the rows/cells being supplemented. These routes do not create a direction-matched customer list without the current development contract.
3. Create a Run Context with `run_id`, timestamp, task entry mode, platform, detected capabilities, requested output mode, evidence depth, and whether this run defaults to discovery-first or strict deep-check.
4. Run or emulate `scripts/preflight_capabilities.py` when tools are uncertain. Record gaps and downgrade if source-opening or document extraction is unavailable. In a Codex CLI session started with `codex --search`, inspect only the currently visible native `web_search` capability and write the controlled adapter report from actual operation results; do not assume another integration exists.
5. Route to `scoping-lead-research` next unless the task is already a pure verification/export task. The default route remains `using-superleads` → `scoping-lead-research` → `discovery` → `exporting-lead-workbooks`. A specified-object customer background request is a separate research-draft route, not default bulk discovery and not the current formal review/audit route. Do not route every “background check” into strict Review/Audit. Discovery uses the planning, execution, contact, and relevance guides internally as needed; it does not require every Candidate to have an Entity, Observation, ContactClaim, Claim, Assessment, Review, or Audit. Use the strict review/audit route only for an explicit formal verification, contact ownership verification, a contactable list, or a standard development list.

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

For an explicitly approved connected mailbox, capture only inbound mail within the requested folder/label and time/filter scope through `mail.read`. Route it to an Inquiry follow-up queue, not directly to a qualified lead or standard list. Never send, reply, mark read, move, delete, archive, or scan mail by default. Without `mail.read`, request an EML/PDF/mail export.

## Output

Return a concise Run Context and the next Superleads skill to use. Ask only for missing fields that block the minimum research target.

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
