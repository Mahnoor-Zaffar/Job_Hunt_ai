import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User
from backend.repositories.user import UserRepository

pytestmark = pytest.mark.db


@pytest.mark.asyncio
async def test_user_repository_create(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    created = await repo.create(user)

    assert created.id is not None
    assert created.email == "test@example.com"
    assert created.name == "Test User"
    assert created.is_active is True


@pytest.mark.asyncio
async def test_user_repository_get_by_id(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    created = await repo.create(user)
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.email == "test@example.com"


@pytest.mark.asyncio
async def test_user_repository_get_by_email(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    await repo.create(user)
    fetched = await repo.get_by_email("test@example.com")

    assert fetched is not None
    assert fetched.name == "Test User"


@pytest.mark.asyncio
async def test_user_repository_get_by_email_not_found(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    fetched = await repo.get_by_email("nonexistent@example.com")
    assert fetched is None


@pytest.mark.asyncio
async def test_user_repository_count(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    assert await repo.count() == 0

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    await repo.create(user)

    assert await repo.count() == 1


@pytest.mark.asyncio
async def test_user_repository_update(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    created = await repo.create(user)
    updated = await repo.update(created, name="Updated Name")

    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_user_repository_delete(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_123",
    )
    created = await repo.create(user)
    await repo.delete(created)

    assert await repo.count() == 0
