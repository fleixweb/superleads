# Tasks

## 已完成

- `python3 evals/run_evals.py --suite default` 通过
- `python3 evals/run_evals.py --suite deep` 通过
- `python3 evals/run_evals.py --suite all` 通过
- `source.open` 公开 GET 烟测已恢复（`https://example.com`，`200`）
- `tmp/stage5_chillys/` 的 Chilly's 真实背调样本已验证可导出
- `docs/validation/default-discovery-us-generator-aftermarket-run.md` 已记录当前默认发现受限状态

## 当前下一步

1. 继续争取 `search.web`，否则只能依赖用户给定 URL 列表或目录材料。
2. 按 `docs/validation/default-discovery-us-generator-aftermarket-run.md` 再跑至少 2 轮查询。
3. 完成至少 20 个去重 Candidate 的真实执行验证。
4. 记录 SearchLog / Source / Observation / Contact / 导出结果。

## 当前阻塞

- 本次会话的能力预检为 `search.web=unknown`、`source.open=available`。
- `max_output_without_manual_sources=standard_development_list`，但缺少搜索仍不足以自然扩成默认发现候选池。
