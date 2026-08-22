import allure
import pytest

from api import DeviceAPI
from common import assert_json, load_schema, request
from conftest import delete_device, register_device

DEVICE = DeviceAPI.data


@allure.epic("设备管理")
@allure.feature("GET /device/{device_id}")
class TestDeviceDev:
    def setup_class(self):
        self.success_schema = load_schema("device", "device_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

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

    @allure.story("GET-N05")
    @allure.title("错路径 /device/{id}/xxx")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_dev_fail_wrong_path(self, registered_device):
        # GET-N05：/device/{id}/xxx → 404 Not Found
        response = request("GET", DeviceAPI.wrong_path_url(registered_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"
