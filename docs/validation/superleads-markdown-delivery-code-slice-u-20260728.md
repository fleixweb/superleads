# Superleads Code Slice U 验证记录：三路线用户可见 Markdown 交付器

日期：2026-07-28

## 1. 本轮新增

| 文件 | 说明 |
|---|---|
| `scripts/export_superleads_markdown.py` | 三路线统一 Markdown 交付器 |
| `evals/run_superleads_markdown_delivery_evals.py` | 生成型 Markdown 交付 eval runner |
| `evals/cases/superleads_markdown_delivery_cases.json` | 三条 pass + 一条 fail case |
| `evals/fixtures/pass_customer_background_chillys_markdown.json` | Chilly's 单客背调 Markdown 交付 fixture |
| `spec/28-superleads-markdown-delivery-code-slice-u.md` | Slice U 规格说明 |

## 2. 人话展示验收点

| 路线 | 必须看到 | 禁止看到 |
|---|---|---|
| 批量客户开发 | 开发方向四行、发现候选池样表、待确认事项、来源 / 来源状态 | 推荐客户、采购概率、客户背调报告、产品市场分析语言 |
| 单一客户背调 | 一句话先说清、客户一眼看懂、主体关系、联系入口、跟进前注意、信息来源 | 候选客户池、推荐客户、采购概率、内部对象名 |
| 产品出海市场分析 | 先看贸易前提、Google Trends 未执行、候选 HTSUS、COO、海运拼箱、国际快递、待补材料清单 | 值得进入、推荐报价、最佳路线、承诺交期、客户名单 |

## 3. 已验证命令

```bash
python3 -m py_compile scripts/export_superleads_markdown.py evals/run_superleads_markdown_delivery_evals.py
python3 evals/run_superleads_markdown_delivery_evals.py --suite all
```

结果：

| 套件 | 结果 |
|---|---|
| 生成型 Markdown 交付 eval | `4/4` |

## 4. 边界确认

- 交付器不联网、不搜索、不打开来源。
- 批量客户开发只输出候选池，不变正式开发名单。
- 单一客户背调只围绕指定对象，不扩展成批量客户名单。
- 产品出海市场分析只输出客观矩阵，不判断是否进入市场。
- 底层 audit / validation 不通过时，不写 Markdown。

## 5. 回归结果

```bash
python3 evals/run_superleads_user_visible_output_evals.py --suite all
python3 evals/run_product_market_analysis_evals.py --suite all
python3 evals/run_product_market_source_plan_evals.py --suite all
python3 evals/run_product_market_source_collection_evals.py --suite all
python3 evals/run_product_market_collection_merge_evals.py --suite all
python3 evals/run_product_market_collection_pipeline_evals.py --suite all
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
python3 evals/run_evals.py --suite all

git diff --check
```

| 套件 | 结果 |
|---|---|
| 用户可见输出静态 eval | `6/6` |
| 产品市场分析 eval | `42/42` |
| source-plan | `6/6` |
| source collection | `6/6` |
| collection merge | `7/7` |
| collection pipeline | `7/7` |
| default 主套件 | `91/91` |
| deep 主套件 | `637/637` |
| all 主套件 | `677/677` |
| `git diff --check` | 通过 |
