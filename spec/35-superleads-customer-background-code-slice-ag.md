# Code Slice AG：单一客户背调工程资产补齐

## 1. 目标

单一客户背调是 Superleads 的第二条产品路线：

`一个指定对象 → 客户背调报告`

本 Slice 只补齐这条路线的工程资产和回归保护，不把它扩成批量客户开发，也不把它接入正式标准开发名单的强审核链路。

## 2. 用户心智

用户给的是一个公司、品牌、官网、域名、邮箱、地址、Candidate、截图、PDF、Excel、海关材料、Similarweb 材料或其它线索。用户想知道：

| 用户真正想问 | 报告应该回答 | 报告不能回答成 |
|---|---|---|
| 这是谁 | 当前锚点可能对应哪个主体，是否已核实 | 直接把同名公司、品牌站、客服站、母公司混成一个主体 |
| 它公开在做什么 | 已打开来源中看到的产品、渠道、业务角色 | 采购需求、采购量、采购预算、采购概率 |
| 和哪些公司/品牌有关 | 证据支持的主体、品牌、母公司、运营公司、工厂或关联方线索 | 未确认关系、自动合并主体 |
| 怎么联系 | 公开联系入口、转接入口、待确认联系人线索 | 猜邮箱、把 Founder/Owner/董事写成采购负责人 |
| 跟进前注意什么 | 身份冲突、历史信息、来源受限、材料待核实、下一步要问的问题 | 推荐客户、客户价值判断、推荐报价、谈判策略 |
| 信息从哪里来 | 来源、链接/材料、摘录/定位、观察时间、状态 | 搜索摘要变成事实、受限页面变成事实 |

## 3. 数据边界

### 3.1 允许的锚点

`background_research_target.anchors` 可以保留以下输入锚点：

- 公司名称；
- 品牌名；
- 官网或域名；
- 地址、电话、邮箱；
- Candidate ID；
- 用户材料 Source。

`unresolved` 和 `multiple_candidates` 状态下不得填写 `primary_subject_entity_id`，也不得填写 `resolution_observation_ids`。只有可检查来源支持同一主体时，才可进入 `resolved`。

### 3.2 允许的事实对象

单客背调复用通用证据骨架：

`Source → Observation → Claim → ClaimEvidence`

但只围绕当前指定对象及其证据支持的关联闭包渲染。额外批量候选池、无关客户、产品市场矩阵、正式名单对象不得进入用户交付。

### 3.3 禁止的正式链路污染

`customer_background_research` 不产生以下对象：

| 对象 | 为什么禁止 |
|---|---|
| `Assessment` | 背调不做客户分层，不判断推荐开发 |
| `ScopeDecision` | 背调不是当前开发方向资格判定 |
| `ReviewAttestation` | 背调轻验证不需要独立复核背书 |
| `DeliveryManifest` | 背调报告不进入正式名单交付 manifest |

如用户未来明确要求“把这个对象纳入标准开发名单”，必须新开一个独立请求，按批量/正式名单路径重新生成 Brief、Plan、ScopeDecision、Assessment、Review 和 Audit。

## 4. 用户可见输出合同

默认 Markdown 输出 7 张表：

1. 一句话先说清；
2. 客户一眼看懂；
3. 客户、品牌与关联方；
4. 公开业务信号与可沟通角度；
5. 怎么联系、先找谁；
6. 跟进前要注意什么；
7. 信息从哪里来。

输出应说人话：

- “是否具备继续核验基础”，不要写成“值不值得开发”；
- “公开信息不能证明当前采购需求或采购负责人”；
- “Founder / Owner / 董事只是公开职业或注册线索，不等于采购负责人”；
- “wholesale / contact / supplier portal 入口只是沟通入口，不等于采购意愿”；
- “搜索摘要、访问受限页面、用户材料只作线索或材料信号，不形成公司事实”。

空表不能显示一整行 `未提供 | 未提供 | 未提供`。应把缺口写成人能理解的说明，例如“主体尚未解析；暂无可展示的关联信息”。

## 5. 本 Slice 实现范围

| 项目 | 本 Slice 做法 |
|---|---|
| Codex / ChatGPT skill 入口 | 补 `skills/researching-customer-background/agents/openai.yaml` |
| 专属规格文档 | 新增本文件，冻结边界和用户可见合同 |
| 专属 eval runner | 新增 `evals/run_customer_background_research_evals.py` |
| 专属 cases / fixtures | 覆盖 resolved、unresolved、无关候选不外泄、搜索摘要不得解析主体、Assessment/Manifest 不得污染背调 |
| 用户可见 validator | 强化采购负责人 / 采购意愿误导短语阻断 |
| Markdown 表格 | 修复空行全是“未提供”的展示问题 |

## 6. 验收

最小验收命令：

```bash
python3 -m py_compile scripts/background_report.py scripts/export_superleads_markdown.py scripts/validate_research_graph.py scripts/validate_superleads_user_visible_output.py evals/run_customer_background_research_evals.py evals/run_evals.py
python3 evals/run_customer_background_research_evals.py --suite all
python3 evals/run_superleads_user_visible_output_evals.py --suite all
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite all
python3 evals/run_evals.py --suite deep
git diff --check
```
