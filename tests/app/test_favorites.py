from random import randint, choice

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import create_test_token
from database.crud.products import get_product


class TestFavorite:
    @pytest.mark.doesnt_work
    @pytest.mark.positive
    async def test_create_favorites(self, client: AsyncClient, test_user):
        role = choice(["customer", "seller"])
        token = create_test_token(user_id=test_user.id, username=test_user.username, role=role)
        products = await get_product(db=db)
        product_id = choice(products).id

        response = await client.post("/favorites/", json=product_id, cookies={"token": token})
        assert response.status_code == 201

    @pytest.mark.doesnt_work
    @pytest.mark.negative
    async def test_create_favorites(self, client: AsyncClient):
        product_id = randint(999, 9999)

        response = await client.post("/favorites/", json=product_id)
        assert response.status_code == 401