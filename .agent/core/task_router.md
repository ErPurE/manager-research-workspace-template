# Task Router

> 按任务类型选择协议，不按模型选规则。主协议最多 1 个，辅助协议或 workflow 最多再加 1 个。

| 用户请求模式 | 主协议 | 可选 workflow | 默认输出 |
| --- | --- | --- | --- |
| 单篇论文总结、方向调研、概念解释、综述对比 | `protocols/literature_review.md` | `workflows/thinking-map.md` | `notes/literature/`、`research/` 或 `notes/thinking/` |
| 修改 `dashboard/`、调试脚本、排查代码错误 | `protocols/coding_tasks.md` | 无 | 代码变更 + 验证记录 |
| Dashboard inbox pending、前端缓存输入、离线录入内容接管 | `protocols/file_management.md` | `workflows/dashboard-inbox.md` | 正式业务目录 + `.agent/runtime/inbox/processed/` 或 `failed/` |
| 记录实验、补测计划、参数追踪、实验日志 | `protocols/experiment_recording.md` | 无 | `notes/experiments/` |
| 生成 HTML 汇报、PPT 结构、caption、叙事框架 | `protocols/html_ppt_generation.md` | `workflows/thinking-map.md` | `research/` 或 `notes/thinking/` |
| 整理目录、移动文件、更新索引、维护规则文件 | `protocols/file_management.md` | 无 | 文件变更 + 索引同步 |
| 导师消息、导师要求、口头沟通记录 | `protocols/file_management.md` | `workflows/log-guidance.md` | `guidance/` 记录 + `tasks/` 联动 |
| 新任务录入、任务状态调整 | `protocols/file_management.md` | `workflows/add-task.md` | `tasks/todo.json` / `tasks/projects.md` |
| 新灵感记录 | `protocols/file_management.md` | `workflows/new-idea.md` | `notes/ideas/` + `notes/ideas/README.md` |
| 周回顾、周总结归档 | `protocols/file_management.md` | `workflows/weekly-review.md` | `notes/weekly/` 草案或归档 |

## 判定细则

- 如果主目标是“研究理解与比较”，优先走 `literature_review`
- 如果主目标是“成品表达与汇报结构”，优先走 `html_ppt_generation`
- 如果 preflight 发现 Dashboard pending 输入，优先走 `dashboard-inbox`，再按条目类型分流到既有 workflow
- 如果主目标只是“落文件、归档、挪位置、更新索引”，优先走 `file_management`
- 如果任务既要产出内容又要归档文件，内容协议是主协议，`file_management` 只作辅助

## 不要这样做

- 不要因为换了模型，就换一套规则
- 不要同时加载 3 个以上协议
- 不要在没读 runtime 的前提下直接扫整个工作区
