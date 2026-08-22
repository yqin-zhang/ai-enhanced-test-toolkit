import sqlite3
from pathlib import Path

from common.logger import get_logger
from common.yaml_loader import load_yaml

logger = get_logger("db")

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DB_PATH = (_REPO_ROOT / load_yaml("common")["db_path"]).resolve()


def get_device(device_id: str) -> dict | None:
    """只读查 devices。没有该行返回 None。"""
    logger.debug("query device_id=%s db=%s", device_id, _DB_PATH)
    conn = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT device_id, device_name, device_type, status, create_time "
            "FROM devices WHERE device_id = ?",
            (device_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return dict(row)
