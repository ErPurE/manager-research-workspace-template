# Agent Runtime Entry

本工作区使用的是“共享协议 + handoff 机制”。

- 不再按模型维护完整独立规则系统。
- Gemini / Claude / Copilot / Codex 在这里是同一岗位的接班者，不是不同岗位。
- 模型切换时，默认继续同一任务，而不是重新解释一套新制度。

## 启动读取顺序

1. `.agent/core/preflight_checklist.md`
2. `.agent/core/core_rules.md`
3. `.agent/runtime/current_task.md`
4. `.agent/runtime/handoff_note.md`
5. `.agent/runtime/active_context.md`
6. `.agent/core/task_router.md`
7. 匹配的 `.agent/protocols/*.md`
8. 如命中流程，再读取 `.agent/workflows/*.md`
9. 只有确实需要补偿行为时，才读取 `.agent/adapters/model_notes.md`

不要在完成以上步骤前大面积扫描工作区。

## 目录职责

- `profile.md`: 长期用户画像与当前阶段提醒
- `core/`: 所有模型共用的硬规则、preflight、路由和输出骨架
- `protocols/`: 按任务类型拆分的执行协议
- `workflows/`: 具体事件流程，如导师消息、加任务、新灵感、周回顾
- `runtime/`: 当前任务状态、handoff、最小上下文
- `memory/`: 可复用的任务记录和经验沉淀
- `adapters/`: 极薄的模型备注层，不能覆盖共享协议
- `rules/`: 旧结构兼容层，只保留跳转说明，不再作为主规则源

## Runtime 写回规则

- 开始一个新任务时，先更新 `runtime/current_task.md`
- 任务推进中，只把“下一个模型接手必须知道”的信息写进 `runtime/active_context.md`
- 退出、切换模型、额度用尽前，覆盖 `runtime/handoff_note.md`
- 任务完成后，把结果简要归档到 `memory/tasks.json`，并把 `runtime/current_task.md` 置为 `idle`
- 可复用经验写到 `memory/experience.json`，不要塞进 handoff 流水账

## 结构维护

- 更新 agent 系统前，先读 `.agent/core/structure_contract.md`
- 改规则时，优先只改 `.agent/`
- `CLAUDE.md`、`AGENTS.md` 与 `.github/copilot-instructions.md` 必须保持 bootstrap-only
- 更新完成后，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1
```

## 兼容说明

- 旧的 `.agent/rules/*.md` 仍保留，但只作为兼容入口
- `CLAUDE.md`、`AGENTS.md` 与 `.github/copilot-instructions.md` 是平台入口，不是唯一权威源
- 修改工作区规则、个人画像或当前阶段提醒时，规则正文只改 `.agent/`；只有启动顺序或入口路径变化时，才同步 `CLAUDE.md`、`AGENTS.md`、`.github/copilot-instructions.md`
