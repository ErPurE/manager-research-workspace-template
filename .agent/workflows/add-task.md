---
description: 添加新的待办任务
---

# ✅ 添加任务工作流

> 前置：先完成 `.agent/core/preflight_checklist.md`，读取 `.agent/runtime/current_task.md`、`.agent/runtime/handoff_note.md`、`.agent/runtime/active_context.md`。
> 执行结束后，刷新 `runtime/current_task.md` 和 `runtime/handoff_note.md`。

## 权威文件

- 待办任务唯一权威源：`tasks/todo.json`
- 已完成任务归档：`tasks/todo_archive.md`
- 论文 / 学位主项目进度：`tasks/projects.md`
- 不再维护 `tasks/todo.md`

## 快速添加

1. 打开 `tasks/todo.json`
2. 在 `items` 数组中追加一个条目
3. 使用稳定、短小、可读的 `id`，格式建议为 kebab-case
4. 根据任务性质设置：
   - `area`: `research` / `admin` / `personal`
   - `group`: `today` / `week` / `later` / `backlog` / `admin`
   - `status`: `todo` / `in_progress` / `waiting` / `blocked` / `paused` / `done` / `cancelled`
   - `priority`: `1` / `2` / `3`

## 条目模板

```json
{
  "id": "stable-kebab-case-id",
  "title": "能直接行动的一句话任务",
  "area": "research",
  "project": "Paper 1",
  "group": "week",
  "status": "todo",
  "priority": 2,
  "due_label": "本周",
  "due_date": null,
  "tags": ["标签"],
  "note": "必要背景、来源和约束；不要写长篇正文",
  "checklist": [
    {
      "text": "可选子项 1",
      "done": false
    },
    {
      "text": "可选子项 2",
      "done": false
    }
  ]
}
```

## 维护规则

- `title` 必须可行动，避免写成宽泛主题。
- `note` 只放必要背景、来源和约束；导师原话仍应记录到 `guidance/`。
- 同类任务优先合并为一个任务包，用 `checklist` 保存子项；不要把同一目标拆成多个相邻任务。`checklist` 子项推荐使用 `{ "text": "...", "done": false }`，旧字符串格式仍兼容，Dashboard 首次点击时会自动转换为对象格式。
- 如果一个任务包超过 7 个 checklist 子项，说明范围过大，应拆成两个任务包。
- 科研任务和行政杂活不要混在标题里，用 `area` 区分。
- Dashboard 依赖 `group` 分栏展示，不要发明新 group，除非同步改前端和本规则。
- 任务完成后先把 `status` 改为 `done`；周回顾时再归档到 `tasks/todo_archive.md` 并从 JSON 清理。
