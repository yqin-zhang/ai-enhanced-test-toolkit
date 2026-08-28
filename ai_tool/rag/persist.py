"""RAG 模块③ 落盘：把切块编号写入 rag/store/chunks.json。

只存原文，无 embedding。ingest 写入，retriever 通过 load_chunks 读取。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ai_tool import PKG_DIR, load_config

CHUNKS_NAME = "chunks.json"


def store_path() -> Path:
    rel = load_config()["rag"].get("store_dir", "rag/store")
    return (PKG_DIR / rel).resolve()


def chunks_file() -> Path:
    return store_path() / CHUNKS_NAME


def save_chunks(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """编号后写入 chunks.json，返回 count / path。"""
    numbered: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks, start=1):
        numbered.append(
            {
                "id": f"chunk-{i:03d}",
                "title": chunk["title"],
                "text": chunk["text"],
                "source": chunk["source"],
            }
        )

    out_dir = store_path()
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = chunks_file()
    dest.write_text(
        json.dumps({"chunks": numbered}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"count": len(numbered), "path": str(dest)}


def load_chunks() -> list[dict[str, Any]]:
    """读索引；文件不存在返回空列表。"""
    path = chunks_file()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data.get("chunks") or [])
