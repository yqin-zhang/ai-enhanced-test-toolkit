# AI Enhanced Test Toolkit

面向设备管理 REST API 的接口自动化测试工具链。项目包含可控的 FastAPI + SQLite 被测服务、基于 Pytest 的确定性接口回归框架，以及面向 AI Agent 的 MCP + RAG 测试工具原型。

> `ai_auto` 负责稳定、可重复的接口回归；`ai_tool` 负责把测试知识、接口调用、数据库核对和报告输出封装成可编排工具。当前 `ai_tool` 已完成离线编排，未接入大模型 Function Calling，也未使用向量数据库。

## 项目成果

- 覆盖设备注册、列表查询、单设备查询、状态更新、删除、模拟 500 等 **6 类接口**。
- 设计 **40 个测试场景**，经参数化形成 **56 条自动化用例**，覆盖 HTTP 200/400/404/405/422/500。
- Ubuntu 22.04 环境实测：**56 条用例全部通过，单轮耗时 1.32 秒**；该数据为单次全量执行结果。
- 维护 **14 份 JSON Schema**，实现状态码、Schema、业务字段、数据库状态四层校验。
- MCP 提供 **4 个工具**：知识检索、HTTP 调用、SQLite 只读查询、Markdown 报告生成。
- RAG 索引包含 **9 个知识切块**，使用中文二元分词、BM25 和短语加权检索。
- `REG-P01` 编排闭环单次完成 **10 项校验并全部通过**；历史实测 HTTP 请求耗时 **13 ms**。

## 技术栈

Python 3 | FastAPI | SQLAlchemy | SQLite | Pytest | Requests | JSON Schema | Allure | PyYAML | MCP/FastMCP | BM25

## 项目结构

```text
ai-enhanced-test-toolkit/
├── test_projects/device_server.py  # FastAPI 被测服务
├── ai_auto/                        # Pytest 接口自动化
│   ├── api/ common/ data/ schema/ tests/
│   ├── reports/ logs/
│   └── 接口测试.md
├── ai_tool/                        # MCP + RAG 测试工具原型
│   ├── skills/ rag/
│   ├── mcp_server.py mcp_client.py
│   └── demo_task.py
├── device_test.db
└── requirements.txt
```

## 快速开始

### Windows

```bat
git clone https://github.com/yqin-zhang/ai-enhanced-test-toolkit.git
cd ai-enhanced-test-toolkit
py -3.11 -m venv .venv
.\\.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

### Ubuntu / Linux

```bash
git clone https://github.com/yqin-zhang/ai-enhanced-test-toolkit.git
cd ai-enhanced-test-toolkit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 启动被测服务

必须从项目根目录启动，确保 `sqlite:///./device_test.db` 与测试使用同一个数据库。

```bash
python test_projects/device_server.py
```

服务地址：`http://127.0.0.1:8000`；接口文档：`http://127.0.0.1:8000/docs`。

### 执行 Pytest

新开终端，激活同一个虚拟环境后执行：

```bash
cd ai_auto
python -m pytest
```

冒烟测试：

```bash
python -m pytest -m smoke
```

输出目录：`ai_auto/reports/allure-results/`、`ai_auto/reports/allure-report/`（安装 Allure CLI 后）和 `ai_auto/logs/`。

### 执行 ai_tool

保持被测服务运行，回到项目根目录：

```bash
python -m pip install -r ai_tool/requirements.txt
python -m ai_tool.rag.ingest
python -m ai_tool.demo_task
```

执行链路：

```text
检索测试知识 → 调用 POST /device/register → 查询 SQLite
→ 生成 Markdown 报告 → finally 清理临时设备
```

报告输出到 `ai_tool/reports/`，索引输出到 `ai_tool/rag/store/chunks.json`。

启动 MCP Server：

```bash
python -m ai_tool.mcp_server
```

## 自动化测试覆盖

| 接口模块 | 场景数量 | 覆盖内容 |
|---|---:|---|
| 设备注册 | 12 | 正向、重复注册、缺字段、空串、超长、非法 JSON、错误方法 |
| 设备列表 | 4 | 正向、错误方法、动态路由冲突、错误路径 |
| 单设备查询 | 6 | 正向、设备不存在、删除后查询、空路径、错误方法、错误路径 |
| 设备状态修改 | 11 | 合法/非法状态、设备不存在、缺 Body、类型错误、非法 JSON、错误方法 |
| 设备删除 | 5 | 正向、重复删除、设备不存在、空路径、错误路径 |
| Mock 异常 | 2 | 模拟 500、错误方法 |
| **合计** | **40 个场景 / 56 条参数化用例** | **Ubuntu 单轮实测 56 passed，1.32s** |

## 设计要点

- Fixture 自行准备和清理数据，不依赖测试文件执行顺序。
- UUID 动态生成临时设备 ID，并通过用例级清理和 Session 级兜底清理减少脏数据。
- 对写接口执行接口响应与数据库状态一致性校验。
- 对未传 Body、空对象、非法 JSON、字段类型错误、动态路由冲突等场景做差异化断言。
- 状态更新先制造真实状态变化，再验证目标状态，避免默认值导致假通过。
- DB Skill 使用 SQLite `mode=ro`，避免与 FastAPI 抢写；连接失败返回结构化错误。

## AI 辅助测试工作流

当前版本是“工具层 + 确定性编排”原型，不宣称已经实现大模型自主生成测试用例。

1. 读取 `ai_auto/接口测试.md`，服务可用时额外读取 `/openapi.json`。
2. 按 Markdown 二级标题切分，生成9个本地知识块。
3. 使用中文二元分词、BM25 与短语加权召回相关章节。
4. 通过 ToolHub/MCP 调用 HTTP、SQLite 查询和报告生成能力。
5. 对接口响应和数据库记录执行逐项检查并输出 PASS/FAIL。
6. 使用 `finally` 删除临时设备，避免测试数据残留。

### REG-P01 实测结果

- RAG Top-1 命中注册接口测试章节。
- HTTP 返回 `200`，响应 `code=0`、`msg=注册成功`。
- SQLite 成功写入设备，默认 `status=offline`。
- 单次运行完成10项校验并全部通过。
- 单次 HTTP 请求耗时13 ms。

## 项目边界与后续方向

当前版本已完成可运行的接口自动化和 AI 工具编排原型，后续可扩展：接入模型 Function Calling、embedding/Reranker、自然语言测试任务、Playwright UI Skill、GitHub Actions、自动缺陷单和 Docker 部署。

## 项目链接

[https://github.com/yqin-zhang/ai-enhanced-test-toolkit](https://github.com/yqin-zhang/ai-enhanced-test-toolkit)
