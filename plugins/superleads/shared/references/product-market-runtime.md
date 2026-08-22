# 产品市场分析运行时规则

本文件是产品出海市场分析的运行时速查，不替代正式校验器、审计器或 schema。只在路由已确认后读取；资料初审、帮助、元数据和普通客户发现不读取。

## 范围

先确认产品与目标国家/地区。完整趋势、公开价格、准入、税费、出口要求、物流、外部因素只有用户明确要求“完整/整体/全面市场分析”时才执行。用户只问关税、认证、公开价格或物流时，只设置对应的 `analysis_modules_requested`，其他模块写“本轮未执行”。范围不清时先问一个短问题或交付明确标注的最小快照。

## 证据

使用 `ProductMarketAnalysisGraph`。用户可见事实只能来自本 Run 实际打开的 Source/Observation/EvidenceCard，或显式 Gap、Conflict、`not_executed` / `source_restricted` 状态。搜索摘要、Source Pack、历史 Run 和模型记忆只能作为线索。用户材料保持“用户提供资料”，不升级为官方事实。

保留 `verified`、`candidate`、`preliminary_reference`、`business_confirmation_required`、`professional_confirmation_required`、`source_restricted`、`not_executed`、`not_applicable`、`conflict_pending_review` 等状态。不得把候选 HS/HTS 变成最终税率或分类，不得把平台价格变成成交价，不得把趋势变成采购需求，不得替用户判断是否进入市场。

## 执行顺序

脚本可用时，先运行 `scripts/plan_product_market_sources.py` 生成有限 Query Plan，再执行搜索与来源打开。Source/Observation 稳定后，可用 `scripts/compile_product_market_evidence.py` 将紧凑笔记编译为既有图谱对象；编译器不搜索、不打开、不判断权威性。编译前后运行 `scripts/precheck_superleads_uat_input.py`，包含市场事实的交付再由 `validate_product_market_analysis.py` 与 `audit_product_market_analysis.py` 门禁。脚本不可用、导致整个确定性脚本校验链未运行时，按 `../references/no-script-delivery-contract.md` 的唯一契约完成范围、来源、事实、未知项和禁止结论自检，并标注“本环境未运行确定性校验”。如果核心业务规则校验已经运行并通过、仅补充结构检查未运行，则改用“本次已完成核心业务规则校验；补充结构检查未运行。”，不得声称确定性校验未完成或未通过；范围确认、进度和单独澄清不运行门禁，也不作为事实交付。

只有用户明确要求正式报告或 Markdown 导出，且图谱通过严格校验/审计后，才运行正式 exporter。正式阶段如涉及原产地证明、认证、测试、标签、SDS、UN38.3、关税或物流，按实际模块读取对应开发规格；这些规格不属于首次入口上下文。

## 交付

进度与快照说明当前范围、已打开来源、已确认/待确认/受限/未执行数量。最终交付按模块分节，并保留来源 URL、观察时间、冲突和未知项。不得生成客户名单、推荐报价、最佳路线或市场进入建议。
