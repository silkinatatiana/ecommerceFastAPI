import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import get_chat
from models import Chats
from tests.conftest import fake


@pytest_asyncio.fixture
async def test_chat(db: AsyncSession):
    async def _create_chat(user_id: int, employee_id: int):
        chat = Chats(
            user_id=user_id, employee_id=employee_id, topic=fake.sentence(), active=True
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
            active=False,
        )
        db.add(chat)
        await db.flush()
        await db.refresh(chat)
        await db.commit()
        return chat

    return _create_chat


@pytest_asyncio.fixture
async def test_chat_create():
    return {"topic": fake.sentence()}


@pytest_asyncio.fixture
async def fake_chat_id(db: AsyncSession):
    chats = await get_chat(db=db)
    chat_id = 1
    all_chat_ids = [chat.id for chat in chats]
    if all_chat_ids:
        chat_id = max(all_chat_ids) + 1
    return chat_id
