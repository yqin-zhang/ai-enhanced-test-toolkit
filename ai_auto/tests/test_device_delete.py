import uuid

import allure
import pytest

from api import COMMON, DeleteAPI, DeviceAPI, ListAPI
from common import assert_json, get_device, load_schema, request
from conftest import delete_device, register_device

DATA = DeleteAPI.data


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

    # ---------- 新增 P02~P04 / N05~N08 ----------

    @allure.story("DEL-P02")
    @allure.title("删除后从列表消失")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_delete_list_gone(self, registered_device):
        # DEL-P02：删除 200 后，列表按 id 查找为 None，DB 无记录
        device_id = registered_device["device_id"]
        assert_json(request("DELETE", DeleteAPI.url(device_id)), 200, self.success_schema)

        body = assert_json(request("GET", ListAPI.url()), 200)
        assert next((i for i in body["data"] if i["device_id"] == device_id), None) is None
        assert get_device(device_id) is None

    @allure.story("DEL-P03")
    @allure.title("携带 JSON 请求体删除")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_delete_with_body(self, registered_device):
        # DEL-P03：DELETE 带 body，body 被忽略，设备真的被删
        device_id = registered_device["device_id"]
        response = request("DELETE", DeleteAPI.url(device_id), json=DATA["delete_body"])
        assert_json(response, 200, self.success_schema)

        body = assert_json(request("GET", DeviceAPI.url(device_id)), 404, self.error_schema)
        assert body["detail"] == "设备不存在"
        assert get_device(device_id) is None

    @allure.story("DEL-P04")
    @allure.title("携带 query 参数删除")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_delete_with_query(self, registered_device):
        # DEL-P04：DELETE ?force=1，query 被忽略，正常删除
        device_id = registered_device["device_id"]
        response = request("DELETE", DeleteAPI.url(device_id), params=DATA["delete_query"])
        assert_json(response, 200, self.success_schema)

        body = assert_json(request("GET", DeviceAPI.url(device_id)), 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("DEL-N05")
    @allure.title("id 大小写不匹配不得误删")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_delete_case_sensitive(self, common):
        # DEL-N05：注册混合大小写 id，DELETE 其全大写形式 → 404，原 id 仍可查（未被误删）
        device_id = DATA["case_prefix"] + uuid.uuid4().hex[:6]
        payload = {
            "device_id": device_id,
            "device_name": common["device"]["device_name"],
            "device_type": common["device"]["device_type"],
        }
        register_device(payload)
        try:
            response = request("DELETE", DeleteAPI.url(device_id.upper()))
            body = assert_json(response, 404, self.error_schema)
            assert body["detail"] == "设备不存在"

            # 核心回归断言：原 id 设备仍在
            assert_json(request("GET", DeviceAPI.url(device_id)), 200)
            assert get_device(device_id) is not None
        finally:
            delete_device(device_id)

    @allure.story("DEL-N06")
    @allure.title("超长 id（200 字符）")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_delete_long_id(self):
        # DEL-N06：200 字符 id 命中路由但库中不存在 → 404「设备不存在」
        long_id = DATA["long_id"]
        assert len(long_id) == 200
        response = request("DELETE", DeleteAPI.url(long_id))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("DEL-N07")
    @allure.title("集合地址 DELETE /device")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_delete_collection(self):
        # DEL-N07：无尾段 → 框架 404 Not Found
        response = request("DELETE", DeleteAPI.collection_url())
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"

    @allure.story("DEL-N08")
    @allure.title("PATCH 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_delete_fail_patch(self, registered_device):
        # DEL-N08：设备存在时 PATCH → 405；实测 Allow 只声明 GET（框架首个匹配路由）
        response = request(DATA["patch_method"], DeleteAPI.url(registered_device["device_id"]))
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "GET"
