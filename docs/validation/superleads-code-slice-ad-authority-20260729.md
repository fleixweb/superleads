# Code Slice AD Validation — 开放世界来源权威性防错闭环

日期：2026-07-29

## 本轮目标

把 Slice AD「开放世界权威来源识别模型」落到最小工程闭环：

- 不按 200+ 国家/地区硬编码官方来源。
- 强监管事实域的确定性结论必须有 `AuthorityVerificationRecord`。
- 阻断 keyword-only / domain-only / 第三方博客 / 货代 / 行业页 / Source Pack 被升级成主管官方结论。
- 未预置国家/地区时生成动态 authority discovery Query Plan，只输出查询计划，不输出事实。
- 用户可见导出显示来源身份、适用范围、可以当作什么、不能当作什么、权威性核实。

## 已改动

### Schema

`shared/schemas/product-market-analysis.schema.json`

- `EvidenceCard` / `MatrixRowRecord` 新增：
  - `authority_verification_record_ids`
- `ProductMarketAnalysisGraph` 新增可选数组：
  - `authority_profiles`
  - `authority_identity_evidence`
  - `authority_capabilities`
  - `authority_verification_records`
- 新增 Authority 相关 defs：
  - `AuthorityProfile`
  - `AuthorityIdentityEvidence`
  - `AuthorityCapability`
  - `AuthorityVerificationRecord`
  - 对应 level / status / jurisdiction enum

### Validator

`scripts/validate_product_market_analysis.py`

新增防错：

- Authority record 引用完整性校验。
- Verified authority 必须有打开来源 observation。
- Verified authority 必须有非第三方描述的身份核验证据。
- Verified authority 必须有匹配 fact domain 的 capability。
- 强监管事实域确定性 row/card 缺 AuthorityVerificationRecord 失败。
- fact domain 错配失败。
- 目标国 / 出口国 / 原产国 / 起运地角色错配失败。
- keyword-only authority 失败。
- domain-only authority 失败。
- secondary/commercial/media/industry/unknown authority 支撑 required / current / final 等确定性官方要求失败。
- Source Pack / Query Plan / SearchLog 直接支撑事实失败。
- 多弱来源一致写成官方确认失败。
- 修正 proof-of-origin 文案中出现 tariff 时误判成 import_tax 的顺序问题。

### Exporter

`scripts/export_product_market_workbook.py`

新增用户可见列：

- `来源身份`
- `适用范围`
- `可以当作什么`
- `不能当作什么`
- `权威性核实`

Markdown 顶部新增：

- `## 来源权威性 / Authority`

人话边界：来源是否权威要看机构身份、事实域、管辖范围、可见身份核验证据和资料时效；Source Pack、搜索摘要、博客和多弱来源一致不能直接当官方结论。

### Audit

`scripts/audit_product_market_analysis.py`

- 新增 authority limitation 收集：
  - `candidate_needs_check`
  - `secondary_reference_only`
  - `unable_to_verify`
  - `conflicting_identity`
  - `not_executed`
- limitation code：`market_authority_limitation`

### Query Plan

`scripts/plan_product_market_sources.py`

- 对非预置目标国家/地区新增开放世界动态 authority discovery steps。
- 不再因为食品/农产品触发项给非美国目的国套用美国 Source Pack。
- 动态查询组覆盖：
  - 目的国准入 / 标签 / 包装 / 认证
  - COO / proof of origin
  - 官方税则 / 关税 / 贸易救济
  - 预申报 / 运输监管
  - 食品 / 农产品 / 植物检疫触发项
  - 锂电 / 危险品触发项
- 输出仍是 `source_plan_only` / `not_evidence`，不得生成事实。

### Fixtures / Evals

新增或更新：

- 给 5 个旧 pass certification / COO fixture 补 Authority records。
- 新增 pass：
  - `market_pass_authority_official_for_tariff_only.json`
  - `market_pass_authority_cert_body_secondary.json`
  - `market_pass_authority_forwarder_logistics_clue.json`
- 新增 fail：
  - `market_fail_authority_blog_claims_required_cert.json`
  - `market_fail_authority_domain_only_official.json`
  - `market_fail_authority_fact_domain_mismatch.json`
  - `market_fail_authority_jurisdiction_mismatch.json`
  - `market_fail_authority_source_pack_as_fact.json`
  - `market_fail_authority_weak_corroboration_as_official.json`
- 新增 source plan fixture：
  - `source_plan_open_world_thailand_food_brief.json`
- market suite：65 -> 74。
- source plan suite：6 -> 7（含 registry self-check）。

## 已验证

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py scripts/plan_product_market_sources.py  # passed
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
python3 evals/run_product_market_source_plan_evals.py --suite all  # 7/7
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # passed
```

## 边界

- 本轮不联网核验真实机构、法规、税率或认证。
- Source Pack / registry 仍只是入口目录和查询加速器，不能直接支撑事实。
- 多个弱来源一致仍不能变成官方确认；只能作为 corroboration/reference。
- 未预置国家/地区进入动态查询计划，不进入事实输出。
