# ai-enhanced-test-toolkit

测试开发秋招个人 Demo。仓库里有被测服务、一套 pytest 接口自动化，以及 MCP + RAG 的 AI 测试工具骨架。

## 目录

1. **`test_projects/device_server.py`**：设备管理模拟后端（FastAPI + SQLite）。提供注册、列表、查询、改状态、删除和模拟 500。
2. **`ai_auto/`【项目 1】**：pytest + requests 接口自动化。正向 / 异常 / 边界、jsonschema 校验、接口-库一致性、日志和 Allure 报告。说明见 [ai_auto/README.md](ai_auto/README.md)，场景明细见 [ai_auto/接口测试.md](ai_auto/接口测试.md)。
3. **`ai_tool/`【项目 2｜骨架】**：MCP + Skill + RAG。进程内编排跑通「检索 → 调接口 → 对库 → 出报告」；MCP Server 把同一套工具挂到 stdio。说明见 [ai_tool/README.md](ai_tool/README.md)。

## 技术栈

Python 3 | FastAPI | SQLite | SQLAlchemy | Pytest | Requests | jsonschema | Allure | MCP | PyYAML

## 快速开始

```bash
python3 -m venv .venv
source .venv/bin/activate

# 只要跑测试（不含 FastAPI）
pip install -r ai_auto/requirements.txt

# 还要在本机起被测服务时再装
pip install -r test_projects/requirements.txt

# 另开终端启动被测服务（必须在仓库根目录，SQLite 才落在本目录）
.venv/bin/python test_projects/device_server.py

# 跑自动化
cd ai_auto
../.venv/bin/python -m pytest
```

Windows / PowerShell：先 `cd` 进 `ai-enhanced-test-toolkit`，解释器用项目内这个（相对路径要写 `.\.venv\...`，不要写成 `.venv\...`）：

`.\.venv\Scripts\python.exe`

项目 2 骨架：

```powershell
cd D:\面试项目1+2\ai-enhanced-test-toolkit
.\.venv\Scripts\python.exe -m pip install -r ai_tool\requirements.txt
# 被测服务已启动的前提下
.\.venv\Scripts\python.exe -m ai_tool.rag.ingest
.\.venv\Scripts\python.exe -m ai_tool.demo_task
```

两个都要可以 `pip install -r requirements.txt`（会装齐项目 1 + 项目 2）。

更完整的环境、冒烟、日志和 Allure 用法见 [ai_auto/README.md](ai_auto/README.md)。

## 后续方向

- 接入 Playwright，补 UI Skill
- 给项目 2 接 LLM Function Calling，检索侧加 embedding / Reranker
- 自动缺陷报告
