from common import load_yaml

from api.base import join_url


class RegisterAPI:
    data = load_yaml("register")

    @classmethod
    def url(cls) -> str:
        return join_url(cls.data["path"])
