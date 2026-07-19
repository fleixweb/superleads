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

完整参考样例用于理解五类相关性、五类信号状态、联系方式三态和排除记录；它不是每轮默认发现要照抄的图谱模板。

---

## 最低 Candidate 字段清单

每个 Candidate 至少要有：

- `name` 或 `company_name`
- `run_id` / `brief_id` / `plan_id`（与当前 Run 一致）
- 发现来源之一：`source_hint` 或 `source_url` 或 `discovery_refs[].label`
- `dedupe_basis`（非空，去重依据）
- `business_relevance_status`（五取一，见下）
- `business_relevance_basis`（非空）
- `signal_summary`，含五个信号键，每个都有合法 `status`（见下）
- `unknowns` 与 `source_restrictions`（列表，可为空）

`website` 若填写：只接受**安全公开 HTTP(S) URL 或纯公开域名**（如 `example.com`），不自动补协议，不接受 userinfo / 敏感 query/fragment 参数 / 私网 / 非 HTTP(S)。`source_url`、`discovery_refs[].url`、信号 `items[].source_url`、SearchLog `result_url` 同样只接受安全公开 HTTP(S) URL。

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

## 五类公开信号状态

用于 `signal_summary` 的每个键（`business_match` / `website_contact` / `trade_record` / `china_relation` / `product_description_or_hs`）：

| 状态 | 含义 |
|---|---|
| `observed` | 展示来源原文/字段、URL、日期或期间 |
| `not_observed` | 只表示**已查明示范围内**未见，须保留已查来源/期间；不是「已证明不存在」 |
| `not_searched` | 尚未检索，表示未知 |
| `identity_pending` | 信号无法可靠归属同一主体，禁止拼接 |
| `source_restricted` | 登录/付费墙/403/415/工具限制/可见内容不足 |

真实网络中 403 / 415 / 429 / JS 空壳很常见，应如实记为 `source_restricted` 或 `not_observed` 并保留 Candidate，**不能因来源打不开就判定企业不存在或不相关**（见 `docs/validation/claude-code-web-access-baseline.md`）。

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
