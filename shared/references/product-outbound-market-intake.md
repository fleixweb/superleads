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
本轮对象：{产品版本} → {目的国/地区}。
默认出口申报国：{默认/用户指定出口国}；原产国/起运地如果资料不足，会保留待确认。
我会按趋势、公开价格参考、准入合规、进口税费、出口要求、运输路线和近期外部因素整理成表格；不输出是否值得进入，也不生成客户名单。
```

## First response, missing target country/region

```text
可以做，但还缺一个会改变结论的关键前提：目标国家/地区。
请给一个具体国家/地区；如果是欧盟，也建议先指定落地国家，因为税费、标签、EPR、清关和港口会按国家变化。
```

## First response, missing product version

```text
可以做，但现在产品还不够具体。
请尽量给产品型号、材质/成分、用途、规格，或者直接给产品页/PDF；否则只能先做“待确认项清单”，不能给准入、税费和物流的确定路径。
```

## Product trigger reminder

Use this short reminder when product details are thin:

```text
为了避免把认证、税费和运输判断错，我会特别看这些触发项：是否带电/带电池、是否液体/粉末/磁性、是否化学品或危险品、是否接触食品/皮肤/儿童、是否农产品/冷链、是否大宗/散杂/滚装/超限、是否两用物项或受出口管制。你有资料就给；没有的我会写“待确认”，不会默认猜。
```

## Default assumptions

- Default export declaration country can be China, but the user may set any country/region.
- Origin country, departure node, final HS/HTS, COO/proof-of-origin applicability, certification status, packaging, logistics time, and customs pre-filing nodes remain conditional unless supported by opened sources or user documents.
- Online B2B/B2C channels and platform prices are market references only; they do not define traditional B2B customer scope.
