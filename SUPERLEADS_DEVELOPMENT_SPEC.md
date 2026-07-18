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

它以类似通用 Agent Skill 的方式运行于 Codex、Claude Code、Hermes、WorkBuddy 等宿主：Skill 指导 Agent 理解当前任务、调用宿主实际可用工具并组织研究步骤；它不是独立应用界面、客户数据库、工作台或企业合规平台。

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
跨 Agent 外贸客户开发方法
联系方式情报与证据约束方法
客户线索分层交付方法
跨 Agent / 跨平台方法论
```

### 1.1 职责边界

```text
用户当前 Brief：定义本次产品/能力、目标对象、排除对象、国家或地区语义与交付目标
Agent 语义研究：理解自由文本商业语境，生成查询策略，判断候选、冲突与待确认事项
宿主工具：按实际可用能力执行搜索、打开公开来源、读取文件或其他受控操作
轻量脚本门禁：仅阻止可确定的虚构、证据错配、联系方式猜测、实体错配、违反当前 Brief 的正式交付与敏感信息泄漏
用户反馈与人工复核：校正本次业务判断，并在后续任务中改进 Brief、查询和核验方法
```

外贸客户开发的产品边界、应用边界、客户角色、地区含义、竞争对象处理和商业可行性，主要依赖当前用户语境、Agent 的语义研究和人工复核；不得以静态行业词典、默认 ICP 或脚本规则替代这些判断。脚本是交付安全带，不是商业判断器；不得要求用户直接操作内部图谱、Claim、ScopeDecision、Audit 或规则 ID。

### 1.2 平台与公开 HTTP 来源边界

当 Run 记录 `platform` 时，它必须是 canonical host ID：仅小写 ASCII
字母、数字和下划线，不接受前后空白、大小写变体或连字符。该规则不枚举
平台；例如 `hermes`、`claude`、`workbuddy` 都是可用宿主名。`curl`、`wget`、
`python_requests` 等只能是具体读取工具，不能成为平台。

正式公开 HTTP(S) 来源必须无凭证，并拒绝 localhost、`.localhost`、`.local`、
私网、loopback、link-local、reserved、multicast、unspecified 与历史数字 IPv4
写法（包括 `127.1`、`2130706433`、`0x7f000001`）。图谱校验不为任意域名做
DNS 查询，因此该字符串规则不是 DNS rebinding 防护；实际 Shell HTTP 执行器
必须在连接和每次重定向时阻止解析到非公网地址。用户提供 PDF/Excel 的受控
文件来源分支不受此公开 URL 规则影响。

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

其中单公司分析的正式结果必须保留当前用户指定的公司名、URL/domain 或材料引用，
并只输出该解析 Entity；已有客户表补全必须绑定用户提供的表格和每个输出 Entity 的
行/单元格定位。这两类结果不是新客户方向名单，不得使用“符合本次方向”表述，也不能
因设置 `task_mode` 而绕过本次开发边界合同。

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
   当前个人本地部署不提供该交付级别；请求必须被拒绝。
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
independent + 检查通过 → 可标准交付并保留独立复核披露
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

当前个人本地部署不提供 `full_review_package`；该值仅用于拒绝请求或
识别历史产物，不能成为可交付状态。

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

当前个人本地部署不导出完整核查版工作簿。

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
→ initial_lead_list / standard_development_list
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
provenance = discovered_public / user_provided / tool_enriched / manual_input / connected_account
medium = website / social / registry / directory / map / document / spreadsheet / correspondence / image / search_result
access_boundary
owner_hint
artifact_sha256 optional
artifact_name optional
artifact_media_type optional
material_role optional for public Sources; required for user_provided / manual_input / connected_account
parent_source_id optional for connected attachment
message_id / thread_id / received_at / direction / sender_literal / subject_literal optional
message_content_sha256 / mailbox_ref / mail_intake_rule_id optional
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

### 10.2.1 正式来源可用性

正式 Claim 与 `ready` / `export_with_source_note` 联系方式证据只能通过一个共享门禁的两个分支之一：

```text
公开来源分支：
- Source 有有效非空 http:// 或 https:// URL
- Observation 有非空原文
- 保持 capability、ClaimEvidence、Entity、翻译原文、Review、Audit、Manifest 全部既有门禁

用户提供文件分支：
- provenance = user_provided，medium = document 或 spreadsheet
- artifact_sha256 为 64 位小写十六进制，artifact_name 仅为安全文件名
- Observation.capability = document.extract，raw_excerpt 与 content_hash 非空
- snapshot_ref = artifact:sha256:<同一hash>#<安全定位>
- document 至少定位页码/章节；spreadsheet 至少定位工作表与单元格/区域
```

该例外不是聊天粘贴文本、`manual_input`、记忆、搜索摘要、email.verify、company.enrich 或无定位材料的例外。不得存储或导出本地绝对路径、`file://` URI 或内部 artifact hash。门禁只验证哈希格式、链路与引用一致性；未保存原始二进制文件的运行环境不得声称已重新计算并验证文件字节哈希。

### 10.2.2 用户输入材料分层

`material_role` 用于 `user_provided`、`manual_input` 或 `connected_account`，取值固定为：

```text
published_source_copy
user_business_dataset
correspondence_export
user_authored_note
visual_reference
connected_inbound_correspondence
unknown
```

用途矩阵：

| 材料角色 | 正式 Claim / Assessment | ready 联系方式 | export_with_source_note | Candidate / 搜索任务 |
|---|---|---|---|---|
| 公开 HTTP(S) | 允许，沿用全部门禁 | 允许 | 允许 | 允许 |
| published_source_copy | 允许，沿用 hash、定位、实体、翻译链门禁 | 允许 | 允许 | 允许 |
| user_business_dataset | 不允许单独支撑正向 Assessment | 不允许 | 允许，需逐字与归属语境 | 允许 |
| correspondence_export | 只可记录沟通中曾表述，不得作为资格依据 | 不允许 | 允许，需逐字与归属语境 | 允许 |
| user_authored_note | 不允许 | 不允许 | 不允许 | 允许 |
| visual_reference | 不允许 | 不允许 | 不允许 | 允许 |
| connected_inbound_correspondence | 不允许作为资格事实 | 不允许 | 允许，需逐字、同实体与邮件来源说明 | 允许，可创建 Inquiry |
| unknown | 不允许 | 不允许 | 不允许 | 允许 |

用户的产品、能力、开发要求进入 Brief；用户粘贴的公司、竞争对手、联系人和聊天片段只形成 Candidate、Plan、Hypothesis 或 UnassignedContactLead。用户未说明文件性质时，默认 `user_business_dataset` 或 `unknown`，不得自动升级为 `published_source_copy`。必要时只问：`这份材料是原始公开/对方资料，还是你自己整理的历史名单或备注？`

## 16. Phase 2: 本次找客户规则与方向匹配

### 16.0 Phase 2 实施重点

Phase 2 的目标是让 Skill 在真实宿主能力下完成“理解需求 -> 形成 Brief -> 规划 -> 搜索发现 -> 打开来源 -> 收集公开联系方式 -> 判断 -> 复核 -> 导出”的最小研究闭环，而不是把 Superleads 扩展为工作台、合规平台或静态行业决策系统。

产品、行业、国家、地区、客户角色和竞争关系必须由当前用户的自由文本定义。比如中性包装 aftermarket 与原厂件、舞台专业音响与家电音响、“当地实体”与“服务该市场”的区别、经销商/维修商/制造商/终端用户的取舍，均应由 Brief 澄清、Agent 语义判断、公开证据和人工复核共同处理，不能由核心脚本硬编码推断。

协议与脚本只保留高价值、可机械验证的最后一道约束：不得把搜索摘要当正式事实、不得猜测或错配联系方式、不得跨 Entity 拼接证据、不得越过当前 Brief 的明确纳入/排除边界、不得把未打开或无证据对象伪装为已核验客户。除非真实任务反复暴露同一种可确定的交付风险，不得仅为增加 eval 数量而新增 schema、状态机、字段或门禁。

Phase 2 以连续真实业务任务验收，而不是以门禁数量验收。每次任务至少记录候选发现数、成功打开来源数、满足方向和地区证据数、最终可跟进名单数、人工抽查结果、联系方式可用性和用户业务反馈。只有跨任务重复出现的真实问题，才应转化为 fixture、Skill 改进或确定性脚本修复。

### 16.1 当前 Brief 专属合同

新客户开发 Brief 使用 `customer_selection_contract` 记录“本次找什么 / 不找什么 / 怎么判断 / 暂不确定什么”。它的供货说明、商业定位、应用边界、目标对象、排除对象、竞争关系说明与全部规则内容均为自由文本；不得建立产品、行业、国家、地区、应用、客户角色、规模、品牌或渠道的固定业务枚举。

合同只属于当前 Brief 和当前 Run。固定值仅限流程控制：

```text
scope_state: explicit | inferred_low_risk | provisional
ScopeDecision: in_scope | out_of_scope | needs_confirmation | reference_only
规则结果: supported_match | supported_conflict | not_observed | unknown
```

`not_observed` 只表示已查看的公开材料未出现信号，不能表示已证明某类业务不存在。竞争对手、品牌方、制造商及其他参考名称默认仅作搜索/市场参考；只有本 Brief 明确许可后才可进入客户池，且仍须通过同一方向门禁。

### 16.2 用户交互

先以不超过四行自然语言复述：

```text
我理解你卖的是：
本次优先找：
本次不纳入：
判断依据将重点看：
```

只有回答不同会导致客户方向相反时，才追问一至三个短问题。用户已经明确时不重复问。关键歧义未解决时设为 `provisional`，只交付三至五家“方向样本，等待确认后再扩展为正式开发名单”；不得输出标准开发名单或完整核查版正向客户。

### 16.3 Plan、ScopeDecision 与 Assessment

Plan 必须绑定当前 Brief，分别列出正向和排除规则，并让每条规则至少对应一个查询或核验步骤。查询词和搜索提示仅从当前 Brief 推导；排除查询只用于发现风险，正式排除或纳入均需要公开 Observation -> 同 Entity Claim -> ClaimEvidence。

只要新客户开发 Brief 的 `target_country_or_region` 含任一非空用户 literal，
`customer_selection_contract.geography_contract` 即为必填正式合同，不得缺失或为
`null`。它的 `included_geography_literals` 与目标地区的规范化集合必须精确一致，
但 Brief 中原始用户 literal 必须保留。Plan 必须绑定其 geography query group；
每个正式地理准入须以同 Entity、已打开、公开且安全来源中的逐字地区 literal 为
依据，并满足当前 Brief 的 first-party/public 来源关系要求。SearchLog、搜索摘要、
域名后缀、语言、电话区号、关键词和无关 Claim 都不能替代该 Claim。未指定地区的
全球任务不得虚构地区合同或“全球” literal。

`scope_decisions` 记录某 Candidate/Entity 对当前合同的可追溯判断。Candidate 未解析为 Entity 时，只能是 `needs_confirmation` 或 `reference_only`。`supported_match` / `supported_conflict` 必须引用同 Entity、可用于 Assessment 的正式 Claim；用户材料、邮件、图片/OCR、搜索摘要、Candidate 与 Hypothesis 不能替代它。

对新客户开发模式的 `重点开发` / `推荐跟进`：必须有当前 Run、当前 Brief、同一 Entity 的 `in_scope` ScopeDecision；每条 `required_for_positive` 规则必须为 `supported_match`；命中的 `block_when_supported` 排除规则、配置为阻断的 `unknown`、或 `provisional` 合同均阻断正向 Assessment 和标准/完整交付。联系方式、网站、国家、关键词相似度不能绕过方向检查。

### 16.3.1 规则证据映射与 fail-closed 条件

每条当前 Brief 的 selection / exclusion rule 必须声明本轮可接受的通用
`allowed_claim_types`，以及从用户原话和当前 Plan 推导的自由文本
`evidence_markers` / `conflict_markers`。这些不是产品、行业、渠道或国家词典；
核心逻辑不得提供默认业务词。ScopeDecision 对每一条已核查 Claim 必须显式记录
`supports`、`conflicts` 或 `irrelevant`，同时带可追溯的 Claim、逐字存在于正式
Observation 原文的 marker 和理由。`supports` / `conflicts` 只能使用同 Entity、
类型获该 Rule 允许、且有可用于 Assessment 正式来源证据的 Claim。

任何被列为 reviewed 的 Observation 所支撑的正式 Claim 都不得静默遗漏。若排除
rule 的公开原文命中其 `conflict_markers`，ScopeDecision 必须记录冲突或降级为
需确认，不能写成 `not_observed`、`irrelevant` 或正向匹配。`not_observed` 只能
说明本轮已查看材料未显示该信号，绝不是“已证明不存在”。Assessment 的
`basis_claim_ids` 必须包含每条 required selection rule 的 `supports` Claim；地址、
注册地等无关事实不能支撑产品、应用、渠道或业务角色 rule，除非该条当前用户规则
明确允许相应 Claim type 和 marker。

`task_mode=unknown` 只能形成初筛、方向样本或待确认任务，不能生成标准开发名单、
重点开发或推荐跟进。除 `single_company_analysis` 和
`existing_table_enrichment` 外，任何正向正式客户交付都须有实质性当前合同：至少
一条 selection rule，且至少一条 `required_for_positive=true`。`material_list_extraction`
若未具备该完整合同，只能形成初筛或材料结果；要产生正向 Assessment 或正式名单，
同样必须通过完整方向门禁。空合同、全部可选的合同和 `scope_state=provisional` 均
不得绕过此规则。

`sample_first_required=true` 是实际执行的样本门禁：Plan 必须限定一至五家，且只能
导出初筛方向样本。用户确认后必须明确更新 Brief/合同并重新 Review 后，才可形成
正式名单。

`single_company_analysis` 与 `existing_table_enrichment` 不是可自我声明的方向门禁
例外。前者须有当前用户原话和绑定到唯一 Entity 的公司标识、URL/domain 或用户材料；
后者须有用户提供 spreadsheet Source 及每个输出 Entity 的同实体行/单元格 Observation。
它们只能交付“单公司分析结果”或“原表补全结果”，不得写为“符合本次方向”，也不得
扩展输出未绑定的新发现客户。

单公司分析中每一个非空的结构化身份标识都必须独立指向同一 resolved Entity：公司名
仅可与 Entity name/legal name 的保守规范化结果精确一致，URL/domain 仅可与 Entity
website/domain 精确一致。若引用用户材料，必须记录材料中逐字可见的 `entity_literal`，
该 literal 同时须在同 Entity Observation 原文中出现并精确对应 Entity name/legal name
或 domain。已有表格补全的每条行/单元格 binding 也必须有同样的逐字 `entity_literal`。
别名、品牌名、集团名、旧名称、局部名称或近似匹配均进入身份解析/人工核查，不能作为
正式例外交付授权。

`normalize_entities.py` 不得把 normalized name/domain 或 duplicate flag 写入
research graph。它输出 schema-compatible graph copy，身份归一化提示另存为独立
identity review report；提示不是 Claim、EntityRelationship、合并/拆分结论或交付许可。

竞争/品牌参考的完全规范名、已知域名或明确 EntityRelationship 命中时保持
`reference_only`，除非用户在当前 Brief 明确许可。名称近似、集团名、品牌名或法人
名提示不能自动合并，也不得静默作为 `in_scope` 放行；它们必须为 `needs_confirmation`
并进入公司身份解析。只有公开证据证明其为不同主体，或用户明确许可后，才可按当前
合同继续进入正式客户池。

### 16.4 导出和复核

标准开发名单只导出当前 Run 的正向 `in_scope` Entity 及合格联系方式。`needs_confirmation`、`out_of_scope`、`reference_only` 不得进入客户主表、联系人汇总或开发建议；初筛可分区显示业务化标签“需确认 / 不符合本次方向 / 仅作参考”。不得向用户展示 TargetingContract、ScopeDecision、Claim、规则 ID、Review、Audit 或技术引用字段。当前个人本地部署不提供完整核查版。

独立复核必须检查用户原话与合同是否一致、Plan 是否覆盖正向与排除规则、正向客户是否有同实体公开证据、竞争/品牌/制造商或相近应用对象是否误入客户池，以及未知是否被合理化为符合。

这套门禁不改变用户材料、`mail.read`、`image.inspect`、Inquiry、Claim、Contact、Review、Audit、Manifest、hash 与新鲜度规则。它不绑定 MCP、模型、Agent 或平台，不携带默认 ICP；邮件、图片和用户材料仍只能在各自允许的用途内参与当前方向的线索和核验流程。

不得为了“看起来更安全或完整”而引入服务器、账号体系、签名、密钥、OAuth、环境变量信任根、MCP 或平台依赖。当前环境无法可信验证某项属性时，系统必须明确降级并在适用的交付中披露，不得模拟、伪称或自行补造该信任属性。

原始邮件或完整聊天导出可为 `correspondence_export`，但截图、转述和局部粘贴默认是 `visual_reference` 或 `user_authored_note`。沟通记录只能表述“某人在用户提供沟通记录中这样表述”，不能证明企业资质、采购权、真实需求、商标权属或公司关系，也不能进入 `Assessment.basis_claim_ids`。

### 10.2.3 图片、Logo 与名片线索

新增 `image.inspect` 能力合同，用于 OCR、图片文字、Logo 文字和视觉线索。它不绑定 MCP、模型、厂商或 Agent；Windows、macOS、Linux、WSL 的任意可用图片/OCR 工具均可实现。无该能力时请求更清晰图片、可读品牌文字或公开链接。

```text
visual_reference + image.inspect
→ OCR 原文或明确标注的视觉描述
→ Candidate / 搜索任务 / Hypothesis / UnassignedContactLead
→ 外部官网、商标库、注册机构等再核验
```

图片本身不能直接证明 Logo/商标权属、品牌产品归属、联系人采购权或公司授权。多个近似品牌只能输出可能匹配对象和待确认项；只有外部正式来源可形成权属 Claim。

### 10.2.4 已连接邮箱与 Inquiry

`mail.read` 是宿主无关、只读的能力合同。用户必须明确指定邮箱连接、文件夹/标签、时间范围或筛选条件和入站方向；不得默认扫描邮箱或全量邮件。它不绑定 Gmail、Outlook、OAuth、MCP、模型或 API，不保存密码、token、完整原始邮件正文、本地路径或 `file:` URI。

合格的连接来信 Source 必须为 `connected_account + correspondence + connected_inbound_correspondence`，含安全 opaque `mailbox_ref`、入站方向、收件时间、发件人与主题原文、消息内容 SHA-256 与安全 `mail:sha256:<hash>#part=...` 摘录定位。`mail.read` 只可形成 Inquiry、Candidate、外部核验任务和 `export_with_source_note` 联系人，不能支撑 Claim、Assessment、`ready` 联系方式或采购权/企业资质结论。

```text
入站邮件 -> Inquiry（询盘待办） -> 主体解析/外部核验/跟进
公开来源或受控 published_source_copy -> Claim -> Assessment -> 标准开发名单
```

Inquiry 允许 `new`、`triaged`、`needs_entity_resolution`、`ready_for_follow_up`、`closed`，不得写成 qualified、verified_buyer 或 confirmed_purchase。`inquiry_followup_queue` 是独立交付状态与 `--mode inquiry` 导出，不要求完整 Brief/Plan/Assessment，但必须通过 Inquiry 专属审计；它不能伪装成标准开发名单。用户可见字段只显示业务化询盘摘要、待办、待补充信息和“邮件来信（日期）”来源说明，不显示 message/thread ID、hash、完整正文、路径或内部状态。

MailIntakeRule 必须限定非空文件夹/标签、入站、只读与动作白名单。one_shot 必须有明确时间窗口；continuous 必须用户明确批准，且只有宿主提供合规调度/事件能力时才实际运行，否则只表示下次手动运行时应用的筛选规则。严禁发送、回复、标记已读、移动、删除、归档或改写邮件。无 `mail.read` 时请求 EML/PDF/邮件导出。

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
| image.inspect | Observation / Candidate clue | OCR 与视觉线索，不支撑正式 Claim、商标权属或 ready 联系方式 |
| mail.read | Inquiry / source-note contact | 只读入站邮件摘录；不支撑 Claim、Assessment 或 ready 联系方式 |
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
公开 HTTP(S) 与用户提供文件来源均经同一正式来源资格门禁
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
用户文件联系方式的 source 与 association Observation 均通过同一正式来源资格门禁
```

---

### export_workbook.py

规则：

```text
needs_correction 不允许正式交付
初筛客户名单允许弱证据，但必须标注状态
标准开发名单必须包含来源链接和联系方式状态
当前个人本地部署不提供完整核查版
用户文件显示为业务化文件名与页码/工作表定位，不输出路径或 artifact hash
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
用户提供 PDF / Excel 的合法 hash、定位、Claim 与联系方式链可进入标准交付
无 hash、错误 hash、路径名、无定位、错误 capability、错误实体归属与 hold 联系方式泄漏均被阻断或脱敏
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

### Codex CLI 原生 Web Search

```text
codex --search -C <项目目录>
```

此启动方式可能在当前会话提供原生 `web_search`。Superleads 只接受 Agent
根据当前会话实际可见工具和实际操作结果写入的能力报告；本地脚本不自行探测
模型工具，也不安装、配置或绑定任何外部工具服务。

`web_search` 已实际搜索时，只映射为 `search.web`，因此最多输出初筛客户名单。
只有当前会话实际打开一个明确 HTTP(S) URL，取得来源标题或等价标识、可定位的
非空逐字原文摘录，才可记录 `source.open` 已验证。启动参数、模型/Provider 名称、
工具名称、搜索摘要、链接或引用均不能推导 `source.open`。

即使能力报告记录 `source.open`，每条正式事实和联系方式仍必须通过既有来源、
原文、实体归属、翻译链、哈希、复核、审计、新鲜度和交付门禁。搜索摘要不得成为
正式事实或联系方式来源。自定义 model provider 若无原生工具、调用失败或只能返回
摘要，应记录能力缺口并降级为研究计划或初筛客户名单。

原生 Web Search 适配器只拥有 `search.web` 与 `source.open`。它有效时只覆盖
这两个能力；`browser.render`、`document.extract`、`image.inspect`、`mail.read`
和其他能力仍由宿主独立报告并与适配结果合并。适配器版本、映射、操作验证或路径
安全任一错误时，不得授予原生 search/source 能力，但不得因此抹掉合法的独立能力。
只要 Run 带有该适配器报告，每条 Observation 使用的能力都必须在该 Run 的
canonical capabilities 中显式记录为 `available`；未声明、`unknown` 或
`missing` 的独立能力不得支撑正式来源。该要求不改变适配器只拥有两项能力的边界。
多 Run 图谱中，每个 Observation 必须记录其采集 Run，能力检查只看该 Run；历史
Run 不能为当前来源背书，也不能阻断当前 Run 的已验证来源。
```

### Codex CLI Shell HTTP Source Open

```text
Run.platform = codex_cli
Run.capabilities.source.open = available
Observation.capability = source.open
Observation.concrete_tool = curl | wget | python_requests
```

`curl`、`wget` 与 `python_requests` 是 Codex CLI 宿主下的具体只读来源读取
工具，不是平台，也不提供 `search.web`。它们只能通过
`codex_cli_shell_http_source_open` 受控 provider 取得 `source.open`：本次
会话必须记录一次公开、无凭证 HTTP(S) `GET` 成功，包含原始 URL、最终 URL、
2xx 状态、来源标题或等价标识、逐字原文和定位。每条对应 Observation 仍须由
当前 Run 显式报告能力，并且具体工具必须在该 provider 的允许列表中。

不得以 shell 命令存在、curl 已安装或工具名相似推导能力；不得把 shell HTTP
伪装为 native Web Search。禁止 POST、Cookie、Authorization、Token、Password、
本地/file URL、私有/loopback 地址、登录态、私有接口、验证码或任何绕过访问限制
的方式。Native 搜索 provider 与 shell HTTP provider 可在同一 Run 并存；只有
其共享能力映射不冲突时才可聚合。

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
