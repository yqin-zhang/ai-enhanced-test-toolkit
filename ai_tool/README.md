# ai_tool（项目 2）

MCP + Skill + RAG 的 AI 接口测试骨架。本轮不接大模型、不上向量库；一条离线编排就能打项目 1 的设备接口、对 SQLite、写出报告。

面试一句话：项目 1 是确定性的 pytest 回归；项目 2 是同一套被测服务上的 AI 编排层——MCP 暴露测试工具，RAG 提供用例知识，Skill 负责发请求、查库、出报告。

## 目录

```
ai_tool/
  config.yaml       被测地址、库路径、RAG 源、llm 开关（默认关）
  mcp_server.py     官方 MCP stdio 服务，暴露 4 个 tool
  mcp_client.py     进程内 ToolHub（demo 走这里，不拉子进程）
  demo_task.py      REG-P01 离线剧本
  skills/           api / db / report
  rag/              按步骤拆分：load / chunk / persist / tokenize / score / retriever
                    离线入口 ingest.py（①②③）；在线入口 retriever.py（④⑤⑥）
```

四个 MCP 工具：`retrieve_knowledge`、`call_api`、`query_device`、`write_report`。

## 环境

解释器请用项目内虚拟环境，不要用仓库上一层那个空壳 `.venv`：

`d:\面试项目1+2\ai-enhanced-test-toolkit\.venv\Scripts\python.exe`

先进入仓库根目录 `ai-enhanced-test-toolkit/`（不要停在上一层 `面试项目1+2`）。PowerShell 下相对路径必须带 `.\`，否则会把 `.venv` 当成模块名：

```powershell
cd D:\面试项目1+2\ai-enhanced-test-toolkit
.\.venv\Scripts\python.exe -m pip install -r ai_tool/requirements.txt
```

依赖是 `mcp`（官方 SDK，FastMCP）、`requests`、`pyyaml`。不要装 sentence-transformers / chromadb。

## 运行

先起被测服务（必须在仓库根目录启动，SQLite 才是 `device_test.db`）：

```powershell
cd D:\面试项目1+2\ai-enhanced-test-toolkit
.\.venv\Scripts\python.exe test_projects\device_server.py
```

另开终端，同样先 `cd` 到 `ai-enhanced-test-toolkit`：

```powershell
.\.venv\Scripts\python.exe -m ai_tool.rag.ingest
.\.venv\Scripts\python.exe -m ai_tool.demo_task
```

`demo_task` 会：检索「注册正向 / 默认 offline」→ POST 注册一台一次性设备 → 查库核对 `status=offline` → 写 `ai_tool/reports/` → DELETE 清理。

服务没起来会直接退出，并提示先启动 `device_server.py`。

MCP stdio 服务（给 Cursor 等宿主用，本轮不必挂上）：

```powershell
.\.venv\Scripts\python.exe -m ai_tool.mcp_server
```

## 和项目 1 的关系

- 被测服务、库文件共用 `test_projects/device_server.py` + `device_test.db`。
- RAG 默认读 `ai_auto/接口测试.md`，服务已启动时再附带 `/openapi.json`。
- 不 import `ai_auto.common.request`（会绑 Allure/pytest）。Skill 是薄封装，思路对齐项目 1 的 request / db / 报告。
- pytest 用例保持独立，本模块不替代回归集。

## 后续（本轮故意没做）

- `config.yaml` 里 `llm.enabled` 仍为 false：接 OpenAI 兼容接口做 Function Calling。
- 检索换成 embedding + Reranker。
- Playwright UI Skill、自动缺陷单。
