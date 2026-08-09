# Superleads 批量 Markdown 公开联系人显示验证记录（2026-08-10）

## 范围

本次只修复批量客户开发的 Markdown 联系方式汇总交付层。工作簿参考实现
`scripts/export_workbook.py::initial_contact_rows` 未修改；标准开发名单、单客背调、
产品出海市场分析和 `tmp/stage5_chillys/` 未修改。

## 实现要点

- 联系方式汇总为七列：对象、联系人 / 公开职业线索、联系方式、类型、可用状态、待确认原因、来源 / 链接。
- `person_name` / `job_title` 的值放入公开职业线索列，联系方式列显示“未记录可用入口”；LinkedIn URL 仍保留在联系方式列。
- `needs_manual_association_review` 与 `UnassignedContactLead` 仍显示原值并标“待确认归属”，待确认原因非空。
- `hold_no_source` / `hold_inferred` 的值继续由既有脱敏链路从 Markdown、CSV、XLSX 用户可见字段移除。
- 联系采集与研究计划 Skill 增加公司/人员锚定的 LinkedIn、官网、展会、行业协会和公开社媒查询模板；未打开的搜索结果只保留为待验证 URL，不把摘要人名/职位当已核实事实。

## Fixtures / Evals

- 扩展 `evals/fixtures/pass_default_discovery_candidate_pool.json`：Alpha 增加 `Jordan Lee / Sales Manager`，带 `source_observation_id` 和 `needs_manual_association_review`。
- `evals/cases/superleads_markdown_delivery_cases.json` 增加人员字段断言与既有 `pass_hold_inferred_filtered_export.json` 脱敏回归；没有新增 fixture 文件或 eval runner。

## 验证结果

```text
python3 -m py_compile scripts/export_superleads_markdown.py scripts/export_workbook.py scripts/validate_superleads_user_visible_output.py  # passed
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 8/8
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 15/15
python3 evals/run_customer_background_research_evals.py --suite all  # 7/7
python3 evals/run_evals.py --suite default  # 125/125
python3 evals/run_evals.py --suite all  # 718/718
python3 evals/run_evals.py --suite deep  # 675/675
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json --format json  # ok=true, issue_count=0
python3 scripts/check_superleads_plugin_distribution.py --plugin-root /home/fleix/.codex/plugins/cache/fleix/superleads/0.1.7 --source-root /home/fleix/superleads --format json  # ok=true
python3 evals/run_superleads_plugin_distribution_evals.py --suite all  # 6/6
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/collecting-contact-intelligence  # passed
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/writing-research-plans  # passed
git diff --check  # passed
```

运行时缓存已同步到 `/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.7`。
