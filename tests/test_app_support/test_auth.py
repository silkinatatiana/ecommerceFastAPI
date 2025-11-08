import pytest

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import fake


class TestAuth:
    @pytest.mark.positive
    async def test_update_profile(self, client_support: AsyncClient, db: AsyncSession, test_create_support, test_profile_update):
        new_data = test_profile_update
        client_support.cookies.set("token", test_create_support)
        response = await client_support.put("/auth/update", json=new_data, cookies={"token": test_create_support})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == 'Данные профиля успешно обновлены'

    @pytest.mark.negative
    async def test_update_profile_negative(self, client_support: AsyncClient, db: AsyncSession, test_create_support):
        client_support.cookies.set("token", test_create_support)
        response = await client_support.put("/auth/update", json=fake.text(), cookies={"token": test_create_support})
        assert response.status_code == 422

    @pytest.mark.negative
    async def test_update_profile_negative2(self, client_support: AsyncClient, db: AsyncSession, test_profile_update):
        response = await client_support.put("/auth/update", json=test_profile_update)
        assert response.status_code == 303