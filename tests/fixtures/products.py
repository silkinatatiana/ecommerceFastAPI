from random import randint

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.category import get_category
from tests.conftest import fake
from models import Category


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
        "color": None
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