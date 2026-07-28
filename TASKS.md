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
- Slice AA 弱证据外贸场景校准已完成：`spec/30-superleads-weak-evidence-calibration.md`。
- Code Slice AA 用户交付污染 bug + 路由器修复已完成并通过回归，待提交。

## Code Slice AA 已完成内容

1. `scripts/export_superleads_markdown.py`
   - 内部术语替换加英文词边界；不破坏 `The Telegraph`、`Photograph`、`paragraph`、`evaluation`。
   - 支持 lead fixture 的 `extends/patches` 最小解析。
   - 停止为了过固定合同而补 Google Trends / COO / 海运拼箱 / 国际快递 / 待补材料清单样板段。
2. `scripts/validate_superleads_user_visible_output.py`
   - 黑名单检查支持否定语境豁免。
   - 英文内部词 `graph` / `eval` 不再命中普通单词内部。
   - 正向违规如“建议进入”“推荐客户”“采购概率 80%”“候选税号就是最终税率”仍失败。
3. `scripts/route_superleads_intake.py`
   - 增加经销商、批发商、零售商、代理商、连锁、维修商、distributor、wholesaler、retailer、dealer、reseller、service company 等真实外贸客户词。
   - “客户问我要 SDS / UN38.3 / 认证 / 关税 / 物流要求”进入产品出海市场分析。
   - “后市场”“中性包装”不再因 `市场` / `包装` substring 被误判。
4. evals
   - `evals/cases/superleads_route_cases.json` 路由 case 扩展到 11 条。
   - `evals/cases/superleads_user_visible_output_cases.json` 用户可见 case 扩展到 8 条。
   - `evals/cases/superleads_markdown_delivery_cases.json` Markdown delivery case 扩展到 5 条。

## 已验证

```bash
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 8/8
python3 evals/run_superleads_markdown_delivery_evals.py --suite all    # 5/5
python3 evals/run_evals.py --suite default                             # 98/98
python3 evals/run_evals.py --suite deep                                 # 644/644
python3 evals/run_evals.py --suite all                                  # 684/684
python3 evals/run_product_market_analysis_evals.py --suite all          # 50/50
git diff --check                                                        # 通过
```

说明：`python3 evals/run_evals.py --suite all` 当前不包含 market suite；market 需单独运行 `python3 evals/run_product_market_analysis_evals.py --suite all`。

## 当前下一步

1. 提交 Slice AA + Code Slice AA 当前变更。
2. 提交后建议进入 P1：`Code Slice AB：多来源互证 / CorroborationRecord 最小设计与 eval`。
3. 后续再排：时效降级、Authority registry、状态词压缩、单一客户背调工程资产、批量客户开发内核复盘。

## 当前阻塞 / 注意

- 真实默认发现仍受能力限制：没有可记录的真实搜索/打开来源能力时，默认发现只能停在计划或样本池层；不能伪造 SearchLog / Source / Observation。
- `tmp/stage5_chillys/` 必须保留。
