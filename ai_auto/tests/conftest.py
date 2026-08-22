# conftest.py
import uuid

import pytest

from api import COMMON, DeleteAPI, ListAPI, RegisterAPI
from common import request
from common.allure_report import generate_allure_html
from common.logger import get_logger, setup_logging

logger = get_logger("test")


def pytest_configure(config):
    setup_logging()


def pytest_runtest_setup(item):
    logger.info("START %s", item.nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    if call.when != "call":
        return
    report = outcome.get_result()
    logger.info("END %s %s", item.nodeid, report.outcome.upper())


def pytest_sessionfinish(session, exitstatus):
    generate_allure_html()


def register_device(payload=None):
    """需要设备时调用。已存在返回 400，同样视为就绪。"""
    payload = payload or COMMON["device"]
    response = request("POST", RegisterAPI.url(), json=payload)
    assert response.status_code in (200, 400)
    return payload


def delete_device(device_id=None):
    """用例里主动删，或夹具/会话收尾时删。没有该设备时 404，忽略。"""
    device_id = device_id or COMMON["device"]["device_id"]
    response = request("DELETE", DeleteAPI.url(device_id))
    assert response.status_code in (200, 404)
    return response


@pytest.fixture
def common():
    return COMMON


@pytest.fixture
def registered_device(common):
    """已在库中的共享设备：重复注册 / 列表 / 查询等。该条测完再删。"""
    payload = register_device(common["device"])
    yield payload
    delete_device(payload["device_id"])


@pytest.fixture
def new_device(common):
    """尚未注册的临时设备：正向注册用。测完删除。"""
    payload = {
        "device_id": f"auto_{uuid.uuid4().hex[:12]}",
        "device_name": common["device"]["device_name"],
        "device_type": common["device"]["device_type"],
    }
    yield payload
    delete_device(payload["device_id"])


@pytest.fixture(scope="session", autouse=True)
def _cleanup_devices_after_session():
    """整场测试结束：删掉共享设备，以及注册正向残留的 auto_*。"""
    yield
    delete_device(COMMON["device"]["device_id"])
    response = request("GET", ListAPI.url())
    if response.status_code != 200:
        return
    for item in response.json().get("data") or []:
        device_id = item.get("device_id") or ""
        if device_id.startswith("auto_"):
            delete_device(device_id)
