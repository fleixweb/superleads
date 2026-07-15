---
name: scoping-lead-research
description: "Form a Superleads Research Brief, complete the minimum research target, record contact requirements, output mode, evidence depth, target count, and business context without forcing an industry ICP. Use after Superleads intake or when a lead-research request needs structured scoping before planning."
---

# Scoping Lead Research

## Purpose

Create a Research Brief that captures the user's task without turning optional context into core ICP rules.

## Required references

Read `../../shared/references/user-intake.md` and `../../shared/references/product-profile-input.md`. Use `../../shared/schemas/brief.schema.json` for fields.

## Brief fields

Populate `product_or_service`, `scope_axis`, `task_mode`, `contact_detail_level`, `output_mode`, `application_context`, `target_country_or_region`, `target_customer_type`, `target_channel`, `keywords`, `seed_companies`, `seed_urls`, `existing_table`, `competitors_or_brands`, `excluded_targets`, `must_verify_claims`, `evidence_depth`, `target_count`, and optional `business_context`.

## Scoping rules

- For new customer development, require product/service plus at least one scope axis.
- For single-company analysis, existing-table enrichment, PDF/directory/list/screenshot cleanup, require a clear company or parseable material.
- Record desired contact depth explicitly: standard, contact priority, or full review.
- Use user-facing output modes: 初筛客户名单, 标准开发名单, 联系方式优先, 补全已有表格, 完整核查版.

## Output

Return a valid Brief object plus unresolved questions. Keep questions minimal and specific.

## Hard constraints

Do not classify the user as factory/OEM/industrial/consumer by default. Do not add legacy country, size, or customer-type assumptions.
