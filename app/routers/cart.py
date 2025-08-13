import asyncio
from typing import Optional, List

import httpx
import jwt
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from app.backend.db_depends import get_db
from app.config import Config
from app.models import Product
from app.models.cart import Cart
from app.models.users import User
from app.schemas import Cart as cart_schema

router = APIRouter(prefix="/cart", tags=["cart"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}')
async def get_cart_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id == user_id))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='Пользователь не зарегистрирован')

    query = await db.execute(
        select(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .where(Cart.user_id == user_id)
    )

    cart_items = []
    for cart, product in query.all():
        cart_dict = {k: v for k, v in cart.__dict__.items() if not k.startswith('_')}
        product_dict = {k: v for k, v in product.__dict__.items() if not k.startswith('_')}
        cart_dict['product'] = product_dict
        cart_items.append(cart_dict)

    return cart_items


@router.post('/add', status_code=status.HTTP_201_CREATED)
async def add_product_to_cart(product_id: int,
                              user_id: int,
                              count: int,
                              db: AsyncSession = Depends(get_db)):
    try:
        product = await db.scalar(select(Cart).where(Cart.user_id == user_id).where(Cart.product_id == product_id))

        if product:
            result = update_count_cart(product_id=product_id,
                                       user_id=user_id,
                                       count=count,
                                       db=db)
            return result

        result = Cart(user_id=user_id,
                      product_id=product_id,
                      count=count)
        db.add(result)
        await db.commit()
        await db.refresh(result)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении в корзину: {str(e)}"
        )


@router.patch('/update')
async def update_count_cart(
        product_id: int,
        user_id: int,
        count: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        cart_item = await db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == product_id)
        )

        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден в корзине"
            )

        if count > 0:
            cart_item.count = count
            await db.commit()
            await db.refresh(cart_item)
            return cart_item
        else:
            await db.delete(cart_item)
            await db.commit()
            return {"message": "Товар удален из корзины"}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка базы данных: {str(e)}"
        )


@router.delete('/{product_id}')
async def delete_product_from_cart(product_id: int,
                                   token: Optional[str] = Cookie(None, alias='token'),
                                   db: AsyncSession = Depends(get_db)):
    try:

        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        user_id = payload.get("id")

        cart_item = await db.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .where(Cart.product_id == product_id)
        )
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден в корзине"
            )
        await db.delete(cart_item)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка базы данных: {str(e)}"
        )


@router.delete('/clear', status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    products_for_clear = result.scalars().all()

    if not products_for_clear:
        return {'message': 'Корзина пуста'}

    for product in products_for_clear:  # TODO удалить все разом а не в цикле (воспользоваться методом получения всех товаров из корзины и по ним все удалить одной командой)
        await db.delete(product)

    await db.commit()
    return None


@router.get('/', response_class=HTMLResponse)
async def get_cart_html(request: Request,
                        db: AsyncSession = Depends(get_db),
                        token: Optional[str] = Cookie(default=None, alias='token')):
    is_authenticated = False
    cart_products = []

    if token and token != 'None' and token != 'undefined':
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id = payload.get("id")

            async with httpx.AsyncClient() as client:
                response = await client.get(f"{Config.url}/cart/{user_id}")
                response.raise_for_status()

                items = response.json()

                for product in items:
                    cart_products.append({
                        "id": product['product']['id'],
                        "name": product['product']['name'],
                        "description": product['product']['description'],
                        "price": product['product']['price'],
                        "image_urls": product['product']['image_urls'],
                        "count": product['count'],
                        "price_mult_count": product['product']['price'] * product['count']
                    })

        except jwt.ExpiredSignatureError:
            print("Токен истёк")
        except jwt.InvalidTokenError as e:
            print(f"Невалидный токен: {e}")
        except Exception as e:
            print(f"Ошибка при проверке авторизации: {e}")

    return templates.TemplateResponse(
        "cart/cart.html",
        {
            "request": request,
            "is_authenticated": is_authenticated,
            "products": cart_products,
            "shop_name": "PEAR",
            "url": Config.url,
            "descr": "Интернет-магазин электроники"
        }
    )
