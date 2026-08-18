---
name: using-superleads
description: "Use for a concrete batch discovery request with product or keyword, target market, and customer type. For a bare Superleads activation or help request, return static help and do not initialize discovery. Do not use for single-company background research or product market analysis."
---

# 批量发现公开客户信息

## 裸启动

用户只输入 `@`、`@superleads`，或询问帮助、怎么用、你能干嘛等简短使用方法时，直接用用户语言返回：

> Superleads 可帮你批量开发客户、背调指定公司或分析目标市场。直接描述需求即可，例如：找德国做工业传感器的进口商。

不运行工具：不要调用 shell；不搜索、不做能力预检，也不检查版本、创建图谱、导出或加载研究参考。明确要求“帮助”或“详细用法”时，静态阅读 `../../shared/references/superleads-user-guidance.md`；仍不运行工具。

## 路由

对非帮助请求，脚本可用时先以当前用户原文运行：

```bash
python3 ../../scripts/route_superleads_intake.py --text "<current user message>" --format json
```

脚本不可用时，按本节入口边界和当前用户原文直接判断路线；不要尝试启动 shell 或等待 Python，也不要因此阻塞任务。

只使用其 `response_lines`、语言和任务边界；不要展示 JSON、内部阶段名或路径。元数据、资料初审、单一对象、市场分析和组合任务须立即按返回路线交接，不得因为本 Skill 已被选择而强行开始批量发现。

本入口仅处理“产品、关键词、型号/番号/料号 + 市场范围 + 客户类型”的具体批量发现。番号或料号只作为产品锚点，先用宿主实际暴露的公开检索核对身份，不根据编码形状猜产品。不得用于单一客户背调或产品出海市场分析；不得猜 ICP、渠道、采购意向或客户价值。

同一次请求有任意两个或以上明确业务目标时，建立一个父级组合任务；详细规则见 `../../shared/references/composite-task-routing.md`。

## 执行边界

确认是批量发现后，按需阅读 `../../shared/references/batch-discovery-execution.md`。当任务涉及批量、多主体或多查询项时，再读取 `../../shared/references/bulk-execution-strategy.md`；单一对象或单项请求不读取。默认交付是带公开来源状态、未知项与待确认项的候选池，不是推荐客户名单；搜索摘要只是线索，绝不写成 Claim。

仅在用户明确要求正式开发名单、完整核验、深度背调、联系人归属核验或正式 Markdown 导出时，按需阅读 `../../shared/internal-stages/` 中对应的阶段参考和 `../../shared/references/using-superleads-formal-delivery.md`。终局交付才附 `../../shared/references/superleads-user-guidance.md` 的支持与安全尾注；进度和单独澄清不附。
