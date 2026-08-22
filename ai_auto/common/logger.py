import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOGGER_NAME = "ai_auto"
_configured = False


def setup_logging() -> logging.Logger:
    """只写文件，按 logs/<级别>/<日期_时分>/ 分目录。控制台留给 pytest 摘要。"""
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)
    if _configured:
        return logger

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")

    files = (
        ("debug", logging.DEBUG),
        ("info", logging.INFO),
        ("error", logging.ERROR),
    )
    for name, level in files:
        run_dir = LOG_DIR / name / stamp
        run_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(run_dir / f"{name}.log", encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    _configured = True
    return logger


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
