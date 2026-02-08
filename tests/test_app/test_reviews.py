import datetime
from random import choice, randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.products import get_product
from database.crud.review import get_reviews


class TestReviews:
    @pytest.mark.positive
    async def test_get_reviews(
        self,
        client_customer: AsyncClient,
        db: AsyncSession,
        create_product,
        test_data_review,
    ):
        products = await get_product(db=db)
        product = choice(products)
        datetime_of_publication = datetime.datetime.now()
        response = await client_customer.post(
            f"/reviews/create_by/{product.id}", json=test_data_review
        )
        assert response.status_code == 200

        review_by_productid = await get_reviews(db=db, product_id=product.id)

        assert any(
            rev.grade == test_data_review["grade"]
            and abs((rev.comment_date - datetime_of_publication).total_seconds()) < 0.1
            for rev in review_by_productid
        ), "Отзыв не был получен"

    @pytest.mark.negative
    async def test_get_reviews2(
        self, unauthorized_client: AsyncClient, db: AsyncSession
    ):
        product_id = randint(1000, 2000)
        response = await unauthorized_client.get(f"/reviews/{product_id}")
        assert response.status_code == 404

    @pytest.mark.positive
    async def test_create_review(
        self,
        client_customer: AsyncClient,
        db: AsyncSession,
        test_data_review,
        create_product,
        test_product_data,
    ):
        response = await client_customer.post(
            f"/reviews/create_by/{create_product.id}", json=test_data_review
        )

        assert response.status_code == 200
        created_review = response.json()
        review_in_db = await get_reviews(db=db, review_id=created_review["review_id"])
        assert created_review["review_id"] == review_in_db.id, "Отзыв не был создан"

    @pytest.mark.negative
    async def test_create_review2(
        self,
        unauthorized_client: AsyncClient,
        db: AsyncSession,
        test_data_review,
        create_product,
    ):
        response = await unauthorized_client.post(
            f"/reviews/create_by/{create_product.id}", json=test_data_review
        )
        assert response.status_code == 401
