"""RAG 模块① 加载：读 config 里的 Markdown，可选拉 /openapi.json。

只负责拿到原文，切块在 chunk.py。
"""

from __future__ import annotations

from typing import Any

import requests

from ai_tool import PKG_DIR, load_config


def load_markdown_documents(cfg: dict | None = None) -> list[dict[str, str]]:
    """返回 [{text, source}, ...]，文件不存在则跳过。"""
    cfg = cfg if cfg is not None else load_config()
    documents: list[dict[str, str]] = []
    for rel in cfg["rag"].get("sources") or []:
        path = (PKG_DIR / rel).resolve()
        if not path.exists():
            print(f"跳过不存在的源: {path}")
            continue
        documents.append(
            {
                "text": path.read_text(encoding="utf-8"),
                "source": str(path),
            }
        )
    return documents


def fetch_openapi(cfg: dict | None = None) -> dict[str, Any] | None:
    """服务已启动时附带一份路径清单；没起来就跳过，不阻断入库。"""
    cfg = cfg if cfg is not None else load_config()
    if not cfg["rag"].get("fetch_openapi"):
        return None
    base = cfg["device"]["base_url"].rstrip("/")
    url = f"{base}/openapi.json"
    timeout = float(cfg["device"].get("timeout_seconds", 5))
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        spec = response.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"跳过 OpenAPI（服务未启动或不可用）: {exc}")
        return None

    paths = spec.get("paths") or {}
    lines = [f"# {spec.get('info', {}).get('title', 'OpenAPI')}", ""]
    for path, methods in paths.items():
        verbs = ", ".join(sorted(methods.keys())).upper()
        lines.append(f"- {verbs} {path}")
    return {
        "title": "OpenAPI paths",
        "text": "\n".join(lines),
        "source": url,
    }
