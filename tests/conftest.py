import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import app
from app_support.main import app as app_support
from config import Config
from database.db import Base
from database.db_depends import get_db


fake = Faker()
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM

pytest_plugins = [
    "tests.fixtures.chats",
    "tests.fixtures.auth",
    "tests.fixtures.review",
    "tests.fixtures.user",
    "tests.fixtures.products",
    "tests.fixtures.message",
]

engine = create_async_engine(
    Config.SQLALCHEMY_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        async with TestingSessionLocal(bind=conn) as session:
            yield session


async def register_and_login(ac: AsyncClient, role: str) -> str:
    register_data = {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "pass123123",
        "confirm_password": "pass123123",
        "role": role,
    }
    response = await ac.post("/auth/register", json=register_data)
    assert response.status_code == 303, (
        f"Registration failed: {response.status_code}, body: {response.text}"
    )

    token = ac.cookies.get("token")
    assert token is not None, "Token cookie not set after registration"


async def _create_client(
    app_instance, db: AsyncSession, role: str = None
) -> AsyncClient:
    async def override_get_db():
        yield db

    app_instance.dependency_overrides[get_db] = override_get_db

    ac = AsyncClient(transport=ASGITransport(app=app_instance), base_url="http://test")
    await ac.__aenter__()

    if role is not None:
        await register_and_login(ac, role)

    async def cleanup():
        await ac.__aexit__(None, None, None)
        app_instance.dependency_overrides.clear()

    return ac, cleanup


@pytest_asyncio.fixture(scope="function")
async def unauthorized_client(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app, db, role=None)
    yield ac
    await cleanup()


@pytest_asyncio.fixture(scope="function")
async def unauthorized_client_support(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app_support, db, role=None)
    yield ac
    await cleanup()


@pytest_asyncio.fixture(scope="function")
async def client_customer(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app, db, role="customer")
    yield ac
    await cleanup()


@pytest_asyncio.fixture(scope="function")
async def client_seller(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app, db, role="seller")
    yield ac
    await cleanup()


@pytest_asyncio.fixture(scope="function")
async def client_support(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app_support, db, role="support")
    yield ac
    await cleanup()


@pytest_asyncio.fixture(params=["customer", "seller"])
async def client_any(db: AsyncSession, request) -> AsyncClient:
    ac, cleanup = await _create_client(app, db, role=request.param)
    yield ac
    await cleanup()


@pytest_asyncio.fixture(params=["customer", "seller"])
async def client_any_support(db: AsyncSession, request) -> AsyncClient:
    ac, cleanup = await _create_client(app_support, db, role=request.param)
    yield ac
    await cleanup()


@pytest_asyncio.fixture(scope="function")
async def client_support_wrong(db: AsyncSession) -> AsyncClient:
    ac, cleanup = await _create_client(app, db, role="support")
    yield ac
    await cleanup()
