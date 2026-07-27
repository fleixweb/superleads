# 产品出海市场分析 Code Slice H：导出列与 Markdown 展示优化

日期：2026-07-27

## 目标

把 `scripts/export_product_market_workbook.py` 的用户可见输出从“内部字段搬运”优化成更符合真实外贸业务心智的表格：

1. 原产地证明 / COO 要把“目标国规则”和“用户材料状态”分开展示；
2. 默认出口申报国、原产国 / 制造来源、实际起运地 / 起运港要分开展示；
3. 未执行模块要明确，但不要啰嗦；
4. Markdown / CSV 表头使用人话字段名，避免内部 enum / graph / card / gap 语言出现在用户主表中。

## 本轮实现

### 1. CSV 表头人话化

导出器现在会把旧字段名映射成更像外贸表格的字段名，例如：

| 旧字段 | 新展示字段 |
|---|---|
| `样本ID` | `样本编号` |
| `目的国/地区` | `目标销售国家/地区` |
| `出口申报国` | `出口申报国（默认可改）` |
| `原产/制造来源` | `原产国 / 制造来源（证据状态）` |
| `实际起运地` / `起运节点` | `实际起运地 / 起运港（待业务确认）` |
| `候选 HS/HTS` | `候选 HS/HTS（非最终归类）` |
| `税率/金额` | `税率/金额（非最终税额）` |
| `限制说明` / `禁止升级` | `不能推出什么` / `不能写成什么` |

### 2. 贸易前提拆分行

`市场事实总览` 自动补一行 `贸易前提拆分`，用于把以下角色分开：

| 角色 | 展示原则 |
|---|---|
| 目标销售国家/地区 | 从 trade premise / brief 中读取 |
| 出口申报国 | 明确写“本轮出口申报国；默认值可由用户设置” |
| 原产国 / 制造来源 | 带证据等级和状态，如 `L1` 被写成人话“公开页面/产品资料线索” |
| 实际起运地 / 起运港 | 没有具体单据时只写国家 + “具体港口/机场/场站待业务确认” |
| 目的节点 | 未知则写 `未提供`，不猜港口 |

### 3. COO / 原产地证明 Markdown 专区

Markdown 报告新增 `原产地证明 / COO 怎么看` 小节，专门展示：

- 目标国是否要求原产地证明；
- 什么情况下需要；
- 用户现在有没有可用材料；
- 需要用户 / 供应链补什么；
- 不能写成什么。

关键文案：`用户没给 COO，不等于目标国不需要。`

### 4. COO enum 人话化

用户主表中不再只裸露 `conditionally_required`、`normally_not_required`、`user_material_status_unknown` 这类内部状态，而是展示为：

| 内部状态 | 用户可见写法 |
|---|---|
| `conditionally_required` | 条件性需要（如优惠税率、海关要求、贸易救济等） |
| `normally_not_required` | 普通进口通常不要求单独 COO（但原产地标识/海关核验另看） |
| `unable_to_verify` | 未能用权威来源核实 |
| `user_not_provided_but_required` | 用户未提供；若触发上述规则，需要补 |
| `user_provided_valid_for_scope` | 用户已提供；仅限当前订单/批次/范围初步可用 |
| `user_material_status_unknown` | 用户材料状态未知 |

### 5. 未执行模块简写

Markdown 报告顶部新增 `本轮未执行项`，把 `not_executed_modules` 简写成一句：

`Google Trends 长期搜索趋势；线上市场 / 平台价格参考；节假日 / 季节销售窗口；近期外部因素。`

并明确：

`这些项在表格里保留为“未执行”，不编造成趋势、价格、旺季或最新行情结论。`

空表如果对应未执行模块，会显示：

`本轮未执行；不形成趋势、价格、旺季或最新影响结论。`

## 回归断言

已更新 `evals/cases/product_market_analysis_cases.json` 的导出断言，新增覆盖：

| 覆盖点 | fixture |
|---|---|
| 贸易前提拆分、人话字段名 | `market_pass_xingheng_minimum_boundary.json`、`market_pass_uniqlo_minimum_boundary.json` |
| 未执行模块顶部摘要 | `market_pass_not_executed_modules_retained.json` |
| COO 条件性需要 + 用户未提供 | `market_pass_origin_proof_conditionally_required_user_missing.json` |
| 普通进口通常不要求单独 COO | `market_pass_origin_proof_normally_not_required_marking_required.json` |
| 用户已提供 COO 但仅限当前范围 | `market_pass_origin_proof_user_coo_scope_limited.json` |
| 权威来源不足时 unable_to_verify 人话化 | `market_pass_origin_proof_unable_to_verify_source_limited.json` |

## 已验证命令

```bash
python3 -m py_compile scripts/export_product_market_workbook.py evals/run_product_market_analysis_evals.py scripts/validate_product_market_analysis.py scripts/audit_product_market_analysis.py
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

结果：

- market suite：`36/36`
- default suite：`84/84`
- deep suite：`630/630`
- all suite：`670/670`

## 边界

- 本轮只优化展示层和导出断言，不新增真实市场、关税、法规、Google Trends 或物流来源。
- 导出器仍只搬运已审核矩阵、来源、缺口和冲突，不补税率、不猜港口、不生成趋势/价格/认证结论。
- 为兼容既有 eval 和历史夹具，底层 graph enum 不变；人话化发生在 CSV/Markdown 导出层。
