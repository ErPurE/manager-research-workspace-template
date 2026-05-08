# BOOTSTRAP_ONLY

# 科研工作区 Claude Code Bootstrap

本文件是 Claude Code 入口层，不是主规则库。真正的 agent 系统只在 `.agent/`。

## 工作区定位

- 这是科研管理工作区，不是默认软件开发项目
- 默认优先处理 `notes/ideas/`、`tasks/`、`guidance/`、`notes/`、`research/`
- 不主动扫描 `dashboard/` 代码，除非用户明确要求或报错
- 严格按需读取，不大面积预读

## 启动顺序

1. 读取 `.agent/README_agent_runtime.md`
2. 若任务涉及维护 agent 结构，先读 `.agent/core/structure_contract.md`
3. 读取 `.agent/core/preflight_checklist.md`
4. 读取 `.agent/core/core_rules.md`
5. 读取 `.agent/runtime/current_task.md`
6. 读取 `.agent/runtime/handoff_note.md`
7. 读取 `.agent/runtime/active_context.md`
8. 读取 `.agent/core/task_router.md`
9. 再按任务读取对应 `.agent/protocols/*.md` 和 `.agent/workflows/*.md`
10. 长期画像与当前阶段提醒在 `.agent/profile.md`

## Claude Code 导入提示

@.agent/README_agent_runtime.md
@.agent/core/preflight_checklist.md
@.agent/core/core_rules.md
@.agent/runtime/current_task.md
@.agent/runtime/handoff_note.md
@.agent/runtime/active_context.md
@.agent/core/task_router.md

## 维护边界

- `.agent/` 是唯一权威源
- `CLAUDE.md` 只保留 bootstrap，不再承载完整规则、画像镜像、handoff 或 workflow 正文
- `AGENTS.md` 是 Codex 入口层，必须保留并保持 bootstrap-only
- `.github/copilot-instructions.md` 也必须保持 bootstrap-only
- 更新 agent 结构后，运行：

```powershell
powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1
```
