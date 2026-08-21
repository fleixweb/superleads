# Slice AA：Superleads 弱证据外贸场景校准与 P0 修复优先级

日期：2026-07-28

## 1. 本 Slice 要解决什么

本 Slice 接收并复核外部诊断中指出的方向性问题：Superleads 的纪律已经比多数同类项目更稳，但仍有明显的 `Superpowers` 残留——把强证据、二值化、严门禁的结构，套到了一个天然弱证据的外贸公开信息场景。

一句话新校准：

> Superleads 不是强证据二值判定系统，而是弱证据收敛 + 可审计交付系统。

外贸公开信息的真实世界通常不是“已证实 / 未证实”两档，而是：

| 真实外贸信息状态 | 用户真正需要看到什么 |
|---|---|
| 多个弱来源指向同一方向 | 这是“多来源一致线索”，但仍不是最终事实 |
| 一个官方来源打开但日期较旧 | 可引用，但需要显示复核日期和时效风险 |
| 平台、电商、B2B 公开价格存在 | 只能作为线上参考，不是成交价、批发价或推荐报价 |
| 工厂页、新闻、目录提到某国 | 只能形成制造/业务线索，不能自动变 SKU 原产或起运港 |
| 目标国法规/认证/关税未打开 | 必须停在待权威来源确认，不能由常识或用户材料反推 |
| 客户网站有联系入口 | 只能作为联系入口，不等于采购需求、采购负责人或采购概率 |

因此，后续 Superleads 的优先方向应从“更多内部门禁”转向“让弱证据在用户可见报告里有层次、有边界、有来源、有时效”。

## 2. 已确认成立的问题

以下问题经本地文件和脚本快速复核后，判断成立或高度成立。

| 编号 | 问题 | 本地依据 | 影响 |
|---|---|---|---|
| AA-01 | 缺少多来源互证一等对象 | `corroboration` 仅在设计文字中零散出现，现有 graph/validator 仍以单来源二值为主 | 多个弱来源一致的有用信息无法表达 |
| AA-02 | 状态词过多但用户区分力有限 | 市场 schema / label / route 状态并行，用户可见样本只需要少数“候选/待确认/未执行/来源受限/已核实”等 | 填写成本高，易把 enum 当产品价值 |
| AA-03 | 缺少时效降级 | `meta/open-questions.md` 仍把法规与关税复核周期列为开放问题；validator 未做 staleness 门 | 去年/前年法规、关税、物流信息可能被当成当前信息 |
| AA-04 | 认证权威性门目前过粗 | `CERT_AUTHORITY_MARKERS` 仍是 substring 级启发式 | 第三方博客可因含 regulation/official 等词被误判；真实官方域名也可能漏掉 |
| AA-05 | 产品市场导出存在展示补行风险 | `export_superleads_markdown.py` 会在缺少 Google Trends / COO / 海运拼箱 / 国际快递 / 待补材料清单时补样板段 | 交付层可能生成与货物无关的“待确认行”，违背不新增事实的口径 |
| AA-06 | 用户可见 validator 纯子串误报 | `validate_superleads_user_visible_output.py` 对“值得进入/推荐客户/采购概率/graph/eval”等做全文子串扫描 | 合规的否定句、来源名、普通英文词会被误报 |
| AA-07 | Markdown 交付器无边界替换 | `INTERNAL_REPLACEMENTS` 对 `graph` / `eval` 等做普通 `replace` | `The Telegraph`、`Photograph`、`paragraph`、`evaluation` 这类正文会被改坏 |
| AA-08 | 路由器不够贴近真实外贸表达 | `CUSTOMER_MARKERS` 词表缺经销商/批发商/零售商/代理商/连锁等；`市场/包装` substring 容易误伤 | 批量客户开发和产品市场分析入口会走错 |
| AA-09 | 单一客户背调工程资产偏少 | 背调 Skill 用户化较好，但专属 spec/validator/eval 较少，且缺 `agents/openai.yaml` | 用户最常用路线之一缺工程回归保护 |
| AA-10 | 主 `all` 与 market suite 关系不清 | `evals/run_evals.py --suite all` 不调用 `run_product_market_analysis_evals.py` | 数字容易被误读为已覆盖全部市场路线 |

## 3. 不是要推翻，而是要换产品内核

这次校准不是否定此前工作。此前 Slice R/S/T/U/X 的价值在于：

- 三条路线已经分清；
- 用户可见表格化方向正确；
- 不做价值判断、不造客户名单、不把用户材料反推法规要求的纪律是对的；
- 产品出海市场分析的证据边界和 COO / 认证纠偏已经打下基础。

真正需要换掉的是底层思维：

| 旧倾向：Superpowers 残留 | 新方向：Superleads 外贸弱证据模型 |
|---|---|
| 打开 / 没打开 | 打开状态 + 来源类型 + 来源时效 + 可支持字段 |
| 权威 / 不权威 | 官方 / 准官方 / 原始商业来源 / 平台来源 / 行业报告 / 搜索线索，分层展示 |
| 单一来源决定状态 | 多来源一致、冲突、孤立线索、来源受限并列展示 |
| 未达强门槛就挡掉 | 降级为候选、待确认、来源受限、未执行，让用户知道还有什么线索 |
| “完整核查版”式强审计 | 外贸可用的中间档：发现候选池 / 初筛客户名单 / 背调摘要 / 市场矩阵 |
| 用户看内部对象 | 用户看人话表格、来源、日期、条件、不能推出什么 |

## 4. P0：先修会污染用户交付的问题

P0 的定义：会直接影响用户在 Markdown / CSV / ChatGPT app / Codex 中看到的内容，或导致用户入口明显走错。

| 优先级 | 修复项 | 文件 | 验收样例 |
|---|---|---|---|
| P0-1 | 替换内部术语时加边界，不破坏普通正文 | `scripts/export_superleads_markdown.py` | `The Telegraph` / `Photograph` / `paragraph 3` / `evaluation` 不被改写 |
| P0-2 | 用户可见 validator 支持否定语境豁免 | `scripts/validate_superleads_user_visible_output.py` | “不判断是否值得进入”“不做推荐客户排序，也不给采购概率”应通过 |
| P0-3 | 路由器补真实外贸客户词与合规问句 | `scripts/route_superleads_intake.py` | 经销商/批发商/零售商/代理商/连锁进入批量客户开发；SDS/UN38.3/认证/关税/物流要求进入市场分析 |
| P0-4 | 停止交付器为了过校验而注水 | `scripts/export_superleads_markdown.py`、用户可见合同 | 缺少某运输方式时不自动补“海运拼箱/国际快递”样板表；应显示“该模块未执行/未形成矩阵行” |
| P0-5 | 明确主 suite 与 market suite 的覆盖关系 | `TASKS.md`、验证记录 | `run_evals.py --suite all` 与 market suite 分开列，不把 677/677 写成全部路线全覆盖 |

## 5. P1：补弱证据行业的一等结构

| 优先级 | 结构 | 目标 | 第一版不做什么 |
|---|---|---|---|
| P1-1 | `CorroborationRecord` / 多来源一致线索 | 表达 2-3 个独立弱来源指向同一结论，但仍保留候选/待确认边界 | 不把多弱来源自动升级为最终事实 |
| P1-2 | Source freshness / staleness | 按事实域设置复核周期：法规、关税、认证、物流、市场价格、公司信息不同周期 | 不在无打开来源时编造“最新” |
| P1-3 | Authority registry | 用 Source Pack / 域名 / 机构类型判断官方或权威来源 | 不再用 regulation/official/customs substring 放行确定结论 |
| P1-4 | 状态词压缩与映射 | 将内部状态映射到用户真正看得懂的 10 来个状态 | 不让用户看到 30+ enum |
| P1-5 | 中间档交付 | 真正实现“初筛客户名单”或明确删除死枚举 | 不把候选池直接跳到标准开发名单 |

## 6. P2：工程资产补齐

| 模块 | 工程债 | 建议处理 |
|---|---|---|
| 单一客户背调 | 缺专属 spec、validator、更多 fixture、`skills/researching-customer-background/agents/openai.yaml` | 做背调最小规格与回归夹具 |
| 批量客户开发 | 相比产品市场分析缺内核复盘与真实路由覆盖 | 做 Bulk Slice R，同步弱证据候选池原则 |
| Source Pack registry | 现有 registry 壳子多，真实 authority 信息少 | 后续按国家/事实域补权威入口，但仍不是事实库 |
| `full_review_package` 等枚举 | 本地部署不可达或价值不明 | 删除、降级说明，或实现明确业务收益 |

## 7. Code Slice AA 验收清单

本 Slice 文档落地后，进入 Code Slice AA。最小验收：

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AA-EVAL-01 | 替换污染 pass | 导出 Markdown 中 `The Telegraph`、`Photograph`、`paragraph 3`、`evaluation` 原样保留 |
| AA-EVAL-02 | 内部术语仍能替换 | 独立词 `graph` / `eval` / `EvidenceCard` 等仍不外露 |
| AA-EVAL-03 | 否定句 pass | “不判断是否值得进入”“不做推荐客户排序，也不给采购概率”通过用户可见校验 |
| AA-EVAL-04 | 正向违规 fail | “建议进入”“推荐客户”“采购概率 80%”仍失败 |
| AA-EVAL-05 | 路由 pass | “柴油发电机配件经销商”“户外家具零售连锁”进入批量客户开发 |
| AA-EVAL-06 | 市场合规问句 pass | “客户问我要 SDS 和 UN38.3，美国那边到底要不要”进入产品出海市场分析 |
| AA-EVAL-07 | Slice S bulk 样本入口 | “中性包装柴油发电机后市场配件，美国，维修商/零件渠道/经销商”进入批量客户开发，不被“市场/包装”误伤 |
| AA-EVAL-08 | 回归 | 用户可见输出、Markdown delivery、route、default/deep/all 回归通过；market suite 仍单独列出 |

## 8. 非目标

本 Slice AA 不直接解决以下问题：

- 不接入真实 Google Trends / 关税 API / 法规库；
- 不联网补真实国家权威来源；
- 不把 `CorroborationRecord` 直接写进 schema；
- 不重构所有状态枚举；
- 不补单一客户背调全部资产；
- 不把用户商业判断变成模型推荐。

这些进入后续 P1/P2 Slice。

## 9. 决策

从本 Slice 起，Superleads 后续所有新代码切片都应回答四个问题：

1. 它服务三条路线中的哪一条？
2. 它改善哪张用户可见表？
3. 它减少哪类真实外贸误导？
4. 它是否尊重弱证据收敛，而不是强行二值判定？

答不出来的内部工程切片暂缓。
