---
name: analyzing-product-outbound-market
description: "Use for objective analysis of a specified product entering a target country or region. Scope to the requested facts such as public prices, market signals, compliance, duties, export requirements, or logistics. Do not use for customer discovery, company background research, or market-entry recommendations."
---

# 产品出海市场分析

## 静态帮助守卫

用户只输入 `@`、`@superleads`，或询问帮助、怎么用、你能干嘛等简短使用方法时，直接用用户语言返回精简引导。不运行工具：不运行 shell、不搜索、不做能力预检，也不检查版本、创建研究对象或加载市场参考。明确要求详细用法时，只静态阅读 `../../shared/references/superleads-user-guidance.md`。

## 路由优先

在读取其他参考前，脚本可用时先以当前用户原文运行：

```bash
python3 ../../scripts/route_superleads_intake.py --text "<current user message>" --format json
```

脚本不可用时，按本节最小入口和不可变边界直接判断路线；不要尝试启动 shell 或等待 Python，也不要因此阻塞任务。

如果结果不是 `product_outbound_market_analysis`，立即按返回路线交接，不创建市场 Brief 或研究计划。只向用户显示 `response_lines`，不显示 JSON、内部阶段名、路径、解释器、依赖或模块细节。

同一次请求包含任意两个或以上明确业务目标时，按 `../../shared/references/composite-task-routing.md` 建立组合任务；市场分析保持独立的来源用途和事实边界。

## 最小入口

需要产品或品类，以及目标国家/地区。缺少其中之一时只问一个真正阻塞的问题；型号、原产国、候选 HS/HTS、贸易术语或产品资料缺失时降低精度并列为待确认，不把它们都变成首轮问卷。

用户只问关税、认证、公开价格、趋势、出口文件或物流时，只执行相应模块。只有明确要求完整、整体或全面市场分析时才覆盖完整模块。模糊请求先确认范围，或交付明确标注的最小研究快照；未执行模块写“本轮未执行”。

## 不可变边界

- 使用 `ProductMarketAnalysisGraph`，不生成客户名单或客户推荐。
- 搜索摘要、历史 Run、Source Pack 和模型记忆只是线索，不是事实。
- 用户可见事实必须来自本轮实际打开的来源，或显式的未知、冲突、来源受限和本轮未执行状态。
- 候选 HS/HTS 不等于最终分类或税率；平台价格不等于成交价；趋势不等于采购需求。
- 认证要求与用户已有证书是两个对象，不能互相推出。
- 不猜最佳路线、保证时效、最终合规或是否值得进入市场。
- 登录墙、验证码、403、付费墙和动态空壳标记为来源受限，不绕过。

## 按需执行

路由确认后阅读 `../../shared/references/product-outbound-market-intake.md` 和 `../../shared/references/product-market-runtime.md`。当任务涉及批量、多主体或多查询项时，再读取 `../../shared/references/bulk-execution-strategy.md`；单一对象、单一产品、单一国家和单项问题不读取。后者包含模块选择、有限来源计划、紧凑证据编译和正式门禁；入口阶段不得直接加载开发期 `spec/` 文件。

正式研究前运行或模拟 `../../scripts/preflight_capabilities.py --require-formal-research`：脚本可用时运行；脚本不可用时直接检查宿主实际暴露的搜索和来源打开能力。真实来源能力缺失时降低交付层级，可整理用户资料或提供查询计划，但不得伪装成公开来源研究；仅缺少 Python 不得阻塞宿主原生检索和来源读取。

来源已打开后，任何包含市场事实的最终用户可见事实交付，包括按单项范围生成的研究快照，在脚本可用时依次运行输入预检、证据编译、`../../scripts/validate_product_market_analysis.py` 和 `../../scripts/audit_product_market_analysis.py`。脚本不可用时按等价清单逐项自检：产品、目的地和请求模块边界明确；每项事实绑定本轮实际打开来源的 URL、可见原文或位置与观察时间；搜索摘要仍只作为线索；未知、冲突、来源受限和本轮未执行项均保留；不输出未经来源支持的 HS/税率、认证、物流或商业判断。完成后交付并明确标注“本环境未运行确定性校验”。范围确认、进度说明和单独澄清不运行这些门禁，也不能冒充事实交付。只有用户明确要求正式报告、Markdown、CSV 或工作簿导出，且对应 exporter 可用并通过校验时，才声称生成了正式文件。这些脚本不能被搜索摘要或未打开页面替代。

最终交付或终局能力受限说明遵循 `../../shared/references/superleads-user-guidance.md`；进度和单独澄清不附支持尾注。
