# User-facing Output Schema

Use Chinese business sheet names.

Default development workbook:

- 客户信息总表
- 联系方式汇总
- 开发建议
- 官网与来源链接
- 待核查事项
- 风险与说明

Full review workbook:

- 开发需求
- 关键词与搜索思路
- 初筛客户名单
- 客户信息总表
- 联系方式汇总
- 开发建议
- 官网与来源链接
- 待核查事项
- 已排除客户
- 检查说明

Avoid exposing internal artifact names such as Candidate Preview, Research Draft, Audit Package, Entity, ClaimEvidence, ContactClaim, or DeliveryManifest as user-facing sheet names.

## Current-direction presentation

Standard and full customer main tables, contact summaries, and development
suggestions include only entities that are `符合本次方向` in the current task.
`需确认`, `不符合本次方向`, and `仅作参考` may appear only in initial samples,
pending items, or a separate full-review reference/exclusion section; they are
never shown as recommended customers.

Use business labels only. Do not emit targeting-contract or scope-decision
names, rule IDs, Claim/ClaimEvidence identifiers, Candidate/Assessment/
Review/Audit names, internal checks, local paths, file URIs, or hashes in
user-facing workbook cells.
