# 美国柴油发电机后市场默认发现运行记录

- 日期：2026-07-19
- 宿主：Codex CLI（本地开发会话）
- 运行类型：默认发现能力与批量执行验证；不是客户交付物
- 业务语境：中性包装柴油发电机后市场配件；美国；维修商、零件渠道、经销商；排除原厂 OEM 与同行制造商；优先公开联系方式及贸易/China 公开信号。

## 本次能力与结果

`scripts/preflight_capabilities.py --format json` 返回 `search.web=unknown`、
`source.open=unknown`，最大无人工来源输出为 `research_plan_only`。本会话没有
原生搜索或网页打开结果可写入 SearchLog / Source / Observation。

确认本机存在 `curl 8.5.0` 后，尝试了一个只读公开 GET：

```text
https://www.google.com/search?q=diesel+generator+parts+distributor+USA
```

沙箱内请求被配置为使用本地代理，但该代理不可达（curl exit 7）。在受限
沙箱外以相同只读 GET 重试时，收到公开搜索站点的重定向后 20 秒超时、正文为
0 字节（curl exit 28）。没有正文摘录、定位信息或可验证来源，因此该尝试不能形成
SearchLog、Source 或 Observation。

实际唯一 Candidate 数为 **0**；实际打开来源数为 **0**；没有生成候选 JSON、CSV 或
XLSX。这个结果是本宿主的搜索/读取能力阻断，不是搜索收敛，也不代表美国市场没有
相关企业。

## Brief 与覆盖设计

默认发现 Brief 保留以下边界：

- 产品与应用：中性包装柴油发电机后市场配件，面向维修、备件、服务和渠道场景。
- 市场：美国，后续按全国、州与重点城市分层，而不宣称覆盖全部企业。
- 目标角色：发电机维修商、工业/发动机零件渠道商、发电机经销商。
- 排除：原厂 OEM、发电机或零件同行制造商；发现到时保留为
  `explicitly_excluded_or_unrelated`，不混入活跃候选池。
- 补充优先级：公开企业/部门联系入口，再按可访问公开来源补贸易记录、China 关联、
  货描或 HS 信号；不由贸易记录推断 China 采购或当前需求。

待有实际搜索能力时按至少两轮执行：

| 轮次 | 查询组与语言 | 地域 | 来源类别 | 处理目标 |
|---|---|---|---|---|
| 1 | `diesel generator repair`, `generator parts distributor`, `engine generator service`（英语，含 aftermarket / replacement / spare parts 变体） | 美国全国 + CA / TX / FL / IL / PA | 官网、地图/本地服务名录、行业目录 | 建立 Candidate、名称/域名/网址去重，记录实际查询与新增/重复数。 |
| 2 | `generator repair service`, `industrial engine parts`, `authorized generator dealer`（英语，加入城市和州变体） | 首轮覆盖缺口州与城市 | 展会/协会、授权网络、PDF/catalog、公开社媒公司页、公开贸易数据 | 补公开联系入口与信号状态；记录打开成功、403/404/415/429/JS 空壳和受限路径。 |
| 后续按需 | 同义产品、发动机品牌/应用词和贸易货描/HS 检索 | 由前两轮缺口决定 | 公开贸易记录、目录、官网 Contact/Supplier 页面 | 仅对可可靠归属主体补充贸易/China 信号；名称相似记录标 `identity_pending`。 |

## 实际运行统计

| 指标 | 实际值 | 说明 |
|---|---:|---|
| 实际成功搜索 | 0 | 没有可用 `search.web` 结果。 |
| 只读公开 GET 尝试 | 2 | 同一查询：沙箱代理失败 1 次，受限外重试超时 1 次。 |
| 实际打开成功 / 尝试 | 0 / 2 | 未取得正文，成功率 0%。 |
| HTTP/访问失败 | 代理不可达 1；302 后超时 1 | 不是企业或业务相关性结论。 |
| 403 / 404 / 415 / 429 / 登录墙 / JS 空壳 | 0 / 0 / 0 / 0 / 0 / 0 | 本次未取得能分类的目标网页响应。 |
| 去重 Candidate | 0 | 无来源结果，未建立候选池。 |
| 来源类别实际覆盖 | 0 | 官网、目录、协会/展会、贸易数据均未执行。 |
| 业务相关性分布 | 0 / 0 / 0 / 0 / 0 | `directly_related` / `possibly_related` / `explicitly_excluded_or_unrelated` / `identity_pending` / `insufficient_information` 均为 0。 |
| 五类公开信号状态 | 0 个 Candidate | 无 Candidate，未产生业务、官网联系、贸易、China、货描/HS 信号。 |
| 公开联系方式 | 0 | 没有正文来源，未提取或猜测邮箱、电话或联系人。 |
| 贸易/China 信号 | 0 | 没有可归属记录；未将未检索写成未发生。 |

## 抽查与构造摩擦

没有 Candidate，因而没有随机人工抽查的五个样本。默认图谱实际构造迭代为 0：在
没有可追溯公开搜索结果前，没有创建 SearchLog 或 Candidate，避免用失败的工具调用
伪造覆盖或来源。

本次首先被宿主搜索/读取能力阻断；默认 Candidate 的批量构造摩擦尚未被实际测量。最小
骨架只证明 1 Run、1 Brief、1 Plan、1 SearchLog、1 Candidate 可以通过 validate、
initial audit 与 initial export，且默认发现不需要 Entity、Observation、ContactClaim、
Claim、Assessment、Review、Audit 或 Manifest。它不证明 20+ Candidate 的批量记录、
去重、信号补充和导出成本已经得到验证。

## 未覆盖路径与下一轮

未覆盖：美国全国及州/城市查询、官网/联系页、地图/行业目录、协会/展会、授权网络、
PDF/catalog、公开社媒可见页、公开贸易记录与 China 信号路径。

下一轮应先恢复一条可记录的搜索或 `source.open` 路径，或提供用户授权可读的 URL/目录/
展会名单。只有实际返回安全公开 URL、只读读取记录、非空正文摘录和定位信息的结果才
创建 Source / Observation；搜索结果仍只作为 Candidate 定位。

满足该条件后，使用同一美国柴油发电机后市场任务完成至少 20 个去重 Candidate、至少
两轮查询/来源扩展的执行验证，并记录：Agent 构造迭代次数；Candidate / SearchLog /
Source / Observation / Contact 对象数量；JSON 行数或近似 token 成本；去重、相关性与五类
信号状态的错误/修正次数；导出成功率；以及来源成功率与受限分布。这是未完成的执行验证，
不承诺能找到 20 家企业，也不构成客户质量或采购概率结论。
