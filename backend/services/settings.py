"""Settings service — user-scoped key-value persistence.

Provides the backing store for user preferences without polluting
the User model with ever-growing columns.  Keys are namespaced by
convention (e.g. ``notifications.telegram``).
"""

import logging
import uuid

from backend.repositories.infrastructure import SettingsRepository
from backend.services.base import BaseService

logger = logging.getLogger("job_hunting.services.settings")


class SettingsService(BaseService):
    """Manages user-scoped key-value settings."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        super().__init__()
        self._settings = settings_repo

    async def get(self, user_id: uuid.UUID, key: str, default: str | None = None) -> str | None:
        return await self._settings.get_value(user_id, key, default)

    async def set(self, user_id: uuid.UUID, key: str, value: str) -> None:
        await self._settings.set_value(user_id, key, value)

    async def get_all(self, user_id: uuid.UUID) -> dict[str, str]:
        entries = await self._settings.get_all_for_user(user_id)
        return {e.key: e.value or "" for e in entries}

    async def delete(self, user_id: uuid.UUID, key: str) -> bool:
        existing = await self._settings.get_by_user_and_key(user_id, key)
        if existing is None:
            return False
        await self._settings.delete(existing)
        return True
