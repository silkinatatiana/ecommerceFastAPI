from faker import Faker

import pytest_asyncio
from sqlalchemy.ext.asyncio import (create_async_engine, async_sessionmaker)
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

from app.main import app
from app_support.main import app as app_support
from config import Config
from database.db_depends import get_db

fake = Faker()
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM

pytest_plugins = [
    "tests.fixtures.chats",
    "tests.fixtures.auth",
    "tests.fixtures.review",
    "tests.fixtures.user",
    "tests.fixtures.products"
]


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        Config.SQLALCHEMY_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_connection(test_engine):
    async with test_engine.connect() as conn:
        transaction = await conn.begin()
        await conn.begin_nested()
        try:
            yield conn
        finally:
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture(scope="function")
async def db(db_connection):
    session = async_sessionmaker(
        bind=db_connection,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )()
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=Config.url
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client_support(db: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app_support),
        base_url=Config.url_support
    ) as ac:
        yield ac
    app.dependency_overrides.clear()