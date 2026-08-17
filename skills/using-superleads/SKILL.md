---
name: using-superleads
description: "Use for a concrete batch discovery request with product or keyword, target market, and customer type. For a bare Superleads activation or help request, return static help and do not initialize discovery. Do not use for single-company background research or product market analysis."
---

# 批量发现公开客户信息

## Bare Activation Fast Path

This rule takes precedence over every other instruction in this Skill. For a
bare `@`, `@superleads`, or a help/how-to-use request, call
`static_help_response()` and return only its user-facing `response_lines`.
For bare activation, do not read any research reference. Do not inspect files,
use shell commands, run preflight, search, open a source, create a Run/Brief,
export, validate, check versions, or scan caches. Do not describe this branch
as a workflow, a plan, or an initialization step.

The compact guide is the complete response for a bare activation. A user who
explicitly asks for detailed help may receive the longer static guide from the
same helper, still with no operational work. Match the user's language and do
not expose Skill, route, graph, Claim, or validator terminology.

## Batch Discovery Path

Only after the fast path does not apply, classify the request with the pure
intake rules. Metadata and user-material-only requests stay outside batch
research. A named single company, brand, domain, email, address, or social
link routes to `researching-customer-background`; a product entering a target
market routes to `analyzing-product-outbound-market`. A request containing two
or more explicit business objectives becomes a parent composite task with
isolated subroutes.

Use this Skill only when the user has a concrete batch request: customers,
buyers, importers, distributors, or a customer list tied to a product/service
or keyword plus a scope axis such as market, application, customer type, or an
existing table. Do not infer ICP, company size, channel, purchase intent, or
customer value.

不得用于单一客户背调或产品出海市场分析；它们应转到各自公开入口。

## 组合任务

同一次请求有任意两个或以上明确业务目标时，建立一个父级组合任务；不得要求用户为了内部架构而拆成多次调用。按目标建立客户背调子任务、产品市场分析子任务、批量客户发现子任务、表格补全子任务、公开联系人补充子任务，或在前置结果合法后建立最终导出子任务。缺少必要输入的子任务标为等待必要信息，不阻塞其他独立子任务。

不同子任务的独立查询可并行，但同一主体的身份合并、冲突处理，以及最终审核、正式导出和组合报告汇总必须串行。不得伪造后台、流式进度或并行工具能力。不得让一个子任务的来源自动升级为另一个子任务的事实；详细的隔离和交付规则见下面的按需参考。

For a concrete batch request, read
`../../shared/references/batch-discovery-execution.md`. It contains the
required evidence boundaries, discovery snapshot budget, formal-delivery gate,
composite-task isolation, material handling, and user-visible delivery rules.
For a real-business UAT or a formal batch delivery, also read
`../../shared/references/using-superleads-formal-delivery.md`.

## Delivery Boundary

Default delivery is a traceable candidate pool with public-source status,
unknowns, and pending checks. It is not a recommended customer list and does
not state purchase intent. Search snippets remain clues and never become
Claims. Only an explicit request for formal verification, a formal development
list, a complete report, contact ownership verification, or Markdown export
may enter the strict graph, audit, and exporter path.

An explicit formal request follows `using-superleads` ->
`scoping-lead-research` -> `writing-research-plans` ->
`executing-research-plans` -> `verification-before-delivery` -> `exporting-lead-workbooks`.

Only a terminal user delivery follows the footer rules in
`../../shared/references/superleads-user-guidance.md`; progress updates and standalone clarifications do not append the footer.
