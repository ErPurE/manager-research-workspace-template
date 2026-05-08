# Model Notes

> 这里只记录极薄的模型备注层，不能覆盖 `core/` 和 `protocols/`。
> 如果备注和共享协议冲突，一律以共享协议为准。

| 模型 | 常见优势 | 常见风险 | 补偿动作 |
| --- | --- | --- | --- |
| Gemini | 起草快，适合先铺结构 | 长上下文里容易漏掉后段限制 | 任务包压短；强制先读 preflight 和 runtime |
| Claude / Claude Code | 长文理解和整理较稳；Claude Code 默认会读取项目级 `CLAUDE.md` | 容易写太长，把硬规则稀释掉；若缺少 `CLAUDE.md`，可能不会自动进入 `.agent/` 规则链 | 保持 `CLAUDE.md` 为 bootstrap-only；强制固定输出骨架；handoff 只写短句 |
| Copilot | 仓库内文件感知强 | 容易直接跟着当前文件上下文走，跳过全局协议 | 动手前先读 `README_agent_runtime.md` 和 `task_router.md` |
| Codex | 执行、补丁、验证链条清晰 | 容易过度聚焦实现细节 | 先确认任务是否真的属于代码任务，再动代码 |

## 使用边界

- 这些备注只用于“如何减少该模型常犯错”
- 不要把它们扩写成独立制度
- 不要在这里重复 core / protocol 的内容
