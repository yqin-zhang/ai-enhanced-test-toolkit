"""Skill 模块：HTTP。对 device_server 发真实请求。

连接失败返回结构化错误（含启动提示），不向外抛。ok=True 只表示收到 HTTP 响应。
"""

from __future__ import annotations

import time
from typing import Any

import requests

from ai_tool import load_config

_HINT = "请先在仓库根目录启动 test_projects/device_server.py（默认 127.0.0.1:8000）"


def _base_url() -> str:
    return load_config()["device"]["base_url"].rstrip("/")


def _timeout() -> float:
    return float(load_config()["device"].get("timeout_seconds", 5))


def _join(path: str) -> str:
    rel = path if path.startswith("/") else f"/{path}"
    return _base_url() + rel


def call_api(method: str, path: str, json: dict | None = None) -> dict[str, Any]:
    """请求被测接口。连接失败时返回结构化错误，不抛给调用方。"""
    url = _join(path)
    verb = method.upper()
    started = time.perf_counter()
    kwargs: dict[str, Any] = {"timeout": _timeout()}
    if json is not None:
        kwargs["json"] = json
    try:
        response = requests.request(verb, url, **kwargs)
    except requests.ConnectionError as exc:
        return {
            "ok": False,
            "error": "connection_refused",
            "hint": _HINT,
            "method": verb,
            "url": url,
            "detail": str(exc),
        }
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": "request_failed",
            "hint": _HINT,
            "method": verb,
            "url": url,
            "detail": str(exc),
        }

    elapsed = time.perf_counter() - started
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text
    # ok=True 表示拿到了 HTTP 响应，不代表业务 code=0
    return {
        "ok": True,
        "method": verb,
        "url": url,
        "status_code": response.status_code,
        "body": body,
        "elapsed_seconds": round(elapsed, 3),
    }
