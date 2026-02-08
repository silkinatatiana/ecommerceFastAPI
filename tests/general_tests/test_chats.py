import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import fake


class TestChat:
    @pytest.mark.positive1
    async def test_new_message(
        self,
        client_any: AsyncClient,
        client_support: AsyncClient,
        db: AsyncSession,
        test_chat,
        user_and_employee_ids,
    ):
        user_id, employee_id = user_and_employee_ids
        chat = await test_chat(user_id, employee_id)

        message_text = fake.text()
        response = await client_any.post(
            "/messages/create", json={"chat_id": chat.id, "message": message_text}
        )
        assert response.status_code == 201

        message_from_user = response.json()
        assert message_from_user["chat_id"] == chat.id
        assert message_from_user["message"] == message_text
        assert message_from_user["sender_id"] == user_id

        response_support = await client_support.get(
            f"/support/messages/{chat.id}/messages"
        )
        assert response_support.status_code == 200

        message_to_support = response_support.json()
        assert message_to_support["chat_id"] == chat.id

        message = message_to_support["messages"]
        assert len(message) == 1, f"Ожидалось 1 сообщение, получено: {len(message)}"
        msg = message[0]
        assert msg["chat_id"] == chat.id
        assert msg["sender_id"] == user_id
        assert msg["message"] == message_text
        assert msg["id"] == message_from_user["id"]
