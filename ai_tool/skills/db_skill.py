"""Skill 模块：数据库。只读查 devices 表。

库文件相对仓库根，与项目 1 的 device_test.db 相同；用 SQLite URI mode=ro，避免和 FastAPI 抢写。
"""

from __future__ import annotations

import sqlite3
from typing import Any

from ai_tool import REPO_ROOT, load_config


def _db_path():
    rel = load_config()["device"]["db_path"]
    return (REPO_ROOT / rel).resolve()


def get_device(device_id: str) -> dict[str, Any]:
    """只读查一台设备。库不存在或没有该行时不抛异常。"""
    db_path = _db_path()
    if not db_path.exists():
        return {
            "found": False,
            "device": None,
            "db_path": str(db_path),
            "error": "db_missing",
            "hint": "未找到 SQLite 文件。请先在仓库根目录启动 device_server.py。",
        }

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)  # 只读，避免和 FastAPI 抢写
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT device_id, device_name, device_type, status, create_time "
            "FROM devices WHERE device_id = ?",
            (device_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        return {
            "found": False,
            "device": None,
            "db_path": str(db_path),
            "error": "db_query_failed",
            "detail": str(exc),
        }
    finally:
        conn.close()

    if row is None:
        return {"found": False, "device": None, "db_path": str(db_path)}

    device = dict(row)
    create_time = device.get("create_time")
    if create_time is not None:
        device["create_time"] = str(create_time)
    return {"found": True, "device": device, "db_path": str(db_path)}
