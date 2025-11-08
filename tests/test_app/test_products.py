from random import randint

import pytest
from jose import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.crud.products import get_product


class TestProduct:
    @pytest.mark.positive
    async def test_create_product(
            self, client: AsyncClient, db: AsyncSession, test_product_data, test_create_seller):
        product = test_product_data
        client.cookies.set("token", test_create_seller)
        response = await client.post("/products/create", json=product)
        assert response.status_code == 200

        created_product = response.json()
        product_id = created_product["id"]

        product = await get_product(db=db, product_id=product_id)
        assert product is not None
        assert product.name == test_product_data["name"]

    @pytest.mark.positive
    async def test_products_by_category(self, client: AsyncClient, db: AsyncSession, test_product_data, test_create_seller):
        product = test_product_data
        client.cookies.set("token", test_create_seller)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        category_id = created_product["category_id"]
        payload = jwt.decode(test_create_seller, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload["id"]

        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user_id})
        assert response.status_code == 200

    @pytest.mark.negative
    async def test_products_by_category2(self, client: AsyncClient, db: AsyncSession, create_test_user):
        category_id = randint(999, 9999)
        user = create_test_user
        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user.id})
        assert response.status_code == 404