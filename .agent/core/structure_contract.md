# Structure Contract

> 目的：以后更新 agent 系统时，不要把结构重新改坏。

## 一、权威源

- 唯一主系统：`.agent/`
- 平台入口层：`CLAUDE.md`、`AGENTS.md`、`.github/copilot-instructions.md`
- 旧兼容层：`.agent/rules/`

只有 `.agent/` 可以承载真正的规则、protocol、runtime、memory。

## 二、目录职责不能混

- `core/`：共享硬规则、读取顺序、任务路由、输出骨架
- `protocols/`：按任务类型拆协议
- `runtime/`：当前任务状态与 handoff
- `memory/`：长期可复用经验与任务归档
- `adapters/`：极薄模型备注层
- `workflows/`：事件型流程
- `rules/`：仅兼容旧入口，不再扩写

### runtime/inbox 边界

- `.agent/runtime/inbox/` 是 Dashboard 离线录入的运行期待处理队列，不是长期知识库。
- `pending/` 只保存等待 Agent 接管的原始输入。
- `processed/`、`failed/`、`cancelled/` 只保存处理追踪；正式内容必须归档到 `notes/`、`tasks/`、`guidance/`、`research/` 等业务目录。
- Dashboard 只能写入或取消 pending；Agent 负责 processed / failed 状态流转。

## 三、禁止事项

- 禁止重新建立 `gemini_rules`、`claude_rules`、`copilot_rules`、`codex_rules` 一类完整制度
- 禁止把 `CLAUDE.md`、`AGENTS.md` 或 `.github/copilot-instructions.md` 再写成长篇完整镜像
- 禁止把 handoff、当前任务状态、用户画像摘要写回入口文件
- 禁止把共享硬规则复制到多个模型专属文件中分别维护

## 四、允许事项

- 可以在 `.agent/core/` 中更新共享规则
- 可以在 `.agent/protocols/` 中新增任务协议
- 可以在 `.agent/runtime/` 中更新当前任务状态
- 可以在 `.agent/memory/` 中补经验与归档
- 可以在 `.agent/adapters/model_notes.md` 中增加极薄模型备注
- 只有当启动顺序或入口路径变化时，才需要同步改 `AGENTS.md` 与 `.github/copilot-instructions.md`

## 五、更新 agent 的正确顺序

1. 先改 `.agent/`
2. 如果改动影响入口读取顺序，再同步 `CLAUDE.md`、`AGENTS.md`
3. 如果改动影响 Copilot 启动入口，再同步 `.github/copilot-instructions.md`
4. 不需要时，不要碰入口文件
5. 改完后运行 `powershell -ExecutionPolicy Bypass -File .agent\validate_agent_runtime.ps1`

## 六、入口文件必须保持 bootstrap-only

入口文件只允许保留这些内容：

- 工作区一句话定位
- 启动读取顺序
- 几条最关键硬约束
- 指向 `.agent/` 主系统的说明
- 维护边界与验证命令

入口文件不应该再包含：

- 长篇研究输出规则
- 大段个人画像镜像
- 当前阶段提醒长清单
- workflow 细节模板正文

这些内容都应留在 `.agent/`。
