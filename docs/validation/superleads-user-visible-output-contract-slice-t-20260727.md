# Slice T 验收记录：三条路线用户交付标准 / 静态 eval

日期：2026-07-27

## 1. 本轮目标

把 Slice S 中三条真实外贸用户可见样本固化为输出合同和静态 eval，确保后续修改不会把 Superleads 改回内部工作流语言。

本轮不做：

- 不联网；
- 不补真实 Google Trends、法规、税费、物流或客户来源；
- 不生成正式客户名单；
- 不改变产品市场分析事实矩阵；
- 不清理 `tmp/stage5_chillys/`。

## 2. 新增 / 修改文件

| 类型 | 文件 |
|---|---|
| 输出合同 | `spec/27-superleads-user-visible-output-contract-slice-t.md` |
| 静态 validator | `scripts/validate_superleads_user_visible_output.py` |
| 独立 eval runner | `evals/run_superleads_user_visible_output_evals.py` |
| eval cases | `evals/cases/superleads_user_visible_output_cases.json` |
| pass 样本 | `evals/user_visible_outputs/bulk_customer_development_us_generator_aftermarket.md` |
| pass 样本 | `evals/user_visible_outputs/customer_background_chillys.md` |
| pass 样本 | `evals/user_visible_outputs/product_market_xingheng_lifepo4_us.md` |
| fail 样本 | `evals/user_visible_outputs/fail_bulk_customer_recommendation_and_internal_terms.md` |
| fail 样本 | `evals/user_visible_outputs/fail_customer_background_procurement_claim.md` |
| fail 样本 | `evals/user_visible_outputs/fail_product_market_value_and_final_rate.md` |
| 主套件接入 | `evals/run_evals.py` |

## 3. 静态 eval 检查什么

| 检查维度 | 具体规则 |
|---|---|
| 三条路线不串线 | 批量客户开发不能变产品市场分析；单客背调不能输出候选客户池；产品市场分析不能输出客户名单 |
| 人话字段 | 必须出现对应路线的用户可见字段，如“我理解你卖的是”“客户一眼看懂”“先看贸易前提”等 |
| 表格化表达 | Markdown 至少包含对应数量的表格 |
| 内部语言不外露 | 阻断 `EvidenceCard`、`SearchLog`、`Claim`、`MatrixRow`、`graph`、`eval`、本地路径等 |
| 价值判断不外露 | 阻断“推荐客户”“采购概率”“建议进入”“最佳运输方式”“推荐报价”“最终税率就是”等 |
| 证据升级不外露 | 阻断“Google Trends 证明销量”“候选税号就是最终税率”“董事是采购负责人”“公开联系入口说明有采购意愿”“Production 等于 COO”等 |
| 弱证据状态可见 | 要求出现候选、待确认、未执行、来源受限或不能推出等表达 |

## 4. 三个正向样本

| 路线 | 样本文件 | 验收重点 |
|---|---|---|
| 批量客户开发 | `bulk_customer_development_us_generator_aftermarket.md` | 四行开场、候选客户池、相关性状态、联系入口、还要确认什么 |
| 单一客户背调 | `customer_background_chillys.md` | 一句话先说清、客户一眼看懂、关联方、联系入口、注意事项、来源 |
| 产品出海市场分析 | `product_market_xingheng_lifepo4_us.md` | 贸易前提拆分、产品触发项、未执行市场模块、候选 HTSUS、COO、拼箱/快递、待补材料 |

## 5. 三个失败样本

| 失败样本 | 拦截点 |
|---|---|
| `fail_bulk_customer_recommendation_and_internal_terms.md` | 推荐客户、采购概率、内部 EvidenceCard 外露 |
| `fail_customer_background_procurement_claim.md` | 单客背调扩成候选客户池、SearchLog/Claim 外露、董事/公开入口升级 |
| `fail_product_market_value_and_final_rate.md` | 建议进入、最佳路线、最终税率、Google Trends 销量、Production 等于 COO |

## 6. 已验证命令

| 命令 | 结果 |
|---|---|
| `python3 -m py_compile scripts/validate_superleads_user_visible_output.py evals/run_superleads_user_visible_output_evals.py evals/run_evals.py` | 通过 |
| `python3 evals/run_superleads_user_visible_output_evals.py --suite all` | `6/6` |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `42/42` |
| `python3 evals/run_evals.py --suite default` | `90/90` |
| `python3 evals/run_evals.py --suite deep` | `636/636` |
| `python3 evals/run_evals.py --suite all` | `676/676` |

说明：deep/all 曾直接输出完整 JSON 导致终端命令超时；随后改为重定向到 `/tmp` 后读取摘要，结果均通过。

## 7. 验收结论

Slice T 通过。现在三条路线的用户可见交付已经有静态回归保护：

- 批量客户开发继续是候选客户池；
- 单一客户背调继续围绕指定对象；
- 产品出海市场分析继续是市场与准入矩阵；
- 内部对象语言、价值判断和典型证据升级会被静态 eval 阻断。

下一步建议先提交 Slice R / S / T 当前变更；之后再决定进入哪一个真正改善用户可见交付的 Code Slice。
