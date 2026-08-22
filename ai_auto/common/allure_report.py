import shutil
import subprocess
from pathlib import Path

from common.logger import get_logger

logger = get_logger("allure")

REPORT_ROOT = Path(__file__).resolve().parents[1] / "reports"
RESULTS_DIR = REPORT_ROOT / "allure-results"
HTML_DIR = REPORT_ROOT / "allure-report"


def generate_allure_html() -> bool:
    """把 allure-results 生成到 reports/allure-report/。没有 Allure CLI 则跳过。"""
    allure = shutil.which("allure")
    if not allure:
        logger.info("未找到 allure 命令，跳过生成 reports/allure-report")
        return False
    if not RESULTS_DIR.exists():
        logger.info("没有 allure-results，跳过生成报告")
        return False
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [allure, "generate", str(RESULTS_DIR), "-o", str(HTML_DIR), "--clean"],
        check=False,
    )
    if completed.returncode != 0:
        logger.error("allure generate 失败，exit=%s", completed.returncode)
        return False
    logger.info("Allure 网页已写入 %s/index.html", HTML_DIR)
    return True
