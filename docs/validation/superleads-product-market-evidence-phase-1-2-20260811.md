# Superleads Product-Market Evidence Compiler Phase 1.2 Validation

日期：2026-08-11

## 范围

本轮只降低产品出海市场分析中重复 JSON 的手工录入成本。没有新增正式
Graph schema 字段、validator、错误码、route、delivery status 或搜索能力。

新增编译器输入：

- `authority_notes`：将人工明确、绑定已打开 Observation 的 Authority 断言展开为既有四类 Authority 对象；默认 `candidate_needs_check` / `not_reviewed`，不从域名、机构名或 URL 自动识别官方来源，也不升级状态。
- `matrix_row_templates`：复用既有行结构；证据笔记用 `target_row_ids` 引用模板，同时保留 `row` / `rows` 兼容。
- `authority_note_ids`：证据笔记的紧凑 AuthorityVerificationRecord 引用，输出仍只写既有 `authority_verification_record_ids`。

## 冻结基线

独立盲测目录：`/tmp/superleads-uat-electric-kettle-blind-20260810T144151Z`。

| 指标 | 基线 |
|---|---:|
| 场景 | 220–240 V / 1500 W 普通电水壶，中国出口美国 |
| 耗时 | 2,990 秒 |
| 手工 JSON | base graph 1,389 行 + compact notes 622 行 |
| opened Source / Observation | 8 / 8 |
| EvidenceCard | 8 |
| MatrixRow | 16 |
| Gap | 12 |
| validator / audit / export / claimed path | 全部通过 |

本轮没有在具备 Web Search 的新环境中重新计时，因此不声称已经降低百分比。

## 离线等价回放

使用同一盲测的 `base_graph.json` 与 `compact_notes.json`，重新运行 Phase 1.2
编译器，输出：

- 8 EvidenceCards、16 MatrixRows、2 ProductAttributes；
- validator `issue_count=0`；
- audit `passed` / `ready_with_limitations`；
- Markdown 导出 16 张表；
- claimed-path 检查 `ok=true` / `issue_count=0`；
- 既有用户属性和证据边界保持不变。

这是离线回放，不是新的搜索 UAT。

## 验证结果

| 检查 | 结果 |
|---|---:|
| `tests/test_product_market_evidence_compiler.py` | 7/7 |
| 产品市场 eval | 75/75 |
| 插件分发 eval | 6/6 |
| 主 default suite | 126/126 |
| 主 all suite | 719/719 |
| 主 deep suite | 676/676 |
| Skill quick validation | passed |
| 插件缓存 | `0.1.11` 已安装并同步 |

## 新一轮真实 UAT 状态

当前会话执行 `python3 scripts/preflight_capabilities.py --format json` 的结果为：

- `search.web=unknown`
- `source.open=unknown`
- `formal_research_status=blocked`
- 缺少错误码：`formal_research_search_capability_missing`、`formal_research_source_open_capability_missing`

因此没有执行新的联网搜索或来源打开，没有生成新的正式市场报告。下一次具备
当前 Run 的搜索和来源打开能力时，必须重新执行同一电水壶场景，记录手工行数和
耗时，再与上述冻结基线比较。

## 2026-08-11 独立真实 UAT 复测

随后在具备 Codex 原生 Web Search 的新 Run 中完成独立复测：

- 目录：`/tmp/superleads-uat-electric-kettle-phase-1-2-20260811T050529Z`
- `search.web` / `source.open`：available；`formal_research_status=ready`
- 耗时：1504 秒；搜索调用 7 次、查询 22 条
- 成功打开 13 个来源并形成 13 条 Observation；4 个受限、1 个无可提取结果
- base graph 443 行；compact notes 816 行；手工输入 1259 行
- EvidenceCard 13；MatrixRow 17；Gap 13；Authority notes 6
- validator、audit、Markdown、workbook、用户可见和 claimed-path 全部通过
- 相对冻结基线：耗时减少 1486 秒、手工输入减少 752 行；覆盖量同时增加

本轮证明 Phase 1.2 在该真实场景上确实降低了重复录入和总耗时。该结论仅适用于
当前电水壶/美国场景，不代表所有国家或产品都有相同降幅。下一阶段应验证报告的
事实收敛与风险优先级表达，而不是继续增加编译器规则或国家 Source Pack。
