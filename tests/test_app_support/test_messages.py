import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.messages import get_message
from general_functions.auth_func import get_user_id_by_token
from tests.conftest import fake


class TestMessage:

    @pytest.mark.positive
    async def test_send_message(self, client_support: AsyncClient, db: AsyncSession, test_chat, create_test_user
):
        token = client_support.cookies.get("token")
        employee_id = get_user_id_by_token(token=token)
        user_id = create_test_user.id
        chat = await test_chat(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()

        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})
        assert response.headers.get("Location") == f"/support/chats/{chat.id}/view"

        messages = await get_message(db=db, chat_id=chat.id)
        assert any(m.message == message_text for m in messages), "Сообщение не найдено"

    @pytest.mark.negative
    async def test_send_message_negative(self, client_support: AsyncClient, db: AsyncSession, test_chat_negative,
                                         create_test_user):
        token = client_support.cookies.get("token")
        employee_id = get_user_id_by_token(token=token)
        user_id = create_test_user.id
        chat = await test_chat_negative(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()

        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})
        assert response.status_code == 400

    @pytest.mark.negative
    async def test_send_message_negative2(self, client_any_support: AsyncClient, db: AsyncSession, test_chat, create_test_user):
        token = client_any_support.cookies.get("token")
        employee_id = get_user_id_by_token(token=token)
        user_id = create_test_user.id
        chat = await test_chat(user_id=user_id, employee_id=employee_id)
        message_text = fake.text()
        response = await client_any_support.post(f"/support/messages/{chat.id}/send", data={"message": message_text})

        assert response.status_code == 403