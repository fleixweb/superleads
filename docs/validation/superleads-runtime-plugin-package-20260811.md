# Superleads Runtime Plugin Package Validation

日期：2026-08-11

## 目的

将可运行的 Superleads 插件内容与开发仓库中的历史 UAT、网页抓取、fixtures 和评测
材料分开。源码 `tmp/stage5_chillys/` 仍保留；构建过程不移动、不删除它。

## 工件合同

`scripts/build_superleads_plugin_package.py` 默认生成 `dist/superleads/`，只包含：

- `.codex-plugin/`
- `.claude-plugin/plugin.json`
- `hooks/`
- `skills/`
- `scripts/`
- `shared/`
- `spec/`

严格分发检查拒绝 `tmp/`、`evals/`、`tests/`、`docs/`、`.git/`、`.agents/`、
`.plugin-eval/`、Python bytecode 和 symlink。它还核查每个 Skill 的 `../../scripts`、
`../../shared`、`../../spec` 相对引用，防止精简工件漏带运行脚本。

## 验证

```bash
python3 -m py_compile scripts/build_superleads_plugin_package.py \
  scripts/check_superleads_plugin_distribution.py \
  evals/run_superleads_plugin_distribution_evals.py
python3 scripts/build_superleads_plugin_package.py --format json
python3 scripts/check_superleads_plugin_distribution.py \
  --plugin-root dist/superleads --source-root . --runtime-package --format json
python3 evals/run_superleads_plugin_distribution_evals.py --suite all
```

结果：

- 工件：122 files，1,821,708 bytes。
- 相对引用：49 条，全部存在。
- 分发 eval：9/9 passed。
- 负例：缺少 product-market Skill、spec、hook、hook target、Skill 直接引用的脚本，或
  包内出现 `tmp/old-uat.txt`，均被拦截。

## 实际安装验证

本机 marketplace symlink 已从源码根目录改为指向
`/home/fleix/superleads/dist/superleads`，随后执行：

```bash
codex plugin add superleads@fleix --json
python3 scripts/check_superleads_plugin_distribution.py \
  --plugin-root /home/fleix/.codex/plugins/cache/fleix/superleads/0.1.12 \
  --source-root . --runtime-package --format json
```

结果：Codex 安装 `0.1.12` 到
`/home/fleix/.codex/plugins/cache/fleix/superleads/0.1.12`；缓存占用 2.2 MB，顶层仅有
`.claude-plugin`、`.codex-plugin`、`hooks`、`scripts`、`shared`、`skills` 和 `spec`。严格
检查 `issue_count=0`，确认缓存不含 `tmp/`、`evals/`、`tests/` 或 `docs/`。
