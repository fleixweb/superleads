# Code Slice X：认证 / 目的国准入要求防错闭环验证记录

日期：2026-07-28

## 本次目标

把 Slice W 的业务口径落到代码层：产品出海市场分析里的“认证”默认是目标国家/地区准入要求判断，不是等待用户提供证书。

## 本次新增 / 更新

| 文件 | 变化 |
|---|---|
| `shared/schemas/product-market-analysis.schema.json` | 新增 `certification_requirement` 专门结构；`MatrixRowType` 增加 `certification_requirement` / `destination_requirement` |
| `scripts/validate_product_market_analysis.py` | 新增认证/准入要求与用户材料状态分列校验、官方/权威来源校验、证书入口/测试报告/渠道要求/用户证书升级拦截 |
| `evals/cases/product_market_analysis_cases.json` | market suite 从 42 个扩展到 50 个 case |
| `evals/fixtures/market_pass_certification_requirement_destination_rule_split.json` | pass：锂电运输测试与文件要求按目标国规则与用户材料状态分列 |
| `evals/fixtures/market_pass_channel_requirement_separated_from_law.json` | pass：纺织标签官方要求与渠道/客户要求分列 |
| `evals/fixtures/market_fail_user_missing_certificate_as_not_required.json` | fail：用户没给证书被写成目标国不需要认证 |
| `evals/fixtures/market_fail_certificate_entry_as_certified.json` | fail：产品页证书入口被升级为已具备认证 / 已合规 |
| `evals/fixtures/market_fail_test_report_as_certification.json` | fail：测试报告被当成认证 |
| `evals/fixtures/market_fail_channel_requirement_as_legal_mandatory.json` | fail：渠道/平台要求被写成法律或海关强制 |
| `evals/fixtures/market_fail_user_certificate_as_destination_compliant.json` | fail：用户证书被写成目标国认可 / 产品已合规 / 可清关 |
| `evals/fixtures/market_fail_certification_requirement_without_official_source.json` | fail：确定性目标国认证要求没有官方/权威来源 |

## 新增错误码

| 错误码 | 拦截内容 |
|---|---|
| `market_certification_requirement_user_material_conflated` | 目标国认证/准入要求状态与用户材料状态混写，或用户缺证书反推不需要认证 |
| `market_certificate_entry_promoted_to_certified` | 证书下载入口 / 证书页面被升级为已认证 / 已合规 |
| `market_test_report_promoted_to_certification` | 测试报告被写成认证、批准或可替代认证 |
| `market_channel_requirement_promoted_to_legal` | 渠道、客户、平台要求被写成法律、法规或海关强制 |
| `market_user_certificate_promoted_to_destination_compliance` | 用户提供的证书/测试报告被升级为目标国认可、产品已合规、可销售或可清关 |
| `market_certification_requirement_without_authority` | `required` / `conditionally_required` / `normally_not_required` / `not_applicable` 等确定性准入要求缺少官方或权威来源 |

## 验收断言

| 断言 | 结果 |
|---|---|
| 认证要求行能独立表达目标市场要求状态 | 通过 |
| 用户材料状态与目标国要求状态分列 | 通过 |
| 没有用户证书不等于目标国不需要认证 | 通过 |
| 产品页 certificate 入口不能升级为已认证 | 通过 |
| test report 不能升级为 certification | 通过 |
| 渠道/客户要求不能升级为法律或海关强制 | 通过 |
| 用户证书不能升级为目标国认可、产品已合规或可清关 | 通过 |
| 确定性目的国准入要求需要官方/权威来源 | 通过 |
| 本轮不联网、不新增真实法规事实，只做静态 fixture 防错 | 通过 |

## 验证命令

| 命令 | 结果 |
|---|---|
| `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_pass_certification_requirement_destination_rule_split.json evals/fixtures/market_pass_channel_requirement_separated_from_law.json` | 通过 |
| `python3 scripts/validate_product_market_analysis.py evals/fixtures/market_fail_user_missing_certificate_as_not_required.json evals/fixtures/market_fail_certificate_entry_as_certified.json evals/fixtures/market_fail_test_report_as_certification.json evals/fixtures/market_fail_channel_requirement_as_legal_mandatory.json evals/fixtures/market_fail_user_certificate_as_destination_compliant.json evals/fixtures/market_fail_certification_requirement_without_official_source.json` | 按预期失败并命中目标错误码 |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `50/50` 通过 |
| `python3 evals/run_evals.py --suite default` | `91/91` 通过 |
| `python3 evals/run_evals.py --suite deep` | `637/637` 通过；首次 120s 超时后以 300s 超时重跑通过 |
| `python3 evals/run_evals.py --suite all` | `677/677` 通过 |
| `git diff --check` | 通过 |

## 结论

Code Slice X 已把“认证不是让用户先交证书，而是判断目标市场准入要求”的口径做成 schema / validator / fixtures 的硬约束。导出器仍只搬运已审矩阵，不生成真实法规结论、不补认证事实、不做价值判断。
