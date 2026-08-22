from common import load_yaml

COMMON = load_yaml("common")
BASE = COMMON["base_url"].rstrip("/")


def join_url(path: str) -> str:
    return BASE + path
