from random import randint

import pytest_asyncio

from tests.conftest import fake


@pytest_asyncio.fixture
async def test_data_review():
    return {
        "grade": randint(1, 5),
        "comment": fake.text(),
        "photo_urls": [fake.word() for _ in range(fake.random_int(1, 5))],
    }
