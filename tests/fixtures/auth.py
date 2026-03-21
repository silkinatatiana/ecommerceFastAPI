from datetime import UTC, datetime, timedelta
from random import choice, randint

import jwt
import pytest
import pytest_asyncio

from tests.conftest import ALGORITHM, SECRET_KEY, fake


@pytest_asyncio.fixture
async def login_data_negative():
    return {"username": fake.user_name(), "password": "fhgvhjvhjg"}


@pytest.fixture
def create_test_token():
    def _make_token(user_id: int, username: str, role: str):
        expire = datetime.now(UTC) + timedelta(hours=1)
        payload = {
            "sub": username,
            "id": user_id,
            "role": role,
            "is_admin": False,
            "exp": expire,
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return _make_token


@pytest_asyncio.fixture(scope="function")
async def create_fake_token() -> str:
    payload = {
        "user_id": randint(100, 1000),
        "exp": datetime.utcnow() + timedelta(minutes=randint(10, 40)),
        "iat": datetime.utcnow(),
        "role": choice(["seller", "customer"]),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
