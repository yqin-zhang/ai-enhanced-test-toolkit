"""MCP 模块：stdio Server，把四个测试工具挂到官方协议上。

工具名与 mcp_client.ToolHub 一致：retrieve_knowledge / call_api / query_device / write_report。
真正执行走 ToolHub，本文件只做协议包装。入口：python -m ai_tool.mcp_server
"""

from __future__ import annotations

import warnings
from typing import Any

from ai_tool import load_config
from ai_tool.mcp_client import ToolHub

# mcp 1.x 导入 FastMCP 时的无害告警
warnings.filterwarnings(
    "ignore",
    message="Field 'lifespan' has an incomplete definition",
)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # mcp SDK v2 把 FastMCP 改名为 MCPServer
    from mcp.server import MCPServer as FastMCP

_hub = ToolHub()  # 与 demo_task 共用同一套 Skill，避免两套实现
_name = load_config()["mcp"].get("server_name", "ai-tester")
mcp = FastMCP(_name)


@mcp.tool()
def retrieve_knowledge(query: str, top_k: int = 3) -> dict[str, Any]:
    """从接口测试文档中检索相关用例知识。"""
    return _hub.retrieve_knowledge(query, top_k)


@mcp.tool()
def call_api(method: str, path: str, json_body: str = "") -> dict[str, Any]:
    """调用被测设备接口。json_body 为 JSON 字符串，GET/DELETE 可留空。"""
    return _hub.call_api(method, path, json_body=json_body)


@mcp.tool()
def query_device(device_id: str) -> dict[str, Any]:
    """只读查询 SQLite 中的设备行，用于接口-库对照。"""
    return _hub.query_device(device_id)


@mcp.tool()
def write_report(title: str, body_markdown: str) -> dict[str, Any]:
    """把一次 AI 测试的检索、请求、库核对写成 Markdown 报告。"""
    return _hub.write_report(title, body_markdown)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
