# Workflow: dashboard-inbox

## 适用场景

- preflight 发现 `.agent/runtime/inbox/pending/` 中存在 Dashboard 缓存输入。
- 用户要求处理“前端缓存区”“Dashboard inbox”“离线录入内容”。

## 最小读取

1. `.agent/runtime/inbox/README.md`
2. `.agent/runtime/inbox/pending/*.json` 的文件清单
3. 需要处理的 pending JSON 正文
4. 按条目类型再读取对应 workflow：
   - `idea` -> `.agent/workflows/new-idea.md`
   - `task` -> `.agent/workflows/add-task.md`
   - `guidance` -> `.agent/workflows/log-guidance.md`
   - `note` / `freeform` / `file_edit_review` -> 先按 `task_router.md` 判断，必要时使用 `file_management`

不要因为 inbox 存在就扫描整个工作区。

## 启动反馈

首次实质性回复前必须说明：

- pending 总数
- 各 `kind` 数量
- 本轮准备处理的范围
- 是否有无法自动判断归档位置的条目

## 路由规则

- `idea`: 走 `new-idea`，归档到 `notes/ideas/` 并同步 `notes/ideas/README.md`。
- `task`: 走 `add-task`，归档到 `tasks/todo.json`；若是论文/学位主项目，再同步 `tasks/projects.md`。
- `guidance`: 走 `log-guidance`，归档到 `guidance/`，并联动 `tasks/`。
- `note`: 若 `context.target_path` 或内容能明确指向目录，则归档到对应业务目录；否则先询问用户。
- `freeform`: 能明确判断时按最合适的 workflow 处理；不能明确判断时先询问用户，不要强行归档。
- `file_edit_review`: 检查 `context.target_path` 指向的文件是否需要同步 README、索引、任务状态或 handoff；不重复改写用户刚保存的正文。

## 状态写回

处理成功后：

1. 更新 JSON：
   - `status`: `processed`
   - `updated_at`: 当前时间
   - `result.processed_at`: 当前时间
   - `result.target_paths`: 本次实际写入或同步的正式文件路径
   - `result.summary`: 一句话说明处理结果
2. 移动到 `.agent/runtime/inbox/processed/YYYY-MM/`。
3. 从 `pending/` 删除原文件。

处理失败后：

1. 更新 JSON：
   - `status`: `failed`
   - `updated_at`: 当前时间
   - `result.error`: 失败原因或缺失信息
2. 移动到 `.agent/runtime/inbox/failed/`。
3. 在 `.agent/runtime/handoff_note.md` 写明 blocker 和下一步。

## 边界

- 不处理 `cancelled/`。
- 不把 inbox 当长期知识库；正式内容必须进入业务目录。
- 不为了处理 inbox 扩大读取范围；每条只读它实际需要的目标目录 README 和相关文件。
- 多条 pending 可以批量处理，但遇到含糊条目时，只暂停该条，不阻塞其他明确条目。

## Dashboard API Agent 模式

Dashboard 提供可视化 API Agent 面板，用来让低价 OpenAI-compatible / Anthropic-compatible API 辅助处理 pending 缓存。

- API 配置保存在 `.agent/runtime/local_api_profiles.json`，该文件必须保持 gitignored，不得提交真实密钥。
- API 调用产生的预览记录保存在 `.agent/runtime/agent_runs/`，该目录必须保持 gitignored。
- 前端只展示 masked API key；旧密钥留空保存时由后端沿用，不把明文回传给浏览器。
- 模型不能直接写文件或执行命令；它只能返回 JSON action plan。
- 允许的 action type 是 `upsert_todo`、`replace_json`、`write_text`、`replace_text`、`process_inbox`。
- 处理任务类缓存时优先使用 `upsert_todo`，不要为了新增一个任务让模型输出完整 `tasks/todo.json`；这会造成 token 浪费，也容易让 API 网关在计费后断开连接。
- 后端只允许写受限路径：`tasks/todo.json`、`guidance/README.md`、`guidance/`、`notes/`、`research/`，以及必要的 `.agent/runtime/active_context.md`、`.agent/runtime/handoff_note.md`、`.agent/memory/tasks.json`。
- 推荐先点“生成预览”，人工确认 plan 后再点“应用预览”；不要默认自动应用低价模型输出。
- 如果 API 模型输出含糊、造证据、破坏 schema、中文乱码或 action path 越界，必须拒绝应用并改由人工/Codex 处理。
- 若出现 `API HTTP 403 / 1010`，优先判断为服务商网关拦截客户端指纹或 Base URL 不是实际 API endpoint；先用 Dashboard 的“测试连接”验证 profile，再检查是否应改用真实 API 子域名、完整 `/v1` endpoint 或不拦截服务端调用的供应商。
- 若出现 `Remote end closed connection without response`，通常表示供应商已接收并可能计费，但生成/回传响应时被网关超时或断流；先压缩 prompt、限制输出、使用 `upsert_todo` 等细粒度 action，并查看 `.agent/runtime/agent_runs/` 中保存的 failed run。
