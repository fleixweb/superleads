# Tasks

## 已完成

- 产品出海市场分析 Slice 1-13 及 Code Slice A-M 已完成。
- Slice R 产品内核复盘已完成，确认 Superleads 是外贸业务情报产品，不是通用工作流框架。
- Slice S 三路线真实外贸样本已完成。
- Slice T 用户可见输出合同与静态 eval 已完成。
- Code Slice U 三路线用户可见 Markdown 交付器已提交：`43f2ef7 Add Superleads Markdown delivery exporter`。
- Code Slice V README / Skill 使用说明 / 常用命令示例已提交：`8ea336a Document Superleads Markdown delivery usage`。
- Slice W 目的国认证 / 准入要求判断纠偏已提交：`8f6703a Calibrate product market certification requirements`。
- Code Slice X 认证 / 目的国准入要求防错闭环已提交：`85197d7 Add certification requirement guardrails`。
- Slice AA 弱证据外贸场景校准已完成并提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AA 用户交付污染 bug + 路由器修复已完成并提交：`b3145fc Calibrate weak-evidence delivery guardrails`。
- Code Slice AB 多来源互证 / CorroborationRecord 最小闭环已完成，待提交。

## Code Slice AB 已完成内容

1. schema
   - `ProductMarketAnalysisGraph` 新增可选 `corroboration_records`。
   - `MatrixRowRecord` 新增可选 `corroboration_record_ids`。
   - `CorroborationRecord` 表达多来源一致、单点来源、独立来源不足、冲突、来源受限、未执行。
2. validator
   - 阻断单来源冒充多来源。
   - 阻断同域名/同 owner 冒充多个独立来源。
   - 阻断未打开来源参与互证。
   - 阻断 SearchLog / 搜索摘要 / Query Plan 直接作为互证事实。
   - 阻断冲突被隐藏成多来源一致。
   - 阻断多弱来源一致把矩阵行升级为 `verified` / 最终事实。
3. exporter
   - 导出新增人话列：`多来源互证情况`、`互证边界`、`下一步核实`。
   - 仍只搬运已审核矩阵和安全字段，不新增事实。
4. evals
   - 新增 `market_pass_multi_source_corroboration_reference.json`。
   - 新增 6 个 fail fixture：single source、same domain、conflict hidden、search summary、overstated verified、unopened source。
   - market suite 现为 `57/57`。

## 已验证

```bash
python3 -m py_compile scripts/validate_product_market_analysis.py scripts/export_product_market_workbook.py scripts/audit_product_market_analysis.py
python3 evals/run_product_market_analysis_evals.py --suite all  # 57/57
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 98/98
python3 evals/run_evals.py --suite all  # 684/684
python3 evals/run_evals.py --suite deep  # 644/644
git diff --check  # 通过
```

说明：`python3 evals/run_evals.py --suite all` 当前不包含 market suite；market 需单独运行 `python3 evals/run_product_market_analysis_evals.py --suite all`。

## 当前下一步

1. 提交 Code Slice AB 当前变更。
2. 提交后建议进入 `Code Slice AC：时效降级 / freshness`。
3. 后续再排：Authority registry、状态词压缩、单一客户背调工程资产、批量客户开发内核复盘。

## 当前阻塞 / 注意

- 真实默认发现仍受能力限制：没有可记录的真实搜索/打开来源能力时，默认发现只能停在计划或样本池层；不能伪造 SearchLog / Source / Observation。
- `tmp/stage5_chillys/` 必须保留。
