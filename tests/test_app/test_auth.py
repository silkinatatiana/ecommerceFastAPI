import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.users import get_user


class TestAuth:
    @pytest.mark.positive
    async def test_register(
        self, unauthorized_client: AsyncClient, db: AsyncSession, get_user_data
    ):
        response = await unauthorized_client.post("/auth/register", json=get_user_data)
        assert response.status_code == 303

        user = await get_user(db=db, username=get_user_data["username"])
        assert user is not None
        assert user.email == get_user_data["email"], "Пользователь не зарегистрирован"

    @pytest.mark.negative
    async def test_register2(
        self,
        unauthorized_client: AsyncClient,
        db: AsyncSession,
        test_data_user_negative,
    ):
        response = await unauthorized_client.post(
            "/auth/register", json=test_data_user_negative
        )
        assert response.status_code == 400

        user = await get_user(db=db, username=test_data_user_negative["username"])
        assert user is None

    @pytest.mark.negative
    async def test_login(
        self, unauthorized_client: AsyncClient, db: AsyncSession, login_data_negative
    ):
        response = await unauthorized_client.post(
            "/auth/login", json=login_data_negative
        )
        assert response.status_code == 401
