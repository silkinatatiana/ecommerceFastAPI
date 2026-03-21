import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.users import get_user
from general_functions.auth_func import get_user_id_by_token
from schemas import ProfileUpdate
from tests.conftest import fake
from tests.functions import validate_json_response


class TestAuth:
    @pytest.mark.positive
    async def test_update_profile(
        self, client_support: AsyncClient, db: AsyncSession, test_profile_update
    ):
        new_data = test_profile_update
        response = await client_support.put("/auth/update", json=new_data)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Данные профиля успешно обновлены"

        validate_json_response(json_data=new_data, schema_class=ProfileUpdate)
        token = client_support.cookies.get("token")
        assert token is not None, (
            "Client is not authenticated — token missing in cookies"
        )

        user_id = get_user_id_by_token(token=token)
        updated_user = await get_user(db=db, user_id=user_id)
        assert all(
            new_data[field] == getattr(updated_user, field) for field in new_data.keys()
        ), (
            f"Данные профиля не обновлены. Ожидалось: {new_data}, получено: {{k: getattr(updated_user, k, '<missing>') for k in new_data}}"
        )

    @pytest.mark.negative
    async def test_update_profile_negative(
        self, client_support: AsyncClient, db: AsyncSession
    ):
        response = await client_support.put("/auth/update", json=fake.text())
        assert response.status_code == 422

    @pytest.mark.negative
    async def test_update_profile_negative2(
        self,
        unauthorized_client_support: AsyncClient,
        db: AsyncSession,
        test_profile_update,
    ):
        response = await unauthorized_client_support.put(
            "/auth/update", json=test_profile_update
        )
        assert response.status_code == 303
        assert response.headers["Location"] == "/auth/create"
