# Manager 科研工作区模板

一个以可视化前端为中心的本地科研管理器，也是一套可交接、可记忆、可长期维护的 Agent 工作区。

你不需要先理解所有文件。日常使用只需要打开 Dashboard：记录想法、整理任务、保存导师/合作者反馈、查看笔记，让 AI Agent 在合适的时候接管和归档。

> This repository is a clean public template. It contains no personal profile, private tasks, research records, API keys, or runtime history.

## 它适合谁

- 正在做论文、实验、项目或长期研究的人。
- 想把任务、灵感、导师建议、笔记放在一个本地工作区里的人。
- 想让 Codex、Claude Code、Copilot 或其他 Agent 在同一套规则下接力工作的人。
- 想用低价 OpenAI-compatible / Anthropic-compatible API 辅助整理缓存内容，但又不想让模型直接乱改文件的人。

## 快速开始

1. 安装 Python 3.x。
2. 运行 `dashboard/start.bat`。
3. 浏览器打开 `http://127.0.0.1:5000`。
4. 在 Dashboard 里开始录入任务、灵感、指导记录和笔记。
5. 打开 `.agent/profile.md`，填入你自己的研究背景、写作偏好和协作习惯。

## 日常怎么用

- **总览**：查看任务、灵感、指导记录、笔记和待处理缓存数量。
- **快速录入**：想到什么先放进缓存区，不必当场整理。
- **任务面板**：用常规 todo 软件的方式管理任务包、优先级、状态和 checklist。
- **导师指导 / 笔记 / 灵感**：用 Markdown 保存长期科研上下文。
- **文件查看与编辑**：在前端打开 Markdown，编辑后自动备份，也可以让 Agent 复查。
- **API Agent**：配置多个 API profile，先生成处理预览，再人工确认应用。

## Dashboard 是主要入口

这个模板不是要求你每天手动维护一堆文件。文件系统是底层数据，Dashboard 才是主要工作台。

典型流程：

1. 你在 Dashboard 里快速写下“要补导师说的参考文献”。
2. 这条内容进入 `.agent/runtime/inbox/pending/`。
3. Agent 或 API Agent 读取缓存，生成一个处理预览。
4. 你确认后，它把内容写入 `tasks/`、`guidance/`、`notes/` 或 `research/`。
5. 缓存项被标记为已处理，正式内容进入长期目录。

## `.agent/` 为什么重要

`.agent/` 是这个仓库最有价值的部分之一。它让这个工作区不只是“文件夹 + 前端”，而是一个可长期协作的 Agent Workspace。

它可以：

- 保存你的长期画像：研究方向、写作偏好、当前阶段、常见提醒。
- 记录可复用经验：例如某类任务应该怎么处理，某些错误以后如何避免。
- 维护 handoff：一个模型工作到一半，另一个模型可以继续，不必重新扫整个项目。
- 管理 workflows：新增任务、记录指导、处理缓存、写实验记录都有固定流程。
- 约束 AI 行为：低价模型只能返回 action plan，真正写文件由本地后端按白名单执行。

你可以在 AI 对话中说：

- “记住我更喜欢先宽后窄地写汇报。”
- “以后导师消息都先归到 guidance，再同步任务。”
- “把这次踩坑写进经验，后续 Agent 不要再犯。”

这些内容应该进入 `.agent/profile.md`、`.agent/memory/experience.json` 或对应 workflow，而不是散落在聊天记录里。

## API Agent 能处理什么

当前 API Agent 不是只能生成任务 JSON。它的设计目标是处理 Dashboard 缓存区里的多种内容：

- `task`：生成或更新 `tasks/todo.json`，目前测试最充分。
- `guidance`：可写入 `guidance/` 并同步索引或任务。
- `idea`：可写入 `notes/ideas/`。
- `note` / `freeform`：可按内容写入 `notes/`、`research/` 或其他允许目录。
- `file_edit_review`：可检查前端编辑后是否需要同步索引、任务或 handoff。

需要注意：当前版本对 `task` 的细粒度动作 `upsert_todo` 最成熟；其他类型依赖模型返回 `write_text`、`replace_text`、`process_inbox` 等 action，使用时建议先看预览再应用。低价 API 输出不稳定时，应由 Codex/Claude Code 人工接管。

## 数据边界

- `tasks/todo.json` 是任务唯一权威源。
- `.agent/` 是 Agent 规则、记忆、画像和交接的权威源。
- `.agent/runtime/local_api_profiles.json` 保存本地 API key，必须保持 untracked。
- `.agent/runtime/agent_runs/` 保存本地 API 调用记录，必须保持 untracked。
- 不要把私人画像、真实科研记录、导师内容、任务列表或 API key 发布到公开仓库。

## 验证命令

```powershell
python -m py_compile dashboard\server.py
node --check dashboard\app.js
powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1
```

---

# Manager Research Workspace Template

Manager is a local research workspace centered around a visual Dashboard, plus an Agent workspace that can remember preferences, hand off work, and safely process captured research context.

You do not need to understand every file before using it. Open the Dashboard, capture things quickly, review Agent previews, and let the workspace organize tasks, notes, guidance, and research records over time.

## Quick Start

1. Install Python 3.x.
2. Run `dashboard/start.bat`.
3. Open `http://127.0.0.1:5000`.
4. Start from the Dashboard.
5. Fill `.agent/profile.md` with your own research background and collaboration preferences.

## What You Use Day To Day

- Dashboard overview for ideas, tasks, guidance, notes, and inbox items.
- Quick capture for thoughts that are not ready to organize yet.
- Todo board backed by `tasks/todo.json`.
- Markdown notes for guidance, ideas, research, and long-term context.
- API Agent profiles for OpenAI-compatible and Anthropic-compatible providers.
- Preview-before-apply workflow so low-cost models do not directly mutate your workspace.

## Why The Agent Folder Matters

`.agent/` is the workspace brain. It stores:

- User profile and collaboration preferences.
- Reusable experience and lessons learned.
- Runtime handoff notes for model-to-model continuity.
- Workflows for tasks, guidance, ideas, inbox processing, and writing/research work.
- Safety boundaries for what AI models may read, propose, and write.

This makes the repository useful not only as a research dashboard, but as a durable Agent workspace.

Version: v2.0.0-template
