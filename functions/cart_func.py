from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.main import logger
from database.db_depends import get_db
from models import Cart


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