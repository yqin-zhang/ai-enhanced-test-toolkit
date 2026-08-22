import json
from pathlib import Path

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schema"


def load_schema(api: str, name: str) -> dict:
    with (SCHEMA_ROOT / api / name).open(encoding="utf-8") as f:
        return json.load(f)
