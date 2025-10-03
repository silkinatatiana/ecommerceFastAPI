from typing import Optional

import httpx
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse, RedirectResponse

from database.crud.decorators import handler_base_errors
from database.crud.orders import create_new_order, get_orders, update_status
from database.crud.users import get_user
from database.db_depends import get_db
from app.config import Config
from models import Product
from functions.auth_func import get_user_id_by_token
from functions.product_func import update_stock
from schemas import OrderResponse

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
        total_count = await get_orders(func_count=True,
                                       user_id=user_id,
                                       db=db)
        offset = (page - 1) * per_page

        orders = await get_orders(sort_desc=True,
                                  user_id=user_id,
                                  offset=offset,
                                  limit=per_page,
                                  db=db)
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
    order = await get_orders(order_id=order_id, db=db)

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
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_id = get_user_id_by_token(token)

        user = await get_user(user_id=user_id, db=db)
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

        order = await create_new_order(user_id=user_id,
                                       products=products_data,
                                       summa=total_sum,
                                       db=db)

        async with httpx.AsyncClient() as client:
            response = await client.delete(
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


@router.patch('/cancel_order/{order_id}')
async def cancel_order(order_id: int,
                       token: Optional[str] = Cookie(default=None, alias='token'),
                       db: AsyncSession = Depends(get_db)):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        await update_status(order_id=order_id, db=db, new_status='CANCELLED')
        return f'Заказ № {order_id} отменен'

    except HTTPException:
        raise

    except SQLAlchemyError as e:
        print(f"Общая ошибка SQLAlchemy: {e}")
        await db.rollback()

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Произошла внутренняя ошибка при отмене заказа'
        )


@router.get('/order/{order_id}', response_class=HTMLResponse)
@handler_base_errors
async def order_page(request: Request,
                     order_id: int,
                     token: Optional[str] = Cookie(default=None, alias='token'),
                     db: AsyncSession = Depends(get_db)
):
    is_authenticated = False
    if not token:
        return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

    user_id = get_user_id_by_token(token)
    if user_id:
        is_authenticated = True

    order = await get_orders(order_id=order_id, db=db)
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
        "is_authenticated": is_authenticated,
        'user_id': user_id,
        'shop_name': Config.shop_name,
        'descr': Config.descr
    }
    return templates.TemplateResponse("orders/order_page.html", context)

