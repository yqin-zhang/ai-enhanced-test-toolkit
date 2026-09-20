import uuid

import allure
import pytest

from api import ListAPI, StatusAPI
from common import assert_json, load_schema, request
from conftest import delete_device, register_device

LIST = ListAPI.data


def _new_payload(device_name="温度传感器", device_type="sensor"):
    return {
        "device_id": f"auto_{uuid.uuid4().hex[:12]}",
        "device_name": device_name,
        "device_type": device_type,
    }


@allure.epic("设备管理")
@allure.feature("GET /device/list")
class TestDeviceList:
    def setup_class(self):
        self.url = ListAPI.url()
        self.success_schema = load_schema("list", "list_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    # ---------- 正向 ----------

    @allure.story("LIST-P01")
    @allure.title("列表包含已注册设备")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_device_list_success(self, registered_device):
        # LIST-P01：按 device_id 查找，不写死 data[1]
        response = request("GET", self.url)
        body = assert_json(response, 200, self.success_schema)
        item = next(
            (x for x in body["data"] if x["device_id"] == registered_device["device_id"]),
            None,
        )
        assert item is not None
        assert item["device_name"] == registered_device["device_name"]
        assert item["device_type"] == registered_device["device_type"]

    @allure.story("LIST-P02")
    @allure.title("多台设备全部可查")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_list_multi_devices(self):
        # LIST-P02：注册 3 台不同 id，列表按 id 逐个定位，字段各自一致
        devices = [
            _new_payload(device_name=f"多台设备{i}", device_type=f"type{i}")
            for i in range(3)
        ]
        for dev in devices:
            register_device(dev)
        try:
            response = request("GET", self.url)
            body = assert_json(response, 200, self.success_schema)
            for dev in devices:
                item = next((x for x in body["data"] if x["device_id"] == dev["device_id"]), None)
                assert item is not None
                assert item["device_name"] == dev["device_name"]
                assert item["device_type"] == dev["device_type"]
        finally:
            for dev in devices:
                delete_device(dev["device_id"])

    @allure.story("LIST-P03")
    @allure.title("三态设备齐全")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_list_three_statuses(self):
        # LIST-P03：online/offline/fault 各一台，列表中三态均在且 status 与更新一致
        targets = [
            (_new_payload(), "online"),
            (_new_payload(), "offline"),
            (_new_payload(), "fault"),
        ]
        for dev, status in targets:
            register_device(dev)
            # 显式置位（offline 也 PUT 一次，防止默认值造成假绿）
            request("PUT", StatusAPI.url(dev["device_id"]), json={"status": status})
        try:
            response = request("GET", self.url)
            body = assert_json(response, 200, self.success_schema)
            for dev, status in targets:
                item = next((x for x in body["data"] if x["device_id"] == dev["device_id"]), None)
                assert item is not None
                assert item["status"] == status
        finally:
            for dev, _ in targets:
                delete_device(dev["device_id"])

    @allure.story("LIST-P04")
    @allure.title("删除后从列表消失")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_list_after_delete(self):
        # LIST-P04：注册 → 删除 → 列表按 id 查找为 None
        dev = _new_payload()
        register_device(dev)
        delete_device(dev["device_id"])

        response = request("GET", self.url)
        body = assert_json(response, 200, self.success_schema)
        item = next((x for x in body["data"] if x["device_id"] == dev["device_id"]), None)
        assert item is None

    @allure.story("LIST-P05")
    @allure.title("未定义 query 参数被忽略")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_list_ignore_query(self):
        # LIST-P05：带任意 query 仍 200，data 为数组
        response = request("GET", self.url, params=LIST["ignored_query"])
        body = assert_json(response, 200, self.success_schema)
        assert isinstance(body["data"], list)

    @allure.story("LIST-P06")
    @allure.title("尾斜杠 307 重定向")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_list_trailing_slash(self):
        # LIST-P06：禁止自动跟随；307 且 Location 指向无斜杠地址，无响应体
        response = request("GET", self.url + "/", allow_redirects=False)
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert location.rstrip("/").endswith("/device/list")
        assert not response.text

    # ---------- 异常 ----------

    @allure.story("LIST-N01")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", LIST["wrong_methods"])
    def test_device_list_fail_method(self, method):
        # LIST-N01：仅 POST/PUT → 405；DELETE 会被 {device_id} 吃成 404
        response = request(method, self.url)
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"

    @allure.story("LIST-N02")
    @allure.title("路径不被 {device_id} 抢占")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_list_not_captured_as_id(self):
        # LIST-N02：不能被 /device/{device_id} 抢成 404，data 必须是数组
        response = request("GET", self.url)
        body = assert_json(response, 200, self.success_schema)
        assert isinstance(body["data"], list)

    @allure.story("LIST-N03")
    @allure.title("错路径")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("case", LIST["wrong_paths"])
    def test_device_list_fail_wrong_path(self, case):
        # LIST-N03：/device/xxx 是「设备不存在」；/devices/list 才是 Not Found
        response = request("GET", ListAPI.wrong_url(case["path"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == case["detail"]

    @allure.story("LIST-N04")
    @allure.title("PATCH 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_list_fail_patch(self):
        # LIST-N04：PATCH → 405，Allow 声明 GET
        response = request("PATCH", self.url)
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"

    @allure.story("LIST-N05")
    @allure.title("HEAD 方法（实测未自动支持）")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_list_fail_head(self):
        # LIST-N05：HEAD → 405，Allow: GET，HEAD 响应无 body，不做 JSON 断言
        response = request("HEAD", self.url)
        assert response.status_code == 405
        assert response.headers.get("Allow") == "GET"
        assert not response.text

    @allure.story("LIST-N06~N07")
    @allure.title("路径大小写 / 双斜杠：{case}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "case",
        LIST["case_paths"],
        ids=lambda c: c["path"],
    )
    def test_device_list_case_and_dslash(self, case):
        # LIST-N06：/device/LIST 被当 id → 404「设备不存在」
        # LIST-N07：//device/list 前缀不匹配 → 404「Not Found」
        response = request("GET", ListAPI.wrong_url(case["path"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == case["detail"]
