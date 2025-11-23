import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.messages import get_message
from tests.conftest import fake


class TestMessage:

    @pytest.mark.positive
    async def test_send_message(self, client_support: AsyncClient, client_any: AsyncClient, db: AsyncSession, test_chat,
                                user_and_employee_ids
):
        user_id, employee_id = user_and_employee_ids
        chat = await test_chat(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()

        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})
        assert response.headers.get("Location") == f"/support/chats/{chat.id}/view"

        messages = await get_message(db=db, chat_id=chat.id)
        assert any(m.message == message_text for m in messages), "Сообщение не найдено"

    @pytest.mark.negative
    async def test_send_message_negative(self, client_support: AsyncClient, client_any: AsyncClient, db: AsyncSession,
                                         test_chat_negative, user_and_employee_ids):
        user_id, employee_id = user_and_employee_ids
        chat = await test_chat_negative(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()

        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})
        assert response.status_code == 400

    @pytest.mark.negative
    async def test_send_message_negative2(self, client_any_support: AsyncClient, client_any: AsyncClient,
                                          db: AsyncSession, test_chat, user_and_employee_ids):
        user_id, employee_id = user_and_employee_ids
        chat = await test_chat(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()
        response = await client_any_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})

        assert response.status_code == 403