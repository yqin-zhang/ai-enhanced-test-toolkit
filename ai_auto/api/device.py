from common import load_yaml

from api.base import join_url


class DeviceAPI:
    data = load_yaml("device")

    @classmethod
    def url(cls, device_id: str) -> str:
        return join_url(cls.data["path_template"].format(device_id=device_id))

    @classmethod
    def empty_url(cls) -> str:
        return join_url("/device/")

    @classmethod
    def wrong_path_url(cls, device_id: str) -> str:
        return cls.url(device_id) + cls.data["wrong_suffix"]
