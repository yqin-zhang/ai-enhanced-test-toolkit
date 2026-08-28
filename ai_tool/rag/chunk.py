"""RAG 模块② 分块：按 Markdown 二级标题切开。

表格留在对应章节；产出 {title, text, source}，不含 id。
"""

from __future__ import annotations

import re
from typing import Any


def split_markdown(text: str, source: str) -> list[dict[str, Any]]:
    """按 ## 切块；文首无标题部分记为「概述」。"""
    chunks: list[dict[str, Any]] = []
    parts = re.split(r"(?m)^##\s+", text)
    preamble = parts[0].strip()
    if preamble:
        chunks.append({"title": "概述", "text": preamble, "source": source})
    for part in parts[1:]:
        lines = part.splitlines()
        title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()
        chunks.append(
            {
                "title": title,
                "text": f"## {title}\n\n{body}",
                "source": source,
            }
        )
    return chunks
