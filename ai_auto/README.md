# ai_auto

设备管理接口自动化（pytest + requests）。被测服务是仓库里的 FastAPI Demo，覆盖注册、列表、查询、改状态、删除和模拟 500。

场景明细见 [接口测试.md](接口测试.md)（文档 40 条；参数化后约 56 条）。

## 目录

```
ai_auto/
  api/          接口 URL 封装
  common/       请求、断言、schema/yaml 加载、日志
  data/         用例数据（YAML）
  schema/       JSON Schema（含 common 通用错误体）
  tests/        用例和夹具
  logs/         运行日志（按级别 + 时间戳分目录）
  reports/      Allure 原始结果（allure-results）
  pytest.ini
```

不依赖 `pytest.mark.order`。需要设备的用例用 `registered_device` / `new_device` 自己注册和清理。

## 环境

在仓库根目录：

```bash
python3 -m venv .venv
source .venv/bin/activate

# 只要跑测试
pip install -r ai_auto/requirements.txt

# 本机还要起被测服务时再装
pip install -r test_projects/requirements.txt
```

测试依赖在 `ai_auto/requirements.txt`（pytest、requests、jsonschema、pyyaml、allure-pytest）。被测服务依赖在 `test_projects/requirements.txt`（fastapi、uvicorn、sqlalchemy、pydantic），不会跟着测试一起装。

查看 HTML 报告还需要本机安装 [Allure Commandline](https://allurereport.org/docs/install/)，例如：

```bash
# 任选其一
sudo apt install allure
npm install -g allure-commandline
```

## 启动被测服务

另开一个终端，在仓库根目录：

```bash
.venv/bin/python test_projects/device_server.py
```

- Base URL：`http://127.0.0.1:8000`（改地址改 `data/common.yaml`）
- 文档：`http://127.0.0.1:8000/docs`
- 不要用 `python -m test_projects/device_server.py`（`-m` 要的是模块名，不是路径）

服务需先起来再跑测试。

## 跑测试

```bash
cd ai_auto

# 全量（控制台只出摘要和失败，日志在 logs/）
../.venv/bin/python -m pytest

# 冒烟：注册 / 列表 / 查询 / 改状态(online) / 删除
../.venv/bin/python -m pytest -m smoke

# 单条排查时再开 -vs，看实时输出
../.venv/bin/python -m pytest -vs tests/test_device_status.py::TestDeviceStatus::test_device_status_fail_not_exist
```

冒烟只覆盖 CRUD 正向。异常、边界、mock 500 走全量。默认不加 `-vs`，避免全量 56 条把失败刷没。

## Allure 报告

pytest 已配置 `--alluredir=reports/allure-results`。跑完测试后，若本机有 Allure CLI，会自动生成静态网页到 **`reports/allure-report/`**（可直接放进仓库）。

```bash
cd ai_auto
../.venv/bin/python -m pytest          # 或 -m smoke
# 自动写入 reports/allure-report/index.html
```

本机需要 [Allure Commandline](https://allurereport.org/docs/install/)（依赖 Java）：

```bash
sudo apt install allure
# 或
npm install -g allure-commandline
```

没有 CLI 时只留下 `reports/allure-results/`，装好后再跑一遍测试，或手动：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
```

打开方式：

- 用浏览器打开 `reports/allure-report/index.html`
- 若页面空白（`file://` 限制），在该目录起一个本地服务：

```bash
python3 -m http.server 8080 --directory reports/allure-report
# 浏览器访问 http://127.0.0.1:8080
```

`allure serve` 是临时预览，关进程网页就没了；要留在项目里用 `generate` 后的 `allure-report`。

## 断言约定

- 嵌套 / 数组 / 422：用各接口 `schema/` 下的 jsonschema
- 400 / 404 / 405 / 500 扁平 `{"detail": "..."}`：用 `schema/common/error.schema.json`，文案仍由用例断言
- 入口统一是 `assert_json`（状态码 → 解析 body → 可选 schema）

## 日志

每次运行写入：

```
logs/info/2026-08-22_1051/info.log     # 用例起止、方法、URL、状态码
logs/debug/2026-08-22_1051/debug.log   # 含请求/响应正文
logs/error/2026-08-22_1051/error.log   # 状态码不符、schema 失败、连接失败
```

三个目录共用同一次时间戳。全绿时 `error.log` 可以为空。日志只写文件，不打控制台。

## 路由注意

`GET/DELETE /device/{device_id}` 会吃掉 `/device/` 后任意一段：

- `GET /device/lists`、`DELETE /device/list` → 业务 404「设备不存在」
- `GET /devices/list` → 框架 404 `Not Found`
- 列表的 405 只测 POST/PUT，不要测 DELETE `/device/list`
- 注册的 405 不要测 GET `/device/register`（会被当成查 id=`register`）

## 未纳入

- 注册 / 改状态 / 删除在 DB commit 失败时的 500（Demo 不好稳定构造）
