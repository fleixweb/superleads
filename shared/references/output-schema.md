# User-facing Output Schema

Use Chinese business sheet names.

Default discovery workbook:

- 发现候选池
- 联系方式汇总
- 官网与来源链接
- 搜索覆盖与收敛
- 待核查事项
- 已排除客户
- 风险与说明

Standard development workbook:

- 客户信息总表
- 联系方式汇总
- 开发建议
- 官网与来源链接
- 待核查事项
- 风险与说明

Full review workbook:

- 开发需求
- 关键词与搜索思路
- 发现候选池
- 客户信息总表
- 联系方式汇总
- 开发建议
- 官网与来源链接
- 待核查事项
- 已排除客户
- 检查说明

Avoid exposing internal artifact names such as Candidate Preview, Research Draft, Audit Package, Entity, ClaimEvidence, ContactClaim, or DeliveryManifest as user-facing sheet names.

## Default discovery presentation

发现候选池以 `directly_related` 和 `possibly_related` 为主体，并单独保留
`identity_pending`、`insufficient_information` 和明确排除记录。默认输出展示：

- 发现来源与发现链接
- 去重依据
- 业务相关性状态与依据
- 官网/联系方式、贸易、China、货描/HS 的统一状态
- 主体匹配状态
- 未知项、来源受限与下一步待验证
- 搜索覆盖、未覆盖路径与收敛说明

`not_observed` 仅表示“已查未见”，`not_searched` 表示“未知”，都不是商业否定结论。

`directly_related`、`possibly_related` 和
`explicitly_excluded_or_unrelated` 必须展示来自已观察业务/产品/服务/应用/角色/渠道/
地域或明确排除事实的 `business_match` 信号：至少一条非空说明及其来源标签或安全公开
URL。`identity_pending` 和 `insufficient_information` 可展示主体冲突、未知和来源缺口，
不能为了填表伪造已观察业务信号，也不能因此静默删除 Candidate。工作簿只展示安全、无
凭据的公开 HTTP(S) 发现和信号 URL：URL userinfo、敏感 query/fragment 参数（含 SPA
fragment route 内嵌 query）、本地/
私网/回环地址和非 HTTP(S) scheme 均不导出。官网/域名列可保留纯公开域名文本，但不自动
补全或猜测协议；无安全 URL 时保留来源标签或受限说明而不猜测链接。

## Current-direction presentation for standard delivery

Standard and full customer main tables, contact summaries, and development
suggestions include only entities that are `符合本次方向` in the current task.
`需确认`, `不符合本次方向`, and `仅作参考` may appear only in initial samples,
pending items, or a separate full-review reference/exclusion section; they are
never shown as recommended customers.

Use business labels only. Do not emit targeting-contract or scope-decision
names, rule IDs, Claim/ClaimEvidence identifiers, Candidate/Assessment/
Review/Audit names, internal checks, local paths, file URIs, or hashes in
user-facing workbook cells.
