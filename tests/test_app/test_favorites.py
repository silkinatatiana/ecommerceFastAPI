import pytest
import json
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestFavorite:
    @pytest.mark.positive
    async def test_create_favorites(self, client: AsyncClient, db: AsyncSession, test_create_seller, test_create_client, test_product_data):
        product = test_product_data
        client.cookies.set("token", test_create_seller)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post("/favorites/", json={'product_id': product_id}, cookies={"token": test_create_client})
        assert response.status_code == 201

    @pytest.mark.negative
    async def test_create_favorites_negative(self, client: AsyncClient, db: AsyncSession, test_create_seller, test_create_support, test_product_data):
        product = test_product_data
        client.cookies.set("token", test_create_seller)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post("/favorites/", json={'product_id': product_id}, cookies={"token": test_create_support})
        assert response.status_code == 403


