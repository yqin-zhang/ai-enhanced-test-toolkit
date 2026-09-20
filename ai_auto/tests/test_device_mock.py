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

    @allure.story("MOCK-N02a~c")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", MOCK["wrong_methods"])
    def test_device_mock_fail_method(self, method):
        # MOCK-N02a/b/c：POST/PUT/DELETE → 405，Allow 声明 GET
        response = request(method, self.url)
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"

    @allure.story("MOCK-N03")
    @allure.title("连续多次恒定 500")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_mock_stable_500(self):
        # MOCK-N03：连续 3 次均 500，detail 一致，无偶发成功
        for _ in range(MOCK["repeat_times"]):
            response = request("GET", self.url)
            body = assert_json(response, 500, self.error_schema)
            assert body["detail"] == "模拟服务器内部错误"

    @allure.story("MOCK-N04")
    @allure.title("携带 query 不影响结果")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_with_query(self):
        # MOCK-N04：?a=1&b=2 不影响结果，仍 500 且 detail 不变
        response = request("GET", self.url, params=MOCK["query_params"])
        body = assert_json(response, 500, self.error_schema)
        assert body["detail"] == "模拟服务器内部错误"

    @allure.story("MOCK-N05")
    @allure.title("携带 body 不影响结果")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_with_body(self):
        # MOCK-N05：GET 携带 JSON body 仍 500（服务不读 body）
        response = request("GET", self.url, json=MOCK["get_body"])
        body = assert_json(response, 500, self.error_schema)
        assert body["detail"] == "模拟服务器内部错误"

    @allure.story("MOCK-N06")
    @allure.title("尾斜杠 307 重定向")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_trailing_slash(self):
        # MOCK-N06：禁止自动跟随；307 且 Location 指向无斜杠地址，无响应体
        response = request("GET", MockAPI.trailing_url(), allow_redirects=False)
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert location.endswith("/mock/server500")
        assert not location.endswith("/server500/")
        assert not response.text

    @allure.story("MOCK-N07")
    @allure.title("PATCH 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_fail_patch(self):
        # MOCK-N07：PATCH → 405，Allow 声明 GET
        response = request(MOCK["patch_method"], self.url)
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"

    @allure.story("MOCK-N08")
    @allure.title("HEAD 方法无响应体")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_fail_head(self):
        # MOCK-N08：HEAD → 405，Allow 声明 GET，且无响应体（不做 schema）
        response = request(MOCK["head_method"], self.url)
        assert response.status_code == 405
        assert response.headers.get("Allow") == "GET"
        assert not response.text

    @allure.story("MOCK-N09")
    @allure.title("路径大写 /mock/SERVER500")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_upper_path(self):
        # MOCK-N09：路径大小写敏感 → 框架 404 Not Found
        response = request("GET", MockAPI.upper_url())
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"

    @allure.story("MOCK-N10")
    @allure.title("多一段子路径 /mock/server500/xxx")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_mock_sub_path(self):
        # MOCK-N10：多一段 → 框架 404 Not Found
        response = request("GET", MockAPI.sub_url())
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"
