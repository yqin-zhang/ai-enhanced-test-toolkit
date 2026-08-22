from common import load_yaml

from api.base import join_url


class ListAPI:
    data = load_yaml("list")

    @classmethod
    def url(cls) -> str:
        return join_url(cls.data["path"])

    @classmethod
    def wrong_url(cls, path: str) -> str:
        return join_url(path)
