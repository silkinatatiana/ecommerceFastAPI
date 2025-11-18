from random import choice, randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.products import get_product


class TestReviews:
    @pytest.mark.positive
    async def test_get_reviews(self, client: AsyncClient, db: AsyncSession, test_product_data, test_seller_token, test_data_review, test_customer_token):
        product = test_product_data
        client.cookies.set("token", test_seller_token)
        await client.post("/products/create", json=product)

        products = await get_product(db=db)
        assert products, "No products in DB for testing"

        product = choice(products)
        test_review = test_data_review

        response = await client.post(f"/reviews/create_by/{product.id}", json=test_review, cookies={"token": test_customer_token})
        assert response.status_code == 200

        response = await client.get(f"/reviews/{product.id}")
        assert response.status_code == 200
        reviews_by_id = response.json()
        assert any(rev == test_review for rev in reviews_by_id), "Отзыв не был получен"

    @pytest.mark.negative
    async def test_get_reviews2(self, client: AsyncClient, db: AsyncSession):
        product_id = randint(1000, 2000)
        response = await client.get(f"/reviews/{product_id}")
        assert response.status_code == 404

    @pytest.mark.positive
    async def test_create_review(self, client: AsyncClient, db: AsyncSession, test_data_review, test_seller_token,
                                 test_customer_token, test_product_data):
        product = test_product_data # TODO вынести в отдельную фикстуру, внутри них можно делать assert
        client.cookies.set("token", test_seller_token)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post(f"/reviews/create_by/{product_id}", json=test_data_review, cookies={"token": test_customer_token})
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        # TODO зайти в БД и проверить что создалось в БД

    @pytest.mark.negative
    async def test_create_review2(self, client: AsyncClient, db: AsyncSession, test_data_review, test_product_data, test_seller_token):
        product = test_product_data
        client.cookies.set("token", test_seller_token)
        await client.post("/products/create", json=product)
        products = await get_product(db=db)
        assert products, "No products in DB for testing"

        product = choice(products)
        client.cookies.clear()
        response = await client.post(f"/reviews/create_by/{product.id}", json=test_data_review)
        assert response.status_code == 401

