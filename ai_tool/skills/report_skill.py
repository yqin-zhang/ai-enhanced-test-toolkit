"""Skill 模块：报告。写入 ai_tool/reports/ 并打印到控制台。不走 Allure。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ai_tool import PKG_DIR

REPORT_DIR = PKG_DIR / "reports"


def write_report(title: str, body_markdown: str) -> dict[str, Any]:
    """落盘一份 Markdown，返回 path。"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in title)[:40]  # 文件名去掉非法字符
    path = REPORT_DIR / f"{safe}_{stamp}.md"
    text = f"# {title}\n\n{body_markdown.rstrip()}\n"
    path.write_text(text, encoding="utf-8")
    print(text)
    return {"ok": True, "path": str(path), "title": title}
