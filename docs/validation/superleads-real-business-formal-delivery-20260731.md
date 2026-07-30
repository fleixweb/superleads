# Superleads 真实业务正式交付链路补强

日期：2026-07-31

## 背景

真实业务黑盒调用暴露了新的漂移：reference graph 的统一 Markdown 导出已经正确，但 Agent 在真实搜索/整理客户池后，仍可能手写一份看起来像正式交付的 Markdown 表格，并把内部公开信号状态当作用户可见 `依据状态`。

典型坏输出包括：

- `依据状态 = 已观察`
- `依据状态 = 已观察；需确认`
- `依据状态 = 已观察；来源受限`

这些都不是 Slice AE 冻结的用户可见状态词。正式交付应该使用 `已有明确依据`、`可作为线索`、`需补充资料`、`来源受限`、`说法冲突待复核` 等状态。

## 本轮修复

| 位置 | 改动 |
|---|---|
| `scripts/validate_superleads_user_visible_output.py` | 新增 `user_visible_basis_status_internal_leak`，阻断 `依据状态` 列或 `依据状态 xxx` 行中出现 `已观察`、`未检索`、`主体待确认`、`已解析` 以及 `已观察；需确认` / `已观察；来源受限` 等内部状态 |
| `evals/user_visible_outputs/fail_bulk_customer_real_uat_internal_basis_status.md` | 新增真实 UAT 风格 fail 样本，复现英国保温杯客户池手写报告把 `已观察` 当成 `依据状态` 的错误 |
| `evals/cases/superleads_user_visible_output_cases.json` | 将上述 fail 样本纳入用户可见输出 eval，期望错误码为 `user_visible_basis_status_internal_leak` |
| `skills/using-superleads/SKILL.md` | 明确真实业务正式 Markdown 交付必须有已保存 graph JSON 路径和 exporter JSON 成功结果；只有搜索笔记或手写表格时只能称为 research draft / source-collection note |
| `skills/exporting-lead-workbooks/SKILL.md` | 同步正式导出规则：不能声称 `ok=true` / `issue_count=0`，除非 validator/exporter 实际运行；导出前必须修掉内部依据状态 |
| 插件缓存 `~/.codex/plugins/cache/fleix/superleads/0.1.3/skills/...` | 已同步两个 Skill 文件，供新窗口正式调用读取 |
| `scripts/check_superleads_formal_markdown_delivery.py` | 冒烟检查新增 Skill 片段要求，并校验真实 UAT fail 样本确实被 validator 阻断 |

## 关键验收点

- reference graph 继续能通过统一 Markdown exporter。
- Northshore 仍显示 `待确认 / 可能相关 / 来源受限`。
- 真实 UAT 风格坏样本必须失败，且失败码包含 `user_visible_basis_status_internal_leak`。
- 新窗口 Skill 调用不能把没有 graph JSON 的手写客户表称为正式 Markdown 交付。
- `已观察公开来源` 可以出现在 `来源 / 来源状态`，但不能出现在 `依据状态`。

## 已验证

```bash
python3 -m py_compile scripts/validate_superleads_user_visible_output.py scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json  # passed, issue_count=0
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 14/14
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_evals.py --suite default  # 122/122
python3 evals/run_evals.py --suite all  # 714/714
python3 evals/run_evals.py --suite deep  # 671/671
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks  # passed
git diff --check  # passed
```

关键回归：

```json
{
  "code": "user_visible_basis_status_internal_leak",
  "value": "已观察"
}
```

## 结论

本轮没有新增 output mode、delivery status、exporter mode 或 audit 分支；只把真实业务正式交付链路继续收紧：真实搜索后的手写表格不能冒充正式交付，`依据状态` 不能再泄漏内部公开信号状态。
