import json
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_road_rules() -> dict[str, str]:
    return _load_json("road_rules.json")


def get_speed_limits() -> dict[str, str]:
    return _load_json("speed_limits.json")


def get_rule(topic: str) -> str | None:
    rules = get_road_rules()
    return rules.get(topic)


def get_speed_limit(area: str) -> str | None:
    limits = get_speed_limits()
    return limits.get(area)
