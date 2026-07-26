from pathlib import Path
from typing import Any
import os
import yaml


_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config" / "rules"


class DigestConfig:
    def __init__(self, config_dir: str | Path | None = None):
        self._config_dir = Path(config_dir) if config_dir else _CONFIG_DIR
        self._cache: dict[str, Any] = {}

    def _load(self, name: str) -> dict[str, Any]:
        if name not in self._cache:
            path = self._config_dir / name
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {path}")
            with open(path) as f:
                self._cache[name] = yaml.safe_load(f) or {}
        return self._cache[name]

    @property
    def accepted_titles(self) -> dict[str, Any]:
        return self._load("accepted_titles.yaml")

    @property
    def rejected_titles(self) -> dict[str, Any]:
        return self._load("rejected_titles.yaml")

    @property
    def preferred_technologies(self) -> dict[str, Any]:
        return self._load("preferred_technologies.yaml")

    @property
    def scoring(self) -> dict[str, Any]:
        return self._load("scoring.yaml")

    @property
    def categories(self) -> dict[str, Any]:
        return self._load("categories.yaml")

    @property
    def job_preferences(self) -> dict[str, Any]:
        return self._load("job_preferences.yaml")

    @property
    def accepted_explicit(self) -> list[str]:
        return [t.lower().strip() for t in self.accepted_titles.get("explicit", [])]

    @property
    def accepted_related(self) -> list[str]:
        return [t.lower().strip() for t in self.accepted_titles.get("related", [])]

    @property
    def rejected_patterns(self) -> list[str]:
        return [p.lower().strip() for p in self.rejected_titles.get("patterns", [])]

    @property
    def reject_internships(self) -> bool:
        return self.rejected_titles.get("reject_internships", True)

    @property
    def tech_domains(self) -> dict[str, list[str]]:
        return {
            k: [t.lower().strip() for t in v]
            for k, v in self.preferred_technologies.get("domains", {}).items()
        }

    @property
    def scoring(self) -> dict[str, Any]:
        return self._load("scoring.yaml")

    @property
    def confidence_config(self) -> dict[str, Any]:
        return self.scoring.get("confidence", {})

    @property
    def scoring_thresholds(self) -> dict[str, Any]:
        return self.scoring.get("thresholds", {})

    @property
    def cat_configs(self) -> list[dict[str, Any]]:
        return self.categories.get("categories", {})

    @property
    def preferences(self) -> dict[str, Any]:
        return self.job_preferences.get("preferences", {})

    @property
    def max_per_category(self) -> int:
        return self.preferences.get("max_per_category", 10)

    @property
    def max_total(self) -> int:
        return self.preferences.get("max_total", 50)

    @property
    def min_score(self) -> int:
        return 70

    @property
    def min_confidence(self) -> str:
        return self.preferences.get("min_confidence", "medium")

    @property
    def max_days_old(self) -> int:
        return self.preferences.get("max_days_old", 30)

    def get_tech_domain(self, domain: str) -> list[str]:
        return self.tech_domains.get(domain, [])

    def get_category_config(self, key: str) -> dict[str, Any] | None:
        return self.cat_configs.get(key)

    def category_keys(self) -> list[str]:
        return list(self.cat_configs.keys())

    def category_label(self, key: str) -> str:
        cfg = self.cat_configs.get(key, {})
        return cfg.get("label", key)

    def category_title_patterns(self, key: str) -> list[str]:
        cfg = self.cat_configs.get(key, {})
        return [t.lower().strip() for t in cfg.get("title_patterns", [])]

    def category_tech_domains(self, key: str) -> list[str]:
        cfg = self.cat_configs.get(key, {})
        return cfg.get("tech_domains", [])


_default_config = None


def get_config(config_dir: str | Path | None = None) -> DigestConfig:
    global _default_config
    if config_dir:
        return DigestConfig(config_dir)
    if _default_config is None:
        _default_config = DigestConfig()
    return _default_config
