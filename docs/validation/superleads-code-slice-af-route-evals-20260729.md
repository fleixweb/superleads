# Code Slice AF：三路线入口路由纠偏 / route eval

日期：2026-07-29

## 目标

把 Superleads 三条用户入口的首句路由进一步收稳：

1. 批量客户开发；
2. 单一客户背调；
3. 产品出海市场分析。

本轮只做 deterministic intake guardrail 和静态 eval，不联网、不生成客户、不创建 Brief / Candidate / Lead / ProductMarketAnalysisGraph。

## 本轮纠偏点

| 问题 | AF 处理 |
|---|---|
| 普通 `市场` / `包装` / `后市场` 词容易把客户开发误判成市场分析 | 市场分析只由明确的产品出海、准入、税费、认证、物流、COO、趋势等问题触发；`开发某地市场` 仍按外贸口语理解为客户开发 |
| `客户问我要 SDS / UN38.3` 这类合规问题容易被 `客户` 二字带到批量开发 | 合规、税费、认证、COO、清关、技术文件等问题优先进入产品出海市场分析 |
| `查一下 example.com 靠不靠谱` 这类单客背调口语不够稳 | 增加靠不靠谱、真买家/中间商、背后的公司是谁、官网/域名/邮箱/LinkedIn 等指定对象锚点 |
| `找需要 UL/CE 认证的进口商` 容易被认证词误判为市场分析 | 如果认证词是在描述目标客户属性，仍走批量客户开发；只有用户明确“并分析/准入/关税/要求”才拆成市场分析 + 客户开发 |
| 混合任务缺少可断言字段 | 路由输出增加 `secondary_routes` 和 `route_order`；eval 可校验 split 的第二阶段是批量客户开发 |
| 路由 eval 只能跑主套件 | 新增独立 `evals/run_superleads_route_evals.py`，支持快速跑三路线入口回归 |

## 输出字段约定

| 字段 | 含义 |
|---|---|
| `route` | 本轮先执行的主路线 |
| `next_skill` | 下一步建议进入的 Skill |
| `split_customer_development` | 是否识别出“产品市场分析 + 找客户”的拆阶段需求 |
| `secondary_routes` | 拆阶段时的后续路线，例如 `bulk_customer_development` |
| `route_order` | 建议执行顺序；混合任务为产品市场分析在前、批量客户开发在后 |
| `missing_fields` | 只列最小阻塞字段，不做行业问卷 |
| `response_lines` | 用户可见的简短入口回应，不暴露内部 graph / Claim / EvidenceCard 等术语 |

## 新增 / 覆盖样例

| 输入 | 期望 |
|---|---|
| `这个产品出口欧盟需要 CE 吗` | 产品出海市场分析 |
| `中国纺织品出口美国需要原产地证吗` | 产品出海市场分析 |
| `48V锂电池到沙特要 SABER 吗，清关还要什么文件` | 产品出海市场分析 |
| `帮我找有 CE 认证需求的欧洲进口商` | 批量客户开发 |
| `帮我找需要 CE 认证的欧洲进口商` | 批量客户开发 |
| `找美国需要UL认证的进口商` | 批量客户开发 |
| `帮我找美国锂电池进口商，并分析一下关税和准入要求` | 先产品出海市场分析，再批量客户开发 |
| `查一下 acmebattery.com 靠不靠谱` | 单一客户背调 |
| `这个公司是真买家还是中间商？官网 example.com` | 单一客户背调 |
| `这个 LinkedIn / 官网 / 邮箱背后的公司是谁` | 单一客户背调 |
| `请找美国户外家具 retail chains，不要做市场分析` | 批量客户开发 |
| `只做产品出海市场分析，不找客户` | 产品出海市场分析，缺目标国家/地区 |
| `我不要做产品出海市场分析，找美国客户` | 批量客户开发 |

## 边界

- 路由器不是语义模型，只是静态防错 guardrail；模糊表达仍可回到 `using-superleads` 追问。
- `secondary_routes` 只表达拆阶段顺序，不代表自动执行第二阶段。
- “认证需求的进口商 / 有 UL 需求的客户”是客户属性，不等于用户要系统判断 UL 是否法律强制。
- 产品出海市场分析仍不生成客户名单、不判断是否值得进入、不推荐价格、不输出最终税率。
- 没有真实可记录搜索 / 打开来源能力时，后续默认发现仍停在计划或样本池层。

## 验证

已执行：

```bash
python3 -m py_compile scripts/route_superleads_intake.py evals/run_superleads_route_evals.py evals/run_evals.py  # passed
python3 evals/run_superleads_route_evals.py --suite all  # 25/25
python3 evals/run_evals.py --suite default  # 113/113
python3 evals/run_evals.py --suite all  # 699/699
python3 evals/run_evals.py --suite deep  # 659/659
python3 evals/run_product_market_analysis_evals.py --suite all  # 74/74
git diff --check  # passed
```
