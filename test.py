# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Импортируем приложения
from app.main import app as client_app
from app_support.main import app as support_app

# Импортируем зависимости и модели
from app.database import Base, get_db
from app.models import User, Product, Order, ChatMessage  # убедитесь, что все модели импортированы
from app.auth import create_access_token

# Тестовая БД (меняйте под вашу конфигурацию)
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ecommerce_test"

engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,  # уменьшает overhead при тестах
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Создаём все таблицы перед тестами и удаляем после."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def override_get_db():
    """Фикстура для подмены сессии БД."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(override_get_db):
    """TestClient для клиентского приложения (app)."""
    def _get_db_override():
        yield override_get_db

    client_app.dependency_overrides[get_db] = _get_db_override
    with TestClient(client_app) as c:
        yield c
    client_app.dependency_overrides.clear()

@pytest.fixture
def support_client(override_get_db):
    """TestClient для панели поддержки (app_support)."""
    # Предполагается, что app_support тоже использует get_db из app.database
    from app_support.dependencies import get_db as get_support_db  # ← проверьте путь!

    def _get_db_override():
        yield override_get_db

    support_app.dependency_overrides[get_support_db] = _get_db_override
    with TestClient(support_app) as c:
        yield c
    support_app.dependency_overrides.clear()

@pytest.fixture
def create_user(override_get_db):
    """Создаёт тестового пользователя и возвращает его данные."""
    db = override_get_db
    email = "user@example.com"
    username = "testuser"
    password = "password123"

    # Хешируем пароль (пример — замените на вашу функцию)
    from app.utils import get_password_hash
    hashed_pw = get_password_hash(password)

    user = User(email=email, username=username, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": email, "username": username, "password": password}

@pytest.fixture
def auth_headers(create_user):
    """Возвращает заголовки с JWT-токеном для авторизованного пользователя."""
    token = create_access_token(data={"sub": create_user["username"]})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def create_product(override_get_db):
    """Создаёт тестовый товар."""
    db = override_get_db
    product = Product(name="Тестовый ноутбук", description="...", price=50000, stock=10)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_add_to_cart(client, auth_headers, create_product):
    response = client.post("/cart/add",
                           json={"product_id": create_product.id},
                           headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Товар добавлен в корзину"


def test_get_cart(client, auth_headers, create_product):
    # Сначала добавим
    client.post("/cart/add", json={"product_id": create_product.id}, headers=auth_headers)
    # Потом получим
    response = client.get("/cart/", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["product_id"] == create_product.id


# Запустить все тесты
# pytest tests/ -v