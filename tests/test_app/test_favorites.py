import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestFavorite:
    @pytest.mark.positive
    async def test_create_favorites(self, client: AsyncClient, db: AsyncSession, test_seller_token, test_client_token, test_product_data):
        product_data = test_product_data
        client.cookies.set("token", test_seller_token)
        response = await client.post("/products/create", json=product_data)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post("/favorites/", json={'product_id': product_id}, cookies={"token": test_client_token})
        assert response.status_code == 201
        response = await client.get("/favorites/", cookies={"token": test_client_token})
        fav_products = response.json()
        assert any(fav['product_id'] == product_id for fav in fav_products), "Товар не был добавлен в избранное"

    @pytest.mark.negative
    async def test_create_favorites_negative(self, client: AsyncClient, db: AsyncSession, test_seller_token, test_support_token, test_product_data):
        product = test_product_data
        client.cookies.set("token", test_seller_token)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post("/favorites/", json={'product_id': product_id}, cookies={"token": test_support_token})
        assert response.status_code == 403


