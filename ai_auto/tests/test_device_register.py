import allure
import pytest

from api import COMMON, RegisterAPI
from common import assert_json, get_device, load_schema, request

REGISTER = RegisterAPI.data


def _fail_422_payloads():
    cases = list(REGISTER["fail_422"])
    oversize = REGISTER["oversize"]
    device_name = "温度传感器"
    device_type = "sensor"
    cases.append({
        "device_id": "d" * oversize["device_id"],
        "device_name": device_name,
        "device_type": device_type,
    })
    cases.append({
        "device_id": "dev001",
        "device_name": "n" * oversize["device_name"],
        "device_type": device_type,
    })
    cases.append({
        "device_id": "dev001",
        "device_name": device_name,
        "device_type": "t" * oversize["device_type"],
    })
    return cases


@allure.epic("设备管理")
@allure.feature("POST /device/register")
class TestDeviceRegister:
    def setup_class(self):
        self.url = RegisterAPI.url()
        self.success_schema = load_schema("register", "register_success.schema.json")
        self.schema = load_schema("register", "register_fail.schema.json")
        self.illegal_schema = load_schema("register", "register_fail_illegal_json.schema.json")
        self.invalid_schema = load_schema("register", "register_fail_json_invalid.schema.json")
        self.missing_schema = load_schema("register", "register_fail_missing.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("REG-P01")
    @allure.title("注册成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_device_register_success(self, new_device):
        # 正向必须用未注册 id，不能用 registered_device（夹具已注册，再 POST 是 400）
        response = request("POST", self.url, json=new_device)
        body = assert_json(response, 200, self.success_schema)
        assert body["data"]["device_id"] == new_device["device_id"]

        row = get_device(new_device["device_id"])
        assert row is not None
        assert row["device_id"] == new_device["device_id"]
        assert row["device_name"] == new_device["device_name"]
        assert row["device_type"] == new_device["device_type"]
        assert row["status"] == "offline"

    @allure.story("REG-N01")
    @allure.title("重复注册")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail(self, registered_device):
        # 重复注册 → 400
        response = request("POST", self.url, json=registered_device)
        body = assert_json(response, 400, self.error_schema)
        assert body["detail"] == "设备ID已存在，重复注册"

    @allure.story("REG-N02~N07")
    @allure.title("缺字段 / 空串 / 超长 → 422")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("payload", _fail_422_payloads())
    def test_device_register_fail_2(self, payload):
        # REG-N02~N07：缺字段 / 空对象 / 空串 / 超长 → 422；N05 `{}` 和 N08 未传 body 不合并
        response = request("POST", self.url, json=payload)
        assert_json(response, 422, self.schema)

    @allure.story("REG-N08")
    @allure.title("未传 body")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail_missing_body(self):
        # REG-N08：未传 body，不要带 json= / data=；loc=["body"]，input=null
        response = request("POST", self.url)
        assert_json(response, 422, self.missing_schema)

    @allure.story("REG-N09")
    @allure.title("body 不是 JSON 对象")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail_not_object(self):
        # REG-N09：json= 发出去是合法 JSON 字符串，不是对象
        response = request("POST", self.url, json=REGISTER["illegal_body"])
        assert_json(response, 422, self.illegal_schema)

    @allure.story("REG-N10")
    @allure.title("JSON 语法错误")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail_invalid_json(self):
        # REG-N10：语法错误必须 data= 发原文，json= 会先被序列化
        response = request(
            "POST",
            self.url,
            data=REGISTER["invalid_body"].encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        assert_json(response, 422, self.invalid_schema)

    @allure.story("REG-N11")
    @allure.title("错误方法 {method}")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.parametrize("method", REGISTER["wrong_methods"])
    def test_device_register_fail_method(self, method):
        # REG-N11：PUT/PATCH → 405；不要 GET，会被 /device/{id} 吃成 404
        response = request(method, self.url, json=COMMON["device"])
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
