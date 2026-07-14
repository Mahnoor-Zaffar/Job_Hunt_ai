from pathlib import Path
from typing import Any

import yaml

from backend.schemas.base import BaseSchema

COMPANIES_YAML_PATH = Path(__file__).resolve().parent / "companies.yaml"


class CompanyConfig(BaseSchema):
    """A single company entry in the ATS configuration."""

    name: str
    platform: str
    careers_url: str
    api_key: str | None = None
    locations: list[str] | None = None
    skip: bool = False


def load_companies(path: Path | None = None) -> list[CompanyConfig]:
    """Load company configurations from the YAML file.

    Returns a flat list of :class:`CompanyConfig` objects.  Entries
    marked ``skip: true`` are excluded.
    """
    file_path = path or COMPANIES_YAML_PATH
    raw: dict[str, Any] = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    entries: list[dict[str, Any]] = raw.get("companies", [])
    parsed = [CompanyConfig(**entry) for entry in entries]
    return [c for c in parsed if not c.skip]
