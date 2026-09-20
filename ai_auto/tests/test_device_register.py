import uuid

import allure
import pytest

from api import COMMON, DeviceAPI, RegisterAPI, StatusAPI
from common import assert_json, get_device, load_schema, request
from conftest import delete_device, register_device

REGISTER = RegisterAPI.data


def _new_payload(**overrides):
    """构造一台未注册设备的载荷，默认 auto_ 前缀，用例结束由夹具/手动清理。"""
    payload = {
        "device_id": f"auto_{uuid.uuid4().hex[:12]}",
        "device_name": "温度传感器",
        "device_type": "sensor",
    }
    payload.update(overrides)
    return payload


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
        self.not_object_schema = load_schema("register", "register_fail_not_object.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    # ---------- 正向 ----------

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

    @allure.story("REG-P02~P07")
    @allure.title("合法长度边界 {case}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "case",
        REGISTER["boundary_fields"],
        ids=lambda c: f"{c['field']}={c['length']}",
    )
    def test_device_register_boundary(self, case):
        # REG-P02~P07：id 1/64、name 1/128、type 1/64 恰好达界均 200
        field, length = case["field"], case["length"]
        payload = _new_payload()
        if field == "device_id":
            # 固定值跨轮次可能已存在，先清理；b*1 / b*64
            payload["device_id"] = "b" * length
            delete_device(payload["device_id"])
        elif field == "device_name":
            payload["device_name"] = "n" * length
        else:
            payload["device_type"] = "t" * length
        try:
            response = request("POST", self.url, json=payload)
            body = assert_json(response, 200, self.success_schema)
            assert body["data"]["device_id"] == payload["device_id"]

            row = get_device(payload["device_id"])
            assert row is not None
            assert len(row[field]) == length
            assert row[field] == payload[field]
        finally:
            delete_device(payload["device_id"])

    @allure.story("REG-P08~P10")
    @allure.title("中文 / 空格类名称：{kind}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize("kind", ["chinese", "spaces", "spaces_only"])
    def test_device_register_charset(self, kind):
        # REG-P08 中文；REG-P09 前后空格不 trim；REG-P10 纯空格（长度达标）
        charset = REGISTER["charset"][kind]
        payload = _new_payload(
            device_id=f"auto_{uuid.uuid4().hex[::3][:10]}",
            device_name=charset["device_name"],
        )
        if kind == "chinese":
            payload["device_id"] = f"中文_{uuid.uuid4().hex[:8]}"
            payload["device_type"] = charset["device_type"]
        try:
            response = request("POST", self.url, json=payload)
            assert_json(response, 200, self.success_schema)

            row = get_device(payload["device_id"])
            assert row is not None
            assert row["device_name"] == payload["device_name"]
        finally:
            delete_device(payload["device_id"])

    @allure.story("REG-P11")
    @allure.title("多传未知字段被忽略")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_extra_field(self):
        # REG-P11：额外字段不入库，name/type 与提交一致
        extra = REGISTER["extra_field"]
        payload = _new_payload()
        payload[extra["name"]] = extra["value"]
        try:
            response = request("POST", self.url, json=payload)
            assert_json(response, 200, self.success_schema)

            row = get_device(payload["device_id"])
            assert row is not None
            assert row["device_name"] == payload["device_name"]
            assert row["device_type"] == payload["device_type"]
            assert extra["name"] not in row
        finally:
            delete_device(payload["device_id"])

    @allure.story("REG-P12")
    @allure.title("删除后同 id 可重新注册，状态重置为 offline")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_register_again_after_delete(self, new_device):
        # REG-P12：注册 → 删除 → 同 id 重注，200 且状态回到默认 offline
        register_device(new_device)
        # 先改成 online，验证重注后状态确实被重置
        request("PUT", StatusAPI.url(new_device["device_id"]), json={"status": "online"})
        delete_device(new_device["device_id"])

        response = request("POST", self.url, json=new_device)
        assert_json(response, 200, self.success_schema)

        query = request("GET", DeviceAPI.url(new_device["device_id"]))
        body = assert_json(query, 200)
        assert body["data"]["status"] == "offline"
        assert get_device(new_device["device_id"])["status"] == "offline"

    # ---------- 业务异常 ----------

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

    # ---------- 新增：类型 / 结构 / 协议 ----------

    @allure.story("REG-N12~N18")
    @allure.title("字段类型错误 {case}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "case",
        REGISTER["field_type_errors"],
        ids=lambda c: f"{c['field']}-{type(c['value']).__name__}",
    )
    def test_device_register_fail_field_type(self, case):
        # REG-N12~N18：字段值为数字 / null / 数组 → 422 string_type
        payload = {"device_id": "dev001", "device_name": "温度传感器", "device_type": "sensor"}
        payload[case["field"]] = case["value"]
        response = request("POST", self.url, json=payload)
        assert_json(response, 422, self.schema)

    @allure.story("REG-N19")
    @allure.title("顶层 body 为数组")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail_not_object_array(self):
        # REG-N19：json=[1,2] → 422 model_attributes_type，input 回显数组
        response = request("POST", self.url, json=REGISTER["non_object_array"])
        assert_json(response, 422, self.not_object_schema)

    @allure.story("REG-N20")
    @allure.title("顶层 body 为 null 字面量")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_fail_json_null(self):
        # REG-N20：json=None 发出 4 字节 null，与 N08 响应同形（missing/body/null）
        response = request("POST", self.url, json=None)
        assert_json(response, 422, self.missing_schema)

    @allure.story("REG-N21~N23")
    @allure.title("非 application/json 发送：{kind}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("kind", ["form", "raw", "text_plain"])
    def test_device_register_fail_content_type(self, kind):
        # REG-N21 form / N22 无 Content-Type / N23 text/plain → 422，input 均为字符串
        payload = _new_payload()
        if kind == "form":
            kwargs = {"data": payload}
        else:
            import json as _json

            kwargs = {"data": _json.dumps(payload, ensure_ascii=False).encode("utf-8")}
            if kind == "text_plain":
                kwargs["headers"] = {"Content-Type": "text/plain"}
        response = request("POST", self.url, **kwargs)
        assert_json(response, 422, self.illegal_schema)

    @allure.story("REG-N24")
    @allure.title("尾斜杠 307 重定向")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_register_trailing_slash(self):
        # REG-N24：禁止自动跟随；307 且 Location 指向无斜杠地址，无响应体
        response = request(
            "POST",
            self.url + "/",
            json=_new_payload(),
            allow_redirects=False,
        )
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert location.rstrip("/").endswith("/device/register")
        assert not response.text

    @allure.story("REG-N25")
    @allure.title("GET 打注册地址被动态路由接管")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_get_path(self):
        # REG-N25：GET /device/register 被当成查 id=register → 404「设备不存在」
        response = request("GET", self.url)
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "设备不存在"

    @allure.story("REG-N26")
    @allure.title("重复注册不得覆盖原数据")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_register_duplicate_keeps_original(self, registered_device):
        # REG-N26：用不同 name/type 重注 → 400，原记录字段保持不变
        tampered = {
            "device_id": registered_device["device_id"],
            "device_name": "被篡改的新名称",
            "device_type": "new_type",
        }
        response = request("POST", self.url, json=tampered)
        assert_json(response, 400, self.error_schema)

        query = request("GET", DeviceAPI.url(registered_device["device_id"]))
        body = assert_json(query, 200)
        assert body["data"]["device_name"] == registered_device["device_name"]
        assert body["data"]["device_type"] == registered_device["device_type"]

        row = get_device(registered_device["device_id"])
        assert row["device_name"] == registered_device["device_name"]
        assert row["device_type"] == registered_device["device_type"]
