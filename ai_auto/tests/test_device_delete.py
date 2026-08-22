import allure
import pytest

from api import DeleteAPI, DeviceAPI
from common import assert_json, get_device, load_schema, request


@allure.epic("设备管理")
@allure.feature("DELETE /device/{device_id}")
class TestDeviceDelete:
    def setup_class(self):
        self.success_schema = load_schema("delete", "delete_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("DEL-P01")
    @allure.title("删除成功后再查为 404")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_device_delete_success(self, registered_device):
        # DEL-P01：已存在设备删除成功，再 GET 同一 id 为 404
        device_id = registered_device["device_id"]
        response = request("DELETE", DeleteAPI.url(device_id))
        assert_json(response, 200, self.success_schema)

        query = request("GET", DeviceAPI.url(device_id))
        query_body = assert_json(query, 404, self.error_schema)
        assert query_body["detail"] == "设备不存在"
        assert get_device(device_id) is None

    @allure.story("DEL-N01")
    @allure.title("删除不存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_delete_fail_not_exist(self, new_device):
        # DEL-N01：从未注册的临时 id
        response = request("DELETE", DeleteAPI.url(new_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("DEL-N02")
    @allure.title("重复删除")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_delete_fail_twice(self, registered_device):
        # DEL-N02：刚删除成功，再 DELETE 同一 id
        device_id = registered_device["device_id"]
        first = request("DELETE", DeleteAPI.url(device_id))
        assert_json(first, 200, self.success_schema)

        second = request("DELETE", DeleteAPI.url(device_id))
        body = assert_json(second, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("DEL-N03")
    @allure.title("空路径 DELETE /device/")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_delete_fail_empty_path(self):
        # DEL-N03：DELETE /device/ 实测 404 Not Found，不是「设备不存在」
        response = request("DELETE", DeleteAPI.empty_url())
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"

    @allure.story("DEL-N04")
    @allure.title("错路径 /device/{id}/delete")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_delete_fail_wrong_path(self, registered_device):
        # DEL-N04：/device/{id}/delete → 404 Not Found
        response = request("DELETE", DeleteAPI.wrong_path_url(registered_device["device_id"]))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"
