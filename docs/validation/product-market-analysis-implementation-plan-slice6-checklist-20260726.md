# 产品出海市场分析：Slice 6 实现前执行计划验收清单（2026-07-26）

本清单用于人工验收 `spec/17-product-outbound-market-analysis-implementation-plan.md`。本轮只做实现计划，不写代码。

## 1. 验收范围

| 项目 | 当前结果 |
|---|---|
| 被验收文件 | `spec/17-product-outbound-market-analysis-implementation-plan.md` |
| 关联规格 | Slice 1-5 所有产品出海市场分析规格 |
| 验收方式 | 人工核对实现顺序、最小切片、fixture、错误码和非目标 |
| 代码实现 | 未执行 |

## 2. 实现顺序验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| Schema 优先 | 通过 | 第一片是 `ProductMarketAnalysisGraph` schema 骨架 |
| Validator 紧随 | 通过 | 第二片检查状态、来源和禁止升级 |
| Fixture 先行 | 通过 | 明确 pass/fail fixture 和 case 配置 |
| Audit 在导出前 | 通过 | 错误升级必须先阻断交付 |
| 导出只搬运矩阵行 | 通过 | 导出器不推理新事实 |
| 真实来源采集后置 | 通过 | Trends、关税、法规、物流数据接入放后面 |

## 3. 防回归验收

| 风险 | 检查结果 | 说明 |
|---|---|---|
| 影响现有 default/deep/all | 通过 | 计划建议 market suite 先独立稳定 |
| 污染客户开发图谱 | 通过 | 明确不合并进 ResearchGraph 主对象 |
| 把产品分析变客户名单 | 通过 | 不使用 Candidate/Claim/Assessment 做主对象 |
| 真实搜索黑箱 | 通过 | 第一轮不接真实搜索 |
| 导出器生成新事实 | 通过 | 禁止导出器补税率、港口、合规结论 |

## 4. 首批 fixture 与错误码验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| 有 6 个第一批 pass fixture | 通过 | Xing Heng、UNIQLO、搜索候选、未执行保留、派生 Wh、冲突保留 |
| 有 10 个第一批 fail fixture | 通过 | 覆盖搜索摘要、Skill 摘要、QCVN/UN38.3、HTSUS、网页标签、Trends、物流、港口、未执行、内部泄露 |
| 有第一批错误码 | 通过 | critical / major 分级明确 |
| 错误码贴近真实外贸风险 | 通过 | 税费、合规、锂电运输、标签、物流、来源均覆盖 |

## 5. 当前结论

| 项目 | 结论 |
|---|---|
| Slice 6 文档层验收 | 通过 |
| 是否写了代码 | 没有 |
| 是否可以进入代码实现 | 可以，但需要用户明确说“开始写代码/开始实现” |
| 推荐下一步 | 若继续不写代码：做 Slice 7 Skill 文案/用户入口设计；若开始实现：先做 Code Slice A-C，即 schema、validator、首批 fixtures |
