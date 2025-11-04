from random import randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import create_test_token


class TestChat:

    @pytest.mark.doesnt_work
    @pytest.mark.positive
    async def test_chats_close(self, client: AsyncClient, test_chat, test_user):
        token = create_test_token(user_id=test_user.id, username=test_user.username, role="customer")
        chat = test_chat

        response = await client.patch("/chats/close", json=chat.id, cookies={"token": token})
        assert response.status_code == 204

    @pytest.mark.negative
    async def test_chat_create(self, client: AsyncClient, test_chat_create, test_user):
        token = create_test_token(user_id=test_user.id, username=test_user.username, role="unknown")
        response = await client.post("chats/create", json=test_chat_create, cookies={"token": token})
        assert response.status_code == 403

    @pytest.mark.negative
    async def test_chat_by_id(self, client: AsyncClient, test_user):
        token = create_test_token(user_id=test_user.id, username=test_user.username, role="customer")
        chat_id = randint(9999, 9999999)
        response = await client.get(f"/chats/{chat_id}", cookies={"token": token})

        assert response.status_code == 404