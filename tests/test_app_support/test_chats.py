from random import randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestChat:

    # @pytest.mark.positive
    # async def test_get_all_chats(self, client_support: AsyncClient, db: AsyncSession, test_create_support):
    #     client_support.cookies.set("token", test_create_support)
    #     response = await client_support.get("/support/chats/", cookies={"token": test_create_support})
    #
    #     assert response.status_code == 200

    @pytest.mark.negative
    async def test_get_all_chats_negative(self, client_support: AsyncClient, db: AsyncSession, test_create_client):
        client_support.cookies.set("token", test_create_client)
        response = await client_support.get("/support/chats/", cookies={"token": test_create_client})

        assert response.status_code == 303

    # @pytest.mark.negative
    # async def test_chat_by_id(self, client_support: AsyncClient, db: AsyncSession, test_create_support):
    #     client_support.cookies.set("token", test_create_support)
    #     chat_id = randint(9999, 9999999)
    #     response = await client_support.get(f"/support/chats/{chat_id}", cookies={"token": test_create_support})
    #
    #     assert response.status_code == 404