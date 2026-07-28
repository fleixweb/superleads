# 决策记录

## 2026-07-26：设立产品出海市场分析为独立路线

- 决策：新增“产品出海市场分析”，与批量客户开发、单一客户背调并列。
- 原因：产品市场、准入、税费、物流与出口要求不是客户发现或单客身份核验的子问题。
- 后果：不得自动产生客户名单、客户范围或市场进入建议。

## 2026-07-26：采用开放式产品属性与监管触发模型

- 决策：不以固定品类或消费品/电商逻辑建模；以可扩展属性矩阵触发条件化研究。
- 原因：国际贸易涉及普通货、危险品、两用物项、农产品、冷链、散杂货、滚装和重大件等大量不同世界。

## 2026-07-26：贸易地理前提必须拆分

- 决策：卖方/出口申报国、原产国、实际起运国/港、目的国/港分别记录；中国仅为用户可修改的默认出口申报国。
- 原因：税费、贸易救济、出口控制、路线和申报要求依赖的地理前提不同。

## 2026-07-26：报告只给客观参考

- 决策：报告以表格和信息矩阵呈现事实、来源、日期、条件、限制与待确认项；不输出是否进入市场、价格、客户或运输方式的价值判断。
- 原因：商业决策由用户承担，系统必须避免把不完整公开信号包装成建议。

## 2026-07-26：首批参数化验收样本

- 决策：以“越南原产锂电产品出口美国”与“中国原产纺织品出口美国”作为首批端到端验收路径。
- 原因：两条路径分别覆盖危险品/锂电运输与原产地税费、纺织成分/标签/税则细分等高风险差异；同时验证出口申报国、原产国、实际起运国和目的国的拆分。
- 边界：它们是参数化测试样本，不是越南、中国或美国的硬编码支持范围。缺少电池参数、纺织成分、HS 或起运信息时必须保留待确认状态。

## 2026-07-26：样本 Brief 先行

- 决策：在采集具体市场、法规、税费和物流信息之前，先为两个首批样本建立结构化输入 Brief。
- 原因：锂电和纺织品均不能只凭产品名称确定危险品路径、HS、税费、标签、出口要求或适用运输方式。
## 2026-07-26：首批验收样本具体化为 Xing Heng / UNIQLO

- 决策：将两条参数化验收路径落到两个真实公开样本：Xing Heng `48V20Ah` LiFePO4 电池包（Design No. `BAT001.02`）与 UNIQLO Men's Corduroy Overshirt（Product ID `470177`）。
- 原因：两个样本公开资料足以验证产品属性抽取、原产地证据等级、候选 HTSUS、认证/测试报告边界和表格化缺口展示。
- 边界：Xing Heng 的 Vietnam Register / QCVN 91 文件不得当作 UN38.3 或 SDS；UNIQLO 网页标签信息不得当作实物标签已核验；两者候选税号均不得当最终归类或最终税率。
## 2026-07-26：先冻结输出矩阵，再进入代码实现

- 决策：在编写 Skill、脚本或导出器前，先为产品出海市场分析新增 `spec/12-product-outbound-market-analysis-output-matrix-and-acceptance.md`。
- 原因：该模块风险不在“能不能生成文字”，而在能否把已核实、候选、待确认、未执行和不得输出项清楚分开。
- 后果：下一步实现应先做静态样本 Markdown / XLSX 矩阵，验证结构和负向断言，再接入真实搜索、法规、趋势和物流来源。
## 2026-07-26：Slice 1 先用静态样例验证交付形态

- 决策：先用已复核字段生成两份静态 Markdown 样例报告，验证表格化表达和负向断言。
- 原因：产品出海市场分析的第一风险是表达边界错误，先验证“怎么说”和“不能说什么”，再接入更多数据。
- 后果：下一步可以进入 XLSX/CSV 表头与状态枚举设计；联网趋势、价格和市场报告采集继续后置。
## 2026-07-26：Slice 2 冻结 XLSX/CSV 工作簿合同

- 决策：为产品出海市场分析新增 `spec/13-product-outbound-market-analysis-workbook-contract.md` 和 Slice 2 最小样例矩阵。
- 原因：外贸用户最终会在表格中复核和转交信息，必须先保证未知项不丢失、状态不空白、候选结论不升级。
- 后果：后续导出器或 Skill 实现必须保留 12 张业务工作表、状态枚举、空值规则和两个样本的关键缺口行。
## 2026-07-26：Slice 3 冻结证据边界校验规则

- 决策：新增 `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md`，把候选税号、测试报告、网页标签、原产地线索、运输方式、市场信号等证据边界写成可检查规则。
- 原因：产品出海市场分析最容易出错的地方是把“看到线索”升级为“已合规/最终税率/可运输/值得进入”。
- 后果：后续 Markdown、CSV、Skill 输出和 evals 都应按这些规则做负向校验；没有新增证据时必须降级到候选、待确认、未执行或来源受限。

## 2026-07-26：Slice 4 冻结 Skill 分工互证流程

- 决策：新增 `spec/15-product-outbound-market-analysis-skill-orchestration.md`，把六个 Skill 的输入、输出、证据卡、互证矩阵、打回规则、状态流转和交付门禁冻结为产品规格。
- 原因：该功能必须防止搜索黑箱、外部模型摘要和前序 Skill 摘要直接变成事实；不同事实域也必须互相挑错，而不是串行累积幻觉。
- 后果：后续实现应先落地证据卡和互证门禁，再接入真实市场、法规、税费和物流采集；冲突、缺口、未执行必须保留到最终报告和工作簿。

## 2026-07-26：Slice 5 冻结数据模型与 eval 夹具设计

- 决策：新增 `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md`，将产品出海市场分析建模为独立 `ProductMarketAnalysisGraph`，并冻结 EvidenceCard、状态流转、SkillHandoff、MatrixRow、Gap/Conflict、eval 分层、首批 pass/fail fixture 和错误码草案。
- 原因：产品市场分析不是客户发现或单客背调，不能强行塞进 Candidate / Claim / Assessment；同时必须在实现前明确哪些错误由 schema、validator、audit、export 或静态文本测试拦截。
- 后果：后续实现应按 schema、validator、audit/export、eval fixtures 分切片推进；搜索摘要、Skill 摘要、候选税号、网页标签、运输候选和未执行模块的错误升级都必须有回归测试。

## 2026-07-26：Slice 6 冻结实现前执行计划

- 决策：新增 `spec/17-product-outbound-market-analysis-implementation-plan.md`，把后续代码实现拆成 schema、validator、fixtures、audit、export、eval 集成、Skill 接入和真实来源接入八个步骤。
- 原因：如果直接接真实搜索、Google Trends、税费或物流来源，最容易先生成“看起来完整但边界错误”的报告；第一轮必须先做防错闭环。
- 后果：开始写代码前需用户再次明确同意；第一轮建议只做 Code Slice A-C 或 A-E，且 market suite 先独立运行，不影响现有客户开发/背调 eval。

## 2026-07-26：Slice 7 冻结 Skill 文案与用户入口设计

- 决策：新增 `spec/18-product-outbound-market-analysis-skill-copy-and-user-entry.md`，冻结产品出海市场分析的用户入口、触发词、非触发词、首轮回应、追问规则、未来 Skill 名称/description 和 `using-superleads` 路由草案。
- 原因：用户不会用内部 graph、EvidenceCard 或 eval 语言表达需求；入口文案必须符合外贸业务心智，同时避免把市场分析误路由成客户名单或把“值不值得做”写成价值判断。
- 后果：后续实现入口时应按该文案区分产品市场分析、批量客户开发和单客背调；首轮最多追问 3 个关键问题，缺资料时保留待确认而不是补猜。

## 2026-07-26：Slice 8 冻结真实来源采集策略

- 决策：新增 `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md`，冻结真实来源采集流程、能力门槛、来源优先级、Query Plan、Source/Observation 记录规则、“最新”口径、Source Pack 概念和两个样本来源路径。
- 原因：产品出海市场分析最终必须依赖可打开、可定位、可复核的公开/用户来源；但如果没有先定义来源策略，就容易把搜索摘要、平台价格、付费报告摘要或物流经验当成确定事实。
- 后果：后续真实采集必须先做 Brief 和能力预检；搜索只做线索，打开来源才形成 Observation；Source Pack 只能是“去哪里找”的目录，不是事实库。

## 2026-07-26：Slice 9 冻结 Source Pack 字段合同

- 决策：新增 `spec/20-product-outbound-market-analysis-source-pack-contract.md`，将 Source Pack 明确定义为来源入口目录，并冻结 SourcePack、SourceEntry、QueryTemplate、ObservationRequirement、PackRouteRule、状态枚举、产品触发标签和 eval / audit 错误码草案。
- 原因：Superleads 不能一个国家一个国家硬编码事实，也不能让 Pack 里的入口被误用成法规、税率、认证、物流或价格结论；必须先把“来源目录”和“事实证据”分层。
- 后果：后续 Source Pack 只能生成 Query Plan 和待打开入口；任何用户可见事实仍必须来自本次打开来源形成的 Observation / EvidenceCard，且 MatrixRow 不得直接引用 SourcePack 或 SourceEntry 作为事实来源。

## 2026-07-26：Slice 10 冻结 Source Pack 种子样例设计

- 决策：新增 `spec/21-product-outbound-market-analysis-source-pack-seed-samples.md`，用美国、中国、越南、跨太平洋物流、美国市场信号、锂电通用规则、纺织服装通用规则和产品原始来源设计第一批 Source Pack 种子样例。
- 原因：字段合同还比较抽象，需要用 Xing Heng 锂电和 UNIQLO 纺织两个样本验证 Pack 如何被 Brief 和产品标签触发，同时防止样例滑向国家事实库。
- 后果：种子样例只允许包含入口类型、查询槽位、观察要求、路由和边界；不得包含具体税率、认证结论、固定物流时效、趋势结论、价格区间或市场进入建议。

## 2026-07-26：Slice 11 冻结端到端运行剧本

- 决策：新增 `spec/22-product-outbound-market-analysis-end-to-end-runbook.md`，把 Brief、Source Pack、Query Plan、SearchLog / Source、Observation、EvidenceCard、MatrixRow 和 Markdown / XLSX 交付串成端到端人工运行剧本。
- 原因：前面已分别冻结输出、证据边界、Skill 分工、数据模型、Source Pack 和种子样例，但仍需要一份剧本验证真实运行时每一步怎么升级、打回、降级和对用户说人话。
- 后果：后续实现应按剧本中的三道门禁和状态流转落地；没有 Brief 冻结、没有打开来源、没有 EvidenceCard 边界或触发禁止升级时，不得生成确定结论。

## 2026-07-26：Slice 12 冻结 MVP 收口与实现前边界

- 决策：新增 `spec/23-product-outbound-market-analysis-mvp-freeze.md`，把 Slice 1-11 收口为 MVP-0 防错闭环、MVP-1 安全交付骨架、MVP-2 Skill 入口接入、MVP-3 真实来源采集四层，并冻结第一轮优先 Code Slice A-C。
- 原因：产品出海市场分析的最大风险不是“信息少”，而是把候选、摘要、Pack、网页标签、测试报告、趋势、价格或物流线索升级为事实结论；实现必须先拦错。
- 后果：下一步只有两条清晰路径：先提交 Slice 1-12 文档，或在用户明确同意后开始 Code Slice A-C；第一轮不接 Google Trends、关税 API、真实法规库或 Source Pack registry。

## 2026-07-27：Slice 13 冻结目标国原产地证明 / COO 要求判断

- 决策：新增 `spec/24-product-outbound-market-analysis-origin-proof-requirements.md`，并把 COO / proof of origin 从“用户是否提供资料”纠偏为目的国准入、清关、税费、贸易协定和贸易救济中的独立判断项。
- 原因：真实外贸业务里，用户是否已有 COO 不能决定目标国家/地区是否要求原产地证明；产品出海市场分析必须先按目标国官方/权威来源回答“是否需要、何时需要、接受什么文件”，再单独展示用户材料准备状态。
- 后果：既有产品合同、工作簿合同、证据边界、Skill 分工、真实来源采集策略、Source Pack 合同和端到端 runbook 已同步 `origin_proof_requirement` 语义；后续代码实现应新增 schema / validator / pass-fail fixture，阻断“用户没给 COO => 不需要 COO”“marking => COO”“优惠 proof => 所有进口都需要”等错误升级。

## 2026-07-27：Code Slice F 落地 COO / 原产地证明防错规则

- 决策：将 Slice 13 的 COO / proof of origin 规则落入 schema、validator、独立 market suite 和首批 pass/fail fixtures。
- 原因：真实外贸分析不能把“用户有没有 COO”当成目标国规则结论，也不能把 Made in、优惠原产地证明、用户文件或无来源判断升级为确定性清关结论。
- 后果：`origin_proof_requirement` 成为产品准入矩阵中的专门行类型；确定性 `required / conditionally_required / normally_not_required` 必须有官方/权威来源引用；无权威来源只能降级到 `unable_to_verify`。

## 2026-07-27：Code Slice G 落地产品出海市场分析 Skill 入口

- 决策：新增 `analyzing-product-outbound-market` Skill，并把 `using-superleads`、`route-map`、`user-intake` 更新为三路线并列入口：产品出海市场分析、批量客户开发、客户背调。
- 原因：A-F 已具备产品市场分析的数据和防错闭环，但用户真实入口仍可能被误路由成找客户或单客背调；必须先把入口和拆阶段规则固化。
- 后果：用户要趋势/价格/准入/税费/出口/物流/COO/外部因素时进入产品出海市场分析；用户要客户名单仍走批量开发；用户指定公司/域名背调仍走客户背调；“市场分析 + 找客户”先做市场分析，客户开发需另行确认。

## 2026-07-27：Code Slice H 优化产品出海市场分析导出展示

- 决策：产品出海市场分析的 CSV / Markdown 导出层使用人话字段名，并在 Markdown 顶部新增“先看贸易前提”“原产地证明 / COO 怎么看”“本轮未执行项”三个展示区。
- 原因：真实外贸用户需要先看目标销售国、出口申报国、原产国/制造来源和实际起运地是否分清；COO / proof of origin 也必须先看目标国规则，再看用户材料状态，不能让 enum 或内部字段名承担解释。
- 后果：底层 graph/schema 状态枚举保持不变；导出器只做展示映射，不新增事实、不补税率、不猜港口、不生成市场趋势或价格结论。

## 2026-07-27：Slice R 冻结 Superleads 产品内核与去 Superpowers 化校准

- 决策：Superpowers 只作为执行纪律参考；Superleads 的产品本体必须是外贸业务情报产品，围绕批量客户开发、单客背调、产品出海市场分析三条路线。
- 原因：继续沿 A-M 做内部证据链可能滑向通用工作流框架，偏离外贸用户可见价值；证据链应服务客户、公司、产品、国家、税费、物流、准入等真实外贸对象。
- 后果：暂缓 EvidenceCard 草稿队列等纯内部层建设；下一步优先做真实三路线用户可见样本，用业务交付校准产品方向。后续新 Slice 进入 active bet 前，必须回答它服务哪条业务路线、减少哪类真实误导、用户可见收益是什么。

## 2026-07-27：Slice S 用三条真实外贸样本校准用户可见交付

- 决策：用批量客户开发、单一客户背调、产品出海市场分析三条路线各跑一份用户可见样本，优先验收 Superleads 是否像外贸产品。
- 原因：Slice R 已指出继续做内部 EvidenceCard 队列有过度工程化风险；需要先用业务样本检查用户看到的表格、字段和边界。
- 后果：下一步优先把三条样本固化为输出合同 / 静态 eval，再决定是否恢复 Code Slice N。

## 2026-07-27：Slice T 冻结三条路线用户可见输出合同

- 决策：将批量客户开发、单一客户背调、产品出海市场分析三条路线的用户可见样本固化为 Markdown 输出合同和静态 eval。
- 原因：Slice S 只能证明人工样本方向正确；后续继续改代码时仍可能出现路线串线、内部对象名外露、价值判断或证据升级。
- 后果：新增用户可见输出 validator 和 3 pass / 3 fail 样本，并接入主 eval；后续新 Slice 必须先说明它改善哪条路线的哪张用户可见表，而不是只增加内部工作流层。

## 2026-07-28：Code Slice U 落地三路线 Markdown 交付器

- 决策：新增 `scripts/export_superleads_markdown.py`，把批量客户开发、单一客户背调、产品出海市场分析三条路线统一渲染为用户可见 Markdown，并在写出前运行 Slice T 用户可见输出合同校验。
- 原因：Slice T 已冻结“用户应该看到什么”，下一步必须把合同接到真实导出链路，避免用户继续看到内部 graph / EvidenceCard / SearchLog / eval 语言。
- 后果：三条路线现在都有可回归的 Markdown 交付入口；底层 audit 或用户可见校验不通过时不写文件。后续应优先把该命令接入 README、Skill 使用说明和实际使用入口，而不是继续做纯内部证据层。

## 2026-07-28：Code Slice V 把三路线 Markdown 交付写入 README / Skill / 常用命令

- 决策：不继续新增内部证据层，而是先把 `export_superleads_markdown.py` 的三路线用法写入 README、相关 Skill 说明、共享参考和 `docs/superleads-common-commands.md`。
- 原因：Code Slice U 已具备统一 Markdown 交付器；下一步真实收益是让用户和 Agent 知道批量客户开发、单一客户背调、产品出海市场分析分别怎么提需求、怎么导出、哪些话不能写。
- 后果：README 面向普通用户讲三条路线和样例 prompt；Skill 面向 Agent 明确 Markdown / CSV / XLSX 选择；常用命令面向本地流程记录最小命令。执行逻辑保持不变，不新增搜索、事实生成、推荐客户、采购概率、是否值得进入、推荐报价或最终税率判断。

## 2026-07-28：Slice W 纠偏认证 / 准入要求判断

- 决策：把产品出海市场分析中的“认证”从“用户是否提供证书”纠偏为“目标国家/地区对该产品可能要求哪些认证、测试、注册、标签、包装或准入文件”，并把目标国要求状态与用户材料状态分列。
- 原因：真实外贸用户往往并不知道需要什么证书；如果系统先等用户提供证书，会误导成材料核验工具，而不是产品出海市场准入分析工具。
- 后果：后续规格、Skill、导出和 eval 应新增 `certification_requirement` / `destination_requirement` 思路；用户没给证书不能推出不需要认证，用户给了证书也不能推出目标国认可或产品已合规。

## 2026-07-28：Code Slice X 落地认证 / 目的国准入要求防错规则

- 决策：将 Slice W 的认证/准入口径落入 schema、validator 和 market fixtures，新增 `certification_requirement` / `destination_requirement` 专门行结构。
- 原因：产品出海市场分析必须先帮用户判断目标市场可能要求哪些认证、测试、注册、标签、包装、进口许可或运输文件，而不是等用户先提供证书；用户材料状态不能反推目标国法规要求。
- 后果：确定性目标国认证/准入要求必须有官方或权威来源；用户没给证书、产品页证书入口、测试报告、渠道要求、用户证书都不能升级为“目标国不需要 / 已认证 / 法律强制 / 目标国认可 / 产品已合规 / 可清关”。

## 2026-07-28：Slice AA 校准 Superleads 为弱证据收敛系统

- 决策：接收外部诊断中成立的问题，将 Superleads 从强证据二值判定口径进一步校准为“弱证据收敛 + 可审计交付”系统。
- 原因：外贸公开信息大量处于多弱来源、来源受限、日期不一、渠道口径不同的中间状态；如果只用打开/没打开、权威/不权威两档，会挡掉有用线索或诱发字符串启发式误放行。
- 后果：先进入 Code Slice AA 修复用户交付污染和路由误判；后续 P1 再补多来源互证、时效降级、Authority registry、状态词压缩和中间档交付。新 Slice 必须说明服务哪条路线、改善哪张用户可见表、减少哪类外贸误导。

## 2026-07-28：Code Slice AB 落地多来源互证最小结构

- 决策：在产品出海市场分析图谱中新增可选 `corroboration_records`，用于表达“多个独立弱来源指向同一方向”，并在导出中显示为人话的多来源互证情况、互证边界和下一步核实。
- 原因：真实外贸公开信息大量处于弱证据中间态；1 个弱来源与 3 个独立弱来源一致不应被抹平成同一“待确认”，但多弱来源也不能升级为最终事实、推荐、最终税率或合规结论。
- 后果：market validator 现在会阻断单来源冒充多来源、同域名冒充独立来源、未打开来源互证、搜索摘要互证、冲突被隐藏，以及多弱来源把矩阵行升级为 `verified`。时效降级和 Authority registry 进入后续 Slice。
