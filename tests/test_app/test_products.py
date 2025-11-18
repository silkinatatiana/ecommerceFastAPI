from random import randint

import pytest
from jose import jwt
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.crud.products import get_product
from schemas import CreateProduct
from tests.conftest import fake
from tests.functions import validate_json_response


class TestProduct:
    @pytest.mark.positive
    async def test_create_product(self, client: AsyncClient, db: AsyncSession, test_product_data, test_seller_token):
        product = test_product_data
        client.cookies.set("token", test_seller_token)
        response = await client.post("/products/create", json=product)
        assert response.status_code == 200

        created_product = response.json()
        product_id = created_product["id"]

        product = await get_product(db=db, product_id=product_id)
        assert product is not None
        validate_json_response(json_data=product, schema_class=CreateProduct)
        assert product.name == test_product_data["name"] # TODO зайти в БД проверить

    @pytest.mark.positive
    async def test_products_by_category(self, client: AsyncClient, db: AsyncSession, test_product_data, test_seller_token):
        product = test_product_data
        client.cookies.set("token", test_seller_token) # TODO разделить на авторизованных и неавторизованных клиентов (4 клиента в конфтест)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        category_id = created_product["category_id"]
        payload = jwt.decode(test_seller_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload["id"]

        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user_id})
        products_by_category = response.json()

        assert response.status_code == 200
        assert all(prod["category_id"] == category_id for prod in products_by_category["products"])

    @pytest.mark.positive
    async def test_products_by_category2(self, client: AsyncClient, db: AsyncSession, test_product_data, test_seller_token):
        product = test_product_data
        client.cookies.set("token", test_seller_token)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        category_id = created_product["category_id"]
        payload = jwt.decode(test_seller_token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload["id"]
        colors = fake.word()
        built_in_memory: fake.word()

        response = await client.get(f"/products/by_category/{category_id}",
                                    params={"user_id": user_id, "colors": colors, "built_in_memory": built_in_memory})
        products_by_category = response.json()

        assert response.status_code == 200
        assert all(prod["category_id"] == category_id for prod in products_by_category["products"])

    @pytest.mark.negative
    async def test_products_by_category2(self, client: AsyncClient, db: AsyncSession, create_test_user, create_category_id):
        category_id = create_category_id
        user = create_test_user
        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user.id})
        assert response.status_code == 404
