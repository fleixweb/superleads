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
2. Check the minimum research target. For new customer development require product/service plus at least one scope axis. For single-company, existing table, PDF/directory/list/screenshot tasks, require only a clear company or parseable material.
3. Create a Run Context with `run_id`, timestamp, task entry mode, platform, detected capabilities, requested output mode, and evidence depth.
4. Run or emulate `scripts/preflight_capabilities.py` when tools are uncertain. Record gaps and downgrade if source-opening or document extraction is unavailable.
5. Route to `scoping-lead-research` next unless the task is already a pure verification/export task.

## Output

Return a concise Run Context and the next Superleads skill to use. Ask only for missing fields that block the minimum research target.

## Hard constraints

- Do not import old industry Skill defaults or assume ICP, country, company size, channel, or platform.
- Do not treat weak evidence as failure; plan to label it.
- Do not allow search snippets to become Claims later.
