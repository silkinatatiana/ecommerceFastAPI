from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, HTTPException

from config import Config
from database.crud.orders import get_orders
from database.crud.users import get_user
from general_functions.auth_func import checking_access_rights
from models import Product


async def fetch_orders_for_user(
    user_id: int,
    page: int,
    per_page: int,
    db: AsyncSession
):
    total_count = await get_orders(func_count=True, user_id=user_id, db=db)
    offset = (page - 1) * per_page
    orders = await get_orders(
        sort_desc=True,
        user_id=user_id,
        offset=offset,
        limit=per_page,
        db=db
    )
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