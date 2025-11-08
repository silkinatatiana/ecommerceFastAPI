from random import choice

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import fake
from models import User, Chats


@pytest_asyncio.fixture
async def test_chat(db: AsyncSession, create_test_user: User):
    employee = User(
        username=fake.user_name(),
        email=fake.email(),
        role=choice(["customer", "seller"]),
        hashed_password="fake_hashed_password"
    )
    db.add(employee)
    await db.flush()

    chat = Chats(
        user_id=create_test_user.id,
        employee_id=employee.id,
        topic=fake.sentence(),
        active=True
    )
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    await db.commit()

    return chat


@pytest_asyncio.fixture
async def test_chat_negative(db: AsyncSession, create_test_user: User):
    employee = User(
        username=fake.user_name(),
        email=fake.email(),
        role=choice(["customer", "seller"]),
        hashed_password="fake_hashed_password"
    )
    db.add(employee)
    await db.flush()

    chat = Chats(
        user_id=create_test_user.id,
        employee_id=employee.id,
        topic=fake.sentence(),
        active=False
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