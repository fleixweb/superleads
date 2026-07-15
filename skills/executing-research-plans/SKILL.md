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

## Access handling

If a page is blocked, inaccessible, login-wall, or unavailable, record that status. Do not invent page content and do not let that observation support a Claim.

## Hard constraints

- `search.web` must never directly support a Claim.
- Do not infer contact ownership from proximity alone on multi-company pages.
- Do not finalize identity merges; route conflicts to `resolving-company-identity`.
