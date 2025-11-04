# from random import choice, randint
#
# import pytest
# from httpx import AsyncClient
#
# from conftest import create_test_token
# from database.crud.products import get_product
#
#
# class TestReviews:
#     @pytest.mark.positive
#     async def test_get_reviews(self, client: AsyncClient):
#         products = await get_product(db=db)
#         assert products, "No products in DB for testing"
#
#         product = choice(products)
#         response = await client.get(f"/reviews/{product.id}")
#         assert response.status_code == 200
#
#     @pytest.mark.negative
#     async def test_get_reviews2(self, client: AsyncClient):
#         product_id = randint(1000, 2000)
#         response = await client.get(f"/reviews/{product_id}")
#         assert response.status_code == 404
#
#     @pytest.mark.doesnt_work
#     @pytest.mark.positive
#     async def test_create_review(self, client: AsyncClient, test_data_review, test_user):
#         token = create_test_token(user_id=test_user.id, username=test_user.username, role="customer")
#         products = await get_product(db=db)
#         assert products, "No products in DB for testing"
#         product = choice(products)
#         response = await client.post(f"/reviews/create_by/{product.id}", json=test_data_review, cookies={"token": token})
#         assert response.status_code == 200 # TODO не работает
#
#         data = response.json()
#         assert data["user_id"] == test_user.id
#         assert data["product_id"] == product.id
#
#     @pytest.mark.negative
#     async def test_create_review2(self, client: AsyncClient, test_data_review):
#         products = await get_product(db=db)
#         assert products, "No products in DB for testing"
#         product = choice(products)
#         response = await client.post(f"/reviews/create_by/{product.id}", json=test_data_review)
#         assert response.status_code == 401
#
