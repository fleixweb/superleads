# 产品出海市场分析 Code Slice G：Skill 入口与路由最小闭环

日期：2026-07-27

## 目标

把 Slice 7 的“Skill 文案 / 用户入口设计”落到可执行的最小闭环中，让 Superleads 能明确区分：

- 产品出海市场分析；
- 批量客户开发；
- 单一客户背调；
- 已有客户表补全；
- “先分析市场再找客户”的拆阶段场景。

本轮不接真实搜索、不做真实国家法规库、不自动生成市场事实，只做入口和路由边界。

## 变更范围

### 新增 Skill

新增：`skills/analyzing-product-outbound-market/`

- `SKILL.md`
  - 名称：`analyzing-product-outbound-market`
  - 中文显示：产品出海市场分析
  - 触发：产品 + 目标国家/地区 + 趋势、价格、准入、税费、出口要求、物流、COO、外部因素等分析。
  - 禁止：客户名单、客户推荐、市场进入建议、推荐价格、最佳运输方式、候选税号升级最终税率、COO/marking 混同等。
- `agents/openai.yaml`
  - 提供 UI 名称、简短说明和默认 prompt。

已运行：

```bash
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market
```

结果：`Skill is valid!`

### 更新 Superleads 总入口

更新：`skills/using-superleads/SKILL.md`

新增路由规则：

- 用户核心请求是一个产品进入/出口某国家或地区的趋势、价格、准入、税费、出口、物流、COO 或外部因素分析 → `analyzing-product-outbound-market`。
- 用户要找客户/买家/进口商/客户名单 → 批量客户开发。
- 用户指定公司/品牌/域名/邮箱/地址做背调 → 客户背调。
- 用户同时要求“市场分析 + 找客户” → 拆两步，先做产品出海市场分析，不自动生成客户名单。

### 新增入口参考文档

新增：`shared/references/product-outbound-market-intake.md`

内容包括：

- 产品出海市场分析触发/非触发边界；
- 首轮四行回应模板；
- 缺目标国家/地区、缺产品版本时的追问模板；
- 产品触发项提示；
- 默认出口申报国、原产国、起运地、HS/HTS、COO、证书、物流时效等前提边界。

### 更新共享入口文档

更新：

- `shared/references/route-map.md`
- `shared/references/user-intake.md`

新增“产品出海市场分析”作为与批量客户开发、客户背调并列的入口。

### 新增确定性路由脚本

新增：`scripts/route_superleads_intake.py`

用途：

- 对用户首句进行轻量路由分类；
- 输出 `route`、`next_skill`、`split_customer_development`、`missing_fields`、`response_lines`；
- 作为 eval 防回归工具，不替代正式 Brief 或研究逻辑。

覆盖边界：

| 用户表达 | 预期 |
|---|---|
| 做产品出海市场分析：锂电池出口美国 | `product_outbound_market_analysis` |
| 分析纺织品标签、关税、COO、物流 | `product_outbound_market_analysis` |
| 市场能不能做，顺便找客户 | 先 `product_outbound_market_analysis`，并 `split_customer_development=true` |
| 找美国锂电池进口商客户 | `bulk_customer_development` |
| 背调 examplebattery.com | `customer_background_research` |
| 分析带电池产品认证、关税和物流，但缺国家 | `product_outbound_market_analysis` + `missing_fields=[target_country_or_region]` |

### 新增 route eval

新增：`evals/cases/superleads_route_cases.json`

更新：`evals/run_evals.py`

- 静态套件现在会执行 `scripts/route_superleads_intake.py`；
- 每个 route case 校验：`route`、`next_skill`、`split_customer_development`、`missing_fields` 和用户可见回应关键短语。

### 新增行为提示样本

新增：`evals/behavioral/product-market-route-prompts.json`

覆盖：

- 直接产品出海市场分析；
- 纺织标签/关税/COO/物流；
- “市场能不能做 + 找客户”的拆阶段；
- 纯找客户仍走批量客户开发；
- 纯背调仍走客户背调；
- PDF/带电池产品作为产品资料线索，不自动证明 UN38.3/SDS/原产地/承运可走。

## 验证结果

已执行：

```bash
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/analyzing-product-outbound-market
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all
```

结果：

| 命令 | 结果 |
|---|---:|
| `quick_validate.py skills/analyzing-product-outbound-market` | `Skill is valid!` |
| `python3 evals/run_product_market_analysis_evals.py --suite all` | `36/36` |
| `python3 evals/run_evals.py --suite default` | `84/84` |
| `python3 evals/run_evals.py --suite deep` | `630/630` |
| `python3 evals/run_evals.py --suite all` | `670/670` |

default/deep/all 数量增加是因为新增 route cases 和行为入口静态检查被纳入主 eval。

## 边界说明

- `route_superleads_intake.py` 只是轻量路由 guardrail，不做真实研究、不生成 Brief、不创建 graph。
- 真实产品市场分析仍必须走 Source / Observation / EvidenceCard / MatrixRow 防错链路。
- 用户要求找客户时，仍走批量客户开发；市场分析中的线上渠道、价格和季节节点只作参考，不自动变成客户范围。
- 用户要求背调指定对象时，仍走客户背调；不扩展成按产品找客户或通用市场分析。
