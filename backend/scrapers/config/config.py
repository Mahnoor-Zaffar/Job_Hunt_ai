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
