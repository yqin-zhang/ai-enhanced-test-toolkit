"""MCP 模块：进程内 ToolHub。

demo_task 走这里，不拉 MCP 子进程；mcp_server 也转调同一套实现，避免两套逻辑。
"""

from __future__ import annotations

import json
from typing import Any

from ai_tool.rag.retriever import retrieve
from ai_tool.skills.api_skill import call_api as _call_api
from ai_tool.skills.db_skill import get_device
from ai_tool.skills.report_skill import write_report as _write_report

TOOL_NAMES = (
    "retrieve_knowledge",
    "call_api",
    "query_device",
    "write_report",
)


class ToolHub:
    """四个 MCP 工具的进程内实现，和 mcp_server 暴露的名字一致。"""

    def retrieve_knowledge(self, query: str, top_k: int | None = None) -> dict[str, Any]:
        return retrieve(query, top_k)

    def call_api(
        self,
        method: str,
        path: str,
        json_body: dict | str | None = None,
    ) -> dict[str, Any]:
        payload = json_body
        # MCP tool 入参用字符串更稳，进程内也可直接传 dict
        if isinstance(json_body, str):
            payload = json.loads(json_body) if json_body.strip() else None
        return _call_api(method, path, json=payload)

    def query_device(self, device_id: str) -> dict[str, Any]:
        return get_device(device_id)

    def write_report(self, title: str, body_markdown: str) -> dict[str, Any]:
        return _write_report(title, body_markdown)

    def call(self, name: str, **kwargs: Any) -> dict[str, Any]:
        if name not in TOOL_NAMES:
            raise ValueError(f"未知工具: {name}，可选 {TOOL_NAMES}")
        return getattr(self, name)(**kwargs)

    def list_tools(self) -> list[str]:
        return list(TOOL_NAMES)
