# 产品出海市场分析：真实业务感 fixture 补充验证（2026-07-26）

## 1. 本轮目标

用户要求：在已有 Code Slice A-E 基础上，**再补几条更贴近真实业务的 pass/fail fixture**。

本轮不接真实 Google Trends、关税 API、法规库或 Source Pack registry；仍以静态 fixture 验证证据边界和导出安全。

## 2. 新增 pass fixture

| fixture | 业务场景 | 验证重点 |
|---|---|---|
| `market_pass_tianneng_lithium_realistic_boundary.json` | Tianneng `TMLiN-4810S1` 锂电动力电池，越南工厂线索，出口美国 | 公开目录可核实型号、48V、10Ah、尺寸、重量；`480 Wh = 48 V × 10 Ah` 只能是派生计算；越南工厂新闻不能升级为 SKU 原产地、起运港或税费结论；UN38.3/SDS/包装/起运节点保留缺口 |
| `market_pass_xm_canvas_realistic_boundary.json` | XM Textiles `Canvas-270` 涤棉工作服面料，中国出货线索，出口美国 | TDS 可核实成分、克重、门幅、织法；中国生产/采购/出货线索不能升级 SKU 原产地或起运港；Oeko-Tex 文字与 `0 Certificates` 冲突保留；纺织归类和美国标签保持待专业确认 |
| `market_pass_platform_price_reference_only.json` | UNIQLO 零售页标价作为线上市场参考 | 零售/平台挂牌价只作初步参考；不得升级为成交价、批发价、外贸目标价或推荐报价；导出允许出现否定语境中的“不是推荐价格” |

## 3. 新增 fail fixture

| fixture | 真实业务常见错误 | 预期拦截 |
|---|---|---|
| `market_fail_factory_news_as_sku_origin_and_port.json` | 把越南工厂新闻写成 SKU 原产越南，并默认海防港 | `market_guess_departure_port` |
| `market_fail_textile_cert_and_hts_overstated.json` | 把产品页证书文字写成 SKU 已认证，同时把纺织候选归类写成最终 HTSUS / 最终税率 | `market_candidate_hs_promoted_to_final` |
| `market_fail_platform_price_as_recommended_transaction_price.json` | 把零售挂牌价写成成交价、外贸目标价或推荐价格 | `market_platform_price_promoted`，并由 `market_value_judgment` 兜底阻断 |

## 4. Validator 补充

新增错误码：`market_platform_price_promoted`。

触发条件：用户可见矩阵行或证据卡中，线上价格 / 平台价格 / 零售标价 / listing price 等被升级为：

- 成交价；
- 批发价；
- 外贸目标价；
- 推荐价格 / 推荐报价。

该规则补齐 Slice 5 设计中已有但首批代码未实现的 `market_platform_price_promoted` 场景。

## 5. 已执行验证

```bash
python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_*.json
python3 scripts/validate_product_market_analysis.py evals/fixtures/market_fail_*.json
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

本文件创建时验证结果：market suite `27/27`；default `77/77`；deep `623/623`；all `663/663`。

## 6. 边界确认

| 检查项 | 结果 |
|---|---|
| 搜索摘要未写成事实 | 通过 |
| 工厂/出货线索未在 pass 样本升级为 SKU 原产地 | 通过 |
| 起运港未在 pass 样本默认 | 通过 |
| UN38.3 / SDS / 包装未被公开目录替代 | 通过 |
| 面料 TDS 未升级为标签合规或最终 HTSUS | 通过 |
| 证书冲突未被隐藏 | 通过 |
| 平台/零售价格未在 pass 样本升级成交价或推荐价 | 通过 |
| fail 样本能阻断真实业务中的常见越界表述 | 通过 |
| 导出不暴露本地路径、hash、token URL 或内部 ID | 通过 |
