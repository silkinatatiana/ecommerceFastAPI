import pytest
from httpx import AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
from database.crud.products import get_product
from tests.conftest import fake


class TestProduct:
    @pytest.mark.positive
    async def test_create_product(
        self, client_seller: AsyncClient, db: AsyncSession, create_product
    ):
        new_product = await get_product(db=db, product_id=create_product.id)
        assert new_product.category_id == create_product.category_id, (
            f"Не создан товар в категории: {create_product.category_id}"
        )
        assert new_product.price == create_product.price, (
            f"Не создан товар по цене: {create_product.price}"
        )
        assert new_product.stock == create_product.stock, (
            f"Не создан товар в количестве: {create_product.stock}"
        )

    @pytest.mark.positive
    async def test_products_by_category(
        self, unauthorized_client: AsyncClient, db: AsyncSession, create_product
    ):
        response = await unauthorized_client.get(
            f"/products/by_category/{create_product.category_id}"
        )
        products_by_category = response.json()
        assert response.status_code == 200
        assert all(
            prod["category_id"] == create_product.category_id
            for prod in products_by_category["products"]
        )

    @pytest.mark.positive
    async def test_products_by_category2(
        self, client_any: AsyncClient, db: AsyncSession, create_product
    ):
        token = client_any.cookies.get("token")
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload["id"]
        colors = fake.word()

        response = await client_any.get(
            f"/products/by_category/{create_product.category_id}",
            params={
                "user_id": user_id,
                "colors": colors,
                "built_in_memory": fake.word(),
            },
        )
        products_by_category = response.json()

        assert response.status_code == 200
        assert all(
            prod["category_id"] == create_product.category_id
            for prod in products_by_category["products"]
        )

    @pytest.mark.negative
    async def test_products_by_category_negative2(
        self,
        client_any: AsyncClient,
        db: AsyncSession,
        create_test_user,
        create_category_id,
    ):
        category_id = create_category_id
        token = client_any.cookies.get("token")
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload["id"]
        response = await client_any.get(
            f"/products/by_category/{category_id}", params={"user_id": user_id}
        )
        assert response.status_code == 404
