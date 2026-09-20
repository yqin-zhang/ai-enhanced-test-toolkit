from common import load_yaml

from api.base import join_url


class MockAPI:
    data = load_yaml("mock")

    @classmethod
    def url(cls) -> str:
        return join_url(cls.data["path"])

    @classmethod
    def trailing_url(cls) -> str:
        return cls.url() + "/"

    @classmethod
    def upper_url(cls) -> str:
        return join_url(cls.data["upper_path"])

    @classmethod
    def sub_url(cls) -> str:
        return cls.url() + cls.data["sub_suffix"]
