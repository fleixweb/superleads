# 产品出海市场分析 Slice 13 验收清单：目标国原产地证明 / COO 要求判断（2026-07-27）

## 1. 本轮目标

用户确认：COO / 原产地证书不是单纯的“用户有没有提供资料”，而是目标国家/地区准入、清关、税费、贸易协定和贸易救济规则中的必要条件判断。

本轮只做产品设计文档，不写代码、不新增 fixture、不联网验证具体国家规则。

## 2. 被验收文件

| 文件 | 作用 |
|---|---|
| `spec/24-product-outbound-market-analysis-origin-proof-requirements.md` | 冻结 COO / proof of origin 需求判断规则 |
| `spec/10-product-outbound-market-analysis-contract.md` | 将 COO 要求纳入产品合同、证据合同和验收样本边界 |
| `spec/13-product-outbound-market-analysis-workbook-contract.md` | 增加 `origin_proof_requirement` 专门行和双状态字段 |
| `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md` | 增加 COO / marking / preferential proof 的禁止升级规则 |
| `spec/15-product-outbound-market-analysis-skill-orchestration.md` | 将 COO 要求纳入 Skill C 主动判断和 Skill F 交付复核 |
| `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md` | 增加目标国原产地证明真实来源采集策略 |
| `spec/20-product-outbound-market-analysis-source-pack-contract.md` | 增加 `destination_origin_proof_pack` 和查询组触发规则 |
| `spec/22-product-outbound-market-analysis-end-to-end-runbook.md` | 将 COO 要求纳入端到端 Query Plan、EvidenceCard、MatrixRow 和门禁 |

## 3. 关键纠偏验收

| 检查项 | 结果 | 说明 |
|---|---|---|
| COO 不再只作为用户材料缺口 | 通过 | 文档明确目标国规则线与用户材料线分离 |
| 用户未提供 COO 不等于目标国不需要 | 通过 | 已列为禁止升级和 fail fixture 草案 |
| 目标国是否需要必须主动查询 | 通过 | 已定义证据优先级与必须查询维度 |
| 输出支持“需要 / 条件性需要 / 通常不要求 / 未能核实” | 通过 | 已新增要求状态枚举 |
| Country of Origin Marking 不等于 COO | 通过 | 已列术语边界和禁止误导 |
| Preferential proof of origin 不泛化成所有进口都需要 | 通过 | 已列禁止误导与 fail fixture 草案 |
| 用户提供 COO 不等于海关最终裁定 | 通过 | 已保留原产地证据等级和专业确认边界 |

## 4. 工作流验收

| 环节 | 结果 | 说明 |
|---|---|---|
| Brief | 通过 | 要记录目标国、原产国/出口国、起运地、候选 HS 缺口 |
| Skill C | 通过 | 目的国准入/税费 Skill 必须主动判断 origin proof requirement |
| Skill D | 通过 | 出口国 Skill 只处理出口侧签发/申领程序，不替代目的国要求 |
| Skill F | 通过 | 交付复核需检查“目标国要求”和“用户资料状态”是否分列 |
| Source Pack | 通过 | 已定义 `origin_proof_requirement` 查询组触发条件 |
| 工作簿 | 通过 | 已设计并同步专门行类型和字段合同 |
| 既有规格同步 | 通过 | 已同步产品合同、工作簿、证据边界、Skill 分工、真实来源采集、Source Pack、端到端 runbook |

## 5. 未来 eval 验收草案

| 类别 | 覆盖点 |
|---|---|
| Pass | 条件性需要 + 用户未提供；普通进口通常不要求 COO 但要求 marking；用户 COO 仅限订单/批次；官方来源不足时 unable_to_verify |
| Fail | 用户没给被写成不需要；marking 写成 COO；优惠 proof 泛化所有进口；COO 写成海关裁定；无官方来源写确定性要求 |

## 6. 结论

Slice 13 设计验收通过，且已同步回既有产品合同、真实来源采集策略、Skill 分工、工作簿合同、Source Pack 合同和端到端 runbook。下一步如果开始代码，应先做 schema/validator/fixture 增量切片。
