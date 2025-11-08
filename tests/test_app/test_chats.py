from random import randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.auth import create_test_token


class TestChat:

    @pytest.mark.positive
    async def test_chats_close(self, client: AsyncClient, db: AsyncSession, test_chat, test_create_client):
        client.cookies.set("token", test_create_client)
        chat = test_chat

        response = await client.patch("/chats/close", params={"chat_id": chat.id}, cookies={"token": test_create_client})
        assert response.status_code == 204

    @pytest.mark.negative
    async def test_chat_create(self, client: AsyncClient, db: AsyncSession, test_chat_create, create_test_user, create_test_token):
        token = create_test_token(user_id=create_test_user.id, username=create_test_user.username, role="unknown")
        response = await client.post("chats/create", json=test_chat_create, cookies={"token": token})
        assert response.status_code == 403

    @pytest.mark.negative
    async def test_chat_by_id(self, client: AsyncClient, db: AsyncSession, create_test_user, create_test_token):
        token = create_test_token(user_id=create_test_user.id, username=create_test_user.username, role="customer")
        chat_id = randint(9999, 9999999)
        response = await client.get(f"/chats/{chat_id}", cookies={"token": token})

        assert response.status_code == 404