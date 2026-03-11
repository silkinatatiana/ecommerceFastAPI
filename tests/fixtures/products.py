from random import randint
from unittest.mock import patch

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from config import Config
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


def _make_create_form_data(product_data: dict):
    """Подготовка FormData для создания товара с изображением."""
    data = {k: str(v) for k, v in product_data.items() if v is not None and k != "image_urls"}
    minimal_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14"
        b"\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' "
        b",#\x1c\x1c(7),01444\x1f'9=82<.7\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01"
        b"\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08"
        b"\x01\x01\x00\x00?\x00\xf9\x7f\xff\xd9"
    )
    files = {"file": ("test.jpg", minimal_jpeg, "image/jpeg")}
    return data, files


@pytest_asyncio.fixture(scope="function")
async def create_product(
    client_seller: AsyncClient, db: AsyncSession, test_product_data
):
    product_data = test_product_data
    data, files = _make_create_form_data(product_data)
    s3_url = f"{Config.S3_PUBLIC_URL or 'http://test'}/users/1/test.jpg"
    with patch("app.routers.products.s3_client") as mock_s3:
        mock_s3.upload_fileobj.return_value = s3_url
        mock_s3.public_url = Config.S3_PUBLIC_URL or "http://test"
        response = await client_seller.post("/products/create", data=data, files=files)
    assert response.status_code == 200, response.text
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
        form_data, files = _make_create_form_data(data)
        s3_url = f"{Config.S3_PUBLIC_URL or 'http://test'}/users/1/test.jpg"
        with patch("app.routers.products.s3_client") as mock_s3:
            mock_s3.upload_fileobj.return_value = s3_url
            mock_s3.public_url = Config.S3_PUBLIC_URL or "http://test"
            response = await client_seller.post(
                "/products/create", data=form_data, files=files
            )
        assert response.status_code == 200
        created_product = response.json()
        product_in_db = await get_product(db=db, product_id=created_product["id"])
        assert created_product["name"] == product_in_db.name
        return product_in_db

    return _create_product
