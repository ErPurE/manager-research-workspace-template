# Protocol: file_management

## 适用场景

- 目录整理
- 文件新建 / 移动 / 重命名
- README、索引、任务文件维护
- 规则文件、镜像入口同步

## 必做步骤

1. 完成 preflight，读取 runtime
2. 如果任务涉及 `.agent/`、`AGENTS.md` 或 `.github/copilot-instructions.md`，先读取 `.agent/core/structure_contract.md`
3. 先看目标目录 `README.md`（如果存在）
4. 能更新已有文件就不要新建新文件
5. 新建、移动或重命名后，同步更新受影响的索引或 README
6. 若修改的是工作区规则、个人画像或当前阶段提醒，规则正文只改 `.agent/`；只有入口读取顺序变化才同步 `CLAUDE.md`、`AGENTS.md`、`.github/copilot-instructions.md`
7. 若修改的是 agent 结构本身，结束前运行 `.agent/validate_agent_runtime.ps1`

## 路径硬规则

- 根目录不放临时文件、输出文件、脚本
- Windows 上写含中文的 JSON/Markdown 时，优先用 `apply_patch`；不要用 PowerShell heredoc 或 shell 内联 Python 生成正文，写完必须用 UTF-8 方式回读验证
- `notes/literature/` 放单篇论文阅读笔记
- `notes/thinking/` 放原理梳理、头脑风暴、方法思考
- `notes/learning/` 放课程或技术学习笔记
- `notes/experiments/` 放实验计划和实验日志
- `research/` 放综合性调研、对比表、系统性 review 材料
- `notes/ideas/` 放灵感与未固化想法
- `tasks/` 默认维护 `todo.json`、`todo_archive.md` 与 `projects.md`

## 任务管理硬规则

- `tasks/todo.json` 是待办任务唯一权威数据源，不再维护 `tasks/todo.md`
- `tasks/todo.json` 条目必须使用稳定 `id`；`area` 用于区分 `research` / `admin` / `personal`；`group` 用于 Dashboard 分组：`today` / `week` / `later` / `backlog` / `admin`
- `status` 只使用 `todo` / `in_progress` / `waiting` / `blocked` / `paused` / `done` / `cancelled`
- 同一目标、同一交付物或强依赖的一组事项优先合并为一个任务包，用 `checklist` 保存子项；避免 Dashboard 出现同类任务刷屏
- `checklist` 子项可以是旧字符串，也可以是对象 `{ "text": "...", "done": false, "updated_at": "..." }`；后续新增或改写时优先使用对象格式，以便 Dashboard 单独标记子任务完成。
- 已完成项可暂时保留为 `done`，周回顾时摘要归档到 `tasks/todo_archive.md` 后再从 JSON 中清理
- `tasks/projects.md` 只记录论文 / 学位主项目
- 若创建新灵感，更新 `notes/ideas/README.md`
- 若记录导师消息，联动 `guidance/`、`tasks/`，必要时更新 `notes/ideas/`

## handoff 必写项

- 新建 / 更新 / 移动了哪些文件
- 哪些索引或镜像已同步
- 哪些清理动作暂缓执行
- 下一步还需要检查的路径
