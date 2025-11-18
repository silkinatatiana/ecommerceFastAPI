import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import fake
from models import Chats


@pytest_asyncio.fixture
async def test_chat(db: AsyncSession):
    async def _create_chat(user_id: int, employee_id: int):
        chat = Chats(
            user_id=user_id,
            employee_id=employee_id,
            topic=fake.sentence(),
            active=True
        )
        db.add(chat)
        await db.flush()
        await db.refresh(chat)
        await db.commit()
        return chat

    return _create_chat


@pytest_asyncio.fixture
async def test_chat_negative(db: AsyncSession):
    async def _create_chat(user_id: int, employee_id: int):
        chat = Chats(
            user_id=user_id,
            employee_id=employee_id,
            topic=fake.sentence(),
            active=False
        )
        db.add(chat)
        await db.flush()
        await db.refresh(chat)
        await db.commit()
        return chat

    return _create_chat


@pytest_asyncio.fixture
async def test_chat_create():
    return {
        "topic": fake.sentence()
    }