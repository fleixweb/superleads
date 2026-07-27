# 产品出海市场分析 Code Slice F：COO / 原产地证明要求校验

日期：2026-07-27

## 目标

把 Slice 13 的“目标国原产地证明 / COO 要求判断”落到第一轮代码防错闭环中。

本轮不联网、不判断真实美国规则，只做结构和边界校验：

- COO / proof of origin 必须拆成两条线：
  - 目标国规则状态：目标国家/地区是否需要、何时需要原产地证明。
  - 用户材料状态：用户当前是否已提供、是否适用当前订单/批次/SKU。
- 用户没给 COO 不能推出目标国不需要。
- Made in / Production / origin marking 不能写成 COO 文件要求或已满足 COO。
- 优惠税率 proof of origin 不能泛化成所有普通进口都需要 COO。
- 用户提供 COO 不能写成海关最终原产地裁定。
- `required` / `conditionally_required` / `normally_not_required` 等确定性状态必须有官方/权威来源引用；否则只能降级到 `unable_to_verify`。

## 变更范围

### Schema

更新：`shared/schemas/product-market-analysis.schema.json`

新增：

- `OriginProofRequirementStatus`
  - `required`
  - `conditionally_required`
  - `normally_not_required`
  - `not_applicable`
  - `unable_to_verify`
- `OriginProofUserMaterialStatus`
  - `user_provided_valid_for_scope`
  - `user_provided_needs_review`
  - `user_not_provided_but_required`
  - `user_not_provided_and_not_required_for_current_scenario`
  - `user_material_status_unknown`
- `MatrixRowType`
  - 新增 `origin_proof_requirement`
- `OriginProofRequirementRecord`
  - `sample_id`
  - `target_country_or_region`
  - `origin_or_export_country`
  - `candidate_hs_hts`
  - `requirement_status`
  - `trigger_conditions`
  - `acceptable_documents`
  - `user_material_status`
  - `authority_source_refs`
  - `user_material_refs`
  - `limitation_note`

`MatrixRowRecord` 允许：

- `row_type`
- `origin_proof_requirement`

### Validator

更新：`scripts/validate_product_market_analysis.py`

新增错误码：

| 错误码 | 拦截的问题 |
|---|---|
| `market_origin_proof_user_material_conflated` | 目标国规则状态和用户材料状态混写，或用户未提供被反推为不需要 COO |
| `market_origin_marking_conflated_with_coo` | Made in / Production / origin marking 被写成 COO 文件要求或已满足 COO |
| `market_origin_preferential_overgeneralized` | 优惠税率 proof of origin 被泛化成所有普通进口都需要 COO |
| `market_user_coo_promoted_to_official_ruling` | 用户 COO 被写成海关/主管机关最终原产地裁定 |
| `market_origin_requirement_without_authority` | 确定性 COO 要求状态没有官方/权威来源引用 |

同时更新 `evals/run_product_market_analysis_evals.py`：独立 market suite 现在会校验 fail case 的 `expected_error_codes`，避免“失败了但不是预期原因”。

## 新增 pass fixtures

| fixture | 覆盖场景 |
|---|---|
| `market_pass_origin_proof_conditionally_required_user_missing.json` | 目标国官方来源显示优惠/特定场景条件性需要 proof of origin，用户未提供；通过，因为两条线分列 |
| `market_pass_origin_proof_normally_not_required_marking_required.json` | 普通进口示范场景通常不要求单独 COO，但 marking / Made in 另行展示；通过，因为没有混同 |
| `market_pass_origin_proof_user_coo_scope_limited.json` | 用户提供 COO，但只限当前发票/订单/样本范围；通过，因为没有泛化成所有 SKU，也没有写海关最终裁定 |
| `market_pass_origin_proof_unable_to_verify_source_limited.json` | 未打开足够权威来源；通过，但状态为 `unable_to_verify` / `source_restricted` |

## 新增 fail fixtures

| fixture | 预期错误码 |
|---|---|
| `market_fail_user_missing_coo_as_not_required.json` | `market_origin_proof_user_material_conflated` |
| `market_fail_marking_as_coo_required.json` | `market_origin_marking_conflated_with_coo` |
| `market_fail_preferential_origin_as_all_imports.json` | `market_origin_preferential_overgeneralized` |
| `market_fail_coo_as_final_origin_ruling.json` | `market_user_coo_promoted_to_official_ruling` |
| `market_fail_origin_requirement_without_official_source.json` | `market_origin_requirement_without_authority` |

## 验证结果

已执行：

```bash
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

结果：

| 命令 | 结果 |
|---|---:|
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `36/36` |
| `python3 evals/run_evals.py --suite default` | `77/77` |
| `python3 evals/run_evals.py --suite deep` | `623/623` |
| `python3 evals/run_evals.py --suite all` | `663/663` |

## 边界说明

- 本轮 fixture 中的 CBP / USITC 等文字仍是静态 eval 样本，不是对真实美国规则的最新联网核验。
- Source / Observation 结构只用于验证“必须有官方/权威来源引用”的数据链路。
- 导出器仍只搬运 `matrix_rows.user_visible_cells`，不补税率、不猜港口、不生成 COO 规则事实。
- 产品是否进入目标市场仍不由系统判断。
