# 产品出海市场分析内部状态外露失败样本

## 先看贸易前提

| 项目 | 当前值 | 依据状态 | 为什么重要 |
|---|---|---|---|
| 目标销售国家/地区 | 美国 | business_confirmation_required | 决定进口准入、税费和运输口径 |
| 出口申报国 | 中国 | technical_docs_required | 默认出口国可改 |
| 原产国 / 制造来源 | 中国 | user_not_provided_but_required | 不能把网页产地当 COO |
| 实际起运地 / 起运港 | 待业务确认 | not_executed | 不能猜港口 |

## 产品档案与触发项

| 字段 | 当前看到什么 | 依据状态 | 不能推出什么 |
|---|---|---|---|
| 产品 | 示例锂电池包 | verified | 不能推出可出运 |
| 文件 | SDS 未见 | technical_docs_required | 不能写无需 SDS |

## 产品准入与合规要求

| 项目 | 规则结论 | 用户材料状态 | 依据状态 | 不能写成什么 |
|---|---|---|---|---|
| COO / 原产地证明 | unable_to_verify | user_not_provided_but_required | candidate_needs_check | 不能因用户未提供 COO 就写“不需要” |
| 认证 | conditionally_required | user_material_status_unknown | secondary_reference_only | 不能写已合规 |

## 进口税费

| 项目 | 当前值 | 依据状态 | 说明 |
|---|---|---|---|
| 候选 HTSUS | 8507.60.00 | candidate | 不能写成最终税率 |
| 税率时效 | 旧税表 | stale_needs_recheck | 不能当最新税率 |

## 运输方式、路线与申报节点

| 方式 | 当前可说什么 | 依据状态 | 关键缺口 |
|---|---|---|---|
| 海运 | 本轮未核验 | not_executed | 不能写最佳路线 |
| 国际快递 | 需按带电货核验 | professional_confirmation_required | 不能写承诺交期 |

## 信息来源与待确认事项

| 信息 | 来源 | 依据状态 | 待确认事项 |
|---|---|---|---|
| 来源 | 示例来源 | source_restricted | 需打开原始来源 |
