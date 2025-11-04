from random import choice, randint

import pytest

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import create_test_token
from database.crud.category import get_category
from database.crud.products import get_product


class TestProduct:
    @pytest.mark.positive1
    async def test_create_product(self, client: AsyncClient, db: AsyncSession, test_product_data, test_user):
        #TODO сделать отдельную фикстуру, которая создает юзера через ручку бекенда (фикстура на тест (scope=что-то)
        #TODO получаю юзера, из него токен. Сделать отдельные фикстуры на создание юзеров с разными ролями
        response = await client.post("/products/create", json=test_product_data, cookies={"token": token},
                                     headers={'Content-Type': 'application/json'})
        print(response.json())
        assert response.status_code == 200 # TODO status_code 500

        # created_product = response.json() # TODO может быть, не json
        # product_id = created_product["id"]
        #
        # product = await get_product(db=db, product_id=product_id)
        # assert product is not None
        # assert product.name == test_product_data["name"]

    @pytest.mark.positive
    async def test_products_by_category(self, client: AsyncClient, db: AsyncSession, test_user):
        categories = await get_category(db=db)
        assert categories, "No categories in DB for testing"
        category_id = choice(categories).id
        user = test_user
        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user.id})
        assert response.status_code == 200

    @pytest.mark.negative
    async def test_products_by_category2(self, client: AsyncClient, db: AsyncSession, test_user):
        category_id = randint(999, 9999)
        user = test_user
        response = await client.get(f"/products/by_category/{category_id}", params={"user_id": user.id})
        assert response.status_code == 404