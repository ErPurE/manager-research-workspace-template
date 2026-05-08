# Shared Core Rules

> 这是所有模型共用的主规则。`adapters/model_notes.md` 只能做补偿备注，不能覆盖本文件。

## 规则优先级

1. `.agent/README_agent_runtime.md`
2. `.agent/core/core_rules.md`
3. `.agent/core/preflight_checklist.md`
4. `.agent/runtime/current_task.md`
5. `.agent/runtime/handoff_note.md`
6. `.agent/runtime/active_context.md`
7. `.agent/core/task_router.md`
8. 匹配的 `.agent/protocols/*.md`
9. 匹配的 `.agent/workflows/*.md`
10. `.agent/adapters/model_notes.md`

## 共享硬规则

1. 所有模型是同一岗位的接班者。换模型等于换接手人，不等于换制度。
2. 禁止再为每个模型维护完整独立规则系统。
3. 按任务类型选择协议，不按模型名称选规则。
4. 先做 preflight，再开始 substantive work。
5. 严格按需读取；如果 runtime 已经列出 working set，不要重新扫全工作区。
6. 这是科研管理工作区。除非用户明确要求或报错，不主动查看 `dashboard/` 代码。
7. 保存文件前，先看目标目录 `README.md`；已有文件能更新就不要新建。
8. 不要把临时文件、输出文件、脚本扔到根目录。
9. 修改工作区规则、个人画像或当前阶段提醒时，规则正文只写入 `.agent/`；只有启动顺序或入口路径变化时，才同步 `CLAUDE.md`、`AGENTS.md`、`.github/copilot-instructions.md`。
10. `tasks/todo.json` 是待办任务唯一权威数据源；用 `area` 区分科研主要工作、行政杂活和个人事项，用 `group` 区分 today/week/later/backlog/admin；已完成项定期归档到 `tasks/todo_archive.md`；`tasks/projects.md` 只记录论文/学位主项目。
11. 稳定的用户信息写入 `profile.md`；任务状态写入 `runtime/`；可复用经验写入 `memory/experience.json`。
12. 研究类文档必须遵守理解辅助结构；代码、文件管理等效率型任务不套研究模板。
13. 如果任务涉及维护 agent 系统本身，先读取 `.agent/core/structure_contract.md`。
14. `CLAUDE.md`、`AGENTS.md` 与 `.github/copilot-instructions.md` 只允许做 bootstrap 入口，不再承载完整规则正文。

## Runtime 规则

- `runtime/current_task.md` 是当前任务的权威状态。
- `runtime/handoff_note.md` 只保留最近一次交接，不写流水账。
- `runtime/active_context.md` 只保留最小必要上下文，防止下一个模型重扫工作区。
- 失败方法、已确认事实、未解决问题，必须显式写入 runtime，而不是隐含在长文里。
- 如果 handoff 文件超过一屏，说明写多了，应该压缩。
- 更新 agent 结构后，运行 `.agent/validate_agent_runtime.ps1`。

## Workflow Bridge

- 请求明显命中 workflow 时，先完成 preflight，再读取对应 workflow。
- workflow 负责“这类事件要联动哪些文件”。
- protocol 负责“这类任务具体怎么做”。
- 若二者冲突：全局约束遵守 `core_rules.md`，任务细节遵守对应 workflow。
