# Slice W：目的国认证 / 准入要求判断纠偏验证记录

日期：2026-07-28

## 本次要纠正的问题

产品出海市场分析里的“认证”不能被理解成“用户先提供证书，系统再判断证书是否可用”。这只是真实业务中的材料匹配子场景。

正确口径是：用户可能完全不知道目标市场需要什么证书、测试、注册、标签、包装或准入文件，Superleads 应先基于产品属性和目标国家/地区分析“目标市场可能要求什么”，再单独展示“用户现在有没有对应材料、材料是否匹配”。

## 本次新增 / 更新

| 文件 | 变化 |
|---|---|
| `spec/29-product-outbound-market-analysis-certification-requirement-calibration.md` | 新增 Slice W 规格，冻结认证/测试/注册/标签的两层对象、状态、字段、来源优先级和禁止升级规则 |
| `spec/10-product-outbound-market-analysis-contract.md` | 同步“认证不是等待用户证书”的产品合同口径 |
| `spec/12-product-outbound-market-analysis-output-matrix-and-acceptance.md` | 同步准入矩阵必须分列目标国要求状态和用户材料状态 |
| `spec/13-product-outbound-market-analysis-workbook-contract.md` | 同步目标国认证要求状态与用户材料状态分列表达 |
| `spec/14-product-outbound-market-analysis-evidence-boundary-rules.md` | 增加目标国认证要求与用户证书状态不得混写的证据边界 |
| `spec/15-product-outbound-market-analysis-skill-orchestration.md` | 同步 Skill C / F 的准入职责与互证规则 |
| `spec/16-product-outbound-market-analysis-data-model-and-eval-fixtures.md` | 预留 `certification_requirement` / `destination_requirement` 行类型和禁止流转 |
| `spec/19-product-outbound-market-analysis-real-source-collection-strategy.md` | 同步认证/测试/注册/标签来源采集策略 |
| `spec/20-product-outbound-market-analysis-source-pack-contract.md` | 同步认证准入 Source Pack / query group 口径 |
| `shared/references/product-outbound-market-intake.md` | 同步用户入口话术：没有证书也能先分析目标市场要求 |
| `shared/references/output-schema.md` / `shared/references/route-map.md` | 同步三路线导出与产品市场路由口径 |
| `skills/analyzing-product-outbound-market/SKILL.md` / `skills/using-superleads/SKILL.md` | 同步 Skill 使用说明和硬约束 |
| `README.md` / `README.zh-CN.md` / `README.en.md` / `docs/superleads-common-commands.md` | 同步用户入口示例和常见口径 |

## 纠偏后的人话模型

| 旧误解 | 新口径 |
|---|---|
| 用户要先给证书，系统才分析认证 | 用户可以不知道需要什么，系统先按目标国和产品属性列“可能需要查什么” |
| 用户没给证书，所以该项无法分析 | 用户没给证书只影响材料状态；目标国要求仍要尽量查官方/权威来源 |
| 用户给了 CE/FCC/UL/FDA 等文件，所以产品已合规 | 用户文件要核对型号、标准、国家、日期、签发机构、适用范围；不能直接写目标国认可 |
| 认证就是一张证书 | 可能是认证、测试报告、注册、DoC、标签、包装、EPR、进口许可、检疫、SDS、UN38.3 或渠道要求 |
| 渠道要求就是法规要求 | 平台/零售商/客户要求必须单列，不能写成海关或法律强制 |

## 验收断言

| 断言 | 结果 |
|---|---|
| “认证”默认解释为目标国准入要求判断 | 通过 |
| 用户证书状态与目标国要求状态分列 | 通过 |
| 没有用户证书时仍允许输出目标市场待查路径 | 通过 |
| 用户提供证书不能升级为目标国已认可或产品已合规 | 通过 |
| 产品页证书入口不能升级为已具备认证 | 通过 |
| 官方/权威来源不足时不能写需要或不需要 | 通过 |
| 渠道/客户要求与法律/海关强制要求分开 | 通过 |
| 本 Slice 不联网、不新增法规事实、不改执行逻辑 | 通过 |

## 验证命令

| 命令 | 结果 |
|---|---|
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market` | 通过 |
| `python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads` | 通过 |
| `python3 evals/run_superleads_user_visible_output_evals.py --suite all` | `6/6` 通过 |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `42/42` 通过 |
| `git diff --check` | 通过 |

## 结论

Slice W 已把“认证”纠偏为产品出海市场分析中的目标国准入需求判断：先查目标市场可能要求哪些认证/测试/注册/标签/包装/文件，再看用户现有材料是否覆盖当前产品和场景。它与 COO / 原产地证明的纠偏逻辑保持一致，不把用户材料缺失或存在直接升级为法规结论。
