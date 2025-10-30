import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from database.crud.users import get_user


@pytest.mark.asyncio
async def test_register(client: AsyncClient, db: AsyncSession):
    response = await client.post("/auth/register", json={
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser123",
        "email": "test123@example.com",
        "password": "pass123",
        "confirm_password": "pass123",
        "role": "customer"
    })
    assert response.status_code == 200

    user = await get_user(username="testuser123")
    assert user is not None
    assert user.email == "test123@example.com"