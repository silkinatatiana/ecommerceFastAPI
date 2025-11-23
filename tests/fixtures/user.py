from random import choice

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from general_functions.auth_func import get_user_id_by_token
from tests.conftest import fake
from models import User


@pytest_asyncio.fixture
async def get_user_data(): # test_data_user
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
async def create_test_user(db: AsyncSession) -> User:
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


@pytest_asyncio.fixture
async def create_test_support(db: AsyncSession) -> User:
    user = User(
        username=fake.user_name(),
        email=fake.email(),
        role="support",
        hashed_password="fake_hashed_password"
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture(scope='function')
async def test_profile_update():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email()
        }


@pytest_asyncio.fixture
async def user_and_employee_ids(client_any: AsyncClient, client_support: AsyncClient):
    token_support = client_support.cookies.get("token")
    token_user = client_any.cookies.get("token")

    if not token_user or not token_support:
        raise ValueError("Токены не найдены в куках клиентов. Убедитесь, что клиенты аутентифицированы.")

    employee_id = get_user_id_by_token(token=token_support)
    user_id = get_user_id_by_token(token=token_user)

    return user_id, employee_id