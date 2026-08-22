import allure
import pytest

from api import DeviceAPI, StatusAPI
from common import assert_json, get_device, load_schema, request
from conftest import delete_device, register_device

STATUS = StatusAPI.data

# ST-N03/N04/N05：都是字符串但不在允许列表，业务返回 400
_REJECT_STATUS = (
    STATUS["illegal_status"] + STATUS["wrong_case_status"] + [STATUS["empty_status"]]
)


@allure.epic("设备管理")
@allure.feature("PUT /device/{device_id}/status")
class TestDeviceStatus:
    def setup_class(self):
        self.missing_schema = load_schema("status", "status_fail_missing.schema.json")
        self.missing_status_schema = load_schema("status", "status_fail_missing_status.schema.json")
        self.wrong_type_schema = load_schema("status", "status_fail_wrong_type.schema.json")
        self.invalid_schema = load_schema("status", "status_fail_json_invalid.schema.json")
        self.success_schema = load_schema("status", "status_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("ST-P01")
    @allure.title("改为合法状态：{status}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(item, marks=pytest.mark.smoke)
            if item == STATUS["sample_status"]
            else item
            for item in STATUS["legal_status"]
        ],
    )
    def test_device_status_success(self, registered_device, status):
        # ST-P01：合法状态更新成功，再 GET 确认已变
        # 注册默认 offline；目标也是 offline 时先改成别的，避免「没改也是 offline」假绿
        device_id = registered_device["device_id"]
        url = StatusAPI.url(device_id)
        before = assert_json(request("GET", DeviceAPI.url(device_id)), 200)["data"]["status"]
        if before == status:
            other = next(s for s in STATUS["legal_status"] if s != status)
            assert_json(request("PUT", url, json={"status": other}), 200, self.success_schema)
            before = other

        response = request("PUT", url, json={"status": status})
        assert_json(response, 200, self.success_schema)

        query_body = assert_json(request("GET", DeviceAPI.url(device_id)), 200)
        assert query_body["data"]["status"] == status
        assert query_body["data"]["status"] != before

        row = get_device(device_id)
        assert row is not None
        assert row["status"] == status

    @allure.story("ST-N01")
    @allure.title("设备不存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_fail_not_exist(self, new_device):
        # ST-N01：从未注册的临时 id
        response = request(
            "PUT",
            StatusAPI.url(new_device["device_id"]),
            json={"status": STATUS["sample_status"]},
        )
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("ST-N02")
    @allure.title("删除后再改")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_fail_after_delete(self, new_device):
        # ST-N02：先注册再删，再改同一 id
        register_device(new_device)
        delete_device(new_device["device_id"])
        response = request(
            "PUT",
            StatusAPI.url(new_device["device_id"]),
            json={"status": STATUS["sample_status"]},
        )
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("ST-N03~N05")
    @allure.title("非法状态 {status}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("status", _REJECT_STATUS, ids=lambda s: s or "empty")
    def test_device_status_fail_illegal(self, registered_device, status):
        # ST-N03/N04/N05：busy、大小写、空串 → 400「非法状态」，不是 422
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json={"status": status},
        )
        body = assert_json(response, 400, self.error_schema)
        assert "非法状态" in body["detail"]

    @allure.story("ST-N06")
    @allure.title("json={{}} 缺少 status")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_fail_missing(self, registered_device):
        # ST-N06：json={} 缺 status → 422；loc=["body","status"]，input={}
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json=STATUS["missing_body"],
        )
        assert_json(response, 422, self.missing_status_schema)

    @allure.story("ST-N07")
    @allure.title("未传 body")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_fail_missing_body(self, registered_device):
        # ST-N07：未传 body，不要带 json= / data=；loc=["body"]，input=null
        response = request("PUT", StatusAPI.url(registered_device["device_id"]))
        assert_json(response, 422, self.missing_schema)

    @allure.story("ST-N08")
    @allure.title("status 类型错误")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("status", STATUS["wrong_type_status"])
    def test_device_status_fail_wrong_type(self, registered_device, status):
        # ST-N08：数字或 null → 422
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json={"status": status},
        )
        assert_json(response, 422, self.wrong_type_schema)

    @allure.story("ST-N09")
    @allure.title("JSON 语法错误")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_fail_invalid_json(self, registered_device):
        # ST-N09：语法错误必须 data= 发原文，json= 会先被序列化
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            data=STATUS["invalid_body"].encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        assert_json(response, 422, self.invalid_schema)

    @allure.story("ST-N10")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", STATUS["wrong_methods"])
    def test_device_status_fail_method(self, method, registered_device):
        # ST-N10：GET/POST → 405
        response = request(method, StatusAPI.url(registered_device["device_id"]))
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
