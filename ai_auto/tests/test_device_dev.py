import re
import uuid

import allure
import pytest

from api import DeviceAPI, StatusAPI
from common import assert_json, load_schema, request
from conftest import delete_device, register_device

DEVICE = DeviceAPI.data
CREATE_TIME_PATTERN = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"


def _new_payload(device_id=None):
    return {
        "device_id": device_id or f"auto_{uuid.uuid4().hex[:12]}",
        "device_name": "温度传感器",
        "device_type": "sensor",
    }


@allure.epic("设备管理")
@allure.feature("GET /device/{device_id}")
class TestDeviceDev:
    def setup_class(self):
        self.success_schema = load_schema("device", "device_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    # ---------- 正向 ----------

    @allure.story("GET-P01")
    @allure.title("查询已注册设备")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_device_dev_success(self, registered_device):
        # GET-P01：data 是对象，不是列表
        response = request("GET", DeviceAPI.url(registered_device["device_id"]))
        body = assert_json(response, 200, self.success_schema)
        assert isinstance(body["data"], dict)
        assert body["data"]["device_id"] == registered_device["device_id"]
        assert body["data"]["device_name"] == registered_device["device_name"]
        assert body["data"]["device_type"] == registered_device["device_type"]

    @allure.story("GET-P02")
    @allure.title("device_id 长度边界 {case}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "case",
        DEVICE["boundary_ids"],
        ids=lambda c: f"length={c['length']}",
    )
    def test_device_dev_boundary(self, case):
        # GET-P02a/b：id 长度 1 / 64 恰好达界 → 200，id 完整一致
        device_id = "b" * case["length"]
        delete_device(device_id)
        register_device(_new_payload(device_id))
        try:
            response = request("GET", DeviceAPI.url(device_id))
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["device_id"] == device_id
            assert len(body["data"]["device_id"]) == case["length"]
        finally:
            delete_device(device_id)

    @allure.story("GET-P03")
    @allure.title("中文 id")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_dev_chinese_id(self):
        # GET-P03：中文 id（requests 自动编码）→ 200，中文原样返回
        device_id = f"中文_{uuid.uuid4().hex[:8]}"
        register_device(_new_payload(device_id))
        try:
            response = request("GET", DeviceAPI.url(device_id))
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["device_id"] == device_id
        finally:
            delete_device(device_id)

    @allure.story("GET-P04")
    @allure.title("id 含空格")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_dev_space_id(self):
        # GET-P04：id=`a b`（%20 编码）→ 200，返回 id 原样带空格
        device_id = DEVICE["special_ids"]["space"]
        delete_device(device_id)
        register_device(_new_payload(device_id))
        try:
            response = request("GET", DeviceAPI.url(device_id))
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["device_id"] == device_id
            assert " " in body["data"]["device_id"]
        finally:
            delete_device(device_id)

    @allure.story("GET-P05")
    @allure.title("id 含点号")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_dev_dot_id(self):
        # GET-P05：id=`a.b` → 200，点号不被当成分隔符
        device_id = DEVICE["special_ids"]["dot"]
        delete_device(device_id)
        register_device(_new_payload(device_id))
        try:
            response = request("GET", DeviceAPI.url(device_id))
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["device_id"] == device_id
        finally:
            delete_device(device_id)

    @allure.story("GET-P06")
    @allure.title("create_time 时间格式")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_dev_create_time(self, registered_device):
        # GET-P06：create_time 形如 YYYY-MM-DD HH:MM:SS（schema 已校验，再显式断言）
        response = request("GET", DeviceAPI.url(registered_device["device_id"]))
        body = assert_json(response, 200, self.success_schema)
        assert re.match(CREATE_TIME_PATTERN, body["data"]["create_time"])

    @allure.story("GET-P07")
    @allure.title("三态查询：{status}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("status", DEVICE["statuses"])
    def test_device_dev_three_statuses(self, status):
        # GET-P07a/b/c：显式置位 online/offline/fault（含 offline，防默认值假绿）后查询
        device = _new_payload()
        register_device(device)
        request("PUT", StatusAPI.url(device["device_id"]), json={"status": status})
        try:
            response = request("GET", DeviceAPI.url(device["device_id"]))
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["status"] == status
        finally:
            delete_device(device["device_id"])

    @allure.story("GET-P08")
    @allure.title("带 query string 不影响结果")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_dev_query_string(self, registered_device):
        # GET-P08：带任意 query 的响应体与不带参数完全一致
        plain = request("GET", DeviceAPI.url(registered_device["device_id"]))
        with_query = request(
            "GET",
            DeviceAPI.url(registered_device["device_id"]),
            params=DEVICE["query_params"],
        )
        assert_json(with_query, 200, self.success_schema)
        assert plain.json() == with_query.json()

    @allure.story("GET-P09")
    @allure.title("尾斜杠 307 重定向")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_trailing_slash(self, registered_device):
        # GET-P09：禁止自动跟随；307 且 Location 指向无斜杠地址，无响应体
        device_id = registered_device["device_id"]
        response = request(
            "GET",
            DeviceAPI.url(device_id) + "/",
            allow_redirects=False,
        )
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert location.rstrip("/").endswith(f"/device/{device_id}")
        assert not response.text

    # ---------- 异常 ----------

    @allure.story("GET-N01")
    @allure.title("ID 不存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_dev_fail_not_exist(self, new_device):
        # GET-N01：从未注册的临时 id
        response = request("GET", DeviceAPI.url(new_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("GET-N02")
    @allure.title("删除后再查")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_dev_fail_after_delete(self, new_device):
        # GET-N02：先注册再删，再查同一 id
        register_device(new_device)
        delete_device(new_device["device_id"])
        response = request("GET", DeviceAPI.url(new_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("GET-N03")
    @allure.title("空路径 GET /device/")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_fail_empty_path(self):
        # GET-N03：GET /device/ 实测 404 Not Found，不是「设备不存在」
        response = request("GET", DeviceAPI.empty_url())
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"

    @allure.story("GET-N04")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", DEVICE["wrong_methods"])
    def test_device_dev_fail_method(self, method, registered_device):
        # GET-N04：POST/PUT 打已存在设备 → 405
        response = request(method, DeviceAPI.url(registered_device["device_id"]))
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"

    @allure.story("GET-N05")
    @allure.title("错路径 /device/{id}/xxx")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_fail_wrong_path(self, registered_device):
        # GET-N05：/device/{id}/xxx → 404 Not Found
        response = request("GET", DeviceAPI.wrong_path_url(registered_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"

    @allure.story("GET-N06")
    @allure.title("id 大小写不匹配")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_dev_fail_case_mismatch(self):
        # GET-N06：注册大小写混合 id，查其大写形式 → 404，原 id 仍可查
        device_id = f"Case{uuid.uuid4().hex[:8]}"
        register_device(_new_payload(device_id))
        try:
            upper_resp = request("GET", DeviceAPI.url(device_id.upper()))
            body = assert_json(upper_resp, 404, self.error_schema)
            assert body["detail"] == "设备不存在"

            orig_resp = request("GET", DeviceAPI.url(device_id))
            assert orig_resp.status_code == 200
        finally:
            delete_device(device_id)

    @allure.story("GET-N07~N09")
    @allure.title("特殊 id 查无此设备：{case}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "case",
        DEVICE["nonexistent_ids"],
        ids=lambda c: c["kind"],
    )
    def test_device_dev_fail_special_ids(self, case):
        # GET-N07 SQL 注入样式 / N08 emoji / N09 超长 id：路由匹配但无记录 → 404「设备不存在」
        device_id = case.get("id") or case["repeat"] * case["length"]
        response = request("GET", DeviceAPI.url(device_id))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("GET-N10")
    @allure.title("PATCH 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_fail_patch(self, registered_device):
        # GET-N10：PATCH → 405，Allow 声明 GET
        response = request("PATCH", DeviceAPI.url(registered_device["device_id"]))
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"

    @allure.story("GET-N11")
    @allure.title("HEAD 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_fail_head(self, registered_device):
        # GET-N11：HEAD → 405，Allow: GET，HEAD 响应无 body，不做 JSON 断言
        response = request("HEAD", DeviceAPI.url(registered_device["device_id"]))
        assert response.status_code == 405
        assert response.headers.get("Allow") == "GET"
        assert not response.text
