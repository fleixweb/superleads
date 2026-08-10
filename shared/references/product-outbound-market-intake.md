# Product Outbound Market Intake

Use this reference when routing or starting `产品出海市场分析`.

## Route boundary

Route to `analyzing-product-outbound-market` when the user's core request is:

`one product + target country/region + market/compliance/tax/export/logistics/external-factor analysis`

Typical user wording:

- 产品出海市场分析：某产品到某国。
- 分析某产品出口到某国的趋势、价格、认证、包装、标签、关税、物流。
- 某产品进入某国有什么准入门槛、COO、原产地证明、商检、出口管制或运输要求。
- 某产品在某国能不能做 / 好不好卖：translate into objective facts only.

Do not route here when the core request is:

- 找客户、找买家、开发进口商、客户名单 -> bulk customer development.
- 背调某公司/品牌/域名/邮箱/地址 -> customer background research.
- 补全已有客户表 -> existing table enrichment.

If the user asks for market analysis and customer discovery together, split the work:

1. product outbound market analysis first;
2. customer development only after separate user confirmation.

## First response, enough information

```text
我理解你要做的是：产品出海市场分析。
本轮对象：{产品/品类/候选 HS-HTS} → {目的国/地区}。
默认出口申报国/原产口径：{默认中国/用户指定国家或地区}；如果这个默认不对，告诉我替换即可。
整体分析默认覆盖趋势、公开价格参考、行业资料、准入合规、进口税费、出口要求、运输路线、季节窗口和近期外部因素，并整理成完整十二张表；认证会先查目标市场可能要求什么，再单独看你有没有对应材料；不输出是否值得进入，也不生成客户名单。
如果你只问其中一项，我会只做请求的模块和三张固定表，并在报告开头列明未覆盖范围；需要其它模块可以继续要求。
```

## Requested analysis scope

写 Brief 时使用已有字段 `analysis_modules_requested`：

- 整体市场分析、出口某国分析、进入某国市场分析 -> 完整报告（全部模块）。字段缺失、空数组、无法识别或用户意图不确定时，也按完整报告处理。
- 只问认证、测试、注册、标签、SDS、UN38.3、CE、UL、SABER -> `certification`。
- 只问关税、税率、HS/HTS、税费 -> `import_tax`。
- 只问 COO / 原产地证明 -> `certification`（包含 origin-proof 行）。
- 只问清关、物流、运输、预申报 -> `logistics`。
- 只问出口报关、商检、出口管制 -> `export_requirements`。
- 只问趋势、价格、好不好卖 -> `google_trends` + `online_price` + `market_reports`。

完整报告输出全部十二张表。单项报告只输出所选模块对应的表，加上固定的
`市场事实总览`、`产品档案与触发项`、`信息来源与待确认事项`，不把未请求模块
渲染成表或逐项写成“未执行”。单项报告开头使用以下范围声明模板：

```text
本轮范围：只做了「{请求模块}」一项。
未覆盖：{未请求模块列表}。
需要哪一项可以继续要求。
```

模块词与旧查询组兼容：`destination_compliance`、`origin_proof_requirement`、
`market_signal` 等旧词由导出层映射到准入、趋势/价格/市场资料等对应表，不要在
本轮重命名既有字段或查询组。

## First response, missing target country/region

```text
可以做，但还缺一个会改变结论的关键前提：目标国家/地区。
请给一个具体国家/地区；如果是欧盟，也建议先指定落地国家，因为税费、标签、EPR、清关和港口会按国家变化。
```

## First response, missing product version

```text
可以做。现在资料适合先做品类级 / 候选税号级市场分析。
我会先整理目标市场趋势、公开价格参考、准入合规、税费、出口要求、物流和外部因素；缺型号、材料、BOM、证书或起运港时会写成条件和待确认项，不会直接给最终归类、最终税率、已合规或可清关结论。
```

## Certification / compliance reminder

Use this when the user asks about certification but has not provided
certificates:

```text
可以。认证这块我会先按目标国家/地区和产品属性查“可能需要哪些认证、测试、注册、标签或文件”，不是等你先提供证书。你有现成证书可以发来，我会另外核对它是否覆盖本型号、目标市场和适用标准；如果没有，我会把需要向供应商/认证机构/报关行确认的材料列成清单。
```

## Product trigger reminder

Use this short reminder when product details are thin:

```text
为了避免把认证、税费和运输判断错，我会特别看这些触发项：是否带电/带电池、是否液体/粉末/磁性、是否化学品或危险品、是否接触食品/皮肤/儿童、是否农产品/冷链、是否大宗/散杂/滚装/超限、是否两用物项或受出口管制。你有资料就给；没有的我会写“待确认”，不会默认猜。
```

## Default assumptions

- Default export declaration country and first-pass origin/manufacturing scope can be China, but the user may set any country/region; this is a visible analysis premise, not a customs origin ruling.
- If a field is only `Made in` / production / manufacturing / COO wording, keep it as a manufacturing clue. Do not use it to clear the customs-origin gap, choose an export country, or assert COO / proof-of-origin readiness.
- Product name, category, use description, product URL/PDF, image clue, or HS/HTS code can start first-pass category-level analysis. A missing model/version lowers precision; it does not force the assistant to stop at a pending-material checklist.
- First-pass blocking questions are only product identity and target country/region. Do not ask for IOR/importer of record, Incoterms/trade term, transaction value/quantity, expected entry date, customs broker, BOM, product photos, actual departure port, original certificates, test reports, SDS, or UN38.3 unless the user explicitly asks for final duty, formal customs filing, clearance readiness, or actual shipment arrangement.
- Category-level analysis changes the object granularity only. It never lowers the evidence standard: do not turn candidate HS/HTS, missing certificates, missing BOM, or missing departure port into final classification, final duty, no-certification, general-cargo, clearance-ready, or transportability conclusions.
- Origin country, departure node, final HS/HTS, COO/proof-of-origin applicability, certification requirement applicability, user certification-material status, packaging, logistics time, and customs pre-filing nodes remain conditional unless supported by opened sources or user documents.
- Certification analysis starts with destination-market requirements. User certificates, test reports, SDS, UN38.3, labels, BOM, registrations, or declarations are optional materials for scope matching, not prerequisites for analyzing what the target market may require.
- Online B2B/B2C channels and platform prices are market references only; they do not define traditional B2B customer scope.
