# Superleads 正式 Skill 调用 Markdown 交付收口

日期：2026-07-31

## 背景

正式调用 Superleads Skill 验收时发现：Agent 虽然声称完成了 bulk Markdown 导出，但实际输出是把 `export_workbook.py` 的原始 sheet 手工转成 Markdown。结果 `Northshore Drinkware Distributors` 的 `业务/产品关联信号状态 = 已观察` 被误读成用户可见 `依据状态 = 已观察`，绕开了 Code Slice AH-FIX 刚修复的 `来源受限` 投影。

这说明核心脚本正确，但 Skill 调用说明和插件缓存版本仍允许或诱发旧路径：手工渲染 workbook sheet，而不是强制走统一 Markdown delivery。

## 本轮修复

| 文件/位置 | 改动 |
|---|---|
| `skills/using-superleads/SKILL.md` | 在 Output 中明确：正式 Markdown 交付必须调用 `scripts/export_superleads_markdown.py`；禁止手工从 workbook/CSV 渲染 Markdown；禁止把信号状态列重标为 `依据状态`；命令失败时停止而不是补假报告 |
| `skills/exporting-lead-workbooks/SKILL.md` | 在 Markdown delivery 中明确：bulk/customer/background/market 的 chat-readable 报告必须使用统一导出器；原始 workbook 表头 `公司名称 / 国家/地区 / 官网/域名` 不是合格 bulk Markdown 主表 |
| 插件缓存 `~/.codex/plugins/cache/fleix/superleads/0.1.3/skills/...` | 同步上述两个 Skill 文件，避免正式调用继续读旧缓存 |
| `scripts/check_superleads_formal_markdown_delivery.py` | 新增正式调用冒烟检查：校验本地 Skill 与插件缓存一致、包含强制统一导出器说明，并用 reference graph 真实运行 `export_superleads_markdown.py` 检查 Northshore 为 `可能相关 / 来源受限` |
| `docs/superleads-common-commands.md` | 增加正式 Skill 调用 Markdown 冒烟检查命令 |

## 关键验收点

正式 bulk Markdown 必须具备：

- 由 `scripts/export_superleads_markdown.py --route bulk_customer_development` 生成。
- 开头为 `# 批量客户开发`。
- 包含 `发现候选池样表（候选池不是正式开发名单）`。
- 主表包含 `分区`、`候选客户`、`业务相关性`、`依据状态`、`来源 / 来源状态`。
- 不应出现旧的原始 workbook 主表头 `公司名称 | 国家/地区 | 官网/域名` 作为 chat-facing 主表。
- `Northshore Drinkware Distributors` 必须显示 `待确认 / 可能相关 / 来源受限`，不得把 `已观察` 当成 `依据状态`。

## 已验证

```bash
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/using-superleads  # passed
python3 /home/fleix/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/exporting-lead-workbooks  # passed
python3 -m py_compile scripts/check_superleads_formal_markdown_delivery.py scripts/export_superleads_markdown.py scripts/validate_superleads_user_visible_output.py  # passed
python3 scripts/check_superleads_formal_markdown_delivery.py --fixture shared/references/default-discovery-reference.example.json  # passed, issue_count=0
python3 evals/run_superleads_markdown_delivery_evals.py --suite all  # 5/5
python3 evals/run_superleads_user_visible_output_evals.py --suite all  # 13/13
git diff --check  # passed
```

关键输出：

```markdown
| 待确认 | Northshore Drinkware Distributors | United Kingdom | 经销商 / 分销商 | drinkware distributor 目录条目；公开电话 | 可能相关 | 来源受限 | 442070002222（建议核查后使用） | 补开官网产品页确认保温杯；产品线是否包含 insulated bottle 待确认；目录详情页需登录 | 公开目录列表；搜索组:uk_directory；Northshore Drinkware Distributors；https://directory.example/northshore |
```

## 结论

正式 Skill 调用的 Markdown 交付路径已收口：当用户要 chat-readable 报告时，必须走统一 Markdown delivery；手工渲染 workbook sheet 不再是允许路径。


## 2026-07-31 真实业务 UAT 复核补充

后续真实业务黑盒调用又暴露一个新漂移：reference graph 导出正确，但 Agent 在真实搜索后可能手写客户池表格，并把内部公开信号状态 `已观察`、`已观察；需确认`、`已观察；来源受限` 写进用户可见 `依据状态`。

该问题已在 `docs/validation/superleads-real-business-formal-delivery-20260731.md` 记录并修复：用户可见 validator 新增 `user_visible_basis_status_internal_leak`，正式调用冒烟脚本也会检查真实 UAT fail 样本。


## 2026-07-31 声明路径精确复核补充

真实 UAT 发现：Agent 可能用 graph 成功运行 exporter，却把另一个手写/后处理 Markdown 路径报给用户，同时复用 `ok=true` / `issue_count=0`。本轮已在正式冒烟脚本中新增 `--claimed-graph` / `--claimed-markdown` / `--claimed-route`，用于将声明路径与从声明 graph 新跑出的 exporter 输出做精确比对。

同轮还确认 `export_superleads_markdown.py --route customer_background_research` 支持单客背调；Skill 已禁止声称 Markdown exporter 只支持 bulk。
