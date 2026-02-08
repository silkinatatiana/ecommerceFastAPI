from random import randint

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.category import get_category
from database.crud.products import get_product
from models import Category
from tests.conftest import fake


@pytest_asyncio.fixture(scope="function")
async def test_product_data(db: AsyncSession):
    category = Category(name=fake.word())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    product_data = {
        "name": fake.word().title(),
        "description": None,
        "price": randint(1000, 100000),
        "stock": randint(1, 1000),
        "category_id": category.id,
        "image_urls": [],
        "RAM_capacity": None,
        "built_in_memory_capacity": None,
        "screen": None,
        "cpu": None,
        "number_of_processor_cores": None,
        "number_of_graphics_cores": None,
        "color": None,
    }

    return product_data


@pytest_asyncio.fixture(scope="function")
async def create_category_id(db: AsyncSession):
    fake_category = 1
    all_categories = await get_category(db=db)
    all_category_ids = [cat.id for cat in all_categories]
    if all_category_ids:
        fake_category = max(all_category_ids) + 1
    return fake_category


@pytest_asyncio.fixture(scope="function")
async def create_product(
    client_seller: AsyncClient, db: AsyncSession, test_product_data
):
    product_data = test_product_data
    response = await client_seller.post("/products/create", json=product_data)
    created_product = response.json()
    product_in_db = await get_product(db=db, product_id=created_product["id"])
    assert created_product["name"] == product_in_db.name, "Товар не создан"
    return product_in_db


@pytest_asyncio.fixture(scope="function")
def product_factory(client_seller: AsyncClient, db: AsyncSession, test_product_data):
    async def _create_product(override_data: dict = None):
        data = test_product_data.copy()
        if override_data:
            data.update(override_data)
        response = await client_seller.post("/products/create", json=data)
        assert response.status_code == 200
        created_product = response.json()
        product_in_db = await get_product(db=db, product_id=created_product["id"])
        assert created_product["name"] == product_in_db.name
        return product_in_db

    return _create_product
