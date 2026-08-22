from common import load_yaml

from api.base import join_url


class StatusAPI:
    data = load_yaml("status")

    @classmethod
    def url(cls, device_id: str) -> str:
        return join_url(cls.data["path_template"].format(device_id=device_id))
