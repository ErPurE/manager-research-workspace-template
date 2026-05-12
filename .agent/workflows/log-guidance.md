---
description: 记录导师的指导和建议，并自动联动更新 tasks/notes/ideas/projects
---

# 🎯 记录导师指导工作流

> 前置：先完成 `.agent/core/preflight_checklist.md`，读取 `.agent/runtime/current_task.md`、`.agent/runtime/handoff_note.md`、`.agent/runtime/active_context.md`。
> 执行结束后，刷新 `runtime/current_task.md` 和 `runtime/handoff_note.md`。

## ⚠️ 核心规则：联动更新

**当用户发来老师的消息或对话内容时，必须完成以下全部步骤，不可遗漏：**

### 步骤 1: 记录原始对话 → `guidance/`

在 `guidance/` 目录下创建新文件，文件名格式: `YYYY-MM-DD-主题关键词.md`

使用以下模板:

```markdown
# YYYY-MM-DD 标题

## 📍 信息
- 时间: YYYY-MM-DD
- 形式: 微信/口头/邮件
- 参与者: 老师, 用户

## 💬 老师原话摘要
1. 要点1
2. 要点2

## 📌 关键信息提取

| 项目 | 内容 |
| ---- | ---- |
| ...  | ...  |

## ✅ Action Items
- [ ] 任务1
- [ ] 任务2

## 📝 备注
> ⚠️ 老师可能还有口头沟通的安排未记录在此，以实际沟通为准。
```

### 步骤 2: 联动更新 → `tasks/todo.json`

根据老师消息中提到的任务安排，同步更新 `tasks/todo.json`:
- **新任务**: 添加一个稳定 `id` 的 JSON 条目
- **优先级变化**: 更新 `priority`、`group`、`status`，并在 `note` 中标注来源（如"老师 X/XX 要求"）
- **截止日期**: 如老师提到了时间要求，更新 `due_date` 或 `due_label`
- **状态更新**: 如有任务完成或推进，更新 `status`

### 步骤 3: 联动更新 → `tasks/projects.md`

如果老师的消息涉及项目级别的变化：
- 进度百分比调整
- 里程碑完成/新增
- 项目方向变化

### 步骤 4: 联动更新 → `notes/ideas/`（如适用）

如果老师提到了新的研究方向或想法，在 `notes/ideas/` 中创建或更新对应记录。

### 步骤 5: 确认汇总

完成所有更新后，向用户汇总本次联动更新了哪些文件和内容。

## 注意事项

- 口头沟通用户可能没有完整转述，记录以用户提供的内容为准，不要自行脑补
- 如果消息中的安排与现有任务有冲突，提醒用户确认
- 保留老师的原话关键表述，不要过度改写
