from common import load_yaml

from api.base import join_url


class MockAPI:
    data = load_yaml("mock")

    @classmethod
    def url(cls) -> str:
        return join_url(cls.data["path"])
