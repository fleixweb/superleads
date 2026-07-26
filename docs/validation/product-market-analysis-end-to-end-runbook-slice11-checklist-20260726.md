# 产品出海市场分析：Slice 11 端到端运行剧本验收清单（2026-07-26）

本清单用于人工验收 `spec/22-product-outbound-market-analysis-end-to-end-runbook.md`。本轮只做端到端运行剧本，不写代码，不联网，不新增事实来源。

## 1. 验收范围

| 项目 | 当前结果 |
|---|---|
| 被验收文件 | `spec/22-product-outbound-market-analysis-end-to-end-runbook.md` |
| 关联规格 | Slice 1-10 所有产品出海市场分析规格 |
| 验收方式 | 人工核对流程、状态、门禁、样本剧本、Mermaid、报告骨架和负向断言 |
| 代码实现 | 未执行 |
| 联网采集 | 未执行 |
| 新事实结论 | 未新增 |

## 2. 流程验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| 端到端顺序清楚 | 通过 | Brief -> Pack -> Query Plan -> Search/Source -> Observation -> EvidenceCard -> MatrixRow -> Delivery |
| Source Pack 不变事实 | 通过 | Pack / Entry / QueryTemplate 只产生候选和采集计划 |
| 打开来源才形成 Observation | 通过 | 只有可见、可定位内容可入 Observation |
| EvidenceCard 有边界 | 通过 | 每张卡必须有 supports / does_not_support |
| MatrixRow 有状态 | 通过 | 未知、未执行、来源受限、候选、冲突都要保留 |
| 用户报告表格化 | 通过 | 最终报告骨架按区块矩阵输出，不写长篇散文 |

## 3. 门禁与状态验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| Brief 冻结门 | 通过 | 产品版本、目标国、出口申报国、原产国、起运国需拆开 |
| 证据来源门 | 通过 | 搜索摘要、Pack、Entry、Skill 摘要不得直接成事实 |
| 交付边界门 | 通过 | 候选税号、网页标签、QCVN、趋势、价格、物流不能升级结论 |
| 状态流转 | 通过 | 只有满足来源、定位、日期和适用范围时才可升级 |
| 打回/降级 | 通过 | 缺关键资料时降级为待确认、来源受限、未执行或冲突待复核 |

## 4. 样本剧本验收

| 样本 | 检查结果 | 说明 |
|---|---|---|
| Xing Heng 锂电 Brief | 通过 | 出口申报国、起运港、UN38.3、SDS、包装均保留缺口 |
| Xing Heng Pack 路由 | 通过 | 触发美国准入/税费/市场、锂电、物流、产品原始来源；越南出口需确认 |
| Xing Heng MatrixRow | 通过 | 960Wh 为派生计算；QCVN 不升级 UN38.3/SDS；候选 HTSUS 不升级最终税率 |
| UNIQLO 纺织 Brief | 通过 | Production: China 不等于出口申报国或起运港；实物标签/BOM 保留缺口 |
| UNIQLO Pack 路由 | 通过 | 触发美国准入/税费/市场、纺织通用、产品原始来源；中国出口需确认 |
| UNIQLO MatrixRow | 通过 | 网页 Body/Trim 不升级全成分或实物标签合规；候选 HTSUS 不升级最终归类 |

## 5. 负向断言验收

| 禁止项 | 检查结果 | 说明 |
|---|---|---|
| 搜索摘要写成 Claim | 通过 | 明确只作候选线索 |
| Source Pack 写成事实依据 | 通过 | 明确禁止 Pack / Entry / QueryTemplate 直接支持事实 |
| QCVN 升级 UN38.3/SDS | 通过 | 明确禁止 |
| 网页标签升级实物标签合规 | 通过 | 明确禁止 |
| 候选税号升级最终税率 | 通过 | 明确禁止 |
| 趋势写成销量 | 通过 | 明确禁止 |
| 价格写成推荐价 | 通过 | 明确禁止 |
| 物流写成最佳/承诺 | 通过 | 明确禁止 |
| 输出价值判断 | 通过 | 明确禁止建议进入、值得开发、市场潜力高 |
| 内部信息泄露 | 通过 | 来源表不得暴露本地路径、hash、token、内部 ID |

## 6. 当前结论

| 项目 | 结论 |
|---|---|
| Slice 11 文档层验收 | 通过 |
| 是否写了代码 | 没有 |
| 是否联网采集事实 | 没有 |
| 是否新增税率/法规/价格/物流结论 | 没有 |
| 推荐下一步 | 若继续不写代码：做 Slice 12 MVP 收口与实现前冻结；若开始实现：先做 Code Slice A-C，即 schema、validator、首批 fixtures |
