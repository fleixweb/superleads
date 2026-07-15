---
name: executing-research-plans
description: "Execute Superleads research plans by producing Candidate, Source, Observation, Provisional Entity, and Search Log records from public or user-provided materials. Use when collecting raw research evidence before assessment; never use search snippets as Claims."
---

# Executing Research Plans

## Purpose

Collect raw research artifacts: Candidate, Source, Observation, Provisional Entity, and Search Log. Do not output formal development lists, final advice, purchasing-intent claims, guessed contacts, or Claims.

## Required references

Read `../../shared/policies/tool-capability-policy.md`, `../../shared/policies/claim-and-source-policy.md`, and `../../shared/schemas/source-observation.schema.json`.

## Workflow

1. Run planned searches and record Search Log entries.
2. Treat search results as Candidate clues only.
3. Open or render sources before creating Observations.
4. For every Observation record capability, concrete tool, observed time, access status, title, raw excerpt, locator, hash when possible, language, and translation linkage if applicable.
5. Create Provisional Entity records only when enough name/domain/source context exists.
6. For each current-direction check, record which opened Observations were
   reviewed. A Candidate without a resolved Entity can only remain a direction
   sample or reference; do not mark it as a confirmed prospect.

## User-provided file evidence

For a PDF or spreadsheet that may later support formal delivery, create a `user_provided` document/spreadsheet Source only after `document.extract` has produced an excerpt. Record a lowercase SHA-256 from the original file bytes when available, a safe filename only, `material_role=published_source_copy`, and `artifact:sha256:<hash>#page=...` or `#sheet=...&range=...`. Historical tables use `user_business_dataset`; original mail/chat exports use `correspondence_export`; pasted notes use `user_authored_note` and stay clues. Never store a local path or treat pasted user text as document extraction.

For a logo, product photo, business-card image, or screenshot, use `material_role=visual_reference` and `image.inspect`. Preserve OCR as `ocr_text` and visual descriptions as `visual_description`; create Candidates, queries, Hypotheses, or UnassignedContactLeads only. Use public website, registry, or trademark evidence for any ownership claim.

For an approved connected mailbox, use `mail.read` only for bounded inbound header/body excerpts. Store message SHA-256, opaque mailbox reference, received time, and a safe `mail:sha256:<hash>#part=...` locator, never a password/token/path/full body. Create Inquiry, Candidate, entity-resolution, and external verification tasks. A mail attachment remains `unknown` unless explicitly classified; only a hashed `published_source_copy` document/spreadsheet attachment can later use the formal file path.

## Access handling

If a page is blocked, inaccessible, login-wall, or unavailable, record that status. Do not invent page content and do not let that observation support a Claim.

## Hard constraints

- `search.web` must never directly support a Claim.
- Do not infer contact ownership from proximity alone on multi-company pages.
- Do not finalize identity merges; route conflicts to `resolving-company-identity`.
- Do not promote a competitor, brand, manufacturer, or search seed into the
  customer pool unless the current Brief explicitly permits it and its current
  direction is later supported by formal same-Entity evidence.
