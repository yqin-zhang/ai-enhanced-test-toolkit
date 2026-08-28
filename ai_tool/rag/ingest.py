"""RAG 模块：离线入库入口。串起 load → chunk → persist。

命令：python -m ai_tool.rag.ingest
"""

from __future__ import annotations

from typing import Any

from ai_tool import load_config
from ai_tool.rag.chunk import split_markdown
from ai_tool.rag.load import fetch_openapi, load_markdown_documents
from ai_tool.rag.persist import chunks_file, save_chunks, store_path

__all__ = ["ingest", "chunks_file", "store_path"]


def ingest() -> dict[str, Any]:
    """切块入库，返回 {count, path}。"""
    cfg = load_config()
    chunks: list[dict[str, Any]] = []
    for doc in load_markdown_documents(cfg):
        chunks.extend(split_markdown(doc["text"], doc["source"]))
    openapi = fetch_openapi(cfg)
    if openapi:
        chunks.append(openapi)
    return save_chunks(chunks)


def main() -> None:
    result = ingest()
    print(f"入库 {result['count']} 个切块 -> {result['path']}")


if __name__ == "__main__":
    main()
