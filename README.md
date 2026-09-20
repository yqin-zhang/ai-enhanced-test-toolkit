# 设备管理接口自动化测试

基于 Pytest + Requests 的设备管理 REST API 自动化测试项目。项目自建 FastAPI + SQLite 被测服务，覆盖设备注册、列表查询、单设备查询、状态更新、删除、服务异常模拟，以及跨接口端到端链路与 HTTP 协议契约。

## 项目成果

- 覆盖 **6 类接口 + 跨接口 E2E/契约**，共 **150 条可执行用例**，`pytest` 实际收集数与之一致。
- 覆盖 HTTP **200 / 307 / 400 / 404 / 405 / 422 / 500** 等成功、重定向与异常响应。
- Windows + Python 3.11 环境实测 **150 条用例全部通过，单轮约 6.5 秒**；测试结束后 SQLite 无数据残留。
- 维护 **16 份在用 JSON Schema**（`.schema.json`），对响应结构与错误类型（如 `string_type`、`model_attributes_type`）做精确校验，并跨模块复用同构 Schema。
- 关键写操作均执行 **HTTP 响应 + GET 回查 + SQLite 直连**三重核对。
- 自动生成 Allure 测试报告，并按 debug/info/error 分级记录请求、响应、耗时和失败原因。

## 技术栈

- 测试侧：Python 3.11 | Pytest | Requests | JSON Schema | PyYAML | Allure
- 被测服务：FastAPI | Uvicorn | SQLAlchemy | Pydantic | SQLite

## 被测接口

| 接口 | 方法 | 功能 |
|---|---|---|
| `/device/register` | POST | 注册设备，默认状态为 offline |
| `/device/list` | GET | 查询全部设备 |
| `/device/{device_id}` | GET | 查询单个设备 |
| `/device/{device_id}/status` | PUT | 修改设备状态（online/offline/fault） |
| `/device/{device_id}` | DELETE | 删除设备 |
| `/mock/server500` | GET | 模拟服务器 500 异常 |

服务地址：`http://127.0.0.1:8000`；交互式接口文档：`http://127.0.0.1:8000/docs`。

## 目录结构

```text
ai-enhanced-test-toolkit/
├── test_projects/              # 被测服务（测试不修改其中代码）
│   ├── device_server.py        # FastAPI 服务入口
│   ├── device_test.db          # 运行时生成的 SQLite 数据库
│   └── requirements.txt        # 服务端依赖：fastapi/uvicorn/sqlalchemy/pydantic
└── ai_auto/                    # 自动化测试工程
    ├── api/                    # 每接口一个 URL 封装类（RegisterAPI/ListAPI/DeviceAPI/StatusAPI/DeleteAPI/MockAPI）
    │   └── base.py             # BASE 地址与 join_url
    ├── common/
    │   ├── request.py          # 统一 HTTP 出口，透传 json/data/headers/params/allow_redirects
    │   ├── assert_json.py      # 状态码 + JSON + Schema 统一断言，返回 body
    │   ├── schema.py           # JSON Schema 加载（按子目录）
    │   ├── yaml_loader.py      # YAML 测试数据加载
    │   ├── db.py               # SQLite 只读直连查询
    │   ├── logger.py           # 分级文件日志
    │   └── allure_report.py    # Allure HTML 报告生成
    ├── data/                   # 8 份 YAML 测试数据（common/register/list/device/status/delete/mock/e2e）
    ├── schema/                 # 按接口分子目录的响应 Schema
    ├── tests/                  # 7 个测试文件 + conftest.py 夹具
    ├── reports/                # Allure 原始结果和 HTML 报告（运行产物）
    ├── logs/                   # debug/info/error 日志（运行产物）
    ├── 接口测试.md              # 150 条场景设计、预期与统计（用例编号来源）
    ├── pytest.ini              # Pytest 配置（alluredir、smoke 标记）
    └── requirements.txt        # 测试侧依赖：pytest/requests/allure-pytest/jsonschema/pyyaml
```

## 用例覆盖统计

| 测试文件 | 模块 | 用例数 | 主要覆盖 |
|---|---|---:|---|
| test_device_register.py | 设备注册 | 43 | 正向、重复注册、字段缺失/空串/边界长度、类型错误矩阵、非法 JSON、非对象 body、Content-Type 协商、错误方法 |
| test_device_list.py | 设备列表 | 15 | 列表结构与持久化、query 参数、路由抢占、大小写、协议方法 |
| test_device_dev.py | 单设备查询 | 24 | 正向、不存在/删除后查询、超长/空格/点号/emoji/注入样式路径、尾斜杠、方法契约 |
| test_device_status.py | 状态修改 | 40 | 三态与流转矩阵、幂等、白名单与大小写、校验顺序锁定、类型矩阵、非对象/Content-Type、307、PATCH |
| test_device_delete.py | 设备删除 | 12 | 删除成功与列表一致性、body/query 忽略、大小写防误删、超长 id、集合地址、PATCH |
| test_device_mock.py | Mock 异常 | 12 | 恒定 500、query/body 无影响、错误方法与 Allow、HEAD 无体、307、路径大小写/子路径 |
| test_device_e2e.py | E2E / 契约 | 4 | 完整生命周期、多设备隔离、405 Allow 头契约、未知根路径 404 |
| **合计** |  | **150** | **全量实测 150 passed** |

> 用例编号（如 ST-N11、DEL-P02、E2E-01）与 `接口测试.md` 表格行一一对应，Allure story 即编号。

## 框架设计要点

### 1. 分层封装

- `api/`：每接口一个类，`url()` 由 `data/*.yaml` 的路径模板生成；`BASE` 取自 `data/common.yaml` 的 `base_url`。
- `common/request.py`：唯一 HTTP 出口，自动记录日志与 Allure 附件，`**kwargs` 原样透传 Requests。
- `common/assert_json.py`：一次调用完成状态码、JSON 合法性、Schema 校验，并返回响应 body 供业务断言。
- 数据与代码分离：路径、枚举、边界值、参数化矩阵均在 `data/*.yaml` 维护。

### 2. 用例独立与数据清理

`tests/conftest.py` 提供两级夹具：

- `registered_device`：已在库的共享设备（`dev002` 类数据），用例结束自动删除；
- `new_device`：`auto_` 前缀的 UUID 临时设备，用例结束自动删除。

E2E 用例使用 `auto_e2e_` 前缀自建生命周期并在 `try/finally` 中清理；Session 结束时再扫描删除所有 `auto_*` 残留设备。删除操作容忍 404。

### 3. 四层断言

1. HTTP 状态码；
2. 响应 Body 为合法 JSON；
3. JSON Schema 结构与错误类型；
4. 业务字段值，并对写操作追加 SQLite 直连一致性校验。

### 4. 防止假通过

- 注册默认状态为 `offline`：测试改成 `offline` 时先切到其他合法状态再改回，证明状态确实发生过变化；
- 三态流转必须显式 PUT 置初态，不依赖默认值；
- 列表/单查断言按 `device_id` 查找，不写死列表下标；
- 校验顺序（Pydantic 类型 422 → 状态白名单 400 → 设备存在性 404）有专门用例锁定，防止服务端调整顺序后无感知。

### 5. 协议契约覆盖

- 尾斜杠返回 307：断言必须 `allow_redirects=False`，并核对 `Location` 头与空响应体；
- 405 响应核对 `Allow` 头（如 register 允许 POST、status 允许 PUT）；HEAD 请求只断言状态/Allow/空体，不做 Schema；
- 无 Content-Type、`text/plain` 发送 JSON 原文、表单提交等场景均按实测锁定为 422；
- CT-01 在单条用例内顺序抽查 6 个「方法 + 端点」组合，使 pytest 收集数与设计条数严格一致。

### 6. 日志与报告

每次运行写入 debug/info/error 三类日志；请求方法、URL、请求体、响应体、状态码与耗时同时写入日志并附加到 Allure 步骤。`pytest.ini` 配置 `--clean-alluredir`，每次运行自动清空上次的原始结果。

## 环境准备

### 1. 安装被测服务依赖

```bash
cd test_projects
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 2. 安装测试侧依赖

测试依赖见 `ai_auto/requirements.txt`（pytest、requests、allure-pytest、jsonschema、pyyaml），可装在同一虚拟环境中：

```bash
python -m pip install -r ../ai_auto/requirements.txt
```

## 启动被测服务

**必须从 `test_projects/` 目录启动**，因为服务以 `sqlite:///./device_test.db` 相对路径连接数据库；工作目录决定数据库文件位置，从其他目录启动会生成位置错误的空数据库，导致用例全部连不上预期数据。

```bash
cd test_projects
python device_server.py
```

保持该终端运行，另开终端执行测试。

## 执行测试

测试命令统一在 `ai_auto/` 目录下执行（`pytest.ini` 位于该目录，`pythonpath=.` 使 `api`、`common` 可直接导入）：

```bash
cd ai_auto
python -m pytest                 # 全量 150 条
python -m pytest -v              # 显示每条用例及编号
python -m pytest -m smoke        # 仅核心正向冒烟
python -m pytest -k e2e          # 按关键字筛选（如只跑 E2E）
```

指定单条用例：

```bash
python -m pytest -vs tests/test_device_status.py::TestDeviceStatus::test_device_status_fail_not_exist
```

## Allure 报告

- 原始结果：`reports/allure-results/`；
- 安装 Allure Commandline 后，会话结束会自动生成 HTML 至 `reports/allure-report/`；未安装 CLI 不影响测试执行；
- 手动生成：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

## 注意事项

- **启动目录**：服务必须 `cd test_projects` 后启动；测试必须在 `ai_auto/` 目录执行；
- 用例之间不依赖执行顺序，单条用例可独立运行；
- PowerShell 若提示执行策略（profile 无法加载）属于 shell 噪音，不影响 pytest 结果；
- `device_test.db`、`reports/allure-results`、`logs/` 均为本地运行产物，无需提交；
- 排障顺序：先确认服务存活（访问 `/docs` 或 `/mock/server500` 应返回 500），再确认 8000 端口未被占用，最后检查数据库是否生成在 `test_projects/` 下。
