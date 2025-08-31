from typing import Optional

import httpx
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from app.backend.db_depends import get_db
from app.config import Config
from app.models import User
from app.models.orders import Orders
from app.models.products import Product
from app.functions.auth_func import get_user_id_by_token
from app.functions.product_func import update_stock
from app.schemas import OrderResponse

router = APIRouter(prefix="/orders", tags=["orders"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/user/{user_id}')
async def get_orders_by_user_id(
        user_id: int,
        page: int = Query(1, ge=1, description="Номер страницы"),
        per_page: int = Query(5, ge=1, le=50, description="Количество заказов на странице"),
        db: AsyncSession = Depends(get_db)
):
    try:
        total_count_result = await db.execute(
            select(func.count()).select_from(Orders).where(Orders.user_id == user_id)
        )
        total_count = total_count_result.scalar()

        offset = (page - 1) * per_page

        result = await db.execute(
            select(Orders)
            .where(Orders.user_id == user_id)
            .order_by(desc(Orders.date))
            .offset(offset)
            .limit(per_page)
        )
        orders = result.scalars().all()
        total_pages = (total_count + per_page - 1) // per_page

        return {
            "orders": orders,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )


@router.get('/{order_id}', response_model=OrderResponse)
async def get_order_by_id(order_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    order = await db.scalar(select(Orders).where(Orders.id == order_id))

    if not order:
        return templates.TemplateResponse(
            "exceptions/not_found.html",
            {"request": request}
        )
    return order


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_order(token: Optional[str] = Cookie(None, alias='token'),
                       db: AsyncSession = Depends(get_db)):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Пользователь не авторизован")

        user_id = get_user_id_by_token(token)

        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Пользователь не найден'
            )

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{Config.url}/cart/{user_id}")
            order_products = response.json()

        if not order_products:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Корзина пуста'
            )

        products_data = {}
        total_sum = 0

        for product in order_products:
            await update_stock(product_id=product['product_id'], count=product['count'], db=db)

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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{Config.url}/cart/clear",
                cookies={'token': token}
            )
            response.raise_for_status()
            await db.commit()

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


@router.get('/order/{order_id}', response_class=HTMLResponse)
async def order_page(request: Request,
                     order_id: int,
                     token: Optional[str] = Cookie(default=None, alias='token'),
                     db: AsyncSession = Depends(get_db)
                     ):
    try:
        if not token:
            raise HTTPException(status_code=401, detail="Пользователь не авторизован")

        user_id = get_user_id_by_token(token)

        order_query = select(Orders).where(
            (Orders.id == order_id) &
            (Orders.user_id == user_id)
        )
        order_result = await db.execute(order_query)
        order = order_result.scalar_one_or_none()

        if not order:
            return templates.TemplateResponse(
                "exceptions/not_found.html",
                {"request": request}
            )

        order_products = []
        total_amount = 0

        for product_id, product_data in order.products.items():
            product_query = select(Product).where(Product.id == int(product_id))
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
                'created_at': order.date.strftime("%Y-%m-%d %H:%M"),
                'status': order.status,
                'total_sum': order.summa
            },
            'products': order_products,
            'total_amount': total_amount,
            'user_id': user_id
        }
        return templates.TemplateResponse("orders/order_page.html", context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке страницы заказа: {str(e)}"
        )
