"""Notifications API — preferences and history."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.notification import Notification
from backend.repositories.infrastructure import SettingsRepository
from backend.repositories.notification import NotificationRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseSchema):
    id: str
    user_id: str | None = None
    type: str
    title: str
    message: str
    is_read: bool = False
    read_at: datetime | None = None
    job_id: str | None = None
    sent_via: str | None = None
    created_at: datetime | None = None


class NotificationListResponse(BaseSchema):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationPreferences(BaseSchema):
    telegram_enabled: bool = True
    email_enabled: bool = False
    notify_on_match: bool = True
    notify_on_new_jobs: bool = True
    min_match_score: float = 0.6


def _notification_to_response(n: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=str(n.id),
        user_id=str(n.user_id) if n.user_id else None,
        type=n.type,
        title=n.title,
        message=n.message,
        is_read=n.is_read,
        read_at=n.read_at,
        job_id=str(n.job_id) if n.job_id else None,
        sent_via=n.sent_via,
        created_at=n.created_at,
    )


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    unread_only: bool = Query(False, description="Only unread notifications"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> NotificationListResponse:
    """List notifications for a user."""
    repo = NotificationRepository(db)
    if unread_only:
        items = await repo.get_unread_by_user(user_id, skip=(page - 1) * per_page, limit=per_page)
    else:
        items = await repo.get_by_user(user_id, skip=(page - 1) * per_page, limit=per_page)

    unread = await repo.get_unread_by_user(user_id)

    return NotificationListResponse(
        items=[_notification_to_response(n) for n in items],
        total=len(items),
        unread_count=len(unread),
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    """Mark a notification as read."""
    repo = NotificationRepository(db)
    n = await repo.mark_as_read(notification_id)
    if n is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return _notification_to_response(n)


@router.post("/read-all", response_model=dict[str, Any])
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> dict[str, Any]:
    """Mark all notifications as read for a user."""
    repo = NotificationRepository(db)
    count = await repo.mark_all_read(user_id)
    return {"marked_read": count}


@router.get("/preferences", response_model=NotificationPreferences)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> NotificationPreferences:
    """Get notification preferences for a user."""
    repo = SettingsRepository(db)
    t = await _pref(repo, user_id, "notifications.telegram", "true")
    e = await _pref(repo, user_id, "notifications.email", "false")
    m = await _pref(repo, user_id, "notifications.on_match", "true")
    j = await _pref(repo, user_id, "notifications.on_new_jobs", "true")
    s = await _pref(repo, user_id, "notifications.min_match_score", "0.6")
    return NotificationPreferences(
        telegram_enabled=t == "true",
        email_enabled=e == "true",
        notify_on_match=m == "true",
        notify_on_new_jobs=j == "true",
        min_match_score=float(s),
    )


async def _pref(repo: SettingsRepository, user_id: uuid.UUID, key: str, default: str) -> str:
    setting = await repo.get_by_user_and_key(user_id, key)
    return setting.value if setting and setting.value else default


@router.put("/preferences", response_model=NotificationPreferences)
async def update_preferences(
    body: NotificationPreferences,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> NotificationPreferences:
    """Update notification preferences."""
    repo = SettingsRepository(db)
    await repo.set_value(
        user_id, "notifications.telegram", "true" if body.telegram_enabled else "false"
    )
    await repo.set_value(user_id, "notifications.email", "true" if body.email_enabled else "false")
    await repo.set_value(
        user_id, "notifications.on_match", "true" if body.notify_on_match else "false"
    )
    await repo.set_value(
        user_id, "notifications.on_new_jobs", "true" if body.notify_on_new_jobs else "false"
    )
    await repo.set_value(user_id, "notifications.min_match_score", str(body.min_match_score))
    await db.flush()
    return body
