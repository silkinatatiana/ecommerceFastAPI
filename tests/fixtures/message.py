import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from models import Messages
from tests.conftest import fake


@pytest_asyncio.fixture
async def test_send_message(
    db: AsyncSession, test_chat, user_id: int, employee_id: int, sender_user=True
):
    sender_id = employee_id
    if sender_user:
        sender_id = user_id
    current_chat = test_chat(user_id=user_id, employee_id=employee_id)
    message = Messages(
        chat_id=current_chat.id, message=fake.text(), sender_id=sender_id
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    await db.commit()

    return message
