"""RAG 模块⑥ 检索：读索引、打分、返回 top_k hits。

无索引时返回 error=index_missing。demo_task / ToolHub 调 retrieve()。
"""

from __future__ import annotations

from typing import Any

from ai_tool import load_config
from ai_tool.rag.persist import load_chunks
from ai_tool.rag.score import score_documents
from ai_tool.rag.tokenize import tokenize

__all__ = ["retrieve", "tokenize"]


def retrieve(query: str, top_k: int | None = None) -> dict[str, Any]:
    """按 query 返回 {query, top_k, hits}；hits 含 title / score / text。"""
    cfg = load_config()
    k = int(top_k if top_k is not None else cfg["rag"].get("top_k", 3))
    chunks = load_chunks()
    if not chunks:
        return {
            "query": query,
            "top_k": k,
            "hits": [],
            "error": "index_missing",
            "hint": "请先运行 python -m ai_tool.rag.ingest",
        }

    texts = [f"{c.get('title', '')}\n{c.get('text', '')}" for c in chunks]
    scores = score_documents(query, texts)

    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    hits = []
    for i in ranked[:k]:
        if scores[i] <= 0:
            continue
        chunk = chunks[i]
        hits.append(
            {
                "id": chunk.get("id"),
                "title": chunk.get("title"),
                "source": chunk.get("source"),
                "score": round(scores[i], 3),
                "text": chunk.get("text", ""),
            }
        )
    return {"query": query, "top_k": k, "hits": hits}
