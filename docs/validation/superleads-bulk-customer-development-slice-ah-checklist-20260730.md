# Slice AH 验证记录：批量客户开发发现候选池分区纠偏

日期：2026-07-30

## 范围

本次只冻结产品设计文档，不写代码、不联网采集真实客户、不新增名单数据。

本次纠偏替换了上一版“把 `初筛客户名单` 实现为 L2 弱证据中间档”的方向，改为：

```text
发现候选池内部三分区 + 禁用/拒绝/回落 `初筛客户名单` 绕过口
```

本轮实现后的默认交付仍以 `发现候选池` 为主；`分区`、`依据状态` 和 `可能客户角色` 是候选池内的展示列，不是新的输出层级。

新增 / 更新文档：

- `spec/36-superleads-bulk-customer-development-slice-ah.md`
- `docs/validation/superleads-bulk-customer-development-slice-ah-checklist-20260730.md`
- `HANDOFF.md`
- `TASKS.md`
- `meta/decision-log.md`

## 核验清单

| 项目 | 结果 |
|---|---|
| 明确批量客户开发不是自动推荐客户 | 通过 |
| 明确默认交付为发现候选池 | 通过 |
| 撤销“将 `初筛客户名单` 定义为独立 L2”的旧结论 | 通过 |
| 明确 `初筛客户名单` 当前是 validator 绕过风险 | 通过 |
| 明确后续 Code Slice AH 应优先堵绕过口 | 通过 |
| 明确不新增 output_mode / delivery_status / exporter mode / audit 分支 | 通过 |
| 明确发现候选池内部三分区：可优先人工跟进 / 待确认 / 已排除或仅作参考 | 通过 |
| 明确发现候选池不要求 Claim / ScopeDecision / Assessment / Review / Manifest | 通过 |
| 明确保留标准开发名单为显式正式核查路径 | 通过 |
| 明确当前本地部署不提供完整核查版 | 通过 |
| 明确多来源一致不能升级为采购意愿或已验证客户 | 通过 |
| 明确联系入口不等于采购意愿，公开职位不等于采购负责人 | 通过 |
| 明确客户类型为开放文本，不硬编码 ICP | 通过 |
| 明确 bulk Markdown 缺联系方式汇总、搜索覆盖与收敛、已排除客户、依据状态 | 通过 |

## 非执行项

- 未运行真实搜索。
- 未创建 Candidate、Source、Observation、Claim 或 Assessment。
- 未更新 schema / validator / exporter。
- 未新增真实客户样本。

## 后续建议

进入 Code Slice AH：先堵 `初筛客户名单` 绕过口，再优化 bulk Markdown 发现候选池展示。

建议顺序：

1. `validate_research_graph.py`：`初筛客户名单` 不得绕过默认发现 Candidate 结构检查；建议显式拒绝或强制按发现候选池纪律检查。
2. fixtures/eval：新增 `output_mode=初筛客户名单` 绕过口 fail 样本。
3. `export_superleads_markdown.py`：bulk 路线补联系方式汇总、搜索覆盖与收敛、已排除 / 仅作参考、风险与说明。
4. bulk 主表增加 `分区` 和 `依据状态`。
5. 用户可见 eval：bulk 路线检查依据状态、三分区、禁止推荐客户/采购概率/采购意愿。
