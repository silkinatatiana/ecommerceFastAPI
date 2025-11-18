from random import randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import get_chat
from general_functions.auth_func import get_user_id_by_token
from tests.conftest import fake
from tests.fixtures.auth import create_test_token


class TestChat:

    @pytest.mark.positive
    async def test_chats_close(self, client: AsyncClient, db: AsyncSession, test_chat, test_client_token, create_test_support):
        client.cookies.set("token", test_client_token)
        user_id = get_user_id_by_token(token=test_client_token)
        chat = await test_chat(user_id=user_id, employee_id=create_test_support.id)
        response = await client.patch("/chats/close", params={"chat_id": chat.id}, cookies={"token": test_client_token})
        assert response.status_code == 204

        update_chat = await get_chat(db=db, chat_id=chat.id)
        assert update_chat.active is False, "Чат не закрыт: active=True"

    @pytest.mark.negative
    async def test_chat_create(self, client: AsyncClient, db: AsyncSession, create_test_user,
                               create_test_token, create_test_support):
        chat_data = {
            "user_id": create_test_user.id,
            "employee_id": create_test_support.id,
            "topic": fake.sentence(),
            "active": False
        }
        token = create_test_token(user_id=create_test_user.id, username=create_test_user.username, role="unknown")

        response = await client.post("chats/create", json=chat_data, cookies={"token": token})
        assert response.status_code == 403

    @pytest.mark.negative
    async def test_chat_by_id(self, client: AsyncClient, db: AsyncSession, create_test_user, create_test_token):
        token = create_test_token(user_id=create_test_user.id, username=create_test_user.username, role="customer")
        chat_id = randint(9999, 9999999)
        response = await client.get(f"/chats/{chat_id}", cookies={"token": token})

        assert response.status_code == 404