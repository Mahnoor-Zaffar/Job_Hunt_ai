import os
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "rules" / "ranking_weights.yaml"


def _load() -> dict:
    path = os.environ.get("RANKING_WEIGHTS_PATH", str(_CONFIG_PATH))
    with open(path) as f:
        return yaml.safe_load(f)


def load_weights() -> dict[str, float]:
    data = _load()
    return data.get("weights", {})


def load_labels() -> dict[str, int]:
    data = _load()
    return data.get("labels", {})


def load_actions() -> dict[str, str]:
    data = _load()
    return data.get("actions", {})


def load_max_confidence_threshold() -> int:
    data = _load()
    return data.get("max_confidence_threshold", 90)


def load_confidence_thresholds() -> dict[str, int]:
    data = _load()
    conf = data.get("confidence", {})
    return {
        "high": conf.get("high_threshold", 75),
        "medium": conf.get("medium_threshold", 45),
    }
