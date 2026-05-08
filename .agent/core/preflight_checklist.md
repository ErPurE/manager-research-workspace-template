# Preflight Checklist

> 每次新任务开始、每次模型切换接手，都按这个清单执行。

## A. 最小加载

- [ ] 读取 `.agent/README_agent_runtime.md`
- [ ] 读取 `.agent/core/core_rules.md`
- [ ] 读取 `.agent/runtime/current_task.md`
- [ ] 读取 `.agent/runtime/handoff_note.md`
- [ ] 读取 `.agent/runtime/active_context.md`
- [ ] 读取 `.agent/core/task_router.md`
- [ ] 检查 `.agent/runtime/inbox/pending/` 是否有 Dashboard 缓存输入

## B. 选择执行路径

- [ ] 判断这是“继续当前任务”还是“新任务”
- [ ] 若存在 Dashboard pending 输入，读取 `.agent/runtime/inbox/README.md` 与 `.agent/workflows/dashboard-inbox.md`
- [ ] 选择 1 个主协议：`.agent/protocols/*.md`
- [ ] 如需要，只额外加载 1 个辅助协议或 1 个 workflow
- [ ] 列出接下来必须读取的最小文件集

## C. 写文件前

- [ ] 检查目标目录 `README.md`（如果存在）
- [ ] 检查目标内容是否已存在，优先更新而不是新建
- [ ] 确认路径符合工作区存放规则

## D. 首次实质性回复前

- [ ] 用一句话回显 preflight 结果
- [ ] 格式建议：`Preflight: protocol=<...>; runtime=loaded; next=<...>`
- [ ] 若存在 Dashboard pending 输入，说明 pending 总数、类型分布与本轮接管方式
- [ ] 如果是接班，明确说明“继续 runtime 中记录的任务”，不要重新扫全工作区

## E. 退出或交接前

- [ ] 更新 `.agent/runtime/current_task.md`
- [ ] 覆盖 `.agent/runtime/handoff_note.md`
- [ ] 压缩 `.agent/runtime/active_context.md` 到最小必要信息
- [ ] 若任务完成：归档到 `.agent/memory/tasks.json`，并把 `current_task.md` 置为 `idle`
