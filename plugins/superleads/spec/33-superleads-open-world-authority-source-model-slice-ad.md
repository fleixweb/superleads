# Slice AD：开放世界权威来源识别模型

日期：2026-07-28

## 1. 本 Slice 要纠偏什么

前序建议里提到“先覆盖美国、中国、越南、欧盟占位”的说法有偏差。Superleads 面向的是开放世界外贸任务：用户的默认出口国、原产国、实际起运国、目标销售国家/地区、过境地、港口、认证体系和交易品类都无法预先穷举。

因此，产品出海市场分析不能走“把 200 多个国家/地区逐一列官网”的路线。正确方向是：

> 建立一套开放世界权威来源识别模型：面对任意国家/地区和任意事实域，系统先动态寻找候选主管来源，再用可见证据核验来源身份和适用范围；核验不了就降级，不把字符串、域名后缀、Source Pack 或搜索摘要当成权威事实。

本 Slice 是产品规格冻结，不写代码、不联网、不新增真实法规、关税、认证或国家事实库。

## 2. 一句话原则

**权威来源不是“国家清单”，而是“来源身份 + 事实域 + 管辖范围 + 可见证据 + 时效”的组合判断。**

同一个来源在一个事实域可能权威，在另一个事实域可能只是参考：

| 来源例子 | 可以支持 | 不能自动支持 |
|---|---|---|
| 目的国海关税则入口 | 候选税则、进口税费、部分清关文件入口 | 产品安全认证、市场需求、最终归类 |
| 目的国市场监管 / 产品安全主管机关 | 准入、标签、合格评定要求 | 进口关税、物流时效、现货价格 |
| 认证机构 / 实验室 | 测试标准、认证路径、证书验证线索 | 该认证是否法律强制、产品已合规 |
| 货代 / 报关行博客 | 操作经验、申报线索、物流提醒 | 官方法规要求、最终税率、COO 是否必需 |
| B2B / 电商平台 | 价格、规格、渠道观察 | 认证要求、销量、采购意愿 |
| Google Trends | 相对搜索兴趣 | 真实销量、进口量、GMV |

## 3. 已冻结决策

| 决策 | 含义 | 后果 |
|---|---|---|
| 不做国家穷举 | 不把“美国/中国/越南/欧盟”等样例当覆盖边界 | 未预置国家仍然可以生成查询计划和候选来源发现路径 |
| Source Pack 不是事实库 | Source Pack 只提供入口、查询模板、观察要求 | MatrixRow / EvidenceCard 不得直接引用 Source Pack 得出事实 |
| 权威性不能靠字符串 | 页面出现 `official`、`regulation`、`customs` 等词不等于权威 | validator 后续应阻断 keyword-only authority |
| 权威性不能只靠域名后缀 | `.gov`、`.gov.xx`、`.org`、`.eu`、普通 `.com` 都可能需要核验 | 域名只能作为身份线索之一 |
| 权威性必须绑定事实域 | “这个来源权威吗”要改成“它对哪个事实域权威” | 税费来源不能自动支撑认证，认证机构不能自动支撑法律强制 |
| 权威性必须绑定管辖范围 | 目的国、出口申报国、原产国、起运国、关税同盟、港口、州省可能不同 | 美国来源不能支撑摩洛哥法规，中国出口要求不能支撑美国进口要求 |
| 权威性必须有证据 | 需要记录为什么认为它是主管机关、官方入口、授权机构或二级参考 | 没有身份证据时只能标候选来源或权威性待核实 |
| 无法验证时必须降级 | 查不到或打不开官方来源时，保留查询路径和待核实项 | 不输出确定性“需要 / 不需要 / 现行 / 最新 / 已合规” |

## 4. 与前序 Slice 的关系

| 前序机制 | Slice AD 如何接上 |
|---|---|
| Slice 8 真实来源采集策略 | 把“官方和原始来源优先”细化为“如何识别官方 / 主管 / 授权 / 二级来源” |
| Slice 9 Source Pack 合同 | 明确 Pack 是入口目录，不是权威事实；Pack 可作为发现加速器，但不能作为结论依据 |
| Slice W / X 认证准入纠偏 | 认证要求必须由目标国事实域适配的权威来源支撑，不能由用户材料反推 |
| Slice 13 / Code F COO 纠偏 | COO / proof of origin 必须查目标国规则和适用条件，不能由用户是否提供文件反推 |
| Slice AA 弱证据校准 | 把强二值判断改为弱证据收敛；权威性也应有候选、待核验、辅助参考等中间状态 |
| Code Slice AB 多来源互证 | 多个弱来源可以增强参考价值，但不能替代主管来源；互证不等于官方权威 |
| Code Slice AC 时效降级 | 权威来源也要看来源日期、生效日期和复核窗口；权威但过期仍需降级 |

## 5. 核心对象模型

本 Slice 冻结未来可实现的数据结构方向，字段名为建议名，不要求本轮写代码。

### 5.1 `AuthorityProfile`：来源身份画像

用于描述“这个来源是谁”，不是描述“这个来源说了什么事实”。

| 字段 | 含义 |
|---|---|
| `authority_profile_id` | 来源身份画像 ID |
| `source_id` / `source_entry_id` | 对应本次打开来源，或候选入口 |
| `jurisdiction_type` | 国家、关税同盟、地区、州省、港口、国际组织、承运网络、产品来源等 |
| `jurisdiction_code` / `jurisdiction_name` | 管辖范围代码或名称；未知时保留规范名称 |
| `institution_name` | 机构名称 |
| `institution_name_local` | 当地语言机构名称 |
| `institution_type` | 海关、贸易部、市场监管、标准机构、食品/农业、交通/危险品、港口、认证机构、商会、行业协会、平台、媒体等 |
| `authority_level` | 来源等级，见第 6 节 |
| `authority_basis_summary` | 为什么这样判断其身份和等级 |
| `identity_evidence_ids` | 支撑身份判断的证据 |
| `capability_ids` | 该来源能支持哪些事实域 |
| `known_limitations` | 该来源不能支持什么 |
| `verification_status` | 已核验、候选待核验、无法核验、冲突、未执行 |

### 5.2 `AuthorityIdentityEvidence`：权威性证据

用于记录“为什么认为这个来源属于某机构或某级别”。不能只写模型判断。

| 证据类型 | 作用 | 边界 |
|---|---|---|
| 官方门户链接 | 政府统一门户、主管机关官网链接到该系统 | 强身份线索，但仍要看页面内容和适用范围 |
| 页面页脚 / 机构说明 | 页脚、About、Contact、法定职责说明显示机构身份 | 自称官方时要尽量找交叉证明 |
| 官方法规库 / 公报 | 法律数据库、官方公报、法规发布页面 | 可支持法规出处，但仍需 freshness |
| 授权名单 / 认可名单 | 主管机关列出认证机构、实验室、签证机构 | 只支持“被列入/授权”范围，不支持产品已合规 |
| PDF 来源定位 | PDF 来自官方域名、官方法规库或主管页面 | PDF 文件名不能替代来源身份核验 |
| 机构联系方式 / 地址 | 辅助核验机构身份 | 不能单独支撑权威性 |
| 第三方描述 | 律所、货代、媒体说它是官方 | 只能作线索，不能单独核验权威性 |

### 5.3 `AuthorityCapability`：事实域能力

用于回答“这个来源对哪个事实域有资格说话”。

| 字段 | 含义 |
|---|---|
| `fact_domain` | 进口税费、认证准入、COO、出口管制、物流预申报、市场价格、趋势、产品资料等 |
| `supported_claim_types` | 可支持的结论类型，如候选税则、官方文件要求、注册入口、标签规则等 |
| `unsupported_claim_types` | 明确不能支持的结论类型 |
| `required_applicability_fields` | 产品、HS、用途、材质、运输方式、原产国、目标国、日期等适用条件 |
| `minimum_authority_level` | 该事实域最低需要什么来源等级 |
| `requires_freshness_record` | 是否必须接 Code Slice AC 时效记录 |
| `requires_professional_confirmation` | 是否仍需报关、认证、承运、法律等专业确认 |

### 5.4 `AuthorityVerificationRecord`：本轮核验记录

用于表达“本次报告是否核验了来源权威性”。

| 字段 | 含义 |
|---|---|
| `verification_id` | 本轮核验记录 ID |
| `run_id` / `brief_version_id` | 所属运行与 Brief |
| `source_id` / `observation_ids` | 本次打开的来源和观察 |
| `authority_profile_id` | 关联的来源身份画像 |
| `fact_domain` | 本轮用它支撑的事实域 |
| `verification_status` | `verified_for_fact_domain`、`candidate_needs_check`、`secondary_reference_only`、`unable_to_verify`、`conflicting_identity`、`not_executed` |
| `verification_basis` | 本轮看到哪些可见证据 |
| `cannot_support` | 不能把该来源用于什么结论 |
| `next_verification_steps` | 下一步怎么核实 |

## 6. 来源等级口径

为了避免状态词通胀，内部可以有较细枚举，但用户可见应压缩成人话。首版建议如下：

| 内部等级 | 用户理解 | 可支撑什么 | 不能自动支撑什么 |
|---|---|---|---|
| `primary_official_authority` | 主管机关 / 官方法规或税则来源 | 对应事实域的主要依据 | 最终归类、最终税额、产品已合规、商业建议 |
| `official_service_or_portal` | 官方服务入口 / 政府门户 | 官方入口定位、表单、指南、检索入口 | 若页面不是主管事实域，不能支撑强结论 |
| `official_gazette_or_legal_database` | 官方公报 / 法规库 | 法规文本、发布日期、生效日期 | 具体产品适用仍需归类和条件判断 |
| `delegated_or_recognized_body` | 授权 / 认可机构 | 认证、检测、签证、标准路径线索 | 法律强制性、目标国海关最终认可 |
| `intergovernmental_reference` | 国际组织 / 跨国机制 | 框架、统计、分类、通用规则线索 | 替代目的国现行法规 |
| `industry_or_professional_reference` | 行业协会、律所、报关行、货代 | 背景解释、操作经验、下一步核实方向 | 官方要求、最终税率、已合规 |
| `commercial_market_reference` | 平台、B2B、电商、品牌零售 | 价格、规格、渠道、市场参考 | 法规、认证、销量、采购意愿 |
| `media_or_general_web_reference` | 媒体、博客、普通网页 | 新闻、背景、候选线索 | 强制要求、最新法规、最终结论 |
| `unknown_authority` | 权威性未核实 | 只能保留为待核实来源 | 任何确定性法规、税费、认证、COO 结论 |

## 7. 事实域最低来源要求

| 事实域 | 最低可接受来源 | 可作为辅助的来源 | 无权威来源时怎么写 |
|---|---|---|---|
| 进口税费 / 关税 / 税则 | 目的国海关、官方税则、官方裁定、官方法规库 | 报关行、税则工具、行业解释 | 候选税号 / 税费待官方复核，不写最新或最终税率 |
| 贸易救济 / 附加税 / 配额 | 目的国贸易救济、海关、商务/贸易主管机关 | 律所、行业协会、新闻 | 未核验，不写适用或不适用 |
| 目的国认证 / 准入 | 目的国主管机关、官方法规库、标准/市场准入主管入口 | 认证机构、实验室、律所解释 | `unable_to_verify`，列下一步官方核实路径 |
| 标签 / 包装 / 原产标识 | 目标国监管、海关、消费者保护、环保包装主管来源 | 行业指南、认证机构说明 | 不写已合规；区分网页标签和实物标签 |
| COO / proof of origin | 目的国海关、官方进口指南、贸易协定、rules of origin 官方来源 | 商会、签证机构、报关行解释 | 不写需要/不需要；保留条件和待查来源 |
| 出口要求 / 出口管制 | 出口申报国海关、商务/贸易、管制主管机关、官方清单 | 律所、报关行、行业协会 | 不写可出口/无需许可 |
| 检验检疫 / 食品农产品 | 目的国 / 出口国食品、农业、检疫主管机关 | 行业协会、进口商指南 | 不写可进口/可出口 |
| 危险品 / 锂电运输 | 交通/危险品主管规则、承运人规则、SDS/UN38.3/包装文件 | 货代经验、行业解释 | 不写可出运；列技术文件缺口 |
| 物流预申报 / 港口节点 | 海关、港口、机场、承运人官方规则 | 货代、船司航线资料 | 写候选路径，不写承诺时效 |
| 市场趋势 / 报告 | 官方统计、行业协会、公开报告、Google Trends | 媒体、平台、咨询摘要 | 写参考口径，不写真实销量 |
| 线上价格 / B2B/B2C | 平台商品页、品牌页、公开报价、交易所/指数 | 经销商、报价摘要 | 写规格化参考，不写目标价或成交价 |

## 8. 开放世界动态发现流程

当目标国家/地区没有预置 Source Pack 或 registry entry 时，系统仍应能继续，但只能按能力降级。

### 8.1 标准流程

| 步骤 | 产物 | 说明 |
|---:|---|---|
| 1 | `JurisdictionContext` | 明确目标销售国、出口申报国、原产国、起运国/港、过境地；未知项保留 |
| 2 | `FactDomainPlan` | 按事实域拆分：税费、认证、COO、出口要求、物流、市场信号等 |
| 3 | `AuthorityInstitutionHypothesis` | 猜测应找哪些机构类型：海关、贸易部、标准机构、农业食品、交通危险品、港口等 |
| 4 | `AuthorityDiscoveryQueryPlan` | 用英文、当地语言和必要中文生成查询组 |
| 5 | `CandidateAuthoritySource` | 搜索结果只作为候选来源，不支撑事实 |
| 6 | 打开来源并记录 Observation | 打开后才有可见内容、定位、日期、身份线索 |
| 7 | `AuthorityVerificationRecord` | 核验来源身份、事实域能力和不能支持什么 |
| 8 | EvidenceCard / MatrixRow | 只有通过来源身份、事实域、时效和证据边界后，才进入用户事实矩阵 |

### 8.2 动态查询方向示例

以“土耳其原产食品级塑料杯出口到摩洛哥”为例，系统不需要事先有摩洛哥 Pack，也不能因为没有 Pack 就停掉。它应生成：

| 事实域 | 候选查询方向 |
|---|---|
| 摩洛哥进口税费 | Morocco customs tariff official；目的国语言税则关键词；HS candidate + import duty |
| 摩洛哥食品接触材料准入 | Morocco food contact materials import regulation official；主管机关 + product safety |
| 摩洛哥标签 / 包装 | Morocco labeling packaging requirements official；consumer protection / market surveillance |
| 摩洛哥 COO / proof of origin | Morocco certificate of origin import requirement official；rules of origin；trade agreement Turkey Morocco |
| 土耳其出口要求 | Turkey export requirements plastic products official；Turkey customs export control |
| 物流 / 预申报 | Morocco customs advance manifest；Casablanca port import requirements |

如果只得到搜索摘要或货代博客，用户可见只能写“候选来源 / 待打开核实”，不能写“摩洛哥要求 X 认证”。

## 9. 用户可见展示口径

用户不应该看到复杂内部枚举，而应该看到这几列：

| 人话字段 | 说明 |
|---|---|
| 来源身份 | 主管机关 / 官方入口 / 授权机构 / 行业参考 / 商业参考 / 权威性待核实 |
| 适用范围 | 这个来源对应哪个国家/地区、哪个产品类别、哪个事实域 |
| 可以当作什么 | 可作为税则入口、认证路径、COO 条件线索、物流申报线索等 |
| 不能当作什么 | 不能当最终税率、不能当已合规、不能替代目标国海关裁定、不能当销量 |
| 资料时效 | 接 Code Slice AC，展示来源日期、生效日期、观察日期和复核建议 |
| 下一步核实 | 重新打开官方入口、找报关行、认证机构、承运人、进口商或主管机关确认 |

建议 Markdown 中增加“来源权威性 / 能支撑什么”摘要，而不是只在来源表末尾展示 URL。

## 10. 不能出现的错误

| 错误 | 为什么危险 | 应如何处理 |
|---|---|---|
| 货代博客出现 official/customs/regulation 字样，就支撑 required | 字符串可被任意网页复制 | 降级为行业/操作线索 |
| `.gov` 域名页面就支撑所有事实域 | 政府来源也有部门职责范围 | 检查事实域是否匹配 |
| 认证机构说明某标准，就写目标国强制认证 | 认证机构不一定代表法律强制 | 写“认证路径线索”，目标国强制性待主管来源核实 |
| WTO / WCO / ITC 资料替代目的国法规 | 国际组织通常是框架或统计，不等于目的国现行规则 | 作为辅助定位，不直接支撑强制要求 |
| Source Pack entry 直接变成 EvidenceCard | Pack 只是入口目录 | 必须打开来源形成 Observation |
| 多个弱来源一致就写官方已确认 | 互证不等于主管来源 | 写“多来源方向一致，但仍待官方核实” |
| 用户未提供证书就写不需要认证 | 用户材料状态不能反推目标国规则 | 分列目标国要求和用户材料状态 |
| 原产国、出口国、目标国混用 | 外贸规则依赖不同地理前提 | 分开记录并展示 |
| 官方来源过期仍写最新 | 权威不等于当前有效 | 接 freshness 降级 |

## 11. 未来 Code Slice AD 最小实现边界

Code Slice AD 不应实现全球国家库，而应实现“开放世界来源权威性防错闭环”。

| 模块 | 最小实现 |
|---|---|
| schema | 增加 authority profiles / identity evidence / capabilities / verification records |
| validator | 阻断字符串权威、域名权威、事实域错配、管辖范围错配、Source Pack 直接支撑事实、未打开来源支撑权威结论 |
| query plan | 当 registry 缺失时仍能生成动态 authority discovery 查询组 |
| exporter | 增加用户可见列：来源身份、适用范围、可以当作什么、不能当作什么 |
| audit | 将权威性待核实、事实域不匹配、来源身份冲突暴露为 limitation 或 blocker |
| fixtures/evals | 用少量虚构或脱敏 fixture 验证机制，不把美国/中国/越南作为覆盖边界 |

## 12. 建议错误码草案

| 错误码 | 触发条件 |
|---|---|
| `market_authority_record_missing` | 强监管事实域的确定性矩阵行缺权威性核验记录 |
| `market_authority_source_unopened` | 未打开来源或只有搜索摘要，却支撑权威结论 |
| `market_authority_keyword_only` | 仅靠 `official/customs/regulation` 等字符串判权威 |
| `market_authority_domain_only` | 仅靠域名后缀判权威 |
| `market_authority_identity_evidence_missing` | 权威来源画像缺身份核验证据 |
| `market_authority_fact_domain_mismatch` | 来源事实域能力与矩阵行事实域不匹配 |
| `market_authority_jurisdiction_mismatch` | 来源管辖范围与目标国/出口国/原产国/起运地角色不匹配 |
| `market_authority_secondary_promoted_to_official` | 行业/商业/媒体/货代来源被升级为主管官方来源 |
| `market_authority_registry_used_as_fact` | Source Pack / registry entry 直接支撑 EvidenceCard 或 MatrixRow |
| `market_authority_unknown_required_claim` | 权威性未知的来源支撑 required / normally_not_required 等确定性结论 |
| `market_authority_capability_missing` | 来源没有声明可支持的事实域能力 |
| `market_authority_common_rule_overgeneralized` | 国际/通用规则被泛化为某目的国确定要求 |

## 13. 建议 fixture 设计

| fixture | 预期 | 验收点 |
|---|---|---|
| `market_pass_authority_unknown_country_plan_only.json` | pass | 未预置国家也能生成 authority discovery 查询计划；不输出确定法规结论 |
| `market_pass_authority_official_for_tariff_only.json` | pass | 某来源可支撑税则入口，但不能支撑认证要求 |
| `market_pass_authority_cert_body_secondary.json` | pass | 认证机构作为认证路径参考，不升级为目标国法律强制 |
| `market_pass_authority_forwarder_logistics_clue.json` | pass | 货代资料只支撑物流线索和下一步核实 |
| `market_fail_authority_blog_claims_required_cert.json` | fail | 第三方博客含 official/regulation 字样却支撑 required |
| `market_fail_authority_domain_only_official.json` | fail | 仅靠域名后缀把来源判为官方 |
| `market_fail_authority_fact_domain_mismatch.json` | fail | 海关税则来源支撑产品安全认证结论 |
| `market_fail_authority_jurisdiction_mismatch.json` | fail | 出口国来源支撑目的国进口准入结论 |
| `market_fail_authority_source_pack_as_fact.json` | fail | Source Pack 直接进入 MatrixRow |
| `market_fail_authority_weak_corroboration_as_official.json` | fail | 多个弱来源互证被写成官方已确认 |

## 14. 非目标

本 Slice 不做：

- 不建立全球 200+ 国家/地区官网清单；
- 不联网查真实法规、关税、认证、物流或市场行情；
- 不把任何 Source Pack 种子样例当事实库；
- 不判断真实来源当前是否仍有效；
- 不替代报关、认证、法律、承运和进口商专业确认；
- 不输出是否值得进入市场、推荐客户、采购概率、推荐价格、最终税率或最终合规结论。

## 15. 冻结后的下一步

下一步可进入 **Code Slice AD：开放世界来源权威性防错闭环**。

实现顺序建议：

1. 先加最小 schema：AuthorityProfile / AuthorityIdentityEvidence / AuthorityCapability / AuthorityVerificationRecord；
2. 再加 validator：先阻断最危险的 keyword-only、domain-only、fact-domain mismatch、jurisdiction mismatch、registry-as-fact；
3. 再补 pass/fail fixtures；
4. 再优化 exporter 的人话字段；
5. 最后把 query plan 的动态 authority discovery 接入 Source Pack registry。

Code Slice AD 的验收标准不是“支持了多少国家”，而是：

> 面对未预置国家时，Superleads 能清楚生成待查路径；面对不权威来源时，Superleads 不会把它升级为官方结论。
