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

## 2026-07-31 真实 UAT 第二轮复核

第二轮新窗口 UAT 结果：

| 场景 | 复核结果 | 说明 |
|---|---|---|
| 英国保温杯客户池 | 不通过 | graph validate / audit 均通过，且 graph 能由 exporter 生成合格报告；但用户声明的 Markdown 路径不是该 exporter 输出，仍是另一份手写/后处理报告，缺正式字段并含 `依据状态=已观察` |
| 美国 generator parts | 通过 | graph validate / audit 通过；声明的 Markdown 路径与 exporter 输出一致；用户可见 validator 通过 |
| Chilly’s 单客背调 | 不通过 | graph 实际可由 `export_superleads_markdown.py --route customer_background_research` 成功导出，脚本返回 `ok=true`；新窗口错误声称 Markdown exporter 仅支持 bulk，导致未生成 Markdown |

本轮新增修复：

| 位置 | 改动 |
|---|---|
| `scripts/check_superleads_formal_markdown_delivery.py` | 新增 `--claimed-graph` / `--claimed-markdown` / `--claimed-route`，将真实 UAT 声明的 Markdown 路径与从声明 graph 新跑出的 exporter 输出做 SHA-256 精确比对 |
| `scripts/check_superleads_formal_markdown_delivery.py` | 冒烟检查增加 `customer_background_research` fixture，证明统一 Markdown exporter 支持单客背调 |
| `skills/using-superleads/SKILL.md` | 明确最终回答里的 claimed Markdown path 必须是 exporter 为 claimed graph 写出的原文件，不得后处理替换后复用 `ok=true` |
| `skills/exporting-lead-workbooks/SKILL.md` | 增加真实 UAT 校验命令示例：`--claimed-graph graph.json --claimed-markdown report.md --claimed-route auto` |
| `skills/researching-customer-background/SKILL.md` | 明确客户背调 Markdown 正式交付使用 `export_superleads_markdown.py --route customer_background_research`，不要声称 exporter 只支持 bulk |

已实测：

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_graph.json --claimed-markdown /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_report.md --claimed-route bulk_customer_development --format json  # fails with formal_markdown_claimed_output_mismatch
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_us_generator_parts/graph.json --claimed-markdown /home/fleix/superleads_us_generator_parts/report.md --claimed-route bulk_customer_development --format json  # passed, issue_count=0
python3 scripts/export_superleads_markdown.py /home/fleix/superleads_runs/chillys_bottles_2026-07-31/chillys_background_graph.json --route customer_background_research --output /tmp/chillys_reexport.md --format json  # passed, issue_count=0
```


本轮提交前复验：

```bash
python3 -m py_compile scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/researching-customer-background  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json --format json  # passed, issue_count=0；含 bulk 与 customer_background_research 冒烟
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 14/14
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_us_generator_parts/graph.json --claimed-markdown /home/fleix/superleads_us_generator_parts/report.md --claimed-route bulk_customer_development --format json  # passed, issue_count=0
python3 scripts/export_superleads_markdown.py /home/fleix/superleads_runs/chillys_bottles_2026-07-31/chillys_background_graph.json --route customer_background_research --output /tmp/chillys_reexport.md --format json  # passed, issue_count=0
python3 scripts/check_superleads_formal_markdown_delivery.py --skip-cache --claimed-graph /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_graph.json --claimed-markdown /home/fleix/superleads_runs/uk_drinkware_channels_20260731/uk_drinkware_channels_discovery_report.md --claimed-route bulk_customer_development --format json  # failed as expected: formal_markdown_claimed_output_mismatch
git diff --check  # passed
```

## 固定 UAT 验收步骤

自本轮起，真实业务 UAT 必须固定执行 claimed path 复核：

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py \
  --claimed-graph "$GRAPH" \
  --claimed-markdown "$MARKDOWN" \
  --claimed-route auto \
  --format json
```

验收口径：

- `ok=true` 且 `issue_count=0` 才算通过。
- 只记录 exporter `ok=true` 不算通过；必须同时验证最终 claimed Markdown path 与 claimed graph 的重新导出结果逐字一致。
- 命中 `formal_markdown_claimed_output_mismatch` 时，真实 UAT 直接失败；不得手工修改报告后继续复用旧的 exporter 成功结果。
- 如果没有保存 graph JSON 或 claimed Markdown 文件，只能称为 research draft / source-collection note，不能称为正式 Markdown 交付。
- 三条路线都适用；单客背调用 `customer_background_research`，批量客户开发用 `bulk_customer_development`，不确定时先用 `auto`。

详细清单见 `docs/validation/superleads-real-business-uat-checklist.md`。

## 2026-07-31 claimed path 自动回归

为避免 claimed path 复核只停留在文档，本轮把它接入 `evals/run_superleads_markdown_delivery_evals.py`：

| 回归项 | 期望 |
|---|---|
| 统一 exporter 写出的 Markdown 作为 claimed path | `check_superleads_formal_markdown_delivery.py --claimed-graph ... --claimed-markdown ...` 通过 |
| exporter 输出后被手工追加内容再作为 claimed path | `check_superleads_formal_markdown_delivery.py` 失败，错误码包含 `formal_markdown_claimed_output_mismatch` |

复验：

```bash
python3 -m py_compile evals/run_superleads_markdown_delivery_evals.py scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py  # passed
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 7/7
```

## 2026-08-01 customer_background_research 真实 UAT

单客背调路线用 Chilly’s Bottles 跑真实 UAT，验证 claimed path 门禁不只在 bulk 路线有效。

| 项目 | 结果 |
|---|---|
| route | `customer_background_research` |
| graph JSON | `/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json` |
| Markdown | `/home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md` |
| claimed path check | `ok=true` / `issue_count=0` |
| user-visible validator | `ok=true` / `issue_count=0` / `table_count=7` |

复验：

```bash
python3 scripts/check_superleads_formal_markdown_delivery.py --claimed-graph /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_graph.json --claimed-markdown /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md --claimed-route customer_background_research --format json  # passed, issue_count=0
python3 scripts/validate_superleads_user_visible_output.py /home/fleix/superleads_chillys_bottles_20260731/chillys_customer_background_uat_report.md --route customer_background_research --min-tables 6 --format json  # passed, issue_count=0, table_count=7
```

结论：`customer_background_research` 正式 Markdown 也可由统一 exporter 交付，并通过 claimed path 门禁；不得声称该门禁或 Markdown exporter 只适用于 bulk。
