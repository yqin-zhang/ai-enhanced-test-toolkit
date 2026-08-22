from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_yaml(name: str) -> dict:
    with (DATA_DIR / f"{name}.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)
