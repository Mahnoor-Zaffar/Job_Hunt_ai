import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification
from backend.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Notification, session)

    async def get_unread_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> list[Notification]:
        result = await self.session.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_as_read(self, notification_id: uuid.UUID) -> Notification | None:
        notification = await self.get_by_id(notification_id)
        if notification:
            from datetime import UTC, datetime

            notification.is_read = True
            notification.read_at = datetime.now(UTC)
            await self.session.flush()
        return notification

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
        )
        unread = list(result.scalars().all())
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        for n in unread:
            n.is_read = True
            n.read_at = now
        await self.session.flush()
        return len(unread)
