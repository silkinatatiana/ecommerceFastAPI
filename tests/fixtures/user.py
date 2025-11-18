from random import choice

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

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


# @pytest_asyncio.fixture(scope="function")
# async def test_seller_token(client: AsyncClient, db: AsyncSession):
#     register_data = {
#         "first_name": fake.first_name(),
#         "last_name": fake.last_name(),
#         "username": fake.user_name(),
#         "email": fake.email(),
#         "password": "pass123123",
#         "confirm_password": "pass123123",
#         "role": "seller"
#     }
#
#     response = await client.post("/auth/register", json=register_data)
#
#     assert response.status_code == 303, f"Registration failed: {response.status_code}, body: {response.text}"
#
#     token = response.cookies.get("token")
#     assert token is not None, "Token cookie not set after registration"
#
#     return token
#
#
# @pytest_asyncio.fixture(scope="function")
# async def test_client_token(client: AsyncClient, db: AsyncSession):
#     register_data = {
#         "first_name": fake.first_name(),
#         "last_name": fake.last_name(),
#         "username": fake.user_name(),
#         "email": fake.email(),
#         "password": "pass123123",
#         "confirm_password": "pass123123",
#         "role": choice(["customer", "seller"])
#     }
#
#     response = await client.post("/auth/register", json=register_data)
#
#     assert response.status_code == 303, f"Registration failed: {response.status_code}, body: {response.text}"
#
#     token = response.cookies.get("token")
#     assert token is not None, "Token cookie not set after registration"
#     return token
#
#
# @pytest_asyncio.fixture(scope="function")
# async def test_customer_token(client: AsyncClient, db: AsyncSession): # test_create_customer
#     register_data = {
#         "first_name": fake.first_name(),
#         "last_name": fake.last_name(),
#         "username": fake.user_name(),
#         "email": fake.email(),
#         "password": "pass123123",
#         "confirm_password": "pass123123",
#         "role": "customer"
#     }
#
#     response = await client.post("/auth/register", json=register_data)
#
#     assert response.status_code == 303, f"Registration failed: {response.status_code}, body: {response.text}"
#
#     token = response.cookies.get("token")
#     assert token is not None, "Token cookie not set after registration"
#
#     return token
#
#
# @pytest_asyncio.fixture(scope="function")
# async def test_support_token(client: AsyncClient, db: AsyncSession):
#     register_data = {
#         "first_name": fake.first_name(),
#         "last_name": fake.last_name(),
#         "username": fake.user_name(),
#         "email": fake.email(),
#         "password": "pass123123",
#         "confirm_password": "pass123123",
#         "role": "support"
#     }
#
#     response = await client.post("/auth/register", json=register_data)
#
#     assert response.status_code == 303, f"Registration failed: {response.status_code}, body: {response.text}"
#
#     token = response.cookies.get("token")
#     assert token is not None, "Token cookie not set after registration"
#
#     return token


@pytest_asyncio.fixture(scope='function')
async def test_profile_update():
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email()
        }