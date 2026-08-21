# User Intake

## Intake Modes

Classify the interaction before business routing. `metadata` covers `@superleads`, help, current/installed-version questions, current-capability questions, and the feedback entry; it returns static information with `operations: []` and does not create a Run/Brief, run preflight, search, open sources, scan caches, or export. Read a version only from an explicitly supplied active plugin root's `.codex-plugin/plugin.json`. A remote version check is allowed only after an explicit update request through an injected callback; failure is `本次未能确认远端版本`.

`material_triage` is the user-visible `资料初审` path for material-only PDF, Excel/CSV, or screenshot requests. It organizes only supplied material and pending checks; it does not start public research or create a Run/Brief. `discovery_snapshot` is the ordinary bounded discovery mode. `formal_research` requires explicit intent such as `完整报告`, `正式开发名单`, `标准交付`, `深度背调`, or `联系人归属核验`.

Start from the user's actual task:

1. Company website, company name, or social link.
2. Product name and target country/region.
3. Keywords.
4. Industry, application, or downstream field.
5. Country/region and target customer type.
6. Excel/CSV or pasted customer list.
7. Competitor, brand, seed customer, or reference website.
8. Trade fair directory, PDF, webpage list, screenshot, or search result.
9. Product model, manufacturer part number, OEM number, 番号 or 料号.

指定一个公司、品牌、域名、地址、邮箱、Candidate 或用户材料并要求客户背调，进入“客户背调报告”入口。它不产生新客户批量池，也不要求预先 Entity 解析；可形成独立的轻验证背景报告文件，不进入正式名单 audit 或 manifest。正式标准开发名单仍是独立、明确请求的严格路径。

给出一个产品/型号/产品资料，并要求分析该产品出口或进入某个国家/地区的趋势、公开价格、准入合规、税费、出口要求、运输路线、COO/原产地证明或近期外部因素，进入“产品出海市场分析”入口。它不生成客户名单、不推荐客户类型、不判断是否值得进入，也不把线上渠道或价格参考变成批量客户开发范围。

如果用户同时说“先分析市场再找客户”，先做产品出海市场分析；只有用户看完后明确要找客户，才另启批量客户开发。若用户说“找需要 CE/UL/某认证需求的进口商/客户”，这是目标客户属性，仍属于批量客户开发；若用户问“该产品出口/进入某国是否需要 CE/UL/SDS/UN38.3/COO、关税、标签、清关文件”，这是目标市场准入条件，属于产品出海市场分析。用户明确不做某条路线时，入口路由必须尊重否定条件。

New customer development needs product/service plus at least one scope axis: country/region, customer type, channel, application, keyword, seed company, competitor, existing table, trade fair/PDF/web material.

A model, part number, OEM number, 番号 or 料号 is a valid product anchor. When the user supplies only that code, use 公开检索 to identify the product name, brand/manufacturer association, and compatible product family. This lookup is evidence collection, 不是模型推断. Keep identity pending until an opened public source supports it; never infer the product category from the code shape alone.

Product outbound market analysis needs product identity plus target country/region. Export declaration country may default visibly to China unless the user sets another country. Origin country, departure node, final HS/HTS, certificates, COO/proof of origin, packaging, and logistics timing stay as待确认 when unsupported.

Single-company analysis requires the current user's explicit company name,
URL/domain, or material reference and resolves only that specified Entity.
Existing-table enrichment requires the user-provided spreadsheet and the
specific rows/cells being supplemented. These are analysis or original-table
results, not a way to create a direction-matched customer list without the
current development contract. PDF/fair directory extraction, webpage-list
cleanup, and screenshot/search-result organization require parseable material.
For multi-row or multi-query table enrichment, use `bulk-execution-strategy.md`
for batching, rolling deduplication, intermediate delivery, and resume anchors;
single-row supplementation does not load that reference.

## 本次找什么 / 不找什么 / 怎么判断

For new customer development, first restate the user's natural language in
four short lines: 我理解你卖的是、 本次优先找、 本次不纳入、 判断依据将重点看。
Do not turn this into a fixed industry questionnaire.

Ask only one to three short questions when an answer would lead to a different
customer direction, such as whether named brands or competitors are references
or allowed prospects, whether a business boundary applies, or whether similar
terms represent different applications. If the key ambiguity remains, provide
only three to five `方向样本，等待确认后再扩展`; do not issue a standard list.
If product, country/region, and customer type are already clear, use the fast
candidate-pool first batch of 10 and then ask whether to expand to 30 or 50.
Do not add a country, product type, application, channel,
company size, or customer type that the user did not state.

Treat a competitor, brand, manufacturer, or reference website as a search or
market reference by default. It becomes a prospect only when the user permits
that in this current task; the decision never carries into another Run.
