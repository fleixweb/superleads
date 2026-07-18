# Route Map

Default route: `using-superleads` → `scoping-lead-research` → `writing-research-plans` → `executing-research-plans` → `collecting-contact-intelligence` → `assessing-research-evidence` → `exporting-lead-workbooks`.

Conditional additions:

- Use `resolving-company-identity` when names, domains, branches, brands, legal entities, resellers, or directory/official sources conflict.
- Use `reviewing-lead-research` → `verification-before-delivery` only when the user asks for a formal background check, contact ownership verification, trade/China identity verification, a contactable list, or a standard development list.
- Use `learning-from-feedback` only after user feedback on delivered lead quality or source usefulness.

State machine:

- 默认发现：`scoped` → `planned` → `collecting` → `assessed` → `initial_lead_list`
- 按需深查：`scoped` → `planned` → `collecting` → `assessed` → `under_review` → `remediation_required` → `remediation_submitted` → `re_reviewed` → `checked` → `standard_development_list` / `full_review_package`

弱证据不删除有用候选，只降级为业务相关性、未知项或待核查项。误导性错误才阻断交付。
