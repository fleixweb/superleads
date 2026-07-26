# 产品出海市场分析：实现前执行计划（Slice 6）

本文件冻结 `产品出海市场分析` 从产品规格进入代码实现前的最小执行计划。它不是代码，不创建 schema、fixture、validator 或导出器；它只回答：**如果下一步开始写代码，应该先写什么、后写什么、每一步怎么验收、什么不能碰。**

一句话执行策略：**先做只会拦错的最小闭环，再做导出；先保护证据边界，再接真实搜索和法规数据。**

## 1. Slice 6 边界

| 项目 | 本轮决定 |
|---|---|
| 目标 | 把 Slice 5 的数据模型和 eval 夹具设计拆成可执行的最小代码切片 |
| 当前仍不做 | 不写 Python、不写 JSON Schema、不新增 fixture、不改 eval runner、不改导出器 |
| 后续第一轮实现目标 | 能用最小 `ProductMarketAnalysisGraph` fixture 跑 schema/validator/audit/export 的失败保护闭环 |
| 优先级 | 先防止错误交付，再追求市场信息完整 |
| 非目标 | 不接 Google Trends、不接关税 API、不做真实法规库、不做国家库、不改批量客户开发和单客背调主流程 |

## 2. 实现总原则

| 原则 | 说明 |
|---|---|
| 先验证边界，不先做内容生成 | 第一轮代码只要能拦住错误升级，就是有价值的闭环 |
| 独立模块，不污染客户开发图谱 | 产品市场分析使用独立 schema / validator / audit / export，不把数据塞进 Candidate / Claim / Assessment |
| 复用来源系统，不复用客户结论系统 | 可复用 Source / Observation、安全 URL、导出隐藏内部 ID 的习惯；不复用客户 disposition |
| fixture 先行 | 每条关键禁止升级规则都必须有 fail fixture；每个允许边界都有 pass fixture |
| 导出只搬运 MatrixRow | 导出器不自己推理税率、合规、路线、价格；只把已准备好的行安全输出 |
| 不联网也能验收 | 第一轮全靠静态 fixture 和已确认样本字段，不依赖实时搜索能力 |

## 3. 推荐实现顺序

| 顺序 | 代码切片 | 目标 | 完成标准 |
|---:|---|---|---|
| 1 | Schema 骨架 | 建立 `ProductMarketAnalysisGraph` 最小结构 | 两个 pass fixture 能通过 schema；明显缺字段 fixture 失败 |
| 2 | 语义 validator | 检查状态、来源、禁止升级、Brief 过期 | 核心 fail fixture 返回预期错误码 |
| 3 | eval fixture 与 case 配置 | 把 pass/fail 样本纳入可重复测试 | `product_market_analysis_cases` 可独立运行 |
| 4 | audit 最小门禁 | 判断能否交付：通过、需修正、缺用户资料 | 错误升级必须阻断交付 |
| 5 | CSV/Markdown 最小导出 | 从 MatrixRow 输出 12 张中文表/Markdown 分组 | 不丢未知项，不泄露内部 ID |
| 6 | 集成到统一 eval | 接入现有 `evals/run_evals.py` 或单独 suite | 不影响现有 default/deep/all 结果 |
| 7 | Skill 文档/路由接入 | 明确入口、产物和调用顺序 | 不改变批量客户开发、单客背调现有行为 |
| 8 | 真实来源采集接入 | 再接趋势、价格、法规、税费、物流来源 | 每条新增事实都有 EvidenceCard、来源、日期、状态 |

第一轮建议只做 1-5；第 6 步是否并入统一 eval，可以等独立命令稳定后再做。

## 4. 最小代码切片定义

### 4.1 Code Slice A：Schema 骨架

| 项目 | 计划 |
|---|---|
| 新增文件 | `shared/schemas/product-market-analysis.schema.json` |
| 只包含 | 顶层图谱、runs、briefs、products、trade_premises、attributes、sources、observations、evidence_cards、matrix_rows、gaps、conflicts、handoffs、state_transitions |
| 暂不包含 | 真实市场数据字段全集、国家库、法规库、价格指数接入 |
| 验收 | 最小 Xing Heng / UNIQLO pass fixture 结构通过；缺状态、缺 Brief、缺 EvidenceCard ID 的 fixture 失败 |
| 风险 | schema 太大导致第一轮写不完；解决：只做 Slice 5 必需字段 |

### 4.2 Code Slice B：语义 validator

| 项目 | 计划 |
|---|---|
| 新增文件 | `scripts/validate_product_market_analysis.py` |
| 输入 | `market_*.json` fixture 或未来真实 graph |
| 输出 | JSON 格式校验结果，包含 `ok`、`issue_count`、`issues[].code` |
| 必查规则 | 搜索摘要不能 verified、Skill 摘要不能当 source、候选税号不能最终税率、网页标签不能实物合规、QCVN 不能 UN38.3、未执行不能有结论、内部路径不能导出 |
| 验收 | 所有首批 fail fixture 返回对应错误码；pass fixture 无 critical/major |
| 非目标 | 不判断真实税率正确与否，不联网查法规 |

### 4.3 Code Slice C：eval fixtures 与 case 配置

| 项目 | 计划 |
|---|---|
| 新增文件 | `evals/cases/product_market_analysis_cases.json` |
| 新增 fixture | `evals/fixtures/market_pass_*.json`、`evals/fixtures/market_fail_*.json` |
| 第一批数量 | 建议 6 个 pass + 10 个 fail，不必一次写完 Slice 5 全量清单 |
| 通过样本 | Xing Heng 最小边界、UNIQLO 最小边界、未执行保留、搜索候选、派生 Wh、冲突保留 |
| 失败样本 | 搜索摘要升级、Skill 摘要当来源、QCVN->UN38.3、候选 HTSUS->最终税率、网页标签->实物合规、Google Trends->销量、物流最佳/承诺、起运港猜测、未执行行丢失、内部路径泄露 |
| 验收 | 独立 market eval 命令全绿；失败样本不是 schema 偶然失败，而是命中预期语义错误码 |

### 4.4 Code Slice D：audit 最小门禁

| 项目 | 计划 |
|---|---|
| 新增文件 | `scripts/audit_product_market_analysis.py` |
| 输入 | 已通过 schema 的 ProductMarketAnalysisGraph |
| 输出 | `delivery_status`：`ready_with_limitations`、`blocked_needs_input`、`needs_correction` |
| 阻断条件 | critical 错误、禁止升级、缺矩阵状态、内部信息泄露、Brief 过期仍交付 |
| 可交付但提示 | 未执行模块、待技术资料确认、待业务确认、待专业确认、来源受限 |
| 验收 | 错误升级 fail fixture audit 失败；Xing Heng/UNIQLO 最小样本可 `ready_with_limitations` |

### 4.5 Code Slice E：CSV/Markdown 最小导出

| 项目 | 计划 |
|---|---|
| 新增文件 | `scripts/export_product_market_workbook.py` 或扩展导出框架的独立入口 |
| 输出 | 12 张 CSV；可选单份 Markdown 报告 |
| 数据来源 | 只读取 `matrix_rows.user_visible_cells`、Gap/Conflict/Source 的用户安全字段 |
| 禁止 | 导出器不生成新事实，不补税率，不猜港口，不把 ID/哈希/本地路径写给用户 |
| 验收 | 12 张表齐全；未执行行保留；中文表名；无内部对象名；Xing Heng/UNIQLO 关键缺口可见 |

## 5. 第一轮最小 fixture 套餐

### 5.1 推荐第一批 pass

| 文件名 | 为什么第一批需要 |
|---|---|
| `market_pass_xingheng_minimum_boundary.json` | 验证锂电、高 Wh、UN38.3/SDS 缺口、候选税号、起运港待确认 |
| `market_pass_uniqlo_minimum_boundary.json` | 验证纺织网页信息、实物标签缺口、候选 HTSUS、BOM/克重待确认 |
| `market_pass_search_summary_candidate_only.json` | 验证搜索摘要可以保留为线索但不支持事实 |
| `market_pass_not_executed_modules_retained.json` | 验证未执行模块不丢行 |
| `market_pass_derived_wh_with_formula.json` | 验证派生计算必须有输入卡和公式 |
| `market_pass_conflict_preserved.json` | 验证冲突保留，不强行下结论 |

### 5.2 推荐第一批 fail

| 文件名 | 必须拦住的错误 |
|---|---|
| `market_fail_search_summary_as_verified.json` | 搜索摘要直接写成已核实 |
| `market_fail_skill_summary_as_source.json` | 前序 Skill 摘要当来源 |
| `market_fail_qcvn_as_un38_3.json` | QCVN/Vietnam Register 升级 UN38.3 |
| `market_fail_candidate_htsus_as_final_rate.json` | 候选税号/基础税率升级最终税率 |
| `market_fail_web_label_as_physical_compliance.json` | 网页标签升级实物标签合规 |
| `market_fail_google_trends_as_sales.json` | Google Trends 写成销量/采购需求 |
| `market_fail_logistics_best_or_committed.json` | 运输候选写成最佳方式或承诺交期 |
| `market_fail_departure_port_guessed.json` | 起运港未知却默认常用港口 |
| `market_fail_not_executed_rows_missing.json` | 未执行模块在矩阵中消失 |
| `market_fail_source_local_path_or_hash_leak.json` | 用户可见字段泄露本地路径、哈希或内部 ID |

## 6. 错误码第一批冻结

| 错误码 | 严重度 | 触发条件 |
|---|---|---|
| `market_search_summary_promoted` | critical | 搜索结果/摘要成为 `verified` 或用户可见事实结论 |
| `market_skill_summary_as_source` | critical | source_locator 指向 Skill 摘要、模型总结、无原始来源 |
| `market_qcvn_promoted_to_un38_3` | critical | QCVN/Vietnam Register 被当作 UN38.3/SDS |
| `market_candidate_hs_promoted_to_final` | critical | 候选 HS/HTS 或基础税率被写成最终税率/税额 |
| `market_web_label_promoted_to_physical_compliance` | critical | 网页标签信息被写成实物标签已合规 |
| `market_google_trends_sales_claim` | major | Google Trends 被写成销量、GMV、采购需求或市场份额 |
| `market_logistics_commitment_or_best` | major | 运输方式被写成最佳方式、承诺交期或一定可走 |
| `market_guess_departure_port` | major | 起运港/机场未知却填默认港口 |
| `market_not_executed_row_missing` | major | 用户请求/合同要求的未执行模块没有矩阵行 |
| `market_delivery_internal_leak` | critical | 用户可见导出出现本地路径、哈希、内部对象 ID、带 token URL |
| `market_matrix_row_missing_status` | major | 任意用户可见矩阵行缺状态 |
| `market_brief_stale_result_delivered` | critical | Brief 改版后旧 Skill 结果仍作为当前结论交付 |

## 7. 第一轮不要做的事

| 不做 | 原因 |
|---|---|
| 不接 Google Trends 实时采集 | 先保证 Trends 不会被误写成销量 |
| 不接关税 API 或国家法规库 | 先保证候选税号不被写成最终税率 |
| 不做国家逐一规则硬编码 | 本模块应按事实域和来源路由扩展 |
| 不生成客户名单或客户推荐 | 这是批量客户开发路线的职责 |
| 不让导出器推理新事实 | 导出器只搬运已审核矩阵行 |
| 不合并进现有 ResearchGraph 主 schema | 避免污染客户开发/背调现有审计链路 |
| 不一次性写完全部 fixture | 第一轮先覆盖最高风险错误，后续增量补齐 |

## 8. 与现有测试的关系

| 现有套件 | 第一轮处理 |
|---|---|
| `default` | 不应受影响；产品市场分析不进入默认客户发现 |
| `deep` | 不应受影响；产品市场分析有独立 fixture 与 validator |
| `all` | 初期可以不并入，独立稳定后再并入 |
| 新增 market suite | 建议先做独立命令或 case 文件，避免破坏现有 662/662 稳定状态 |

推荐验收顺序：

1. 先跑现有 `default/deep/all`，确认无回归；
2. 再跑独立 `product_market_analysis` 测试；
3. 最后再考虑把 market suite 纳入 `all`。

## 9. 实现后的用户可见最小成果

第一轮代码完成后，用户不一定能得到完整真实市场报告，但应该能得到一个安全的最小交付：

| 用户看到 | 说明 |
|---|---|
| 两份样本 Markdown/CSV | Xing Heng / UNIQLO 的边界正确、缺口清楚 |
| 12 张中文业务表 | 未执行和待确认不丢失 |
| 明确缺口清单 | SDS、UN38.3、BOM、标签、起运港、最终 HTSUS 等 |
| 来源和限制 | 只展示安全公开来源和用户可理解来源名 |
| 无价值判断 | 不出现建议进入、推荐价格、最佳运输方式 |

## 10. 开始写代码前的检查清单

| 检查项 | 必须满足 |
|---|---|
| 用户明确同意写代码 | 是 |
| 当前未提交变更是否需要先提交或隔离 | 需确认，当前仓库已有大量未跟踪文档和无关目录 |
| 是否保留 `tmp/stage5_chillys/` | 必须保留 |
| 是否避免处理无关未跟踪目录 | 必须避免 `skillhub-package/`、社交卡目录等无关内容 |
| 是否先跑现有 eval | 建议实现前记录 baseline |
| 是否先建最小 fixture 而不是接真实搜索 | 是 |

## 11. Slice 6 完成标准

| 编号 | 完成标准 |
|---|---|
| C-01 | 已把实现拆成 schema、validator、fixture、audit、export、eval 集成、Skill 接入、真实来源接入八个步骤 |
| C-02 | 已明确第一轮只做最小防错闭环，不接真实市场数据 |
| C-03 | 已列出第一批 pass/fail fixture 和错误码 |
| C-04 | 已明确不影响现有 default/deep/all 套件和客户开发/单客背调路线 |
| C-05 | 已明确开始写代码前需要用户再次确认 |
