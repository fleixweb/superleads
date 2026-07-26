# 产品出海市场分析：Slice 9 Source Pack 字段合同验收清单（2026-07-26）

本清单用于人工验收 `spec/20-product-outbound-market-analysis-source-pack-contract.md`。本轮只做字段合同和边界设计，不写代码，不创建真实国家库，不新增事实来源。

## 1. 验收范围

| 项目 | 当前结果 |
|---|---|
| 被验收文件 | `spec/20-product-outbound-market-analysis-source-pack-contract.md` |
| 关联规格 | Slice 5 数据模型、Slice 8 真实来源采集策略 |
| 验收方式 | 人工核对字段、状态、路由、边界和禁止升级 |
| 代码实现 | 未执行 |
| 真实 Source Pack 数据 | 未创建 |
| 联网采集事实 | 未执行 |

## 2. Source Pack 边界验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| Source Pack 不是事实库 | 通过 | 明确只能生成 Query Plan / 待打开来源 |
| Pack 不能直接支持事实 | 通过 | MatrixRow 必须追到 Observation / EvidenceCard |
| Entry 不是 Observation | 通过 | SourceEntry 只是待打开入口 |
| Pack 日期不是事实日期 | 通过 | `last_reviewed_at` 不能当法规/税率/价格日期 |
| 优先级不是事实可信度 | 通过 | P0 仍需打开来源和核对适用范围 |
| 缺 Pack 不补猜 | 通过 | 降级为人工采集计划或来源缺口 |

## 3. 字段合同验收

| 对象 | 检查结果 | 说明 |
|---|---|---|
| `SourcePack` | 通过 | 覆盖 ID、类型、贸易角色、辖区、语言、事实域、触发标签、状态、版本、复核周期和边界说明 |
| `SourceEntry` | 通过 | 覆盖来源名称、所有者类型、权威等级、访问边界、查询槽位、支持/不支持事实域、限制和状态 |
| `QueryTemplate` | 通过 | 覆盖目的、语言策略、查询槽位、必须打开来源等级、拒绝 snippet、fallback 和交接 Skill |
| `ObservationRequirement` | 通过 | 覆盖定位、可见内容、日期、适用条件、限制和阻断条件 |
| `PackRouteRule` | 通过 | 覆盖 Brief 字段、产品标签、触发 Pack、用户确认、缺 Pack 降级和边界说明 |

## 4. Pack 类型验收

| Pack 类型 | 检查结果 | 说明 |
|---|---|---|
| 目的国准入 Pack | 通过 | 不存认证结论 |
| 目的国税费 Pack | 通过 | 不存最终税率 |
| 出口国 Pack | 通过 | 不把原产国自动当出口国 |
| 物流 Pack | 通过 | 不承诺时效或最佳路线 |
| 市场信号 Pack | 通过 | 不做销量、GMV、目标价或进入建议 |
| Common Rule Pack | 通过 | 只作跨域入口，不宣称全球通用结论 |
| Product Original Source Pack | 通过 | 产品资料入口不自动证明原产地、HS、认证或运输可行性 |

## 5. 产品触发标签验收

| 触发范围 | 检查结果 | 说明 |
|---|---|---|
| 普通贸易 | 通过 | `general_goods` 不等于无需认证或普通货 |
| 电气/电池 | 通过 | 覆盖锂电、内置/单独电池、无线等 |
| 危险/化学 | 通过 | 覆盖液体、粉末、危险品、易燃、腐蚀等 |
| 物理运输 | 通过 | 覆盖磁性、超限、散杂、RoRo、冷链等 |
| 人体/消费 | 通过 | 覆盖食品接触、皮肤接触、儿童、PPE、化妆品等 |
| 农业/生物 | 通过 | 覆盖食品、蔬果、花卉、茶叶、植物/动物材料、木包装等 |
| 战略/管制 | 通过 | 覆盖两用、加密、军民两用、制裁敏感等 |
| 大宗/指数 | 通过 | 覆盖钢材、粮食、矿产、能源和指数参考 |

## 6. 样本边界验收

| 样本 | 检查结果 | 说明 |
|---|---|---|
| Xing Heng 锂电 | 通过 | 美国目的国 Pack、锂电 Common Rule Pack、物流 Pack 只形成来源路径；不升级 UN38.3/SDS、起运港或最终税率 |
| UNIQLO 纺织 | 通过 | 美国纺织标签/税费 Pack 和中国出口 Pack 只形成来源路径；不升级实物标签合规、起运港或最终归类 |

## 7. eval / audit 验收

| 验收项 | 检查结果 | 说明 |
|---|---|---|
| Pack 被当证据可拦截 | 通过 | 设计 `market_pack_used_as_evidence` |
| Entry 未打开就成事实可拦截 | 通过 | 设计 `market_pack_entry_used_as_fact` |
| Pack 内混入事实可拦截 | 通过 | 设计 `market_pack_fact_leak` |
| 国家角色混淆可拦截 | 通过 | 设计 `market_pack_scope_mismatch`、`market_pack_origin_export_confusion` |
| 过期仍称最新可拦截 | 通过 | 设计 `market_pack_stale_without_recheck` |
| 内部路径泄露可拦截 | 通过 | 设计 `market_pack_internal_leak` |

## 8. 当前结论

| 项目 | 结论 |
|---|---|
| Slice 9 文档层验收 | 通过 |
| 是否写了代码 | 没有 |
| 是否创建真实国家 Source Pack | 没有 |
| 是否新增法规/税率/价格/物流事实 | 没有 |
| 推荐下一步 | 若继续不写代码：做 Slice 10 Source Pack 种子样例设计；若开始实现：先做 Code Slice A-C，即 schema、validator、首批 fixtures |
