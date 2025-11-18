import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import get_chat
from general_functions.auth_func import get_user_id_by_token


class TestChat:

    @pytest.mark.positive
    async def test_get_all_chats(self, client_support: AsyncClient, db: AsyncSession, test_chat, create_test_user):
        token_support = client_support.cookies.get("token")
        employee_id = get_user_id_by_token(token=token_support)
        user = create_test_user
        await test_chat(user_id=user.id, employee_id=employee_id)
        response = await client_support.get("/support/chats/all")
        assert response.status_code == 200 # TODO нужны ли здесь проверки из БД?

    @pytest.mark.negative
    async def test_get_all_chats_negative(self, client_any_support: AsyncClient, db: AsyncSession):
        response = await client_any_support.get("/support/chats/all")

        assert response.status_code == 303
        assert response.headers.get("Location") == "/auth/create"

    @pytest.mark.negative
    async def test_chat_by_id(self, client_support: AsyncClient, db: AsyncSession):
        chats = await get_chat(db=db)
        chat_id = 1
        all_chat_ids = [chat.id for chat in chats]
        if all_chat_ids:
            chat_id = max(all_chat_ids) + 1
        response = await client_support.get(f"/support/chats/{chat_id}")

        assert response.status_code == 404