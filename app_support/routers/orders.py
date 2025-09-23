from typing import Annotated, Optional
import asyncio

from fastapi import APIRouter, Depends, status, HTTPException, Request, Query, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app_support.database.crud.orders import get_orders, update_status
from app_support.database.db_depends import get_db
from app_support.schemas import OrderResponse
from app.models import *


router = APIRouter(prefix='/support/orders', tags=['orders'])
templates = Jinja2Templates(directory='app_support/templates/')


@router.get('/order/{order_id}', response_model=OrderResponse | None)
async def get_order_by_id(order_id: int,
                          db: AsyncSession = Depends(get_db)):
    result = await get_orders(order_id=order_id, db=db)
    return result


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
                        new_status: str,
                        db: AsyncSession = Depends(get_db)) -> dict:
    try:
        await update_status(order_id=order_id, new_status=new_status, db=db)

        return {'message': f'Статус заказа изменен'}

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )




