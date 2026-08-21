# 产品出海市场分析：Source Pack 种子样例设计（Slice 10）

本文件设计 `产品出海市场分析` 第一批 Source Pack 种子样例。它不是代码，不联网，不创建真实国家来源库，不填最新法规、税率、价格、物流事实，也不把任何入口当成结论。

一句话目标：**用美国 / 中国 / 越南 + Xing Heng / UNIQLO 两个样本，把 Source Pack 未来应该怎么“长出来”讲清楚；每个样例只放来源入口类型、查询槽位、观察要求和边界，不放事实结论。**

## 1. Slice 10 边界

| 项目 | 本轮决定 |
|---|---|
| 目标 | 设计第一批 Source Pack 种子样例的覆盖范围、样例行、路由方式、缺口和验收断言 |
| 当前仍不做 | 不写代码、不联网、不内置真实 URL、不填具体税率/法规/价格/物流时效、不创建可运行 registry |
| 样例覆盖 | 美国目的国准入、美国税费、中国出口、越南出口、物流、市场信号、锂电通用规则、纺织通用规则、产品原始来源 |
| 关键边界 | 样例只说明“应该查什么入口、打开后抽什么、不能推出什么”；不能写成事实库 |

## 2. 为什么首批只做美国 / 中国 / 越南

| 国家/地区 | 在两个样本里的角色 | 为什么适合作为种子样例 |
|---|---|---|
| 美国 | 两个样本的目的国 | 同时触发目的国准入、标签、进口税费、贸易救济、市场信号、预申报等高频事实域 |
| 中国 | UNIQLO 样本的 Production 线索；可作为默认出口申报国样例 | 验证“默认中国可改”“Production 不等于出口申报国”“出口国 Pack 与目的国 Pack 分开” |
| 越南 | Xing Heng 样本的制造/装配来源线索；可能但未确认的出口申报国 | 验证“原产/制造线索不自动触发出口国结论”“起运港不得默认” |

这不是长期国家范围。未来所有国家/地区都按同一字段合同扩展，而不是为每个国家写一套特殊逻辑。

## 3. 首批种子 Pack 清单

| seed_pack_id | Pack 类型 | 辖区/范围 | 主要服务事实域 | 触发来源 | 不包含什么 |
|---|---|---|---|---|---|
| `seed_us_market_access_general` | `destination_market_access_pack` | 美国 | 产品准入、标签、包装、消费者安全、食品/农产品/危险品入口 | 目标国为美国 + 产品属性标签 | 不含“已合规/无需认证”结论 |
| `seed_us_duty_tax_general` | `destination_duty_tax_pack` | 美国 | HTSUS、海关裁定、贸易救济、其它进口税费入口 | 目标国为美国 + HS 候选/原产国状态 | 不含最终税率 |
| `seed_cn_export_general` | `export_country_pack` | 中国 | 海关、商务/贸易、出口管制、商检/检验检疫入口 | 出口申报国为中国 | 不含出口许可结论 |
| `seed_vn_export_general` | `export_country_pack` | 越南 | 出口申报、贸易主管、检验/质量、危险品/农产品出口入口 | 出口申报国确认为越南 | 不因越南制造线索自动触发确定结论 |
| `seed_transpacific_logistics_general` | `logistics_pack` | 中国/越南到美国常见跨太平洋贸易场景 | FCL、LCL、空运、快递、港口/机场、预申报入口 | 起运国/目的国/运输方式/货物属性 | 不含承诺时效或最佳路线 |
| `seed_market_signal_global_to_us` | `market_signal_pack` | 美国市场信号 | Google Trends、统计、协会、公开报告、平台价格、指数/期货入口 | 目标国为美国 + 产品名/行业名 | 不含销量、GMV、推荐价或市场进入建议 |
| `seed_lithium_battery_common_rules` | `common_rule_pack` | 国际/跨境锂电相关入口 | 锂电危险品、UN 情形、SDS、UN38.3、包装、承运限制入口 | `lithium_battery`、`battery_standalone`、`battery_installed` | 不含可出运结论 |
| `seed_textile_apparel_common_rules` | `common_rule_pack` | 纺织/服装跨境规则入口 | 纤维成分、洗护、原产地标识、标签、纺织归类提示入口 | `textile`、`apparel`、`skin_contact` | 不含实物标签合规或最终归类 |
| `seed_product_original_sources` | `product_original_source_pack` | 用户/产品特定 | 产品页、手册、TDS、SDS、证书、BOM、标签照片入口 | 用户 URL/文件/品牌/型号 | 不自动证明原产地、HS、认证或可运输性 |

## 4. Pack 样例字段矩阵

### 4.1 `seed_us_market_access_general`

| 字段 | 样例值 |
|---|---|
| `display_name` | 美国目的国准入来源入口样例 |
| `pack_type` | `destination_market_access_pack` |
| `trade_role` | `destination_market` |
| `jurisdiction_type` | `country` |
| `jurisdiction_name` | 美国 |
| `language_codes` | 英文为主；必要时保留产品原始语言 |
| `fact_domains_supported` | 目的国准入、标签、包装、消费者安全、食品/农产品/危险品入口 |
| `product_trigger_tags` | `general_goods`、`lithium_battery`、`apparel`、`textile`、`food_contact`、`child_product`、`dangerous_goods`、`fresh_produce` 等开放标签 |
| `required_brief_fields` | 目标国、产品版本、产品属性触发项；涉及食品/农产品/危险品时需原产国和技术文件状态 |
| `review_cycle_policy` | `per_run` 用于交付前复核；Pack 本身可周期维护 |
| `pack_boundary_note` | 仅为美国准入来源入口目录，不含具体产品是否合规结论 |
| `blocked_outputs` | 已合规、无需认证、可进口、标签已合规 |

### 4.2 `seed_us_duty_tax_general`

| 字段 | 样例值 |
|---|---|
| `display_name` | 美国进口税费来源入口样例 |
| `pack_type` | `destination_duty_tax_pack` |
| `trade_role` | `import_customs` |
| `jurisdiction_type` | `country` |
| `jurisdiction_name` | 美国 |
| `fact_domains_supported` | 候选 HTSUS、官方税则入口、裁定入口、贸易救济/附加税入口、税基说明入口 |
| `required_brief_fields` | 目标国、原产国状态、产品属性、候选 HS/HTS 或归类缺口 |
| `product_trigger_tags` | `general_goods`、`lithium_battery`、`textile`、`apparel`、`steel`、`food`、`chemical`、`dual_use` 等 |
| `review_cycle_policy` | `per_run`；交付日或交付前短周期复核 |
| `pack_boundary_note` | 仅为美国税费来源入口目录；最终归类和税率必须由本次打开来源 + 实物条件 + 专业确认边界决定 |
| `blocked_outputs` | 最终税率、最终归类、自动适用优惠/附加税结论 |

### 4.3 `seed_cn_export_general`

| 字段 | 样例值 |
|---|---|
| `display_name` | 中国出口国监管来源入口样例 |
| `pack_type` | `export_country_pack` |
| `trade_role` | `export_declaration` |
| `jurisdiction_type` | `country` |
| `jurisdiction_name` | 中国 |
| `fact_domains_supported` | 出口申报、出口管制、两用物项、商检/检验检疫、农产品/食品/危险品出口入口 |
| `required_brief_fields` | 出口申报国=中国、产品版本、产品属性触发项、目的国、原产国状态 |
| `product_trigger_tags` | `general_goods`、`textile`、`lithium_battery`、`dangerous_goods`、`chemical`、`fresh_produce`、`dual_use`、`wood_packaging` 等 |
| `review_cycle_policy` | `per_run` 用于出口管制/商检；普通入口可周期维护 |
| `pack_boundary_note` | 默认中国可见可改；该 Pack 只在出口申报国确认为中国时用于采集，不因卖方中文或中国品牌自动适用 |
| `blocked_outputs` | 无出口限制、无需商检、无需许可证、一定可出口 |

### 4.4 `seed_vn_export_general`

| 字段 | 样例值 |
|---|---|
| `display_name` | 越南出口国监管来源入口样例 |
| `pack_type` | `export_country_pack` |
| `trade_role` | `export_declaration` |
| `jurisdiction_type` | `country` |
| `jurisdiction_name` | 越南 |
| `fact_domains_supported` | 出口申报、贸易主管入口、质量/检验入口、危险品/农产品相关入口 |
| `required_brief_fields` | 出口申报国=越南；如果只有越南制造/装配线索，则先向用户确认出口申报国 |
| `product_trigger_tags` | `general_goods`、`lithium_battery`、`dangerous_goods`、`food`、`fresh_produce`、`chemical`、`bulk_cargo` 等 |
| `review_cycle_policy` | `per_run` 用于具体出口监管和危险品/检疫场景 |
| `pack_boundary_note` | 越南制造/工厂地址/证书线索不等于越南出口申报国；必须由 Brief 或贸易文件确认 |
| `blocked_outputs` | 越南可出口、无需出口许可、默认海防港、默认出口申报国 |

### 4.5 `seed_transpacific_logistics_general`

| 字段 | 样例值 |
|---|---|
| `display_name` | 中国/越南到美国跨太平洋物流来源入口样例 |
| `pack_type` | `logistics_pack` |
| `trade_role` | `departure_logistics` / `transit` |
| `jurisdiction_type` | `region` + `port_or_airport` 可扩展 |
| `jurisdiction_name` | 中国/越南至美国常见贸易路径样例范围 |
| `fact_domains_supported` | FCL、LCL、空运、国际快递、港口/机场/口岸、危险品订舱、预申报、散杂/RoRo/冷链入口 |
| `required_brief_fields` | 起运国/起运节点状态、目的国/目的节点状态、产品尺寸重量、货物属性、运输方式偏好 |
| `product_trigger_tags` | `general_goods`、`lithium_battery`、`dangerous_goods`、`cold_chain`、`breakbulk`、`roro`、`oversize`、`magnetic`、`fresh_produce` 等 |
| `review_cycle_policy` | `per_run`；物流时效、拥堵、危险品接受条件需要短周期复核 |
| `pack_boundary_note` | 只提供物流来源入口；常见区间必须来自打开来源和条件，不能承诺交期 |
| `blocked_outputs` | 最佳路线、保证时效、固定起运港、普通货运输结论、承运人一定接受 |

### 4.6 `seed_market_signal_global_to_us`

| 字段 | 样例值 |
|---|---|
| `display_name` | 美国市场信号来源入口样例 |
| `pack_type` | `market_signal_pack` |
| `trade_role` | `market_signal` |
| `jurisdiction_type` | `country` |
| `jurisdiction_name` | 美国 |
| `fact_domains_supported` | Google Trends、公开统计、行业协会、公开报告、平台/电商/B2B 价格、期货/指数入口 |
| `required_brief_fields` | 目标国、产品名称、行业通用名、当地语言/英文关键词、规格/材质/用途 |
| `product_trigger_tags` | `general_goods`、`apparel`、`lithium_battery`、`commodity_index_reference`、`steel`、`grain`、`mineral`、`giftable` 等 |
| `review_cycle_policy` | `per_run`；价格、趋势和新闻必须带观察日期 |
| `pack_boundary_note` | 市场信号只作客观参考；Google Trends 是相对搜索兴趣，平台价是挂牌参考，不等于销量或成交价 |
| `blocked_outputs` | 市场潜力高、建议进入、推荐价格、目标客户类型、真实销量增长 |

### 4.7 `seed_lithium_battery_common_rules`

| 字段 | 样例值 |
|---|---|
| `display_name` | 锂电产品通用规则来源入口样例 |
| `pack_type` | `common_rule_pack` |
| `trade_role` | `common_rule` |
| `jurisdiction_type` | `global_or_international` |
| `jurisdiction_name` | 锂电跨境运输和危险品规则入口样例 |
| `fact_domains_supported` | UN 编号情形、SDS、UN38.3、包装、危险品分类、承运限制、空运/海运/快递限制入口 |
| `required_brief_fields` | 电池类型、Wh、单独运输/随设备/装入设备、包装状态、SDS/UN38.3 状态、起运/目的国 |
| `product_trigger_tags` | `lithium_battery`、`battery_standalone`、`battery_installed`、`dangerous_goods`、`electrical` |
| `review_cycle_policy` | `per_run`；危险品和承运要求必须按具体运输情形复核 |
| `pack_boundary_note` | 通用锂电入口不能替代目的国/出口国/承运人规则；缺 SDS/UN38.3/包装时只能列待确认 |
| `blocked_outputs` | 可出运、普通货、无需 SDS、已有 UN38.3、承运人接受 |

### 4.8 `seed_textile_apparel_common_rules`

| 字段 | 样例值 |
|---|---|
| `display_name` | 纺织服装通用规则来源入口样例 |
| `pack_type` | `common_rule_pack` |
| `trade_role` | `common_rule` |
| `jurisdiction_type` | `global_or_international` |
| `jurisdiction_name` | 纺织服装归类、标签和成分核验入口样例 |
| `fact_domains_supported` | 纤维成分、织造方式、成衣/面料区分、洗护、原产地标签、尺码/辅料、HTS/HS 归类提示入口 |
| `required_brief_fields` | 产品形态、性别/用途、纤维成分、针织/机织、BOM/实物标签状态、原产国状态、目标国 |
| `product_trigger_tags` | `textile`、`apparel`、`skin_contact`、`cotton`、`woven`、`knit`、`workwear` 等开放标签 |
| `review_cycle_policy` | `per_run`；标签和归类必须按目标国和实物状态复核 |
| `pack_boundary_note` | 网页成分/洗护不等于实物标签已合规；候选 HTS/HS 不等于最终归类 |
| `blocked_outputs` | 实物标签合规、全成分无动物材料、最终归类、无标签风险 |

### 4.9 `seed_product_original_sources`

| 字段 | 样例值 |
|---|---|
| `display_name` | 产品原始资料来源入口样例 |
| `pack_type` | `product_original_source_pack` |
| `trade_role` | `product_source` |
| `jurisdiction_type` | `product_specific` |
| `jurisdiction_name` | 用户给定产品、品牌、制造商、PDF、TDS、SDS、BOM、标签照片 |
| `fact_domains_supported` | 产品身份、型号、规格、材质、成分、证书/测试报告、SDS/UN38.3/BOM/标签照片状态 |
| `required_brief_fields` | 产品名称、型号/SKU/Design No./Product ID、用户文件或公开 URL；没有时仅能列资料清单 |
| `product_trigger_tags` | 全部产品标签均可触发 |
| `review_cycle_policy` | `per_run`；产品版本或文件版本变更必须重跑 Brief |
| `pack_boundary_note` | 产品原始资料能支持产品字段，但不能自动证明海关原产地、最终 HS、目的国合规或运输可行性 |
| `blocked_outputs` | 自动原产地裁定、最终归类、已合规、可运输 |

## 5. 种子 SourceEntry 类型样例

本节只设计入口类型，不填具体 URL，不声称入口当前可用。

| entry_type_id | 所属 Pack | 来源所有者类型 | 权威等级 | 预期内容 | 打开后必须抽取 | 不支持什么 |
|---|---|---|---|---|---|---|
| `entry_us_regulator_product_safety` | 美国准入 | government / standards_body | `primary_official` / `secondary_official` | 产品安全、消费者保护、标签/警示入口 | 产品类别、适用范围、发布日期/观察日期、法规/指南定位 | 不支持产品已合规 |
| `entry_us_textile_labeling` | 美国准入 / 纺织通用 | government | `primary_official` | 纺织成分、护理、原产地或相关标签入口 | 适用产品类别、标签要素、日期、章节定位 | 不支持网页标签已等同实物标签合规 |
| `entry_us_hazardous_material_transport` | 美国准入 / 锂电通用 / 物流 | government / carrier | `primary_official` / `commercial_reference` | 危险品、锂电运输、包装、申报入口 | UN 情形、文件要求、运输方式、限制日期 | 不支持承运人一定接受 |
| `entry_us_hts_tariff` | 美国税费 | customs / government | `primary_official` | 官方税则查询入口 | HTS 层级、税率项、日期、税基、注释、Chapter 99 线索 | 不支持最终归类 |
| `entry_us_customs_rulings` | 美国税费 | customs / government | `primary_official` | 海关裁定入口 | 产品描述、裁定号、日期、适用条件 | 不支持不同产品直接套用 |
| `entry_cn_customs_export` | 中国出口 | customs / government | `primary_official` | 出口申报、监管条件、检验检疫入口 | HS/监管条件、日期、产品范围 | 不支持无出口限制结论 |
| `entry_cn_export_control` | 中国出口 | government | `primary_official` | 出口管制、两用物项、许可入口 | 清单、产品条件、发布日期/生效日期 | 不支持产品不受管制结论 |
| `entry_vn_customs_export` | 越南出口 | customs / government | `primary_official` | 越南出口申报、海关入口 | 适用产品、出口条件、日期、定位 | 不支持默认越南出口申报国 |
| `entry_port_carrier_schedule_guidance` | 物流 | port_authority / carrier / commercial_reference | `primary_official` / `commercial_reference` | 港口、船司、航司、快递、货代公开说明 | 起运/目的节点、运输方式、条件、观察日期 | 不支持承诺交期或最佳路线 |
| `entry_pre_filing_customs` | 物流 | customs / government / carrier | `primary_official` | 目的国/承运预申报节点 | 申报时间点、适用运输方式、责任方、日期 | 不支持替代船司截单/仓库截货 |
| `entry_google_trends` | 市场信号 | platform | `commercial_reference` | 相对搜索兴趣 | 关键词、地区、时间范围、导出/观察日期 | 不支持销量、GMV、采购需求 |
| `entry_market_platform_price` | 市场信号 | platform / commercial_reference | `commercial_reference` | 平台挂牌价、零售价、B2B/B2C 价格 | 规格、币种、税/运费条件、日期、卖家地区 | 不支持成交价或推荐价 |
| `entry_exchange_index` | 市场信号 | exchange / industry_reference | `industry_reference` | 期货、指数、公开报价入口 | 合约月、单位、交割地、币种、日期 | 不支持现货出口价或投资判断 |
| `entry_product_manual_tds` | 产品原始来源 | brand_or_manufacturer / user_file | `original_product_source` / `user_provided` | 产品页、手册、TDS、证书、SDS、UN38.3、BOM、标签照片 | 型号、版本、页码/章节、日期、适用范围 | 不支持自动最终合规或原产地裁定 |

## 6. QueryTemplate 种子样例

| template_id | 查询组 | 目的 | 必需输入 | 推荐语言 | 必须打开来源等级 | fallback |
|---|---|---|---|---|---|---|
| `qt_us_duty_by_candidate_hs` | 税费 | 查候选 HTSUS、官方税则和附加税入口 | 目标国美国、候选 HS/HTS、原产国状态、产品属性 | 英文 | `primary_official` | `candidate_only / classification_gap` |
| `qt_us_market_access_by_trigger` | 准入 | 按产品触发项查美国准入/标签/包装/安全入口 | 目标国美国、产品属性标签 | 英文 | `primary_official` 或 `secondary_official` | `not_executed / source_limited` |
| `qt_export_country_requirements` | 出口 | 查出口申报国监管、管制、商检/检疫入口 | 出口申报国、产品属性、目的国 | 出口国语言 + 英文/中文 | `primary_official` | `export_country_unconfirmed / source_limited` |
| `qt_logistics_route_nodes` | 物流 | 查常见路线、港口/机场/口岸、预申报节点 | 起运国/节点状态、目的国/节点状态、货物属性 | 英文 + 起运国语言 | `primary_official` / carrier / port | `route_candidate_only` |
| `qt_market_signal_terms` | 市场信号 | 查 Google Trends、公开统计/报告、平台价格、指数 | 目标国、产品关键词、规格、行业名 | 英文 + 当地语言 | Google Trends / platform / industry_reference | `not_executed / data_insufficient` |
| `qt_product_original_docs` | 产品资料 | 查产品页、手册、TDS、SDS、UN38.3、BOM、标签照片 | 型号、SKU、制造商/品牌、用户 URL/文件 | 原始来源语言 | `original_product_source` / `user_provided` | `technical_docs_required` |

所有 QueryTemplate 默认 `reject_if_only_snippet = true`。搜索结果摘要只能进入 SearchLog 或候选来源，不得生成 EvidenceCard。

## 7. PackRouteRule 种子样例

| route_rule_id | 触发条件 | 激活 Pack | 需要用户确认 | 边界 |
|---|---|---|---|---|
| `route_target_us` | `target_country_or_region = United States` | 美国准入、美国税费、美国市场信号 | 否 | 目标国美国不等于原产国/出口国/起运港已确认 |
| `route_export_cn` | `export_declaration_country = China` | 中国出口 Pack | 否 | 默认中国必须对用户可见可改 |
| `route_origin_cn_without_export` | 只有 `Production: China` / Made in China，出口申报国未知 | 产品原始来源 Pack；中国出口 Pack 仅作为待确认候选 | 是 | 不能自动按中国出口规则输出结论 |
| `route_origin_vn_without_export` | 只有越南制造/装配线索，出口申报国未知 | 产品原始来源 Pack；越南出口 Pack 仅作为待确认候选 | 是 | 不默认越南出口申报国或海防港 |
| `route_lithium_battery` | 产品标签含 `lithium_battery` | 锂电通用规则、物流、目的国准入、出口国 Pack | 视 SDS/UN38.3/包装状态而定 | 缺关键文件不得判断可出运 |
| `route_textile_apparel` | 产品标签含 `textile` 或 `apparel` | 纺织通用规则、目的国准入、税费、产品原始来源 | 视实物标签/BOM 状态而定 | 网页成分不等于实物标签合规 |
| `route_bulk_or_roro` | 产品标签含 `bulk_cargo`、`breakbulk`、`roro`、`heavy_lift` | 物流、市场信号、出口国 Pack | 需要货量、件重件尺、装卸条件 | 不承诺船型、舱位、港口可操作 |
| `route_agri_food_fresh` | 产品标签含 `food`、`fresh_produce`、`flower`、`tea`、`plant_material` | 目的国准入、出口国、物流/冷链、产品原始来源 | 需要品种、处理方式、检疫/卫生文件状态 | 不写可进口或无检疫要求 |

## 8. ObservationRequirement 种子样例

| requirement_id | 适用入口 | 最低观察要求 | 阻断条件 |
|---|---|---|---|
| `obs_official_regulation` | 官方法规/指南入口 | 来源名称、URL、页面标题/章节、发布日期或观察日期、适用产品类别、可见内容、限制 | 只有搜索摘要；页面无法打开；适用产品类别不匹配 |
| `obs_tariff_lookup` | 官方税则/裁定入口 | 查询参数、HS/HTS 层级、描述、税率项、注释/附加税线索、日期、原产国条件 | 候选税号过粗；无原产国；无法确认 10 位统计后缀 |
| `obs_product_doc` | 产品页/PDF/TDS/SDS/BOM/标签 | 型号/版本、页码/章节、文件名/URL、观察日期、字段值、适用范围 | 型号不一致；文件标题不匹配；只有外部模型总结 |
| `obs_google_trends` | Google Trends | 关键词、地区、时间范围、导出/观察日期、相对搜索兴趣口径 | 没有截图/导出/可复核页面；把趋势写成销量 |
| `obs_platform_price` | 平台/零售/B2B 价格 | 规格、币种、税运费条件、卖家/地区、观察日期、是否可比 | 无规格、无币种、无日期；把挂牌价写成成交价 |
| `obs_logistics_node` | 港口/承运/货代/预申报入口 | 起运/目的节点、运输方式、货物条件、时间口径、观察日期、限制 | 无货物条件；把常见区间写成承诺交期 |
| `obs_news_external_factor` | 新闻/公告/灾害/制裁入口 | 事件日期、发布来源、影响区域、影响链条、时间窗口 | 无日期；无权威来源；做政治/投资判断 |

## 9. 两个样本的种子路由演示

### 9.1 Xing Heng `48V20Ah` LiFePO4 电池包

| 已知/待确认输入 | 触发结果 | 输出边界 |
|---|---|---|
| 目标国：美国 | 激活美国准入、美国税费、美国市场信号 Pack | 只形成采集入口，不输出美国税率或认证结论 |
| 产品：48V20Ah LiFePO4 电池包，Wh 派生 960Wh | 激活锂电通用规则、物流危险品入口、产品原始来源入口 | 缺 UN38.3/SDS/包装不得写可出运 |
| 越南制造/装配来源线索 | 产品原始来源可记录制造线索；越南出口 Pack 需用户确认出口申报国 | 不把越南制造线索自动写成越南出口申报国 |
| 起运港未知 | 物流 Pack 只生成候选港口/机场/路线入口 | 不默认海防港，不写最佳运输方式 |
| 候选 HTSUS `8507.60.00` | 美国税费 Pack 生成官方税则/裁定查询计划 | 不写最终 10 位归类或最终税率 |

### 9.2 UNIQLO Men's Corduroy Overshirt `470177`

| 已知/待确认输入 | 触发结果 | 输出边界 |
|---|---|---|
| 目标国：美国 | 激活美国准入、美国税费、美国市场信号 Pack | 只形成采集入口，不输出最终标签/税费结论 |
| Production: China | 中国出口 Pack 只有在出口申报国确认为中国时进入执行 | 不把 Production 自动等同出口申报国或起运港 |
| Body/Trim 100% Cotton、8-wale corduroy | 激活纺织服装通用规则、产品原始来源入口、美国纺织标签入口 | 网页成分不等于全成分或实物标签合规 |
| 候选 HTSUS `6205.20.20` | 美国税费 Pack 生成官方税则/裁定查询计划 | 不写最终归类或最终税率 |
| 起运港未知 | 物流 Pack 只生成候选路线入口 | 不默认上海、宁波、深圳等港口 |

## 10. 种子样例用户可见说明模板

未来报告可以在“信息来源与待确认事项”中用这种人话说明 Source Pack 覆盖情况：

| 场景 | 用户可见说明 |
|---|---|
| Pack 已用于采集计划 | 本次按美国准入、美国税费、出口国监管、物流和市场信号五类来源目录组织采集；这些目录只说明去哪里查，事实仍以本次打开来源为准。 |
| Pack 缺失 | 当前没有该国家/该事实域的内置来源目录，本轮只能生成手工查询计划，不能输出已核实结论。 |
| Entry 受限 | 某些入口可能需要登录、付费或动态页面渲染，本轮只记录为来源受限，不读取不可见内容。 |
| Pack 过期 | 来源目录需要维护；本轮若用户要求“最新”，必须重新打开官方来源，不得沿用目录维护日期。 |
| 样本关键文件缺失 | 锂电缺 SDS/UN38.3/包装，纺织缺实物标签/BOM 时，对应合规、物流、税费结论保留待确认。 |

## 11. 不做成事实库的样例负向清单

这些内容即使将来很容易从常识或搜索摘要中猜到，也不得写进 Source Pack 种子样例：

| 禁止内容 | 原因 |
|---|---|
| 美国某 HTSUS 的具体税率 | 必须按本次官方税则打开结果、日期、原产国、最终归类判断 |
| 中国或越南某产品出口是否需要许可证 | 必须按出口申报国、HS、产品属性、主管来源和日期判断 |
| 中国/越南到美国的固定海运天数 | 必须按起运港、目的港、船司、货型、季节和观察日期判断 |
| 锂电一定属于某 UN 情形且可运输 | 必须看单独/随设备/装入设备、Wh、SDS、UN38.3、包装和承运条件 |
| UNIQLO 该产品实物标签已合规 | 必须看实物标签/BOM 和目的国标签规则 |
| Google Trends 长期增长 | 必须实际导出/观察关键词、地区、时间范围和日期 |
| 平台价格区间 | 必须打开具体平台页，记录规格、币种、税运费和日期 |
| 推荐客户类型或市场进入建议 | 超出产品出海市场分析边界 |

## 12. Slice 10 完成标准

| 编号 | 完成标准 |
|---|---|
| C-01 | 已给出首批种子 Pack 清单，覆盖美国、中国、越南、物流、市场信号、锂电、纺织和产品原始来源 |
| C-02 | 每个 Pack 样例只含入口、字段、触发、复核和边界，不含事实结论 |
| C-03 | 已给出 SourceEntry、QueryTemplate、PackRouteRule、ObservationRequirement 的种子样例 |
| C-04 | 已演示 Xing Heng / UNIQLO 两个样本如何路由到 Pack，同时保留证据边界 |
| C-05 | 已给出用户可见说明模板，符合外贸人能理解的说法 |
| C-06 | 已列出不得写进 Source Pack 的负向事实清单 |
