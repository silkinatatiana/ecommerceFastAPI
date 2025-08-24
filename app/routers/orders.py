from typing import Optional

import httpx
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select, insert, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import jwt
from starlette.responses import HTMLResponse

from app.backend.db_depends import get_db
from app.config import Config
from app.models import User
from app.models.cart import Cart
from app.models.orders import Orders
from app.models.products import Product
from app.functions import get_user_id_by_token, check_stock

router = APIRouter(prefix="/orders", tags=["orders"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/{user_id}') # возвращает список из словарей-заказов
async def get_orders_by_user_id(user_id: int,
                                db: AsyncSession = Depends(get_db)):
    pass


@router.get('/{order_id}') # возвращает словарь с данными заказа
async def get_order_by_id():
    pass


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_order(token: Optional[str] = Cookie(None, alias='token'),
                       db: AsyncSession = Depends(get_db)) -> dict:
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Пользователь не авторизован")

        user_id = get_user_id_by_token(token)
        if not user_id:
            raise HTTPException(status_code=400, detail="Неверные данные пользователя")

        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Пользователь не найден')

        order_products = None

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/cart/{user_id}")
            order_products = response.json()

        if not order_products:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Товары не найдены'
            )

        products_data = {}
        total_sum = 0

        for product in order_products:
            update_query = (update(Product).where(Product.id == product['product_id']) # TODO вынести в отдельную ручку
                            .values(stock=Product.stock - product['count']))
            await db.execute(update_query)

            products_data[product['product_id']] = {
                'price': product['product']['price'],
                'count': product['count']
            }
            total_sum += product['product']['price'] * product['count']

        order = Orders(
            user_id=user_id,
            products=products_data,
            summa=total_sum
        )
        db.add(order)
        await db.flush()
        await db.commit()

        # async with httpx.AsyncClient() as client: # TODO удалять напрямую из БД
        #     response = await client.post(f"{Config.url}/cart/clear")
        #     response.raise_for_status()

        return {'message': 'Заказ оформлен!',
                'order_id': order.id,
                'redirect_url': f'/orders/{order.id}'}

    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка базы данных: {str(e)}"
        )


@router.patch('/cancel{order_id}')
async def cancel_order():
    pass


@router.get('/{order_id}', response_class=HTMLResponse)
async def order_page(request: Request,
                     order_id: int,
                     token: Optional[str] = Cookie(default=None, alias='token'),
                     db: AsyncSession = Depends(get_db)
                     ):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Пользователь не авторизован")

        user_id = get_user_id_by_token(token)
        if not user_id:
            raise HTTPException(status_code=400, detail="Неверные данные пользователя")

        order_query = select(Orders).where(
            (Orders.id == order_id) &
            (Orders.user_id == user_id)
        )
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Заказ не найден'
            )

        order_products = []
        total_amount = 0

        for product_id, product_data in order.products.items():
            product_query = select(Product).where(Product.id == product_id)
            product_result = await db.execute(product_query)
            product = product_result.scalar_one_or_none()

            if product:
                item_total = product_data['count'] * product_data['price']
                order_products.append({
                    'id': product.id,
                    'name': product.name,
                    'price': product_data['price'],
                    'count': product_data['count'],
                    'image_url': product.image_urls[0],
                    'item_total': item_total
                })
                total_amount += item_total

        context = {
            'request': request,
            'order': {
                'id': order.id,
                'created_at': order.date,
                'status': order.status,
                'total_sum': order.summa
            },
            'products': order_products,
            'total_amount': total_amount
        }
        return templates.TemplateResponse("orders/orders.html", context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке страницы заказа: {str(e)}"
        )
