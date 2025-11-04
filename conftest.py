from typing import Optional
from random import choice, randint
from datetime import datetime, timedelta, timezone
import jwt

import pytest
import asyncio
from faker import Faker
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from config import Config
from database.db_depends import get_db
from database.db import async_session_maker
from models import User, Chats

fake = Faker()
SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM


@pytest_asyncio.fixture(scope="session", autouse=True) # тоже самое сделать для клиента
async def db() -> AsyncSession: # TODO эта фикстура должна быть для сессии всех тестов
    async with async_session_maker() as session:
        async with session.begin() as transaction:
            try:
                yield session
            finally:
                # await transaction.rollback()


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(base_url=Config.url) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_data_user():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "pass123123",
        "confirm_password": "pass123123",
        "role": choice(["customer", "seller"])
    }


@pytest_asyncio.fixture
async def test_data_user_negative():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "username": fake.user_name(),
        "email": fake.email(),
        "password": "pass123123",
        "confirm_password": "pass",
        "role": choice(["customer", "seller"])
    }


@pytest_asyncio.fixture
async def login_data_negative():
    return {
        "username": fake.user_name(),
        "password": "fhgvhjvhjg"
    }


@pytest_asyncio.fixture
async def test_product_data():
    return {
        "name": fake.word().title(),
        "description": None,
        "price": randint(1000, 100000),
        "stock": randint(1, 1000),
        "category_id": randint(1, 4),
        "image_urls": None,
        "RAM_capacity": None,
        "built_in_memory_capacity": None,
        "screen": None,
        "cpu": None,
        "number_of_processor_cores": None,
        "number_of_graphics_cores": None,
        "color": None
    }


@pytest_asyncio.fixture
async def test_data_review():
    return {
        "grade": randint(1, 5),
        "comment": fake.text(),
        "photo_urls": [fake.word() for _ in range(fake.random_int(1, 5))]
    }


@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(
        username=fake.user_name(),
        email=fake.email(),
        role="customer",
        hashed_password="fake_hashed_password"
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def create_test_token(user_id: int, username: str, role: str):
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": username,
        "id": user_id,
        "role": role,
        "is_admin": False,
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest_asyncio.fixture
async def test_chat(db: AsyncSession, test_user: User):
    employee = User(
        username=fake.user_name(),
        email=fake.email(),
        role="seller",
        hashed_password="fake_hashed_password"
    )
    db.add(employee)
    await db.flush()

    chat = Chats(
        user_id=test_user.id,
        employee_id=employee.id,
        topic=fake.sentence(),
        active=True
    )
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    return chat

@pytest_asyncio.fixture
async def test_chat_create():
    return {
        "topic": fake.sentence()
    }