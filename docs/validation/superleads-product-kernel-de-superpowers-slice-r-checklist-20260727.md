# Slice R 验收清单：Superleads 产品内核复盘与去 Superpowers 化校准

日期：2026-07-27

## 验收对象

- `spec/25-superleads-product-kernel-and-de-superpowers-calibration.md`
- `product/00-product-brief.md`
- `product/02-bet.md`
- `spec/10-product-outbound-market-analysis-contract.md`
- `shared/references/route-map.md`
- `shared/references/user-intake.md`
- `skills/using-superleads/SKILL.md`

## 1. 是否把 Superpowers 与 Superleads 分清

| 检查项 | 结果 |
|---|---|
| 明确 Superpowers 只能作为执行纪律参考 | 通过 |
| 明确 Superpowers 不是 Superleads 的产品本体 | 通过 |
| 明确 Superleads 的产品对象来自外贸业务 | 通过 |
| 没有把 Superpowers 写成用户可见卖点 | 通过 |

## 2. 是否重新冻结 Superleads 三条路线

| 路线 | 是否覆盖 | 说明 |
|---|---:|---|
| 批量客户开发 | 是 | 明确交付候选客户池、公开信号、联系人入口、相关性状态，不自动推荐客户 |
| 单一客户背调 | 是 | 明确围绕指定对象核实身份、关系、业务信号、联系入口，不扩展成批量找客户 |
| 产品出海市场分析 | 是 | 明确交付市场与准入信息矩阵，不生成客户名单或市场进入建议 |

## 3. 是否识别 A-M 的价值与风险

| 检查项 | 结果 |
|---|---|
| 没有简单否定 A-M 的证据链工作 | 通过 |
| 说明 A-M 主要解决真实外贸误导风险 | 通过 |
| 指出 Source Pack / EvidenceCard 后续可能过度工程化 | 通过 |
| 建议先跑真实三路线样本，而不是继续增加内部层 | 通过 |

## 4. 是否形成去 Superpowers 化校准规则

| 检查项 | 结果 |
|---|---|
| 每个新功能必须绑定三条业务路线之一 | 通过 |
| 每个新功能必须有用户可见外贸收益 | 通过 |
| 每个新功能必须说明减少哪类真实误导 | 通过 |
| 框架完整性不足以进入 active bet | 通过 |
| 真实样本和业务 fixture 优先于内部对象完整性 | 通过 |

## 5. 是否保留 Superleads 的弱证据哲学

| 检查项 | 结果 |
|---|---|
| 弱证据不删除，只降级展示 | 通过 |
| 误导性升级才阻断 | 通过 |
| 搜索摘要、平台价、候选税号、网页标签、来源受限等边界继续保留 | 通过 |
| 用户可见语言必须人话化 | 通过 |

## 6. 对下一步的影响

本轮将原本建议的 Code Slice N 调整为暂缓。推荐下一步：

```text
Slice S：用真实外贸任务跑一遍三条路线的用户可见样本，检查 Superleads 是否像外贸产品，而不是像工作流框架。
```

最小样本：

1. 批量客户开发样本；
2. 单一客户背调样本；
3. 产品出海市场分析样本。

## 7. 结论

Slice R 验收通过。Superleads 可以继续使用计划、切片、验证、交接、eval 等工程纪律，但后续 active bet 必须回到外贸用户可见价值，避免继续围绕内部证据层做过度工程化扩张。
