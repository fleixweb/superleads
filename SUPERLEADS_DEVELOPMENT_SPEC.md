# Superleads 完整开发规范

版本：vFinal-2  
用途：交给 Codex / Claude Code / Hermes / WorkBuddy 等 Agent 实施开发  
目标：构建一套通用外贸线上客户开发 Skill Suite

---

## 1. 项目定位

项目名：

```text
superleads
```

显示名：

```text
Superleads
```

定位：

```text
Superleads 是一套通用外贸线上客户开发 Skill Suite。
它用于从公开互联网、用户提供文件、官网、目录、PDF、展会资料、地图、社媒可见页面等来源中，发现、整理、核查、分层输出海外潜在客户和联系方式。
```

Superleads 不是：

```text
行业 ICP 库
客户名单数据库
强验证系统
自动外联系统
LinkedIn 抓取器
成交预测系统
销售效果评估系统
某个品类专用 Skill
```

Superleads 是：

```text
外贸客户开发工作流
联系方式情报系统
证据分层系统
客户线索分层交付系统
跨 Agent / 跨平台方法论
```

---

## 2. 最重要的设计原则

### 2.1 外贸开发是弱证据场景

外贸客户开发不适合简单按：

```text
通过 / 失败
```

来处理，而应使用：

```text
初筛线索
推荐跟进
重点开发
需人工核查
暂不建议
排除
```

核心不是：

```text
弱证据不输出
```

而是：

```text
弱证据可以输出，但必须标清楚它是弱证据。
```

---

### 2.2 Superleads 的底线

允许：

```text
输出初筛客户
输出待核查客户
输出目录/展会/地图线索
输出联系方式待确认项
输出只有 contact form 的客户
输出弱证据客户
```

禁止：

```text
猜邮箱
无来源联系方式
把搜索摘要写成事实
把假设写成事实
把 LinkedIn 职位写成采购权事实
把弱证据写成强证据
把待核查客户写成已核查客户
错配公司和联系方式
```

---

### 2.3 联系方式是核心交付物

Superleads 的联系方式策略是：

```text
最大化召回有来源、可归属、可标注的联系方式情报。
```

应尽可能整理：

```text
企业邮箱
部门邮箱
销售邮箱
采购/供应商入口邮箱
个人商务邮箱
公开电话
手机
WhatsApp
传真
Contact form
Supplier portal
询盘入口
LinkedIn 公司页
LinkedIn 个人页可见信息
公开联系人姓名
公开联系人职位
公开地址
地图电话
展会名录联系方式
PDF/catalog 联系方式
第三方目录联系方式
```

不做“联系方式保守化”。  
只防止：

```text
无来源
猜测
错配归属
误导销售
```

---

## 3. 核心不固化行业 ICP

Superleads 核心不默认：

```text
国家
行业
客户规模
客户类型
进口商/经销商/零售商
小企业
大客户
欧洲/北欧
工业/MRO
家居零售
LinkedIn
```

行业经验只能作为：

```text
外部 legacy material
eval fixture
失败案例
可选用户输入
条件化搜索经验
```

不能写进核心规则。

---

## 4. 用户入口模式

不要按“我是工厂 / OEM / 工业品 / 消费品”引导。  
应按用户真实任务入口引导。

```text
你可以从以下任一方式开始：

1. 发一个公司官网、公司名或社媒链接
   我分析单个客户，判断是否值得开发，并尽可能提取联系方式。

2. 发产品名称和目标国家/地区
   我按产品开发客户，生成关键词、初筛客户、联系方式和开发建议。

3. 发一组关键词
   我扩展关键词，按公开来源发现潜在客户。

4. 发行业、应用场景或下游领域
   我按行业链路或应用场景开发客户。

5. 发国家/地区和目标客户类型
   我按市场和客户类型开发客户。

6. 上传 Excel/CSV 或粘贴客户名单
   我补全官网、联系方式、LinkedIn/社媒、来源链接和开发建议。

7. 发竞品、品牌、种子客户或参考网站
   我找相似客户、经销商、dealer、stockist、retailer 或相关买家。

8. 发展会目录、PDF、网页列表、截图或搜索结果
   我整理公司、联系方式和可开发线索。
```

---

## 5. 最小可研究目标

新客户开发至少需要：

```text
产品/服务 + 至少一个范围轴
```

范围轴包括：

```text
国家/地区
客户类型
渠道
应用场景
关键词
种子公司
竞品
已有客户表
展会/PDF/网页材料
```

但以下任务不需要产品 + 范围轴：

```text
单公司分析
已有客户表补全
PDF/展会目录整理
网页列表整理
截图/搜索结果整理
```

这些任务只需要：

```text
明确公司 / 明确材料 / 可解析名单
```

---

## 6. 用户输出模式

面向中国外贸用户，使用业务化命名。

```text
A. 初筛客户名单
   快速找一批可能客户，不做完整核查。

B. 标准开发名单
   打开关键来源，整理联系方式和开发建议。

C. 联系方式优先
   重点找邮箱、电话、表单、LinkedIn、联系人。

D. 补全已有表格
   保留原字段，补官网、联系方式、来源链接和开发建议。

E. 完整核查版
   输出来源链接、联系方式归属、待核查事项和检查说明。
```

避免用户端术语：

```text
候选预览
研究草稿
审计包
企业实体
事实与证据
联系方式归属
交付检查
```

推荐用户端 Sheet：

```text
客户信息总表
联系方式汇总
开发建议
待核查事项
风险与说明
关键词与搜索思路
初筛客户名单
官网与来源链接
已排除客户
检查说明
```

---

## 7. 推荐目录结构

```text
superleads/
  .codex-plugin/
    plugin.json

  skills/
    using-superleads/
    scoping-lead-research/
    writing-research-plans/
    executing-research-plans/
    collecting-contact-intelligence/
    assessing-research-evidence/
    resolving-company-identity/
    reviewing-lead-research/
    verification-before-delivery/
    exporting-lead-workbooks/
    learning-from-feedback/

  shared/
    schemas/
      run.schema.json
      brief.schema.json
      plan.schema.json
      source-observation.schema.json
      research-graph.schema.json
      contact-intelligence.schema.json
      review-finding.schema.json
      delivery-manifest.schema.json

    policies/
      claim-and-source-policy.md
      contact-intelligence-policy.md
      tool-capability-policy.md
      review-and-remediation-policy.md
      profile-policy.md
      platform-adapters.md
      cross-platform-rules.md

    references/
      route-map.md
      red-flags.md
      buyer-archetype-rules.md
      product-profile-input.md
      output-schema.md
      status-labels.md
      user-intake.md

  scripts/
    preflight_capabilities.py
    normalize_entities.py
    validate_research_graph.py
    audit_delivery.py
    export_workbook.py

  evals/
    fixtures/
    cases/
    behavioral/
    integration/
    legacy-derived/
    run_evals.py
```

---

## 8. Skill 职责

### 8.1 `using-superleads`

职责：

```text
自动激活 Superleads
识别任务入口模式
选择后续 Skill
建立 Run Context
检查工具能力
决定输出层级
```

不负责：

```text
不搜索
不生成客户
不写开发建议
不导出
```

触发描述建议：

```yaml
name: using-superleads
description: Use when the user wants to discover, qualify, enrich, organize, audit, or export overseas buyer leads for foreign trade from public or user-provided sources. Trigger for product-based overseas customer development, keyword-based prospecting, country or region lead research, importer/distributor/wholesaler/retailer/brand/OEM/end-user prospecting, public contact collection, customer list enrichment, company website analysis, trade fair/directory/PDF/social visible-source review, and evidence-backed sales lead workbook creation. Also use when the user explicitly says Superleads, superleads, 外贸客户开发, 海外客户开发, 找客户, 开发客户, 潜在客户, 客户名单, 补全客户表, 查联系方式, 找进口商, 找经销商, 找采购联系人, or similar.
```

---

### 8.2 `scoping-lead-research`

职责：

```text
形成 Research Brief
补齐最小可研究目标
记录联系方式需求
记录输出模式
记录业务上下文但不强制分类
```

Brief 字段：

```text
product_or_service
scope_axis
task_mode
contact_detail_level
output_mode
application_context
target_country_or_region
target_customer_type
target_channel
keywords
seed_companies
seed_urls
existing_table
competitors_or_brands
excluded_targets
must_verify_claims
evidence_depth
target_count
business_context optional
```

---

### 8.3 `writing-research-plans`

职责：

```text
生成查询组
规划来源类别
规划联系方式收集目标
定义线索分层标准
定义 Claim 所需证据
定义停止条件
定义降级策略
```

不负责：

```text
不产生客户
不打开网页
不做判断
```

---

### 8.4 `executing-research-plans`

输出：

```text
Candidate
Source
Observation
Provisional Entity
Search Log
```

硬规则：

```text
search.web 只能进入初筛线索 / 搜索记录。
已打开来源才能形成来源记录。
```

不负责：

```text
不输出正式开发名单
不写采购意向
不写最终开发建议
不猜联系方式
不生成 Claim
```

---

### 8.5 `collecting-contact-intelligence`

输出：

```text
ContactPoint
ContactClaim
UnassignedContactLead
```

职责：

```text
提取联系方式
标准化联系方式
判断来源上下文
建立联系方式归属说明
区分可直接使用 / 建议核查后使用 / 待确认归属 / 不可导出
```

联系方式状态：

```text
可直接使用
建议核查后使用
待确认归属
不可导出
```

内联红旗：

| 合理化念头 | 正确处理 |
|---|---|
| 客户需要联系方式，先填 info@domain.com | 禁止。构造邮箱不是观察 |
| 电话在页面上，就挂到这家公司 | 不够。必须有归属上下文 |
| LinkedIn 写 Purchasing Manager，就是采购负责人 | 只能是角色线索，不是采购权事实 |
| email.verify 通过，说明可以导出 | 只能证明质量，不能证明来源 |
| 没归属清楚的联系方式没用 | 不对，进入待确认归属 |

---

### 8.6 `assessing-research-evidence`

职责：

```text
从 Observation 形成 Claim
建立 ClaimEvidence
基于 Claim 形成 Hypothesis
根据 Brief 形成 Assessment
保留冲突证据
```

硬规则：

```text
Claim = 来源可支持的事实
Hypothesis = 商业假设
Assessment = 本轮开发判断
```

重要规则：

```text
Assessment 不能用 Hypothesis 作为准入证据。
Hypothesis 只能影响开发角度、下一步核查动作和人工优先级。
```

---

### 8.7 `resolving-company-identity`

职责：

```text
解析公司、品牌、法人、域名、分支、经销商、平台卖家关系
判断是否同一 Entity
提出合并/拆分/人工核查建议
持久化 EntityRelationship
```

触发：

```text
名称相似
品牌与法人不同
站点冲突
邮箱域名不一致
多国分支
加盟/经销关系不清
第三方目录与官网冲突
收购/改名/控股关系
```

---

### 8.8 `reviewing-lead-research`

职责：

```text
独立语义复核
检查来源是否支持声明
检查联系方式归属是否合理
检查 Hypothesis 是否伪装成事实
检查 Assessment 是否过度确定
检查身份是否错配
检查冲突是否保留
```

review_mode：

```text
independent
self_review_fallback
not_run
```

交付影响：

```text
independent + 检查通过 → 可完整交付
self_review_fallback → 只能带说明交付
not_run → 只能输出初筛/待核查
```

---

### 8.9 `verification-before-delivery`

职责：

```text
交付前确定性检查
验证 research graph
验证联系方式来源和归属
验证 ClaimEvidence
验证 ReviewFinding closure
验证 DeliveryManifest 新鲜度
```

内部状态：

```text
needs_correction
initial_lead_list
standard_development_list
full_review_package
```

用户端：

```text
需修正后交付
初筛客户名单
标准开发名单
完整核查版
```

---

### 8.10 `exporting-lead-workbooks`

默认客户开发版：

```text
客户信息总表
联系方式汇总
开发建议
待核查事项
风险与说明
```

完整核查版：

```text
开发需求
关键词与搜索思路
初筛客户名单
客户信息总表
联系方式汇总
开发建议
官网与来源链接
待核查事项
已排除客户
检查说明
```

---

### 8.11 `learning-from-feedback`

职责：

```text
保存用户对线索资料质量的反馈
用于后续搜索式、来源、联系方式质量排序
```

接受反馈：

```text
公司不相关
联系方式无效
邮箱退信
联系人不相关
客户类型判断错误
重复公司
官网归属错误
来源打不开
产品匹配错误
来源质量高
来源质量差
搜索词有效
搜索词无效
```

不接受为本 Skill 评价指标：

```text
成交率
询盘率
回复率
报价请求率
客户真实需求
销售开发信效果
销售跟进结果
```

只用于：

```text
re-rank
经验沉淀
来源质量判断
搜索式优化
联系方式提取优化
```

不能用于：

```text
Claim 证据
自动 Assessment
跨行业硬规则
成交或采购意向证明
```

---

## 9. 运行状态机

```text
scoped
→ planned
→ collecting
→ assessed
→ under_review
→ remediation_required
→ remediation_submitted
→ re_reviewed
→ checked
→ initial_lead_list / standard_development_list / full_review_package
```

注意：

```text
弱证据不阻断，只降级。
误导性错误才阻断。
```

阻断项：

```text
猜测联系方式
无来源联系方式写入主表
搜索摘要写成事实
Hypothesis 写成 Claim
身份明显错配
联系方式归属错配
不可访问页面被补写内容
导出没有状态说明
```

---

## 10. 核心数据模型

```text
Run
→ Brief
→ Plan
→ Candidate
→ Source
→ Observation
→ Entity
→ EntityRelationship
↔ Claim
↔ ClaimEvidence
↔ Observation
→ ContactPoint
↔ ContactClaim
↔ ClaimEvidence
→ UnassignedContactLead
→ Hypothesis
→ Assessment
→ ReviewFinding
→ Audit
→ DeliveryManifest
```

---

### 10.1 Source

```text
source_id
canonical_url
final_url
publisher_relation = first_party / third_party / unknown
provenance = discovered_public / user_provided / tool_enriched / manual_input
medium = website / social / registry / directory / map / document / spreadsheet / search_result
access_boundary
owner_hint
```

---

### 10.2 Observation

```text
observation_id
source_id
candidate_id optional
entity_id optional
capability
concrete_tool
observed_at
access_status
http_status or unknown
title
raw_excerpt
page_or_dom_locator
content_hash
extraction_method
tool_version
language
translation_status
derived_from_observation_id optional
snapshot_ref optional
```

---

### 10.3 Claim

```text
claim_id
entity_id
claim_type
subject
predicate
typed_value
as_of
claim_scope
support_status
contradiction_status
```

---

### 10.4 ClaimEvidence

```text
claim_evidence_id
claim_id
observation_id
relation = supports / contradicts / contextual
directness
source_authority
independence_group
freshness
excerpt_pointer
```

---

### 10.5 ContactPoint

```text
contact_id
contact_type
normalized_value
source_literal
source_observation_id
source_type
visibility_status
last_seen_at
verification_status
```

---

### 10.6 ContactClaim

```text
contact_claim_id
contact_id
entity_id optional
person_id optional
person_name optional
job_title optional
department optional
relationship_type
association_observation_id
association_claim_evidence_ids
source_context
association_evidence_text
association_locator
association_confidence
is_role_based
is_personal_business
export_status
manual_check_note
```

export_status：

```text
ready
export_with_source_note
needs_manual_association_review
hold_no_source
hold_inferred
```

用户端状态：

```text
可直接使用
建议核查后使用
待确认归属
不可导出
```

---

### 10.7 Hypothesis

```text
hypothesis_id
entity_id
basis_claim_ids
basis_contact_claim_ids optional
hypothesis_text
unknowns
suggested_action
next_verification_action
expires_at
risk_notes
```

---

### 10.8 Assessment

```text
assessment_id
entity_id
brief_id
disposition = 重点开发 / 推荐跟进 / 需人工核查 / 暂不建议 / 排除
basis_claim_ids
missing_requirements
manual_review_required
rationale_structured
related_hypothesis_ids_for_outreach optional
```

注意：

```text
related_hypothesis_ids_for_outreach 只能用于开发角度，不能用于准入证据。
```

---

### 10.9 ReviewFinding

```text
finding_id
severity = critical / major / minor
target_artifact
issue
required_fix
status = open / remediation_submitted / re_reviewed / verified_fixed / accepted_with_disclosure / rejected_with_reviewer_reason
reviewer
review_mode
reviewed_at
```

---

### 10.10 DeliveryManifest

```text
delivery_manifest_id
run_id
brief_id
plan_id
audit_id
audit_graph_hash
research_graph_hash
review_cycle_id
generated_at
delivery_status
output_mode
exported_entity_ids
exported_contact_ids
exported_contact_claim_ids
exported_assessment_ids
output_files
warnings
disclosures
```

导出前：

```text
current_graph_hash == audit_graph_hash
```

否则必须重新检查。

---

## 11. 线索分层规则

### 初筛客户

允许来源：

```text
搜索结果
目录摘要
展会名单
地图结果
未完整打开的公开来源
```

说明：

```text
只能作为初筛，不写成事实核查完成。
```

---

### 推荐跟进

要求：

```text
至少有一个已打开来源
产品/客户类型/市场有一定匹配
有联系方式或可触达入口
```

---

### 重点开发

要求：

```text
官网或高可信来源明确支持匹配
联系方式归属较清楚
开发切入点明确
无严重身份冲突
```

---

### 需人工核查

适用：

```text
来源冲突
联系方式归属不清
客户类型不确定
官网不可访问但目录/展会线索有价值
同名公司不确定
```

---

### 暂不建议 / 排除

适用：

```text
明显不匹配
同行供应商
国家/渠道不符
无开发价值
错误实体
```

---

## 12. 联系方式收集范围

应尽可能收集：

```text
企业通用邮箱
部门邮箱
销售邮箱
采购邮箱
供应商入口邮箱
个人商务邮箱
公开电话
手机
WhatsApp
传真
Contact form
Supplier portal
询盘入口
LinkedIn 公司页
LinkedIn 个人页可见信息
公开联系人姓名
公开联系人职位
公开联系人部门
公开地址
地图电话
展会名录联系方式
PDF/catalog 联系方式
第三方目录联系方式
```

禁止 ready 导出：

```text
根据域名猜的邮箱
根据姓名猜的邮箱
没有来源的电话/手机号
email.verify 发现但无公开来源的邮箱
company.enrich 返回但无法回溯来源的联系人
登录墙/隐藏内容/不可见内容中的信息
ready 状态但无归属证据的联系方式
```

---

## 13. 工具能力矩阵

| Capability | 最高进入层 | 规则 |
|---|---|---|
| search.web | 初筛客户 / 搜索记录 | 不能支撑 Claim |
| source.open | Observation | 可形成来源记录 |
| browser.render | Observation | 可形成来源记录 |
| document.extract | Observation | 可形成文档来源记录 |
| source.capture | Observation | 保存摘录、定位、哈希 |
| url.canonicalize | Source / Entity | 只做归一化 |
| entity.dedupe | Provisional Entity | 不等于最终身份判定 |
| translate.text | Observation transform | 必须保留原文 |
| company.enrich | Candidate clue / contextual | 不能单独支撑主表 |
| email.verify | contact quality | 不证明来源 |
| domain.check | technical Observation | 不证明公司归属 |
| social.visible.read | Observation | 不自动证明采购权 |
| registry.lookup | Observation | 可支撑实体类 Claim |
| trademark.lookup | Observation | 可支撑品牌/商标类 Claim |
| maps.lookup | Observation | 可支撑地图联系方式/地址类 Claim |
| memory.recall | Plan priority | 不能进 Claim / Assessment |

---

## 14. 脚本门禁

### validate_research_graph.py

检查：

```text
ID 闭合
Claim 有 ClaimEvidence
ClaimEvidence 引用 Observation
Assessment 只引用 Claim 作为准入依据
Hypothesis 引用 basis_claim_ids
Candidate 未直接进入 Assessment
search.web 未直接支持 Claim
ContactClaim 引用 ContactPoint 和 Observation
ready ContactClaim 有 association_evidence_text
ReviewFinding 状态合法
```

---

### audit_delivery.py

检查：

```text
联系方式有 source_literal / normalized_value
ContactPoint 有 source_observation_id
ContactClaim 有 source_context / association_evidence_text
ready ContactClaim 有归属证据
无归属联系方式未进入客户主表 ready 字段
person_name / job_title 若填写需有来源
enrichment 未单独支撑主表
blocked/login-wall 未支撑 Claim
Hypothesis 含 unknowns 和 next_verification_action
translated Observation 可追溯原文
critical/major Finding 已处理
Audit graph hash 新鲜
```

---

### export_workbook.py

规则：

```text
needs_correction 不允许正式交付
初筛客户名单允许弱证据，但必须标注状态
标准开发名单必须包含来源链接和联系方式状态
完整核查版必须包含检查说明
```

---

## 15. Eval 体系

### 自动 Eval

```text
schema 合法
ID 链闭合
状态转换合法
搜索摘要不进 Claim
联系方式不猜测
联系方式归属正确
同页多公司不误挂联系方式
Hypothesis 不写成 Claim
Assessment 不用 Hypothesis 做资格判断
Audit hash 失效会阻断交付
ReviewFinding 未处理会阻断正式交付
```

### 行为压力测试

```text
用户要求跳过证据
用户要求猜邮箱
用户要求直接导出
用户要求无视登录墙
用户要求把 LinkedIn 职位当采购负责人
用户要求把搜索摘要当客户事实
用户催促“客户很急，所有联系方式都给我”
```

### 联系方式情报测试

```text
公开邮箱是否提取完整
电话/WhatsApp 是否提取完整
Contact form 是否识别
个人商务联系人是否正确标注
联系方式归属是否正确
同页多公司联系方式是否错配
email-verify 是否未被误用为来源
```

### 用户反馈指标

归属 `learning-from-feedback`，只评估资料质量：

```text
公司不相关
联系方式无效
邮箱退信
联系人不相关
客户类型判断错误
重复公司
官网归属错误
来源打不开
产品匹配错误
来源质量高
来源质量差
搜索词有效
搜索词无效
```

不纳入 Superleads 评价指标：

```text
成交率
询盘率
回复率
报价请求率
客户真实需求
销售开发信效果
销售跟进结果
```

---

## 16. 跨平台与安装

### 跨平台

```text
Python 3 + pathlib
不写死系统路径
兼容 Windows / macOS / Linux / WSL
默认 XLSX；不可用时 UTF-8-SIG CSV
不默认安装全局依赖
工具缺失时降级为初筛客户名单或研究计划
```

### 跨 Agent

```text
Codex：skills + shell/python/file tools + MCP + subagent
Claude Code：Skill/project context + Task reviewer + WebFetch/browser + local scripts
Hermes：Local Browser + Web Search + File Operations + Code Execution
WorkBuddy：平台内置搜索、浏览器、表格工具、工作流 agent
```

### 安装

```text
Codex plugin:
superleads/.codex-plugin/plugin.json

或复制到：
~/.codex/skills/
```

其他 Agent：

```text
复制 skills/
复制 shared/
复制 scripts/
按 platform-adapters.md 映射工具能力
```

---

## 17. 旧 Skill 处理

旧 Skill 不进入核心。

只允许进入：

```text
evals/legacy-derived/
```

作为：

```text
失败案例
fixture
反例
压力测试 prompt
工具误用案例
联系方式幻觉案例
身份错配案例
```

不允许作为：

```text
默认行业规则
默认 ICP
默认客户类型
默认国家
默认开发策略
```

---

## 18. 实现阶段

### Phase 1：协议与门禁

```text
schemas
Research Graph
ReviewFinding schema
remediation state machine
claim/contact/tool policies
validate_research_graph.py
audit_delivery.py
基础 eval
```

### Phase 2：核心研究流

```text
using
scoping
writing
executing
collecting-contact
assessing
verification
exporting
```

### Phase 3：复核与身份解析增强

```text
reviewing-lead-research
resolving-company-identity
reviewer-prompt
entity relationship
复杂冲突 fixture
```

### Phase 4：反馈学习

```text
learning-from-feedback
用户资料质量反馈
更多 eval
CRM / outreach 可选扩展
```

---

## 19. 最终一句话

```text
Superleads 是一套通用外贸线上客户开发 Skill Suite；它不依赖行业 ICP 或大而全提示词，而是用任务入口引导、Source/Observation/Claim/ContactClaim/Hypothesis/Assessment/Audit 数据图、公开联系方式情报最大化、独立复核、分层交付和交付前检查，把外贸客户开发变成可追溯、可检查、可跨平台运行的客户线索研究系统。
```
