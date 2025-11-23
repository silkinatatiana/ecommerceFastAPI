from random import randint

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from general_functions.auth_func import get_user_id_by_token


class TestOrder:
    @pytest.mark.positive
    @pytest.mark.asyncio
    async def test_check_order_status(self, client_customer: AsyncClient, client_support: AsyncClient,
                                      db: AsyncSession, product_factory
    ):
        token = client_customer.cookies.get("token")
        user_id = get_user_id_by_token(token=token)

        for _ in range(randint(1, 3)):
            product = await product_factory()
            count = randint(1, 10)
            response = await client_customer.post("/cart/add", json={"product_id": product.id, "count": count})
            assert response.status_code == 201

            resp = await client_customer.get(f"/cart/{user_id}")
            assert resp.status_code == 200
            cart = resp.json()
            assert len(cart) > 0, "Корзина пуста"

        response = await client_customer.post("/orders/create")
        assert response.status_code == 201, "Заказ не оформлен"

        created_order = response.json()
        order_id = created_order["order_id"]

        response_support = await client_support.get(f"/support/order/{order_id}")

        assert response_support.status_code == 200
        html = response_support.text
        assert str(order_id) in html
        assert "Оформлен" in html
