# 产品出海市场分析：Source Pack 字段合同（Slice 9）

本文件冻结 `产品出海市场分析` 未来可实现的 `Source Pack` 字段合同。它不是代码，不是国家事实库，也不保存任何当前法规、税率、价格、物流时效或市场结论。

一句话定义：**Source Pack 是“去哪里找、怎么找、打开后要看什么”的来源入口目录；它只能生成 Query Plan 和待打开来源，不能直接生成 EvidenceCard 事实。**

## 1. Slice 9 边界

| 项目 | 本轮决定 |
|---|---|
| 目标 | 冻结 Source Pack 的对象边界、字段、类型、状态、路由规则、复核规则和验收断言 |
| 当前仍不做 | 不写代码、不创建真实国家库、不填最新 URL 清单、不查询法规/关税/价格/趋势 |
| 适用对象 | 未来 source registry、Query Plan、SearchLog、Source/Observation、EvidenceCard、validator、audit、Skill 文档 |
| 关键边界 | Source Pack 不是事实库；不能被 Markdown/XLSX 直接引用为事实来源 |

## 2. Source Pack 是什么，不是什么

| 维度 | 是 | 不是 |
|---|---|---|
| 业务作用 | 帮系统知道某个国家/地区/事实域优先去哪类来源找资料 | 替用户判断产品能不能卖、值不值得卖 |
| 数据内容 | 来源入口、机构类型、查询模板、打开要求、抽取要求、复核周期、边界说明 | 关税税率、认证结论、物流承诺、价格区间、趋势结论 |
| 证据地位 | 只能作为采集计划和来源候选 | 不能作为已核实事实、Claim 或 MatrixRow 的事实依据 |
| 生命周期 | 可版本化、可复核、可废弃、可被用户/实现补充 | 不随每次报告自动变成事实 |
| 用户可见 | 可在来源覆盖说明中显示“本次按哪些来源目录查找” | 不应在事实表里显示为“依据 Source Pack 得出” |

Source Pack 的正确用法是：

```text
Brief + ProductAttribute triggers -> 选择 Source Pack -> 生成 Query Plan / 待打开入口 -> 打开来源 -> Observation -> EvidenceCard -> MatrixRow
```

错误用法是：

```text
Brief -> 选择 Source Pack -> 直接输出“该产品需要认证 / 税率为 X / 海运约 X 天 / 建议走某渠道”
```

## 3. 对象层级

| 对象 | 说明 | 可否直接支持事实 |
|---|---|---|
| `SourcePack` | 一组来源入口的集合，按国家/地区、角色和事实域组织 | 否 |
| `SourceEntry` | 一个具体来源入口，如主管部门、税则查询入口、港口公告入口、平台搜索入口 | 否 |
| `QueryTemplate` | 如何围绕产品、国家、HS 候选、属性触发项生成可审计查询 | 否 |
| `ObservationRequirement` | 打开来源后必须抽取哪些定位、日期、字段和限制 | 否 |
| `PackRouteRule` | 什么 Brief / 产品属性触发哪些 Pack 和 Entry | 否 |
| `PackReviewRecord` | Pack 本身是否过期、入口是否失效、是否需维护 | 否 |
| `Source` / `Observation` | 本次实际打开并抽取的网页、PDF、用户文件或可见页面片段 | 是，条件满足后 |
| `EvidenceCard` | 把 Observation 变成可边界化使用的信息卡 | 是，按状态支持 MatrixRow |

## 4. Pack 类型

Source Pack 不按“国家逐一手工写死”实现，而按“贸易角色 + 事实域 + 触发条件”组合。

| Pack 类型 | 主要用途 | 由什么触发 | 不得包含 |
|---|---|---|---|
| `destination_market_access_pack` | 目的国准入、认证、标签、包装、检疫、产品安全入口 | `target_country_or_region` + 产品属性触发项 | 该产品已经合规、无需认证 |
| `destination_certification_requirement_pack` | 目的国认证、测试、注册、标签、包装、进口许可、渠道准入要求入口 | 目标国 + 产品属性触发项 + 用途/销售路径/候选 HS | 需要/不需要某认证的结论、用户证书有效性、产品已合规 |
| `destination_duty_tax_pack` | 目的国官方税则、裁定、贸易救济、进口税费、优惠原产地 / proof of origin 入口 | `target_country_or_region` + 原产国状态 + HS 候选 | 最终税率、最终归类、COO 要求结论 |
| `destination_origin_proof_pack` | 目的国 COO / proof of origin / rules of origin / origin marking 入口 | 目标国 + 原产国/出口国状态 + 候选 HS + 贸易优惠/贸易救济/用户询问 COO | 直接判断用户文件有效、海关最终原产地裁定 |
| `export_country_pack` | 出口申报国海关、商务/贸易、检验检疫、出口管制入口 | `export_declaration_country` | 原产国自动等同出口国、出口许可结论 |
| `logistics_pack` | 港口、机场、口岸、承运人、预申报、路线和运输限制入口 | 起运国/目的国/运输方式/货物属性 | 最佳路线、承诺时效、货代报价 |
| `market_signal_pack` | Google Trends、统计、协会、公开报告、平台价格、指数/期货入口 | 目的国 + 产品名称/行业名/规格 | 销量、GMV、目标价、市场进入建议 |
| `common_rule_pack` | 跨国家或国际通用规则入口，如危险品、锂电、包装、运输通用规则 | 产品属性触发项，如锂电、危化、木包装、冷链 | 某一票货必然可运输或已合规 |
| `product_original_source_pack` | 产品官网、品牌页、手册、TDS、SDS、UN38.3、BOM、标签照片等入口组织 | 用户 URL/文件、品牌/制造商/型号 | 自动证明原产地、HS、认证或可运输性 |

说明：`common_rule_pack` 不代表规则全球一致，只代表它可能跨多个国家或运输体系被引用；真正适用仍要由目的国、出口国、运输方式和货物状态共同判断。

## 5. `SourcePack` 字段合同

| 字段 | 必填 | 说明 | 用户可见 |
|---|---|---|---|
| `source_pack_id` | 是 | 稳定 ID；不得含本地路径或内部敏感信息 | 否 |
| `display_name` | 是 | 人能看懂的名称，如“美国进口税费来源入口包” | 是，可在来源覆盖表显示 |
| `pack_type` | 是 | 使用第 4 节 Pack 类型枚举 | 是 |
| `trade_role` | 是 | `destination_market`、`import_customs`、`export_declaration`、`departure_logistics`、`transit`、`market_signal`、`common_rule`、`product_source` 等 | 是 |
| `jurisdiction_type` | 是 | `country`、`customs_union`、`region`、`subnational`、`port_or_airport`、`carrier_network`、`global_or_international`、`product_specific` | 是 |
| `jurisdiction_code` | 条件必填 | 国家/地区/关区/港口等代码；没有统一代码时写规范名称 | 是 |
| `jurisdiction_name` | 是 | 国家、地区、关税同盟、港口、机构网络或产品来源范围名称 | 是 |
| `language_codes` | 是 | 推荐查询/阅读语言，如英文、目的国语言、出口国语言、中文 | 是 |
| `fact_domains_supported` | 是 | 该 Pack 可帮助查找的事实域 | 是 |
| `fact_domains_not_supported` | 是 | 明确不能支持的事实域 | 是 |
| `product_trigger_tags` | 是 | 适用触发标签；通用品类写 `general_goods`，不能封闭 | 否/摘要可见 |
| `required_brief_fields` | 是 | 使用该 Pack 前 Brief 至少要有哪些字段 | 否 |
| `entry_ids` | 是 | 包内 SourceEntry ID 列表 | 否 |
| `route_rule_ids` | 是 | 触发该 Pack 的规则 | 否 |
| `status` | 是 | `draft`、`active`、`needs_review`、`deprecated`、`suspended` | 是 |
| `version` | 是 | Pack 版本；Pack 改动不等于事实更新 | 是 |
| `created_at` / `updated_at` | 是 | Pack 维护日期 | 否/摘要可见 |
| `last_reviewed_at` | 是 | 最近一次检查入口是否仍可用的日期；不是事实观察日期 | 是 |
| `next_review_due` | 是 | 下一次 Pack 维护建议日期；不是法规生效日期 | 是 |
| `review_cycle_policy` | 是 | `per_run`、`short_cycle`、`periodic`、`event_driven`、`manual_only` 等 | 是 |
| `owner_scope` | 是 | 内置、用户自定义、项目级、组织级、临时会话级 | 否 |
| `pack_boundary_note` | 是 | 必须写明“仅为来源入口目录，不含事实结论” | 是 |
| `blocked_outputs` | 是 | 使用该 Pack 时不得直接输出的结论类型 | 否/验收可见 |

## 6. `SourceEntry` 字段合同

`SourceEntry` 是一个待打开的入口，不是打开后的来源内容。

| 字段 | 必填 | 说明 | 用户可见 |
|---|---|---|---|
| `source_entry_id` | 是 | 稳定 ID | 否 |
| `source_pack_id` | 是 | 所属 Pack | 否 |
| `source_name` | 是 | 来源名称，尽量使用官方或公开名称 | 是 |
| `source_name_local` | 否 | 当地语言名称 | 是 |
| `source_owner_type` | 是 | `government`、`customs`、`standards_body`、`port_authority`、`carrier`、`industry_association`、`exchange`、`platform`、`report_publisher`、`brand_or_manufacturer`、`user_file`、`news` 等 | 是 |
| `source_authority_level` | 是 | `primary_official`、`secondary_official`、`original_product_source`、`industry_reference`、`commercial_reference`、`news_reference`、`user_provided`、`unknown` | 是 |
| `source_type` | 是 | 网页、PDF、法规库、税则查询、裁定库、平台搜索、趋势工具、统计库、公告页、文件等 | 是 |
| `landing_url_or_locator_template` | 是 | 入口 URL 或安全定位模板；不得存登录 token、本地路径、私有 hash | 部分可见 |
| `access_boundary` | 是 | `public`、`requires_login`、`paywalled`、`dynamic_page`、`user_provided`、`restricted`、`unknown` | 是 |
| `query_slots_supported` | 是 | 可填入的查询槽位，如产品名、HS、型号、国家、日期、港口、运输方式 | 否 |
| `search_hint_terms` | 否 | 搜索时可用的机构名/关键词；只作线索 | 否 |
| `expected_content_types` | 是 | 预期会看到的内容，如法规、税率表、标签指南、价格列表、港口公告 | 是 |
| `supports_fact_domains` | 是 | 这个入口打开后可能支持哪些事实域 | 是 |
| `does_not_support_fact_domains` | 是 | 明确不能支持哪些事实域 | 是 |
| `required_observation_fields` | 是 | 打开后必须抽取的字段，如日期、页码、适用产品、税基、单位 | 否 |
| `priority` | 是 | `P0`、`P1`、`P2`、`P3`；表示采集优先级，不表示事实已经可靠 | 否 |
| `fallback_entry_ids` | 否 | 该入口打不开时可尝试的备选入口 | 否 |
| `known_limitations` | 是 | 入口限制，如动态页面、付费墙、只覆盖某类产品、需要专业检索 | 是 |
| `safety_redactions` | 是 | 用户交付时必须隐藏的内容，如本地路径、token、内部 ID | 否 |
| `entry_status` | 是 | `active`、`temporarily_unavailable`、`moved`、`retired`、`duplicate`、`needs_review` | 是 |
| `last_entry_reviewed_at` | 是 | 入口本身最后检查日期；不是本次事实观察日期 | 是 |

## 7. `QueryTemplate` 字段合同

QueryTemplate 用来生成可审计查询组，避免让模型自由发挥。

| 字段 | 必填 | 说明 |
|---|---|---|
| `query_template_id` | 是 | 稳定 ID |
| `source_pack_id` | 是 | 所属 Pack |
| `query_group_id` | 是 | 趋势、价格、准入、`certification_requirement`、税费、`origin_proof_requirement`、出口、物流、外部因素等 |
| `purpose` | 是 | 为什么查，不得只写“了解市场” |
| `required_brief_fields` | 是 | 缺这些字段时不得执行 |
| `required_product_trigger_tags` | 否 | 如锂电、纺织、食品接触、危险品、农产品、散杂等 |
| `language_strategy` | 是 | 英文、目的国语言、出口国语言、中文等组合 |
| `term_slots` | 是 | 产品通用名、型号、HS 候选、成分、规格、国家、年份、运输方式等 |
| `source_entry_scope` | 是 | 允许搜索或打开哪些 Entry |
| `must_open_source_authority_levels` | 是 | 至少要打开哪些来源等级才可形成可核实 Observation |
| `reject_if_only_snippet` | 是 | 默认 true；只有搜索摘要不得形成事实 |
| `expected_observation_fields` | 是 | 打开后应抽取的字段 |
| `expected_matrix_sheet` | 是 | 对应工作簿中的表 |
| `fallback_status` | 是 | 查不到或打不开时写什么状态 |
| `handoff_target_skill` | 是 | 哪个 Skill 消费该查询计划 |

## 8. `ObservationRequirement` 字段合同

ObservationRequirement 规定“打开来源以后，至少要看见什么，才能进入 EvidenceCard”。

| 字段 | 必填 | 说明 |
|---|---|---|
| `observation_requirement_id` | 是 | 稳定 ID |
| `applies_to_source_entry_id` | 是 | 对应 SourceEntry |
| `required_locator` | 是 | URL、页面标题、页码、章节、表格、查询参数、截图区域等 |
| `required_visible_content` | 是 | 必须有可见内容，不允许只有模型总结 |
| `required_source_date_fields` | 条件必填 | 法规、税费、报告、新闻、价格、趋势必须尽量取发布日期/生效日期/观察日期 |
| `required_applicability_fields` | 是 | 适用国家、产品类别、HS、型号、运输方式、时间、订单/批次等 |
| `required_limitations` | 是 | 必须写清楚该来源不能支持什么 |
| `minimum_quote_or_excerpt_policy` | 是 | 保留短摘录或可定位摘要，避免整段复制 |
| `creates_evidence_card_when` | 是 | 形成 EvidenceCard 的最低条件 |
| `blocks_evidence_card_when` | 是 | 什么情况下只能作为候选线索或来源受限 |

## 9. `PackRouteRule` 字段合同

PackRouteRule 负责把 Brief 和产品属性路由到正确 Pack。

| 字段 | 必填 | 说明 |
|---|---|---|
| `route_rule_id` | 是 | 稳定 ID |
| `rule_name` | 是 | 人能看懂的规则名称 |
| `trigger_brief_fields` | 是 | 目的国、出口申报国、原产国、起运国、目的港、贸易术语等 |
| `trigger_product_tags` | 是 | 产品属性标签；可多标签叠加 |
| `excluded_when` | 否 | 哪些条件下不应触发 |
| `source_pack_ids_to_activate` | 是 | 触发哪些 Pack |
| `source_entry_filters` | 否 | 只激活 Pack 内部分 Entry |
| `requires_user_confirmation` | 是 | 是否需用户确认后再执行，如出口申报国未知时 |
| `fallback_when_missing_pack` | 是 | Pack 不存在时如何降级为人工 Query Plan |
| `handoff_to_skill` | 是 | 对应 Skill |
| `boundary_note` | 是 | 不得把触发规则当成事实结论 |

## 10. 产品触发标签

产品触发标签是开放集合，不能把 Superleads 限死在几个品类。第一版至少要支持这些常见标签：

| 标签族 | 示例标签 | 说明 |
|---|---|---|
| 普通贸易 | `general_goods`、`customized_parts`、`project_goods` | 不代表无需认证或普通货运输 |
| 电气/电池 | `electrical`、`lithium_battery`、`battery_installed`、`battery_standalone`、`rf_wireless` | 触发电气安全、无线、锂电运输等来源入口 |
| 危险/化学 | `chemical`、`dangerous_goods`、`liquid`、`powder`、`flammable`、`corrosive`、`aerosol` | 触发 SDS、危险品、包装和承运要求 |
| 物理运输 | `magnetic`、`oversize`、`heavy_lift`、`bulk_cargo`、`breakbulk`、`roro`、`cold_chain` | 触发物流、港口、装卸、温控等入口 |
| 人体/消费 | `food_contact`、`skin_contact`、`child_product`、`toy`、`ppe`、`cosmetic`、`medical_or_health` | 触发消费安全、标签、认证、检测入口 |
| 农业/生物 | `food`、`fresh_produce`、`tea`、`flower`、`seed`、`plant_material`、`animal_material`、`wood_packaging` | 触发检疫、植检、农残、冷链和包装入口 |
| 战略/管制 | `dual_use`、`encryption`、`military_related`、`sanctions_sensitive`、`restricted_end_use` | 触发出口管制、最终用途/最终用户核验入口 |
| 大宗/指数 | `steel`、`grain`、`mineral`、`energy`、`commodity_index_reference` | 触发期货/指数、质量标准、散杂运输入口 |

标签只能触发“查哪些来源”，不能直接形成“需要/不需要某认证”“可/不可运输”“受/不受管制”的结论。

## 11. 状态与优先级枚举

### 11.1 Pack 状态

| 状态 | 说明 | 可否自动用于采集计划 |
|---|---|---|
| `draft` | 草案，字段不完整或未复核 | 不可自动；需人工确认 |
| `active` | 字段完整，入口最近复核过 | 可用于生成 Query Plan |
| `needs_review` | 入口可能过期或需要维护 | 可提示，但关键事实域需复核 |
| `deprecated` | 已废弃，被新 Pack 替代 | 不可使用 |
| `suspended` | 暂停使用，如入口异常、合规不明 | 不可使用 |

### 11.2 SourceEntry 状态

| 状态 | 说明 | 处理 |
|---|---|---|
| `active` | 入口可用或近期可用 | 可进入 Query Plan |
| `temporarily_unavailable` | 临时不可访问 | 记录来源受限，尝试 fallback |
| `moved` | 入口迁移 | 使用新入口，并保留迁移记录 |
| `retired` | 入口已失效 | 不使用 |
| `duplicate` | 与其它入口重复 | 合并到主入口 |
| `needs_review` | 入口待维护 | 可提示，不得称最新 |

### 11.3 来源优先级

| 优先级 | 含义 | 注意 |
|---|---|---|
| `P0` | 主管部门、官方税则、官方法规库、原始产品文件等第一优先入口 | 仍须打开并抽取 Observation |
| `P1` | 官方二级入口、机构指南、裁定/公告库、承运人规则等 | 仍须核对适用范围 |
| `P2` | 行业协会、认证机构、报关行/货代公开解释、交易所/指数入口 | 只能辅助或参考，按事实域降级 |
| `P3` | 平台、媒体、报告摘要、经销商页面、社媒线索 | 多数只能做市场/价格参考或搜索线索 |

优先级表示“先去哪里找”，不表示“已经核实”。

## 12. 路由规则：从 Brief 到 Source Pack

| Brief / 产品条件 | 应触发的 Pack | 必须保留的边界 |
|---|---|---|
| 有目标国家/地区 | 目的国准入 Pack、目的国税费 Pack、目的国原产地证明 Pack、市场信号 Pack | 目标国家不等于出口申报国或原产国 |
| 有出口申报国 | 出口国 Pack | 默认中国也必须可见可改；不能由原产国自动推导 |
| 有实际起运国/港/机场/口岸 | 物流 Pack | 起运节点未知时只能查候选节点 |
| 有运输方式偏好或货物属性触发 | 物流 Pack、Common Rule Pack | 运输候选不等于承运可行 |
| 有锂电、危险品、液体、粉末、磁性 | Common Rule Pack + 目的国/出口国/物流相关入口 | 缺 SDS/UN38.3/包装不得判断可出运 |
| 有纺织、皮肤接触、儿童、食品接触 | 目的国准入 Pack + 目的国原产地证明 Pack + 产品原始来源 Pack | 网页成分/洗护不等于实物标签合规；origin marking 不等于 COO |
| 有农产品、食品、花卉、茶叶、植物/动物材料 | 目的国准入 Pack + 目的国原产地证明 Pack + 出口国 Pack + 物流/冷链 Pack | 未见检疫/卫生/处理文件不得写可进口；COO/植检/卫生证要求需分开查 |
| 有大宗、散杂、RoRo、超限、矿产、钢材、粮食 | 物流 Pack + 市场信号 Pack + 目的国原产地证明 Pack + 出口国 Pack | 指数/期货不等于现货出口价或合同价；配额/贸易救济/原产地证明需官方核验 |
| 用户只给产品名，无国家/贸易前提 | 只能形成资料清单和待确认 Brief | 不生成市场/税费/物流结论 |


### 12.1 `origin_proof_requirement` 查询组触发

当 Brief 或用户材料出现以下任一情况时，应生成 `origin_proof_requirement` 查询组。该查询组仍只能生成 Query Plan / 待打开来源，不能直接生成事实结论。

| 触发条件 | 需要激活的入口 | 边界 |
|---|---|---|
| 用户问是否需要 COO / 原产地证书 | 目的国原产地证明 Pack + 目的国税费 Pack | 先查目标国规则，再展示用户材料状态 |
| 目标国、原产国、候选 HS 已知或部分已知 | rules of origin / proof of origin 官方入口 | 条件不足时写 `unable_to_verify` 或待确认 |
| 用户希望计算关税、优惠税率、FTA/GSP | 优惠原产地 / 协定文本 / 官方指南入口 | 申请优惠需要 proof 不等于普通进口都需要 COO |
| 产品可能触发贸易救济、配额、制裁或敏感品类监管 | 贸易救济/配额/制裁官方入口 | 未核验前不得写适用/不适用 |
| 用户上传 COO、发票、提单、装箱单 | 产品原始来源 Pack + 用户文件观察要求 | 用户文件只支持材料状态，不替代目标国规则 |
| 目的国要求 Made in / origin marking | 标签/marking 官方入口 + origin proof 入口 | marking 与 COO 文件必须分开 |

## 13. Pack 与 EvidenceCard 的硬边界

| 规则 | 正确做法 | 禁止做法 |
|---|---|---|
| Pack 不能直接成证据 | MatrixRow 引用 EvidenceCard，EvidenceCard 引用 Source/Observation | MatrixRow 引用 SourcePack 作为事实来源 |
| Entry 不能直接成证据 | 打开 Entry 后形成 Source/Observation，再抽取 EvidenceCard | SourceEntry 直接支持“税率为 X” |
| QueryTemplate 不能直接成证据 | QueryTemplate 进入 SearchLog / Query Plan | 查询模板总结变事实 |
| Pack 日期不是事实日期 | Pack 维护日期只说明入口是否需要维护 | 把 `last_reviewed_at` 写成法规/税率/价格日期 |
| Pack 优先级不是可信度结论 | P0 优先打开，打开后仍核对适用范围 | P0 直接变“已核实” |
| Pack 缺失不补猜 | 降级为人工采集计划或来源缺口 | 用模型记忆补国家来源或事实 |

未来 validator / audit 应强制：用户可见事实行的 `source_refs` 不得只包含 `source_pack_id`、`source_entry_id` 或 `query_template_id`。

## 14. 用户可见的 Pack 覆盖说明

Source Pack 不应占据用户报告正文事实区，但可以在“信息来源与待确认事项”中用人话展示覆盖情况。

| 展示项 | 示例表达方式 | 不得表达 |
|---|---|---|
| 本次使用的来源目录 | 本次按“目的国税费、目的国准入、出口国、物流、市场信号”五类来源目录组织采集 | 本 Pack 已证明该产品税率/认证 |
| 覆盖状态 | 美国进口税费入口已纳入采集计划；实际税率仍需打开官方税则和确认归类 | 美国税费已确认 |
| 缺失 Pack | 未配置目标国物流来源目录，本轮只能列人工查询计划 | 物流无风险 |
| 入口受限 | 某来源入口需要登录或付费，本轮只记录来源受限 | 已读取付费报告结论 |
| 复核状态 | 来源目录最后维护日期为 X，本次事实仍按实际打开日期为准 | 最新法规为 X |

## 15. 与两个首批样本的关系

### 15.1 Xing Heng `48V20Ah` LiFePO4 电池包

| 触发条件 | Source Pack 路由 | 保留边界 |
|---|---|---|
| 目标国为美国 | 美国目的国准入、税费、原产地证明、市场信号 Pack | 不能直接得出最终税率、COO 要求结论或可进口结论 |
| 产品为锂电池包 | Common Rule Pack 中锂电/危险品/运输入口 | 缺 UN38.3/SDS/包装时不得判断可出运 |
| 越南制造线索 | 若出口申报国未确认，不自动触发越南出口国 Pack 为确定事实 | 不把制造地当出口申报国 |
| 起运港未知 | 物流 Pack 只能形成候选路线入口 | 不默认海防港、空运口岸或最佳方式 |

### 15.2 UNIQLO Men's Corduroy Overshirt `470177`

| 触发条件 | Source Pack 路由 | 保留边界 |
|---|---|---|
| 目标国为美国 | 美国纺织标签/准入、税费、原产地证明、市场信号 Pack | 候选 HTSUS 不能变最终归类；marking 不能变 COO 文件要求 |
| Production: China | 若出口申报国确认为中国，则触发中国出口国 Pack | Production 不等于起运港或出口申报国 |
| 棉制灯芯绒成衣线索 | 产品原始来源 Pack + 目的国标签入口 | 网页 Body/Trim 不等于全成分或实物标签合规 |
| 起运港未知 | 物流 Pack 只能列候选路线来源 | 不默认上海、宁波、深圳等港口 |

## 16. Source Pack 最小通过条件

| Pack 类型 | 最小通过条件 |
|---|---|
| 目的国准入 Pack | 至少有一个 P0/P1 官方或主管来源入口；有适用产品触发标签；有不支持字段说明 |
| 目的国税费 Pack | 至少有官方税则入口和贸易救济/裁定类入口；明确候选归类不等于最终税率 |
| 目的国原产地证明 Pack | 至少有海关/官方进口指南/rules of origin/协定文本入口；明确目标国要求与用户材料状态分离 |
| 出口国 Pack | 至少有海关/商务/贸易/检验检疫/出口管制入口中的核心入口；明确出口申报国与原产国分离 |
| 物流 Pack | 至少区分港口/机场/口岸/承运/预申报入口；明确时效非承诺 |
| 市场信号 Pack | 至少区分 Google Trends、统计/协会/报告、平台/价格/指数入口；明确趋势和价格口径 |
| Common Rule Pack | 至少有触发标签、适用运输/产品范围和目的国/出口国复核要求；不能宣称全球通用结论 |
| Product Original Source Pack | 至少记录用户 URL/文件/产品页入口、型号/版本匹配要求和不能自动支持字段 |

## 17. 禁止字段

未来任何 Source Pack 或 SourceEntry 中不应出现这些事实型字段：

| 禁止字段/内容 | 原因 | 应放在哪里 |
|---|---|---|
| `final_duty_rate`、`latest_tariff_rate` | 税率必须来自本次打开的官方来源和归类条件 | EvidenceCard / MatrixRow |
| `certification_required: true/false` | 是否适用要按产品属性和法规条件判断 | EvidenceCard / Gap |
| `origin_proof_required: true/false`、`coo_required: true/false` | COO / proof of origin 要按本次目标国官方来源、HS、原产地和触发条件判断 | EvidenceCard / MatrixRow |
| `is_compliant`、`can_import`、`can_export` | 属于结论，不是来源入口 | MatrixRow，经证据与专业确认边界后展示 |
| `best_route`、`guaranteed_transit_days` | 物流入口不能承诺路线或时效 | 物流 MatrixRow 的常见区间与条件 |
| `target_price`、`recommended_price` | 产品市场分析不做价格建议 | 价格参考 MatrixRow，只列公开观察值 |
| `trend_is_growing`、`market_potential` | Google Trends/报告需本次观察和口径 | 趋势 MatrixRow，并注明相对搜索兴趣 |
| `recommended_customer_type` | 该模块不做客户开发 | 批量客户开发路线另行处理 |
| 本地路径、token、cookie、内部 hash | 用户交付安全边界 | 内部运行记录也应脱敏 |

## 18. eval / audit 规则草案

| 错误码 | 触发条件 |
|---|---|
| `market_pack_used_as_evidence` | MatrixRow 或 EvidenceCard 直接引用 SourcePack 作为事实来源 |
| `market_pack_entry_used_as_fact` | SourceEntry 未打开就支持事实值 |
| `market_pack_fact_leak` | SourcePack / SourceEntry 存储税率、认证结论、物流承诺、趋势结论等事实 |
| `market_pack_missing_boundary_note` | Pack 未声明“不是事实库”边界 |
| `market_pack_scope_mismatch` | 目的国 Pack 被用于出口国要求，或出口国 Pack 被用于目的国准入 |
| `market_pack_origin_export_confusion` | 原产国被自动当成出口申报国触发确定结论 |
| `market_pack_stale_without_recheck` | Pack / Entry 标为需复核但仍被用于称“最新” |
| `market_pack_query_snippet_claim` | QueryTemplate 或搜索摘要被写成已核实事实 |
| `market_origin_proof_user_material_conflated` | 用户没给 COO 被写成目标国不需要，或目标国规则被写成用户材料缺口 |
| `market_origin_marking_conflated_with_coo` | Made in / origin marking 被写成 COO 文件要求 |
| `market_origin_preferential_overgeneralized` | 优惠税率 proof of origin 被泛化为所有普通进口都需要 |
| `market_user_coo_promoted_to_official_ruling` | 用户 COO 被写成海关最终原产地裁定 |
| `market_origin_requirement_without_authority` | 没有官方/权威来源却写确定性需要/不需要 COO |
| `market_pack_no_official_entry` | 准入/税费/出口管制 Pack 没有官方或主管来源入口却标 active |
| `market_pack_internal_leak` | 用户可见输出泄露本地路径、token、内部 ID 或 hash |

## 19. Slice 9 完成标准

| 编号 | 完成标准 |
|---|---|
| C-01 | 已明确 Source Pack 是来源入口目录，不是事实库 |
| C-02 | 已冻结 SourcePack、SourceEntry、QueryTemplate、ObservationRequirement、PackRouteRule 的字段合同 |
| C-03 | 已定义 Pack 类型、状态、来源优先级和产品触发标签 |
| C-04 | 已明确 Brief / 产品属性如何路由到 Pack |
| C-05 | 已明确 Pack 与 EvidenceCard / MatrixRow 的硬边界 |
| C-06 | 已覆盖 Xing Heng / UNIQLO 两个样本的 Pack 路由边界 |
| C-06a | 已覆盖 `origin_proof_requirement` 查询组和目标国 COO / proof of origin Pack 边界 |
| C-07 | 已提出 future eval / audit 错误码，防止 Source Pack 被当事实库 |
