import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import fake


class TestMessage:

    @pytest.mark.positive
    async def test_send_message(self, client_support: AsyncClient, db: AsyncSession, test_chat, test_create_support):
        chat = test_chat
        message = fake.text()
        client_support.cookies.set("token", test_create_support)

        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message}, cookies={"token": test_create_support})

        assert response.status_code == 303

    @pytest.mark.negative
    async def test_send_message_negative(self, client_support: AsyncClient, db: AsyncSession, test_chat_negative, test_create_support):
        chat = test_chat_negative
        message = fake.text()
        client_support.cookies.set("token", test_create_support)
        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message}, cookies={"token": test_create_support})

        assert response.status_code == 400

    @pytest.mark.negative
    async def test_send_message_negative2(self, client_support: AsyncClient, db: AsyncSession, test_chat, test_create_client):
        chat = test_chat
        message = fake.text()
        client_support.cookies.set("token", test_create_client)
        response = await client_support.post(f"/support/messages/{chat.id}/send", data={"message": message}, cookies={"token": test_create_client})

        assert response.status_code == 403