import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.chats import get_chat


class TestChat:
    @pytest.mark.positive
    async def test_chats_close(
        self,
        client_any: AsyncClient,
        client_support: AsyncClient,
        db: AsyncSession,
        test_chat,
        user_and_employee_ids,
    ):
        user_id, employee_id = user_and_employee_ids
        chat = await test_chat(user_id=user_id, employee_id=employee_id)

        response = await client_any.patch("/chats/close", params={"chat_id": chat.id})
        assert response.status_code == 204

        update_chat = await get_chat(db=db, chat_id=chat.id)
        assert update_chat.active is False, "Чат не закрыт: active=True"

    @pytest.mark.negative
    async def test_chat_create(
        self, client_support_wrong: AsyncClient, db: AsyncSession, test_chat_create
    ):
        response = await client_support_wrong.post(
            "chats/create", json=test_chat_create
        )
        assert response.status_code == 403

    @pytest.mark.negative1
    async def test_chat_by_id(
        self, client_any: AsyncClient, db: AsyncSession, fake_chat_id
    ):
        response = await client_any.get(f"/chats/{fake_chat_id}")

        assert response.status_code == 404
