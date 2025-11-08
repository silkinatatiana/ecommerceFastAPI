from random import choice, randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.products import get_product


class TestReviews:
    @pytest.mark.positive
    async def test_get_reviews(self, client: AsyncClient, db: AsyncSession):
        products = await get_product(db=db)
        assert products, "No products in DB for testing"

        product = choice(products)
        response = await client.get(f"/reviews/{product.id}")
        assert response.status_code == 200

    @pytest.mark.negative
    async def test_get_reviews2(self, client: AsyncClient, db: AsyncSession):
        product_id = randint(1000, 2000)
        response = await client.get(f"/reviews/{product_id}")
        assert response.status_code == 404

    @pytest.mark.positive
    async def test_create_review(self, client: AsyncClient, db: AsyncSession, test_data_review, test_create_seller,
                                 test_create_customer, test_product_data):
        product = test_product_data
        client.cookies.set("token", test_create_seller)
        response = await client.post("/products/create", json=product)
        created_product = response.json()
        product_id = created_product["id"]

        response = await client.post(f"/reviews/create_by/{product_id}", json=test_data_review, cookies={"token": test_create_customer})
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id

    @pytest.mark.negative
    async def test_create_review2(self, client: AsyncClient, db: AsyncSession, test_data_review):
        products = await get_product(db=db)
        assert products, "No products in DB for testing"
        product = choice(products)
        response = await client.post(f"/reviews/create_by/{product.id}", json=test_data_review)
        assert response.status_code == 401

