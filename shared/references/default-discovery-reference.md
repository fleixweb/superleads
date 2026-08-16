# 默认发现参考（Default Discovery Reference）

本文件区分两份 Superleads **默认发现候选池**运行时参考材料：

- **最小骨架（批量默认发现起点）**：[`default-discovery-minimal-skeleton.example.json`](./default-discovery-minimal-skeleton.example.json)
- **完整参考（状态、联系方式、来源与冲突边界）**：[`default-discovery-reference.example.json`](./default-discovery-reference.example.json)

两份样例均由 `evals/run_evals.py` 从共享 references 直接验证（validate 通过、initial 审计通过、initial 导出通过），因此文档与测试不会各自漂移。**请勿把它们复制进 `evals/fixtures/`；需要失败用例时从它们派生或在语义上明确关联。**

> 默认发现**不要求生成** Entity、Claim、ClaimEvidence、ScopeDecision、Assessment、ReviewAttestation、Audit、DeliveryManifest，也不要求完整联系人归属核验。它们只在实际来源、联系方式、主体冲突或用户明确要求的按需深查中按需增加。

---

## 何时进入这个样例

用户以自然语言给出「产品/服务 + 至少一个范围轴（国家/客户类型/渠道/关键词/种子公司/展会材料等）」，且**未**明确要求正式核查、背景调查或标准开发名单时，走默认发现，产出**发现候选池**。样例对应的任务是：

> “帮我找英国经销商/批发商，产品是不锈钢保温杯。”

默认批量发现先从**最小骨架**开始：`runs / briefs / plans / candidates / search_logs`。Candidate 不要求 Entity、Source、Observation、ContactPoint 或 ContactClaim。只有 Agent 实际打开来源并需要保存可核验原文、展示可见联系方式或处理主体冲突时，才按需增加 Source / Observation / Contact 等对象。

完整参考样例用于理解五类相关性、公开信息覆盖状态、联系方式三态和排除记录；它不是每轮默认发现要照抄的图谱模板。

---

## 最低 Candidate 字段清单

每个 Candidate 至少要有：

- `name` 或 `company_name`
- `run_id` / `brief_id` / `plan_id`（与当前 Run 一致）
- 发现来源之一：`source_hint` 或 `source_url` 或 `discovery_refs[].label`
- `dedupe_basis`（非空，去重依据）
- `business_relevance_status`（五取一，见下）
- `business_relevance_basis`（非空）
- `signal_summary`，含八个信号键（`business_match`、`website_contact`、`social_company`、`social_person`、`map_listing`、`trade_record`、`china_relation`、`product_description_or_hs`），每个都有合法 `status`（见下）
- `unknowns` 与 `source_restrictions`（列表，可为空）

`website` 若填写：只接受**安全公开 HTTP(S) URL 或纯公开域名**（如 `example.com`），不自动补协议，不接受 userinfo / 敏感 query/fragment 参数 / 私网 / 非 HTTP(S)。`source_url`、`discovery_refs[].url`、信号 `items[].source_url`、SearchLog `result_url` 同样只接受安全公开 HTTP(S) URL。

`初筛客户名单` 不是默认发现的安全独立层级；当前实现应以 `发现候选池` 承载默认弱证据交付，并在候选池内部用 `分区`、`依据状态` 和公开信号说明表达中间态。

默认发现的 `依据状态` 先看降级信号、再判断是否能显示 `已有明确依据`：同一 Candidate
的任一公开信号出现 `identity_pending` 时显示 `说法冲突待复核`；任一公开信号出现
`source_restricted` 或 `source_restrictions` 非空时显示 `来源受限`；只有没有这些降级
信号时，`business_match.status = observed` 才能显示为 `已有明确依据`。

---

## 业务相关性状态（五取一）

只依据**已观察**的产品/服务/应用/角色/渠道/地域或明确排除事实归类；它不是采购意向、客户质量、商业价值或采购概率。

| 状态 | 何时使用 | 样例候选 |
|---|---|---|
| `directly_related` | 已打开来源直接显示业务符合本次边界 | HydraTrade Supplies |
| `possibly_related` | 有目录/地域/产品线索，但确切业务关系未确认 | Northshore Drinkware |
| `insufficient_information` | 只有弱线索（如展会名单仅公司名），**不得伪造已观察信号** | Peak Bottle Co |
| `identity_pending` | 同名/域名/地址/贸易记录不能可靠归属同一主体，**不得拼接** | Summit Trading |
| `explicitly_excluded_or_unrelated` | 已观察到错误市场/竞品原厂等明确排除事实；**保留在「已排除客户」，不静默删除** | Ironforge Manufacturing |

`directly_related` / `possibly_related` / `explicitly_excluded_or_unrelated` 要求 `signal_summary.business_match.status = observed`，且至少一条带来源标签或安全公开 URL 的说明。`identity_pending` / `insufficient_information` 反而应保留主体冲突、未知与来源缺口，不要为了填表造信号。

---

## 默认公开信息覆盖

批量开发客户的默认 Plan 至少覆盖以下公开来源类别：

- `website`、`directory`、`document`、`social`、`map`、`trade_aggregator`、`search_result`

默认联系方式和公开信息补全目标至少包括：

- `email`、`phone`、`contact_form`、`social_company`、`social_person`
- `person_name`、`job_title`、`address`、`map_phone`、`public_trade_summary`

这些是覆盖计划，不表示每个候选都已经查到结果。对进入本轮输出范围的每个 Candidate，分别记录官网/联系方式、公司公开社媒、公开职业线索、地图和第三方贸易摘要的状态；不能只补查模型主观认为更有价值的候选。

每个来源类别设置有限的每候选查询和打开预算；同一 Run 对相同 canonical/final URL 去重。超过预算必须写 `not_searched` 和“本轮未检索”，不能写成未发现或不存在。

## 阶段、预算与恢复

默认发现按 `breadth_search`（广度搜索）、`source_verification`（有限来源核验）、`supplement`（本轮明确要求的联系人、贸易或历史补充）和 `serial_decision`（主体合并、冲突处理与正式升级）记录阶段。独立查询组只能标“可并行计划”；宿主未明确报告真实并行或流式能力时，状态只能写“分批执行”，不得虚构后台进度。

每个 Run 的可选 `execution_state` 记录查询组数、每组候选上限、每候选核心来源打开上限、联系人/贸易/历史参考是否包含、覆盖完成条件和低增量停止条件。来源缓存只在同一 Run 内按规范化 URL 复用，并记录内容哈希、观察日期、来源主体、事实领域和关联查询组；多个查询组引用同一已打开来源，不重复打开或复制 Observation。

在阶段边界保存 Brief、查询组、SearchLog、已打开来源、Observation、去重结果与完成/未完成状态。中断恢复只继续未完成的本 Run 工作；旧 Run 内容统一标为“历史参考，需重新核验”，除非本轮重新打开并记录，否则不能成为本轮事实或 Claim。状态摘要显示当前范围、候选数、已打开来源数、待确认、来源受限、本轮未执行及下一阶段范围，而非客户价值排序。

## 公开信号状态

用于 `signal_summary` 的每个键：

| 状态 | 含义 |
|---|---|
| `observed` | 展示来源原文/字段、URL、日期或期间 |
| `not_observed` | 只表示**已查明示范围内**未见，须保留已查来源/期间；不是「已证明不存在」 |
| `not_searched` | 尚未检索，表示未知 |
| `identity_pending` | 信号无法可靠归属同一主体，禁止拼接 |
| `source_restricted` | 登录、验证码、403、Cloudflare、付费墙、工具限制、动态空壳或可见内容不足 |

真实网络中 403 / 415 / 429 / JS 空壳很常见，应如实记为 `source_restricted` 或 `not_observed` 并保留 Candidate，**不能因来源打不开就判定企业不存在或不相关**（见 `docs/validation/claude-code-web-access-baseline.md`）。

社媒、地图和贸易摘要还用 `collection_status` 区分：`not_searched`（本轮未检索）、`searched_not_found`（已检索未见）、`search_summary_visible`（仅搜索摘要可见）、`public_page_opened`（公开页面已打开）、`details_restricted`（来源受限）、`identity_pending`（疑似，主体待确认）和 `user_provided_material`（用户提供资料）。社媒和地图搜索摘要只能保存同一 Run SearchLog 绑定的未验证 URL 线索；其中的人名、职位、电话、地址或经营场景不得写成已观察事实。贸易摘要可保留同一 Run SearchLog `visible_excerpt` 中逐字可见的方向、对方名称、日期、产品/HS、起运地或目的地，但仍只是第三方摘要，不能升级为已观察事实、联系人或正式证据。

## 公开页面与受限处理

只使用当前 Run 实际成功并报告为 `available` 的 `search.web`、`source.open`、`browser.render` 或 `document.extract`。`social.visible.read`、`maps.lookup` 等能力名称不能证明宿主一定提供了相应工具；没有独立读取器时，正常打开的公司社媒和地图页面分别作为 `medium: social`、`medium: map` 的普通公开来源记录。已打开的社媒、地图或贸易项必须绑定 `discovered_public`、`access_boundary: public_no_login` 的 Source，以及同一 Run 的 Observation；所有展示字段都要能在 Observation 的可见摘录中复核。名称相同或地址相同不足以归并，必须保留主体待确认。

页面需要登录、出现验证码、返回 403、Cloudflare/人工验证、付费墙、明确禁止自动化、动态空壳或无可靠主体关联时，立即停止该 URL 的自动读取，不重试、不绕过、不使用账号、Cookie、Token、密钥、代理或付费 API。记录“来源受限”，并在 Candidate、覆盖/收敛说明和待确认事项中给出以下对应建议：

- 一般受限：`来源受限：该公开页面需要登录、验证码、付费访问、人工验证或当前 AI 无法正常读取。Superleads 不会绕过这些限制。请你手动打开并查询该页面；如果确认后可以提供公开链接、截图、PDF、Excel 或脱敏资料，我可以继续帮你整理和核对。`
- 动态内容：`来源受限：页面可以访问，但当前 AI 无法自动读取其中的动态内容。请你手动查看并把需要核对的公开内容或截图发给我。`
- 贸易详情：`来源受限：第三方贸易数据详情页需要登录、付费或无法正常打开。当前 AI 不能自动化完成该详情查询，请你使用自己的贸易数据渠道手动核实。`

第三方贸易信息统一显示为“第三方贸易数据聚合站公开摘要，非官方海关记录”。只保留页面或摘要实际可见的方向、对方名称、日期、产品/HS、起运地或目的地及主体匹配状态；不能推出完整采购量、金额、采购周期、采购意愿、采购权限、从中国采购事实、未来订单或该公司一定是目标客户。

---

## 联系方式三态区分

样例覆盖三种典型 `export_status` / 用户端状态：

| 场景 | export_status | 用户端 | 样例 |
|---|---|---|---|
| 来源与归属都明确的公开联系方式 | `ready` | 可直接使用 | HydraTrade 销售邮箱 |
| 公开可见、但归属需再确认 | `export_with_source_note` | 建议核查后使用 | Northshore 公开电话 |
| 有价值但主体未定 | `needs_manual_association_review`（+ `UnassignedContactLead`） | 待确认归属 | Summit 目录电话 |

禁止导出：猜测邮箱、无来源联系方式、跨主体错配。`ready` 的 `association_evidence_text` 必须**点名其归属实体**。

---

## 高频 validator 错误与修正

| 错误码 | 原因 | 修正 |
|---|---|---|
| `default_discovery_candidate_signal_status_missing` | 五个信号键缺一或 status 非法 | 补齐五键，每个 status 用上表五取一 |
| `default_discovery_business_match_not_observed` | 标了 directly/possibly/excluded 却没有 observed 业务信号 | 未真正观察到业务时改标 `insufficient_information` 或 `identity_pending` |
| `default_discovery_business_match_source_missing` | observed 业务信号缺来源 | 给 `items[]` 加 `source_label` 或安全公开 `source_url` |
| `exportable_contact_association_missing_entity_name` | `ready` 联系方式的归属证据没点名实体 | 在 `association_evidence_text` 引用含实体名的原文 |
| `candidate_website_url_not_public` | website 是危险 URL | 用纯域名或安全 HTTP(S) URL；打不开就留来源标签而非猜 URL |
| `candidate_source_url_not_public` / `candidate_signal_source_url_not_public` | 链接含 userinfo/token/私网/非 HTTP(S) | 换安全公开 URL，或保留受限说明 |
| `default_discovery_candidate_run_binding_missing` | Candidate 未绑定当前 Run/Brief/Plan | 补 `run_id` / `brief_id` / `plan_id` |
| `default_discovery_candidate_dedupe_basis_missing` | 缺去重依据 | 补 `dedupe_basis`（如「名称+域名一致」） |

---

## 边界重申

默认发现的目标是**可追溯、带公开信号与未知项的发现候选池**，不是「筛剩少数高质量/正式客户名单」。要形成标准开发名单或正式客户判断，须由用户明确要求并另走深查门禁（Claim → ClaimEvidence → ScopeDecision → Assessment → Review → Audit）。
