"""Skill 子包：测试执行层，不绑 pytest / Allure。

- api_skill：HTTP
- db_skill：只读 SQLite
- report_skill：Markdown 报告
"""
from ai_tool.skills.api_skill import call_api
from ai_tool.skills.db_skill import get_device
from ai_tool.skills.report_skill import write_report

__all__ = ["call_api", "get_device", "write_report"]
