import logging
import uuid

from backend.models.notification import Notification
from backend.repositories.notification import NotificationRepository

logger = logging.getLogger("job_hunting.services.notification")


class NotificationService:
    """Business logic for creating and managing user notifications."""

    def __init__(self, notification_repo: NotificationRepository) -> None:
        self._notifications = notification_repo

    async def create(
        self,
        user_id: uuid.UUID,
        type_: str,
        title: str,
        message: str,
        *,
        job_id: uuid.UUID | None = None,
        metadata_json: str | None = None,
        sent_via: str | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=type_,
            title=title,
            message=message,
            job_id=job_id,
            metadata_json=metadata_json,
            sent_via=sent_via,
        )
        return await self._notifications.create(notification)

    async def get_unread(self, user_id: uuid.UUID) -> list[Notification]:
        return await self._notifications.get_unread_by_user(user_id)

    async def get_all(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Notification]:
        return await self._notifications.get_by_user(user_id, skip, limit)

    async def mark_read(self, notification_id: uuid.UUID) -> Notification | None:
        return await self._notifications.mark_as_read(notification_id)

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        return await self._notifications.mark_all_read(user_id)
