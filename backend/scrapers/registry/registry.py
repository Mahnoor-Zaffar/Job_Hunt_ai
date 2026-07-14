import logging
from collections.abc import Callable
from typing import Any

from backend.scrapers.base.scraper import BaseScraper
from backend.scrapers.config.config import ScraperSettings

logger = logging.getLogger("job_hunting.registry")

_registry: dict[str, type[BaseScraper]] = {}
_source_metadata: dict[str, dict[str, Any]] = {}


def register(
    source: str,
    *,
    display_name: str = "",
    locations: list[str] | None = None,
    interval: int = 30,
) -> Callable[[type[BaseScraper]], type[BaseScraper]]:
    """Decorator that registers a scraper class in the global registry.

    Usage::

        @register("rozee", display_name="Rozee.pk", locations=["Pakistan"])
        class RozeeScraper(BaseScraper):
            ...
    """

    def decorator(cls: type[BaseScraper]) -> type[BaseScraper]:
        if source in _registry:
            logger.warning("Scraper [%s] already registered — overwriting", source)

        cls.source = source
        if display_name:
            cls.display_name = display_name
        cls.scrape_interval_minutes = interval

        _registry[source] = cls
        _source_metadata[source] = {
            "source": source,
            "display_name": display_name or source.replace("_", " ").title(),
            "locations": locations or [],
            "interval_minutes": interval,
        }
        logger.debug("Registered scraper [%s]", source)
        return cls

    return decorator


class ScraperRegistry:
    """Discovers and provides access to registered scraper implementations.

    Scrapers register themselves via the :func:`register` decorator.
    The registry then filters them by configuration and returns
    ready-to-instantiate classes.
    """

    def all(self) -> dict[str, type[BaseScraper]]:
        return dict(_registry)

    def get(self, source: str) -> type[BaseScraper] | None:
        return _registry.get(source)

    def get_metadata(self, source: str) -> dict[str, object] | None:
        return _source_metadata.get(source)

    def get_enabled(self, settings: ScraperSettings | None = None) -> list[type[BaseScraper]]:
        """Return scraper classes that are enabled by configuration.

        If ``settings.ENABLED_SCRAPERS`` is non-empty, only those
        sources are returned.  Sources listed in
        ``settings.DISABLED_SCRAPERS`` are always excluded.
        """
        cfg = settings or ScraperSettings()
        classes = list(_registry.values())

        if cfg.ENABLED_SCRAPERS:
            enabled_set = set(cfg.ENABLED_SCRAPERS)
            classes = [c for c in classes if c.source in enabled_set]

        disabled_set = set(cfg.DISABLED_SCRAPERS)
        classes = [c for c in classes if c.source not in disabled_set]

        return classes

    def list_sources(self) -> list[dict[str, object]]:
        return [
            {
                "source": src,
                **_source_metadata.get(src, {}),
            }
            for src in sorted(_registry)
        ]
