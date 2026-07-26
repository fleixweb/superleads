# 产品出海市场分析：Slice 5 数据模型与 eval 夹具设计验收清单（2026-07-26）

本清单用于人工验收 `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md`。本轮只验收设计，不创建 JSON Schema、不新增 eval fixture、不写实现代码。

## 1. 验收范围

| 项目 | 当前结果 |
|---|---|
| 被验收文件 | `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md` |
| 关联规则 | Slice 2 工作簿合同、Slice 3 证据边界、Slice 4 Skill 分工互证 |
| 样本 | Xing Heng `48V20Ah`；UNIQLO Men's Corduroy Overshirt `470177` |
| 验收方式 | 人工核对对象模型、状态流转、禁止升级断言和 fixture 清单 |
| 代码实现 | 未执行，非本 Slice 范围 |

## 2. 数据模型验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| 独立 ProductMarketAnalysisGraph 已明确 | 通过 | 不把产品市场分析塞进 Candidate / Claim / Assessment |
| 复用 Source / Observation 思路 | 通过 | 来源和观察仍可追溯 |
| Brief 版本机制已明确 | 通过 | Brief 改版后下游 Skill 需重跑或降级 |
| 产品与贸易前提拆分 | 通过 | 产品、出口申报国、原产国、起运国、目的国分开 |
| EvidenceCard 字段完整 | 通过 | 含来源定位、支持范围、不能支持什么、状态、规则 ID |
| SkillHandoffRecord 已定义 | 通过 | 能记录输入 Brief、产出卡、打回和过期状态 |
| MatrixRowRecord 已定义 | 通过 | 工作簿行必须能追到证据卡、缺口或未执行记录 |

## 3. 状态与边界验收

| 风险 | 检查结果 | 当前规则 |
|---|---|---|
| 搜索摘要直接变已核实 | 通过 | 搜索线索只能到候选 |
| Skill 摘要当来源 | 通过 | `source_locator` 不能是前序摘要 |
| 候选税号变最终税率 | 通过 | 明确禁止流转 |
| 网页标签变实物标签合规 | 通过 | 明确禁止流转 |
| 未执行模块生成结论 | 通过 | `not_executed` 不能含事实结论 |
| 来源冲突被隐藏 | 通过 | 必须生成 ConflictRecord |
| 起运港被默认 | 通过 | 需业务确认，不得猜常用港 |
| 内部信息泄露 | 通过 | MatrixRow 要求隐藏本地路径、哈希、内部 ID |

## 4. eval 夹具验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| 有未来文件布局 | 通过 | schema、cases、fixtures、validator、audit/export 均有建议路径 |
| 有 eval 分层 | 通过 | Schema、Evidence、Boundary、Handoff、Export、Static text 六层 |
| 有 pass fixture 清单 | 通过 | 覆盖 Xing Heng、UNIQLO、搜索候选、未执行保留、冲突保留、Brief 改版 |
| 有 fail fixture 清单 | 通过 | 覆盖搜索升级、QCVN/UN38.3、SDS、HTSUS、Google Trends、价格、物流、价值判断等 |
| 有错误码草案 | 通过 | critical / major / minor 分级 |
| 两个样本有最小断言 | 通过 | Xing Heng 与 UNIQLO 均有可实现断言 |

## 5. 当前结论

| 项目 | 结论 |
|---|---|
| Slice 5 文档层验收 | 通过 |
| 是否写了代码 | 没有 |
| 是否新增真实来源事实 | 没有 |
| 是否可进入实现 | 可以，但需用户明确同意写代码 |
| 推荐下一步 | Slice 6：实现前执行计划，拆分 schema、validator、audit、export、eval fixtures 的最小代码切片 |
