"""项目 2 包入口：读 config.yaml，提供 PKG_DIR / REPO_ROOT。

不包含 Skill / RAG / MCP 逻辑。db_path 相对 REPO_ROOT，与 device_server 的 SQLite 对齐。
"""

from pathlib import Path

import yaml

PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parent  # device_test.db 相对仓库根，与 device_server 一致
CONFIG_PATH = PKG_DIR / "config.yaml"


def load_config() -> dict:
    """加载 ai_tool/config.yaml。"""
    with CONFIG_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        raise ValueError(f"空配置: {CONFIG_PATH}")
    return data
