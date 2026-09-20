import json as _json

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
        self.ext_wrong_type_schema = load_schema("status", "status_fail_wrong_type_ext.schema.json")
        self.invalid_schema = load_schema("status", "status_fail_json_invalid.schema.json")
        self.success_schema = load_schema("status", "status_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")
        # 跨模块复用：结构与注册接口同构（model_attributes_type）
        self.not_object_array_schema = load_schema(
            "register", "register_fail_not_object.schema.json"
        )
        self.not_object_string_schema = load_schema(
            "register", "register_fail_illegal_json.schema.json"
        )

    # ---------- 正向 ----------

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

    @allure.story("ST-P02")
    @allure.title("状态流转 {source}→{target}")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.parametrize(
        "case",
        STATUS["transitions"],
        ids=lambda c: f"{c['source']}->{c['target']}",
    )
    def test_device_status_transition(self, new_device, case):
        # ST-P02a~f：显式置 source 初态，再转 target，GET/DB 双重确认
        source, target = case["source"], case["target"]
        register_device(new_device)
        device_id = new_device["device_id"]
        url = StatusAPI.url(device_id)

        assert_json(request("PUT", url, json={"status": source}), 200, self.success_schema)
        assert assert_json(request("GET", DeviceAPI.url(device_id)), 200)["data"]["status"] == source

        assert_json(request("PUT", url, json={"status": target}), 200, self.success_schema)
        assert assert_json(request("GET", DeviceAPI.url(device_id)), 200)["data"]["status"] == target
        assert get_device(device_id)["status"] == target

    @allure.story("ST-P03")
    @allure.title("同态重复提交幂等")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_status_idempotent(self, new_device):
        # ST-P03：当前 online，连续两次 PUT online 均 200，状态始终 online
        register_device(new_device)
        url = StatusAPI.url(new_device["device_id"])
        assert_json(request("PUT", url, json={"status": "online"}), 200, self.success_schema)

        assert_json(request("PUT", url, json={"status": "online"}), 200, self.success_schema)
        assert_json(request("PUT", url, json={"status": "online"}), 200, self.success_schema)

        assert assert_json(request("GET", DeviceAPI.url(new_device["device_id"])), 200)["data"]["status"] == "online"
        assert get_device(new_device["device_id"])["status"] == "online"

    @allure.story("ST-P04")
    @allure.title("多传未知字段")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_extra_field(self, new_device):
        # ST-P04：额外字段被忽略，状态正常更新为 online
        register_device(new_device)
        url = StatusAPI.url(new_device["device_id"])
        response = request("PUT", url, json={"status": "online", "x": 1})
        assert_json(response, 200, self.success_schema)
        assert get_device(new_device["device_id"])["status"] == "online"

    # ---------- 业务 / 入参异常 ----------

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
    @allure.title("status 类型错误：{status}")
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
        assert response.headers.get("Allow") == "PUT"

    # ---------- 新增：校验顺序 / 类型矩阵 / 协议 ----------

    @allure.story("ST-N11~N12")
    @allure.title("不存在设备 + 非法状态 {status}（校验顺序）")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("status", STATUS["not_exist_illegal_status"])
    def test_device_status_not_exist_illegal(self, new_device, status):
        # ST-N11/N12：白名单校验先于设备存在性 → 400，而不是 404
        response = request(
            "PUT",
            StatusAPI.url(new_device["device_id"]),
            json={"status": status},
        )
        body = assert_json(response, 400, self.error_schema)
        assert "非法状态" in body["detail"]

    @allure.story("ST-N13")
    @allure.title("不存在设备 + 数字类型（Pydantic 最先校验）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_not_exist_wrong_type(self, new_device):
        # ST-N13：类型校验最优先 → 422，即使设备不存在
        response = request(
            "PUT",
            StatusAPI.url(new_device["device_id"]),
            json={"status": 1},
        )
        assert_json(response, 422, self.wrong_type_schema)

    @allure.story("ST-N14~N16")
    @allure.title("白名单外字符串 {status}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("status", STATUS["string_reject_status"])
    def test_device_status_string_reject(self, registered_device, status):
        # ST-N14 数字字符串 / N15 前后缀空格 / N16 纯空格 → 400，不做 trim
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json={"status": status},
        )
        body = assert_json(response, 400, self.error_schema)
        assert "非法状态" in body["detail"]

    @allure.story("ST-N17~N19")
    @allure.title("status 类型错误扩展 {value}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize(
        "value",
        STATUS["ext_wrong_type"],
        ids=lambda v: type(v).__name__,
    )
    def test_device_status_ext_wrong_type(self, registered_device, value):
        # ST-N17 布尔 / N18 数组 / N19 对象 → 422 string_type
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json={"status": value},
        )
        assert_json(response, 422, self.ext_wrong_type_schema)

    @allure.story("ST-N20")
    @allure.title("顶层 body 为数组")
    @allure.severity(allure.severity_level.NORMAL)
    def test_device_status_not_object_array(self, registered_device):
        # ST-N20：json=[{...}] → 422 model_attributes_type，复用 register 同构 schema
        response = request(
            "PUT",
            StatusAPI.url(registered_device["device_id"]),
            json=STATUS["non_object_array"],
        )
        assert_json(response, 422, self.not_object_array_schema)

    @allure.story("ST-N21~N23")
    @allure.title("非 application/json 发送：{kind}")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("kind", STATUS["content_type_cases"])
    def test_device_status_content_type(self, registered_device, kind):
        # ST-N21 form / N22 无 Content-Type / N23 text/plain → 422，input 均为字符串
        url = StatusAPI.url(registered_device["device_id"])
        if kind == "form":
            kwargs = {"data": {"status": "online"}}
        else:
            kwargs = {"data": _json.dumps({"status": "online"})}
            if kind == "text_plain":
                kwargs["headers"] = {"Content-Type": "text/plain"}
        response = request("PUT", url, **kwargs)
        assert_json(response, 422, self.not_object_string_schema)

    @allure.story("ST-N24")
    @allure.title("尾斜杠 307 重定向")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_status_trailing_slash(self, registered_device):
        # ST-N24：禁止自动跟随；307 且 Location 指向无斜杠地址，无响应体
        device_id = registered_device["device_id"]
        response = request(
            "PUT",
            StatusAPI.url(device_id) + "/",
            json={"status": "online"},
            allow_redirects=False,
        )
        assert response.status_code == 307
        location = response.headers.get("location", "")
        assert location.rstrip("/").endswith(f"/device/{device_id}/status")
        assert not response.text

    @allure.story("ST-N25")
    @allure.title("PATCH 方法")
    @allure.severity(allure.severity_level.MINOR)
    def test_device_status_fail_patch(self, registered_device):
        # ST-N25：PATCH → 405，Allow 声明 PUT
        response = request("PATCH", StatusAPI.url(registered_device["device_id"]))
        body = assert_json(response, 405, self.error_schema)
        assert body["detail"] == "Method Not Allowed"
        assert response.headers.get("Allow") == "PUT"
