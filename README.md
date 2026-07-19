# Superleads

Superleads 是一套通用外贸线上客户开发 Skill Suite。

## 入口

- `SUPERLEADS_DEVELOPMENT_SPEC.md`：完整开发规范
- `docs/validation/`：验证记录
- `scripts/`：校验、导出、归一化等脚本
- `evals/`：默认/深度评测套件

## 当前状态

最新状态请直接看：

- `HANDOFF.md`
- `TASKS.md`

当前会话已恢复 `source.open` 公开 GET 烟测，`search.web` 仍未知。

## 常用检查

```bash
python3 scripts/preflight_capabilities.py --format json
python3 evals/run_evals.py --suite default
python3 evals/run_evals.py --suite deep
```
