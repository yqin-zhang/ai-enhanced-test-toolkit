# 设备管理接口自动化测试

基于 Pytest + Requests 的设备管理 REST API 自动化测试项目。项目自建 FastAPI + SQLite 被测服务，覆盖设备注册、列表查询、单设备查询、状态更新、删除及服务异常等核心链路。

## 项目成果

- 覆盖 **6 类接口**、**40 个测试场景**，经参数化形成 **56 条可执行用例**。
- 覆盖 HTTP 200、400、404、405、422、500 等常见成功与异常响应。
- Ubuntu 22.04 环境实测 **56 条用例全部通过，单轮耗时 1.32 秒**；该数据为单次全量执行结果。
- 维护 **14 份 JSON Schema**，对响应结构、业务字段和数据库状态进行多层校验。
- 自动生成 Allure 测试报告，并按 debug/info/error 分级记录请求、响应、耗时和失败原因。

## 技术栈

Python 3 | Pytest | Requests | FastAPI | Uvicorn | SQLAlchemy | SQLite | JSON Schema | PyYAML | Allure

## 被测接口

| 接口 | 方法 | 功能 |
|---|---|---|
| `/device/register` | POST | 注册设备，默认状态为 offline |
| `/device/list` | GET | 查询全部设备 |
| `/device/{device_id}` | GET | 查询单个设备 |
| `/device/{device_id}/status` | PUT | 修改设备状态 |
| `/device/{device_id}` | DELETE | 删除设备 |
| `/mock/server500` | GET | 模拟服务器 500 异常 |

## 目录结构

```text
ai_auto/
├── api/                 # 接口 URL 与测试数据封装
├── common/
│   ├── request.py       # HTTP 请求、耗时及日志封装
│   ├── assert_json.py   # 状态码、JSON、Schema 统一断言
│   ├── schema.py        # JSON Schema 加载
│   ├── yaml_loader.py   # YAML 测试数据加载
│   ├── db.py            # SQLite 只读查询
│   ├── logger.py        # 分级文件日志
│   └── allure_report.py # Allure HTML 报告生成
├── data/                # YAML 测试数据
├── schema/              # 成功、错误及参数校验 Schema
├── tests/               # 各接口测试用例及 Fixture
├── reports/             # Allure 原始结果和 HTML 报告
├── logs/                # debug/info/error 日志
├── 接口测试.md           # 测试场景设计与统计
├── pytest.ini            # Pytest 配置
└── requirements.txt     # 测试依赖
```

## 测试设计

### 正向场景

- 注册设备后校验响应中的设备 ID，并从数据库读回记录；
- 查询列表并按设备 ID 定位目标设备，不依赖列表顺序；
- 查询单个设备并核对设备名称、类型和状态；
- 修改设备状态后再次 GET，确认状态真实发生变化；
- 删除设备后再次查询接口和数据库，确认记录已不存在。

### 异常与边界场景

- 重复注册、设备不存在、删除后再查询/修改、重复删除；
- 必填字段缺失、空字符串、超长字段、字段类型错误；
- 未传请求体、空 JSON、JSON 语法错误、JSON 类型不正确；
- 非法设备状态、大小写不匹配、错误请求方法；
- 空路径、错误路径及动态路由冲突；
- 模拟 500 服务异常。

## 测试覆盖统计

| 接口模块 | 场景数 | 参数化后用例 | 主要覆盖 |
|---|---:|---:|---|
| 设备注册 | 12 | 17 | 正向、重复注册、字段校验、非法 JSON、错误方法 |
| 设备列表 | 4 | 6 | 列表结构、路由冲突、错误路径、错误方法 |
| 单设备查询 | 6 | 7 | 正向、设备不存在、删除后查询、路径及方法异常 |
| 状态修改 | 11 | 17 | 合法/非法状态、缺 Body、类型错误、状态持久化 |
| 设备删除 | 5 | 5 | 删除成功、重复删除、设备不存在、路径异常 |
| Mock 异常 | 2 | 4 | 500 响应、错误方法 |
| **合计** | **40** | **56** | **全量实测 56 passed** |

> 场景数按业务测试设计统计；参数化后用例数以 pytest 实际收集结果为准。

## 框架设计要点

### 1. 用例独立与数据清理

使用 `registered_device` 和 `new_device` Fixture 管理测试前置数据。临时设备 ID 通过 UUID 动态生成，并在用例结束后清理；Session 结束时再次扫描并清理 `auto_*` 设备，避免测试脏数据残留。

### 2. 四层断言

统一通过 `assert_json` 完成：

1. HTTP 状态码校验；
2. 响应 Body 是否为合法 JSON；
3. JSON Schema 结构校验；
4. 业务字段及 SQLite 数据一致性校验。

### 3. 防止假通过

设备注册默认状态为 `offline`。状态更新用例在目标状态与当前状态相同时，先切换到其他合法状态，再更新到目标状态，确保断言验证的是实际变化而不是默认值。

### 4. 可定位的日志和报告

每次运行按同一时间戳生成 debug/info/error 三类日志。请求方法、URL、请求体、响应体、状态码和耗时会写入日志，并通过 Allure 附加到对应测试步骤。

## 环境准备

在仓库根目录创建虚拟环境并安装依赖。

Windows：

```bat
py -3.11 -m venv .venv
.\\.venv\\Scripts\\activate
python -m pip install -r requirements.txt
```

Ubuntu / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 启动被测服务

必须从仓库根目录启动，保证服务与测试使用同一个 `device_test.db`。

Windows 和 Linux 均可使用：

```bash
python test_projects/device_server.py
```

服务地址：`http://127.0.0.1:8000`  
接口文档：`http://127.0.0.1:8000/docs`

保持服务终端运行，再打开另一个终端执行测试。

## 执行测试

```bash
cd ai_auto
python -m pytest
```

只运行 CRUD 核心冒烟：

```bash
python -m pytest -m smoke
```

指定单条用例：

```bash
python -m pytest -vs tests/test_device_status.py::TestDeviceStatus::test_device_status_fail_not_exist
```

## Allure 报告

项目已配置 `--alluredir=reports/allure-results`。运行测试后：

- 原始结果位于 `reports/allure-results/`；
- 安装 Allure Commandline 后，HTML 报告位于 `reports/allure-report/`；
- 若未安装 Allure CLI，测试仍可正常执行，只是不生成 HTML 页面。

手动生成报告：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

## 注意事项

- 服务必须从仓库根目录启动，否则相对路径数据库可能落到其他目录；
- 测试建议使用项目自己的 `.venv`，避免调用其他项目的 Python 解释器；
- 不要依赖测试文件执行顺序，单条用例应能独立运行；
- `device_test.db`、Allure 原始结果和运行日志均属于本地运行产物，无需提交到代码仓库。
