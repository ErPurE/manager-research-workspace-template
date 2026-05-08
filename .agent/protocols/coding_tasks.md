# Protocol: coding_tasks

## 适用场景

- 用户明确要求查看或修改 `dashboard/`
- 用户报告脚本或页面运行错误，需要调试
- 用户明确要求写或改本工作区脚本

## 必做步骤

1. 完成 preflight，读取 runtime
2. 先写清目标行为、成功信号和文件范围
3. 只读取相关代码文件，不主动扫 `dashboard/` 全目录
4. 优先修改已有文件；不要为一次性操作在根目录留下临时脚本
5. 做最小必要验证，并记录命令和结果
6. 交付时说明：改了什么、怎么验证、还有什么没确认

## 硬规则

- 这是科研管理工作区，不是默认代码仓库；代码任务必须由用户明确触发
- 不能覆盖或回退用户已有改动
- 如果发现 unrelated dirty changes，绕开它们，不要清理
- 如果调试失败，必须把失败命令、报错和判断写入 handoff
- 涉及实验数据处理的脚本，要放在合适的脚本目录或数据目录，不要乱放
- Windows 上修改 `.bat` 文件时尽量使用 ASCII + CRLF；修改前端 JSON/Markdown 数据后必须验证中文没有变成 `?` 或乱码
- Dashboard API 密钥只能存在 `.agent/runtime/local_api_profiles.json` 这类本机 runtime 文件中；不得写入 README、代码、任务 JSON、handoff 或 git tracked 文件
- 低价 API/Claude Code 只能通过后端受限 action plan 处理缓存，不允许让模型直接执行 shell 或写任意路径

## handoff 必写项

- 已读文件
- 已改文件
- 已运行命令 / 测试
- 成功与失败结果
- 当前 blocker
- 下一步最可能有效的动作
