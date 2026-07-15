import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class ScraperSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SCRAPER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    INTERVAL_MINUTES: int = 30
    MAX_CONCURRENT: int = 5
    TIMEOUT_SECONDS: int = 30
    HEADLESS: bool = True
    MAX_RETRIES: int = 3
    RATE_LIMIT_DELAY: float = 0.5
    ENABLED_SCRAPERS: list[str] = []
    DISABLED_SCRAPERS: list[str] = []
    PROXY_URL: str = ""

    def get_source_setting(self, source: str, key: str, default: str | None = None) -> str | None:
        """Read a per-source environment variable.

        Looks for ``SCRAPER_SOURCE_{SOURCE}_{KEY}``, e.g.::

            SCRAPER_SOURCE_ROZEE_BASE_URL=https://www.rozee.pk
            SCRAPER_SOURCE_ASHBY_API_KEY=abc-123
        """
        env_key = f"SCRAPER_SOURCE_{source.upper()}_{key.upper()}"
        return os.getenv(env_key, default)

    def get_source_int(self, source: str, key: str, default: int) -> int:
        val = self.get_source_setting(source, key)
        if val is not None:
            try:
                return int(val)
            except ValueError:
                pass
        return default
