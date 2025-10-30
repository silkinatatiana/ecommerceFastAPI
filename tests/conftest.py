import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from database.db_depends import get_db
from database.db import async_session_maker


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with async_session_maker() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:
    def override_get_db():
        return db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()