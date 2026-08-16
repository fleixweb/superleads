---
name: researching-customer-background
description: "Use when a user provides one specific company, brand, website/domain, Lead, address, phone, email, or user material and asks for customer background research, deep investigation, due diligence, parent/operating/actual purchasing entity analysis, owned-factory checks, pre-quotation or pre-negotiation intelligence, or key-person clues; NOT for discovering many new customers by product, market, or keywords."
---

# 客户背调研究 Playbook

## 最终交付

Read `../../shared/references/superleads-user-guidance.md` for terminal user-delivery footer rules. The final customer background report follows those rules; progress updates and standalone clarifications do not append the footer.

## 产品定位

Superleads 的主路径不变：

`产品 + 市场/国家/客户类型 -> 批量发现 -> 客户开发名单 -> 公开联系入口与联系状态`

本 skill 是第二功能：

`单个指定对象 -> 客户背调研究草稿`

客户背调不是批量找客户的前置门槛，不替代批量发现；发现的关联实体默认不成为新 Lead，也不会自动把当前对象升级为标准开发名单。

当前已支持 `task_mode=customer_background_research`、`output_mode=客户背调报告`、`background_research_target` 和独立背景报告 XLSX/CSV 导出。报告导出使用轻验证与当前 Brief 范围投影，不生成 `DeliveryManifest`，不进入 delivery status、正式 audit profile 或跨会话 Candidate/Lead 持久化。

## 何时开始与研究锚点

背调可以从一个尚未解析的锚点开始，不要求先有唯一的 resolved Entity。`unresolved` 和 `multiple_candidates` 不得强行填写 `primary_subject_entity_id`；只有同一已解析 Entity 具有实际可检查的同 Entity Observation 时，才填写 `resolved`、主体 ID 和解析 Observation。主体解析本身是研究的第一部分。

可接受的调查锚点包括：

- 公司名称或品牌名；
- 官网、域名或已知页面；
- Lead 或 Candidate 线索；
- 地址、电话或邮箱；
- 用户提供的 PDF、Excel、截图、海关数据、Similarweb 数据或其他第三方材料。

研究草稿必须分开记录以下对象和关系，未确认时保留未确认状态：

- 调查锚点；
- 主对象/已解析主体（如已解析）；
- 品牌站；
- 运营公司候选；
- 母公司候选；
- 真实采购主体候选；
- 关联工厂/供应商候选；
- 未确认关系。

不得因为名称、域名、地址或业务描述相似，就把品牌站、客服站、商标主体、进口商、母公司、分销商或工厂强行合并为同一个 Entity。

## 证据骨架与事实纪律

本 playbook 只复用现有证据骨架：

- `Source -> Observation -> Claim -> ClaimEvidence`；
- `Entity` / `EntityRelationship`；
- `Hypothesis`；
- `ContactPoint` / `ContactClaim` / `UnassignedContactLead`。

只有实际打开或实际可检查的来源，才能建立 `Source` 和 `Observation`。Google、Bing 等搜索摘要只能用于发现候选 URL，不能作为事实、`Observation`、`Claim` 或 `ClaimEvidence`。

只有已解析为同一主体、且有原文支持的事实，才可形成 `Claim + ClaimEvidence`。未确认关系、可能采购主体、自有工厂可能性、潜在痛点、可能切入角度，以及当前任职不明的历史联系人，必须保留为 `Hypothesis`、Unresolved Clue 或 `needs_manual_check`，不能写成事实。

历史资料必须标注快照/页面日期、观察日期和历史状态；它不得覆盖当前官网、当前注册信息或当前公开任职证据。来源发生冲突时保留冲突；单一来源显示 `inactive` 或 `dissolved`，不足以断言企业已停业。

## 覆盖族

以下六个覆盖族按现有证据、用户材料和可用能力选择执行。它们不是全部串行、全部强制的门禁。每个覆盖族都应标注 `observed`、`not_observed`、`not_searched`、`source_restricted`、`identity_pending` 或 `needs_user_input`，并说明范围或限制。缺少 Similarweb、海关、Wayback 或注册库访问能力，不表示客户不存在，也不表示研究失败。

### A. 官网、品牌站与公开文件

- 查看官网、品牌站、About、Contact、Privacy、Terms、页脚、产品页、FAQ、Supplier/Vendor/Wholesale 页面。
- 比对多官网、多域名、品牌站、区域站、多国家 storefront 和分支邮箱域名。
- 检查可实际读取的公开 PDF、DOC、XLS、PPT、catalog、brochure、证书、展会资料和新闻稿。
- 联系表单只记录 URL、字段、用途和可准备草稿的机会；绝不自动提交。
- 文件中的联系人标注文件年份，以及 `historical_contact` 或 `needs_manual_check`，除非存在独立的当前公开归属证据。

### B. 主体、品牌、运营公司与历史关系

- 解析品牌 -> 运营公司 -> 母公司 -> 进口公司/采购主体 -> 关联工厂的关系链；链中每一段独立判断。
- 可检查域名、页脚版权、隐私条款、目录封底、公开注册信息、商标、公开新闻、Whois、旧域名和 Wayback。
- 已有足够证据时使用 `EntityRelationship`；证据不足时记录 unresolved relation，不自动合并。
- 域名注册时间仅是关系或时间线线索，不等于公司成立时间，也不等于当前采购主体。

### C. 产品、渠道、供应链角色与实体经营信号

- 记录可见的产品、包装、材料、规格、设计、受众、卖点，以及零售、批发、进口、品牌、制造、出口等角色信号。
- 检查公开地图地址、门店、仓库、showroom、公开评论和公开经营场景。
- 每个角色都写作“角色 + 证据”；多个角色可以并存。
- 角色、职位或零售覆盖不等于采购权、采购意愿或采购决策权。

### D. 注册、商标、公开社媒与关键人员

- 在可用时检查政府注册库、商标公开库、公开新闻，以及公开 LinkedIn、Facebook、Instagram 页面和公开职业信息。
- 只读取无需登录、用户可见的内容；不登录、不绕过限制、不抓取点赞、粉丝或私密列表。
- LinkedIn 职位只是角色线索，不等于采购负责人或采购权。
- 历史联系人须区分 `historical_contact`、当前任职已验证、仅作邮箱命名样本等状态。

### E. Similarweb、海关与第三方材料

- 先尝试读取实际可正常访问的公开公司页、免费档或公开 SEO 页面。
- 围绕当前背调对象主动构造贸易数据查询，不把这一覆盖族写成被动“先尝试读取”。至少执行英文与中文两侧的对象锚定查询：
  - `"<公司名>" importer OR consignee OR "bill of lading"`
  - `"<公司名>" import records`、`"<公司名>" shipment records`、`"<公司名>" customs data`
  - `site:<公开贸易数据聚合站公司页域名> "<公司名>"`
  - `"<公司名>" supplier "<产品词>"`
  - `"<公司名>" 提单`、`"<公司名>" 进口记录`、`"<公司名>" 采购商`
- 搜索结果摘要里可见的对方名称、日期、品名/HS、起运地或目的地，按第 4 节字段合同记为独立的“疑似进出口记录”；不能因为详情页打不开就丢弃这些字段。摘要不是 `Observation`、`Claim` 或 `ClaimEvidence`。
- 记录实际可见原文、来源 URL、页面定位、页面日期（若可见）和观察日期。
- 遇到 403、Cloudflare、登录墙、付费墙、动态空页或无法打开页面，标记 `source_restricted`；不绕过访问限制、不换代理、不尝试规避反爬。
- 打不开贸易数据详情页时，仍保留搜索摘要可见部分，`visibility=search_snippet_only` 或 `detail_restricted`，并在报告里明确“详情受限”。
- 用户提供的海关导出、Similarweb 报告、截图、Excel、PDF 等，记录为“用户提供第三方材料信号”。
- 公开 teaser 和用户材料都不能外推为完整贸易数据、真实总采购量、当前采购周期、采购力、从中国采购事实或采购意愿。

### F. 围绕该对象的全网交叉核验

- 查询必须锚定指定对象，例如公司名、品牌、域名、地址、公开电话、公开邮箱，结合产品、母公司、商标、关键人员或角色。
- 贸易数据查询也必须锚定当前背调对象，不得扩展成“产品 + 国家找一批同类客户”。
- 不执行“产品 + 国家找一批同类客户”的扩展查询；这属于主路径批量发现。
- 发现竞争对手、兄弟品牌、母公司、工厂或分销商时，默认记录为关联实体或线索，不批量输出为新客户。

## 疑似进出口记录字段合同

贸易摘要必须写入根节点可选数组 `suspected_trade_records`，只在
`task_mode=customer_background_research` 使用；不要复用 `hypotheses`，也不要放入
`Claim`、`ClaimEvidence`、`Assessment` 或 `DeliveryManifest`。记录不包含必填
`entity_id`，主体关联只通过 `subject_match_level` 表达。

每条记录保留以下字段：

- `record_id`、`direction`（`import` / `export` / `unknown`）、`counterparty_name_verbatim`；
- `record_date`（不可见写 `date_not_visible`）、`product_or_hs_verbatim`、`origin_or_destination_verbatim`（可选）；
- `subject_match_level`（`name_exact_address_match` / `name_exact_address_differs` / `partial_match` / `unknown`）；
- `aggregator_source_name`、`aggregator_source_url`（公开 URL、无凭据）；
- `visibility`（`search_snippet_only` / `public_page_opened` / `detail_restricted`）；
- `status`（`suspected_identity_pending` / `not_searched` / `searched_not_found` / `source_restricted`）；
- `cannot_conclude` 固定写明不能推出采购量、采购周期、采购意愿、从中国采购事实；
- `next_step_for_user` 固定写“请用你自己的海关数据渠道按上述字段核实”。

## 联系人与桥接边界

- 不猜邮箱，不从姓名或域名生成邮箱。
- 不把 email deliverability 当作身份或当前任职证明。
- 联系人、邮箱、电话、表单和供应商入口必须保留来源及归属状态。
- Bridge Candidate 仅限公开职业联系人，或公开来源明确陈述的关联关系。
- 不从同姓推断亲属、家族企业关系、老板关系或桥接价值。
- 不把 Founder 或 Owner 默认当采购负责人。
- 联系人归属不明确时，使用待确认归属或 `UnassignedContactLead` 思路，不强行关联到 Entity。

## 客户背调报告研究草稿

默认交付给用户的是业务人员能直接读懂、能据此行动的 Markdown 表格，不使用 `Claim`、`Hypothesis`、`EntityRelationship`、`Observation`、`bridge candidate` 等内部术语作为表头或正文。先给一句不超过两句的白话判断，再按以下六张固定表输出；只有存在 `suspected_trade_records` 时才追加第七张条件表，不输出空的贸易记录表：

1. **客户一眼看懂**：这是谁、公开在做什么、值不值得继续跟、能不能开始联系、下一步怎么做。
2. **客户、品牌与关联方**：名称、它是什么、和客户的关系、目前把握、我们依据什么。
3. **我们看到的业务机会**：我们看到的情况、对我们意味着什么、建议怎么切入、把握程度。
4. **怎么联系、先找谁**：建议联系谁/哪里、为什么先找这里、联系时先问什么、状态。
5. **跟进前要注意什么**：要注意的事、可能影响、建议动作、目前状态。
6. **信息从哪里来**：上面哪条信息、来源、链接或材料、看到的原话或位置、时间、状态。
7. **疑似进出口记录（第三方聚合，待核实）**（条件表）：仅展示公开摘要抓到的疑似记录字段，详情 URL 和原文摘录仍集中放在“信息从哪里来”。

对话表格每张最多六列。URL、原文摘录和复杂来源定位只放在最后的“信息从哪里来”；前五张表不堆砌证据细节。

如果用户要在 Codex / ChatGPT app 中直接阅读 Markdown 报告，优先使用统一交付器：

```bash
python3 scripts/export_superleads_markdown.py graph.json --route customer_background_research --output report.md --format json
```

客户背调 Markdown 正式交付必须有已保存的 graph JSON 和 Markdown exporter 返回的
`ok=true`。不要声称 `export_superleads_markdown.py` 或 Markdown exporter 只支持
批量客户开发；它支持 `customer_background_research`。如果该命令失败，返回失败
payload 或改交付 CSV/XLSX，不要把手写研究摘要称为正式 Markdown 报告。

如需 CSV / XLSX 交接，可使用 `python3 scripts/export_workbook.py graph.json --output-dir out --mode background --format csv` 导出同样的六张固定表；有 `suspected_trade_records` 时同步追加同名条件 sheet。两类导出都只展示当前背景对象、其证据支持的关联主体与线索，不会输出无关批量客户或正式名单内容。

表述规则：

- 只有有可检查同一主体来源支持的内容，才可写“已确认”或“已核实”。
- 不确定关系、采购可能性、联系人职责和客户价值写作“待确认”“建议先问”“可能影响”，不得伪装成事实。
- Founder、Owner、老板等只能作为转接线索，不能写成采购负责人。
- 历史材料必须标为“历史信息，需确认现在是否仍有效”。
- 搜索摘要、访问受限页面和用户提供的第三方材料只能作为线索或材料信号，不得写成已确认的公司事实。
- 疑似进出口记录永远只能写“疑似”，不得升级为已确认记录；`subject_match_level` 不是 `name_exact_address_match` 时，用户可见状态必须写“疑似，主体待确认”。
- 必须写明来源是第三方贸易数据聚合站公开摘要，**非官方海关记录**；详情受限时只保留摘要可见字段。
- 用户下一步统一写“请用你自己的海关数据渠道按上述字段核实”，不得建议购买或推荐任何数据服务商。
- `not_searched` 必须显示“本轮未检索”，`searched_not_found` 必须显示“已检索未见”，不得合并成“暂未找到”。
- “值不值得继续跟”是基于当前可核实信息的跟进建议，不等于采购意愿、客户价值、报价或谈判结论。

V1 不承诺自动网页截图存档。用户提供的截图可以作为材料来源，但不能因为 OCR 或截图内容直接升级为独立公开事实。

## 与严格路径的关系

- 背调不产生 `Assessment`，不做客户分层，也不要求 `ScopeDecision` 或当前开发方向合同。
- 当前背调不要求 `ReviewAttestation`、双 actor、graph hash freshness、`DeliveryManifest` 或 full review。
- 本阶段不要求 `Plan`；不得为了满足当前 Plan 的发现/客户分层字段而伪造 Plan。
- 这不表示放弃事实纪律：来源、URL 安全、联系信息归属、Entity 不乱并、历史与当前区分、以及冲突保留仍必须遵守。
- 将来用户若明确要求把一个已解析实体纳入更严格的正式批量开发名单，必须由独立、明确的请求启动现有严格路径；本 skill 不自动升级。
