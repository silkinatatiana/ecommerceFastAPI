from datetime import timedelta, datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from passlib.context import CryptContext

from app.backend.db_depends import get_db
from app.config import Config
from app.main import logger
from app.models import Product, User, Favorites, Cart
from app.schemas import CartUpdate
from app.exception import NotMoreProductsException

SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')
templates = Jinja2Templates(directory='app/templates/')


async def check_stock(product_id: int,
                      db: AsyncSession = Depends(get_db)):
    stock_product = await db.scalar(
        select(Product.stock)
        .where(Product.id == product_id)
    )
    if not stock_product:
        raise ValueError('Товар отсутствует на складе')

    return stock_product


async def update_stock(product_id: int,
                       count: int,
                       add: bool = False,
                       db: AsyncSession = Depends(get_db)):
    if not add:
        current_count = await check_stock(product_id=product_id, db=db)

        if current_count is None:
            raise ValueError(f"Товар с ID {product_id} не найден")

        if current_count - count < 0:
            raise ValueError(f'К заказу доступно {current_count} ед. товара')

        update_query = (update(Product).where(Product.id == product_id)
                        .values(stock=Product.stock - count))
    else:
        update_query = (update(Product).where(Product.id == product_id)
                        .values(stock=Product.stock + count))

    await db.execute(update_query)
    await db.commit()
    return {'message': 'Количество товара на складе обновлено'}


async def create_access_token(username: str, user_id: int, is_admin: bool, role: str,
                              expires_delta: timedelta):
    payload = {
        'sub': username,
        'id': user_id,
        'is_admin': is_admin,
        'role': role,
        'exp': datetime.now(timezone.utc) + expires_delta
    }

    payload['exp'] = int(payload['exp'].timestamp())
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception

        expire = payload.get("exp")
        if expire is None or datetime.utcnow() > datetime.utcfromtimestamp(expire):
            raise credentials_exception

        return {
            "username": username,
            "id": user_id,
            "is_admin": payload.get("is_admin", False),
            "role": payload.get("role", "user")
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception


def get_user_id_by_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходимо авторизоваться"
        )
    return user_id


async def authenticate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_from_cookie(request: Request):
    token = request.cookies.get("token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await get_current_user(token.replace("Bearer", ""))


async def get_favorite_product_ids(user_id: int,
                                   db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        favorite_query = select(Favorites.product_id).where(Favorites.user_id == user_id)
        favorite_result = await db.execute(favorite_query)
        favorite_product_ids = favorite_result.scalars().all()
        return favorite_product_ids

    except SQLAlchemyError as e:
        logger.error(f"Database error getting favorites for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список избранных товаров"
        )


async def get_in_cart_product_ids(user_id: int,
                                  db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        cart_query = select(Cart.product_id).where(Cart.user_id == user_id)
        cart_result = await db.execute(cart_query)
        in_cart_product_ids = cart_result.scalars().all()
        return in_cart_product_ids

    except SQLAlchemyError as e:
        logger.error(f"Database error getting products in the cart for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список товаров в корзине"
        )


async def update_quantity_cart_add(cart_data: CartUpdate,
                                   cart_item: Cart,
                                   db: AsyncSession = Depends(get_db)):
    stock_product = await check_stock(product_id=cart_data.product_id, db=db)
    if cart_item.count + cart_data.count > stock_product:
        raise NotMoreProductsException()

    cart_item.count += cart_data.count
    await db.commit()
    await db.refresh(cart_item)

    return {
        "product_id": cart_item.product_id,
        "new_count": cart_item.count,
        "removed": False
    }


async def update_quantity_cart_reduce(cart_data: CartUpdate,
                                      cart_item: Cart,
                                      db: AsyncSession = Depends(get_db)):
    if cart_item.count - cart_data.count <= 0:
        await db.delete(cart_item)
        await db.commit()
        return {
            "product_id": cart_item.product_id,
            "new_count": 0,
            "removed": True
        }
    else:
        cart_item.count -= cart_data.count
        await db.commit()
        return {
            "product_id": cart_item.product_id,
            "new_count": cart_item.count,
            "removed": False
        }


def not_found(request: Request):
    return templates.TemplateResponse(
        "exceptions/not_found.html",
        {"request": request}
    )
