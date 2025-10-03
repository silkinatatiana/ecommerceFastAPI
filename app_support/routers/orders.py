from fastapi import APIRouter, Depends, status, HTTPException, Query, Request, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from starlette.responses import HTMLResponse, RedirectResponse

from app_support.config import Config
from database.crud.orders import get_orders, update_status
from database.crud.users import get_user
from database.db_depends import get_db
from schemas import OrderResponse, ChangeOrderStatus
from models import *

router = APIRouter(prefix='/support', tags=['orders'])
templates = Jinja2Templates(directory='app_support/templates/')


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


@router.patch('/change_status/{order_id}')
async def change_status(order_id: int,
                        status_obj: ChangeOrderStatus,
                        token: str = Cookie(None, alias='token'),
                        db: AsyncSession = Depends(get_db)) -> dict:
    try:
        if not token:
            return RedirectResponse(url='/auth/create')

        await update_status(order_id=order_id, new_status=status_obj.new_status, db=db)

        return {'message': f'Статус заказа изменен'}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )


@router.get('/order/{order_id}', response_class=HTMLResponse)
async def get_order_detail(request: Request,
                           order_id: int,
                           token: str = Cookie(None, alias='token'),
                           db: AsyncSession = Depends(get_db)
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create')
        order = await get_orders(order_id=order_id, db=db)
        if not order:
            return templates.TemplateResponse(
                "exceptions/not_found.html",
                {"request": request}
            )

        order_products = []
        total_amount = 0

        user = await get_user(db=db, user_id=order.user_id)

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
            'order': order,
            'products': order_products,
            'total_amount': total_amount,
            'user': user,
            'is_authenticated': True,
            'shop_name': Config.shop_name,
            'descr': Config.descr
        }
        return templates.TemplateResponse("orders/order_page.html", context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при загрузке страницы заказа: {str(e)}"
        )