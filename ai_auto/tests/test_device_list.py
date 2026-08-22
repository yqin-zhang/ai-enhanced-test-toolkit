import allure
import pytest

from api import ListAPI
from common import assert_json, load_schema, request

LIST = ListAPI.data


@allure.epic("设备管理")
@allure.feature("GET /device/list")
class TestDeviceList:
    def setup_class(self):
        self.url = ListAPI.url()
        self.success_schema = load_schema("list", "list_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

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
