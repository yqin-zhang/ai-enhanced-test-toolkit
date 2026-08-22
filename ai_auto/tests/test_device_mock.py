import allure
import pytest

from api import MockAPI
from common import assert_json, load_schema, request

MOCK = MockAPI.data


@allure.epic("设备管理")
@allure.feature("GET /mock/server500")
class TestDeviceMock:
    def setup_class(self):
        self.url = MockAPI.url()
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("MOCK-N01")
    @allure.title("模拟内部错误 500")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_mock_server_500(self):
        # MOCK-N01：模拟内部错误，无业务正向成功态
        response = request("GET", self.url)
        body = assert_json(response, 500, self.error_schema)
        assert body["detail"] == "模拟服务器内部错误"

    @allure.story("MOCK-N02")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", MOCK["wrong_methods"])
    def test_device_mock_fail_method(self, method):
        # MOCK-N02：POST/PUT/DELETE → 405
        response = request(method, self.url)
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
