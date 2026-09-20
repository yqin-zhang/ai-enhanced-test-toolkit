import uuid

import allure

from api import DeleteAPI, DeviceAPI, ListAPI, RegisterAPI, StatusAPI, join_url
from common import assert_json, get_device, load_schema, load_yaml, request
from conftest import delete_device

E2E = load_yaml("e2e")


def _new_device_payload(label=""):
    """生成独立生命周期的设备载荷；label 仅用于区分 A/B/C。"""
    return {
        "device_id": f"{E2E['id_prefix']}{label}{uuid.uuid4().hex[:8]}",
        "device_name": E2E["peer_name"],
        "device_type": E2E["peer_type"],
    }


@allure.epic("设备管理")
@allure.feature("跨接口 E2E / 协议契约")
class TestDeviceLifecycle:
    def setup_class(self):
        self.register_schema = load_schema("register", "register_success.schema.json")
        self.device_schema = load_schema("device", "device_success.schema.json")
        self.list_schema = load_schema("list", "list_success.schema.json")
        self.status_schema = load_schema("status", "status_success.schema.json")
        self.delete_schema = load_schema("delete", "delete_success.schema.json")
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("E2E-01")
    @allure.title("设备完整生命周期")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_device_full_lifecycle(self):
        # 注册 → 单查 → 列表定位 → online/fault 流转 → 删除 → 404 + DB 无记录 + 列表消失
        payload = _new_device_payload()
        device_id = payload["device_id"]
        try:
            # 1) 注册：默认 offline
            assert_json(
                request("POST", RegisterAPI.url(), json=payload),
                200,
                self.register_schema,
            )

            # 2) 单查核对三要素、默认状态、create_time
            body = assert_json(request("GET", DeviceAPI.url(device_id)), 200, self.device_schema)
            data = body["data"]
            assert data["device_id"] == device_id
            assert data["device_name"] == payload["device_name"]
            assert data["device_type"] == payload["device_type"]
            assert data["status"] == "offline"
            assert data["create_time"]
            row = get_device(device_id)
            assert row is not None and row["status"] == "offline"

            # 3) 列表定位
            list_body = assert_json(request("GET", ListAPI.url()), 200, self.list_schema)
            assert next((i for i in list_body["data"] if i["device_id"] == device_id), None) is not None

            # 4) 状态流转：每步接口 + GET + DB 三重核对
            for target in E2E["lifecycle_status_flow"]:
                assert_json(
                    request("PUT", StatusAPI.url(device_id), json={"status": target}),
                    200,
                    self.status_schema,
                )
                got = assert_json(request("GET", DeviceAPI.url(device_id)), 200)
                assert got["data"]["status"] == target
                assert get_device(device_id)["status"] == target

            # 5) 删除：单查 404、DB 无记录、列表消失
            assert_json(
                request("DELETE", DeleteAPI.url(device_id)),
                200,
                self.delete_schema,
            )
            gone = assert_json(request("GET", DeviceAPI.url(device_id)), 404, self.error_schema)
            assert gone["detail"] == "设备不存在"
            assert get_device(device_id) is None
            final_list = assert_json(request("GET", ListAPI.url()), 200)
            assert next((i for i in final_list["data"] if i["device_id"] == device_id), None) is None
        finally:
            delete_device(device_id)

    @allure.story("E2E-02")
    @allure.title("多设备互不干扰")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_multi_device_isolation(self):
        # 注册 A/B/C，只改 B、只删 C；A 不受影响仍在，B 状态独立，C 消失
        peers = [_new_device_payload(label) for label in E2E["peer_labels"]]
        ids = [p["device_id"] for p in peers]
        changed_idx = E2E["peer_changed_index"]
        deleted_idx = E2E["peer_deleted_index"]
        try:
            for payload in peers:
                assert_json(
                    request("POST", RegisterAPI.url(), json=payload),
                    200,
                    self.register_schema,
                )

            # 三台初始均 offline
            for device_id in ids:
                body = assert_json(request("GET", DeviceAPI.url(device_id)), 200)
                assert body["data"]["status"] == "offline"

            # 只改 B
            changed_id = ids[changed_idx]
            assert_json(
                request("PUT", StatusAPI.url(changed_id), json={"status": "online"}),
                200,
                self.status_schema,
            )

            # 只删 C
            deleted_id = ids[deleted_idx]
            assert_json(
                request("DELETE", DeleteAPI.url(deleted_id)),
                200,
                self.delete_schema,
            )

            # A 始终未受影响：仍在、offline、库中有记录
            untouched_id = next(i for idx, i in enumerate(ids) if idx not in (changed_idx, deleted_idx))
            body_a = assert_json(request("GET", DeviceAPI.url(untouched_id)), 200)
            assert body_a["data"]["status"] == "offline"
            assert get_device(untouched_id) is not None

            # B 状态独立变化
            body_b = assert_json(request("GET", DeviceAPI.url(changed_id)), 200)
            assert body_b["data"]["status"] == "online"
            assert get_device(changed_id)["status"] == "online"

            # C 已消失
            body_c = assert_json(request("GET", DeviceAPI.url(deleted_id)), 404, self.error_schema)
            assert body_c["detail"] == "设备不存在"
            assert get_device(deleted_id) is None

            # 列表：A、B 在，C 不在
            list_body = assert_json(request("GET", ListAPI.url()), 200)
            alive = {i["device_id"] for i in list_body["data"]}
            assert untouched_id in alive
            assert changed_id in alive
            assert deleted_id not in alive
        finally:
            for device_id in ids:
                delete_device(device_id)


@allure.epic("设备管理")
@allure.feature("跨接口 E2E / 协议契约")
class TestContract:
    def setup_class(self):
        self.error_schema = load_schema("common", "error.schema.json")

    @allure.story("CT-01")
    @allure.title("405 响应带 Allow 头")
    @allure.severity(allure.severity_level.NORMAL)
    def test_method_not_allowed_allow_header(self, registered_device):
        # 抽查错误方法：Allow 必须声明该端点的正确方法。
        # 注：/device/{id} 同时注册 GET/DELETE，但框架只回首个匹配路由的方法（GET）。
        device_id = registered_device["device_id"]
        probes = [
            ("PUT", RegisterAPI.url(), "POST"),
            ("POST", ListAPI.url(), "GET"),
            ("PATCH", RegisterAPI.url(), "POST"),
            ("PATCH", ListAPI.url(), "GET"),
            ("PATCH", DeviceAPI.url(device_id), "GET"),
            ("PATCH", StatusAPI.url(device_id), "PUT"),
        ]
        for method, url, expect_allow in probes:
            response = request(method, url)
            body = assert_json(response, 405, self.error_schema)
            assert body["detail"] == "Method Not Allowed", (method, url)
            assert response.headers.get("Allow") == expect_allow, (method, url)

    @allure.story("CT-02")
    @allure.title("未知根路径 GET /")
    @allure.severity(allure.severity_level.MINOR)
    def test_unknown_root_path(self):
        # 根路径无路由 → 框架 404，JSON 错误体
        response = request("GET", join_url("/"))
        body = assert_json(response, 404, self.error_schema)
        assert body["detail"] == "Not Found"
        assert response.headers["Content-Type"].startswith("application/json")
