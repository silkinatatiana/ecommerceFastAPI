import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestFavorite:
    @pytest.mark.positive
    async def test_create_favorites(self, client_any: AsyncClient, db: AsyncSession, create_product):
        response = await client_any.post("/favorites/", json={'product_id': create_product.id})
        assert response.status_code == 201
        response = await client_any.get("/favorites/")
        fav_products = response.json()
        assert any(fav['product_id'] == create_product.id for fav in fav_products), "Товар не был добавлен в избранное"

    @pytest.mark.negative
    async def test_create_favorites_negative(self, client_support_wrong: AsyncClient, db: AsyncSession, create_product):
        response = await client_support_wrong.post("/favorites/", json={'product_id': create_product.id})
        assert response.status_code == 403


