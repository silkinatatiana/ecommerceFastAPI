from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select

from app.main import logger
from app.database.db_depends import get_db
from app.functions.product_func import check_stock
from app.models import Cart
from app.schemas import CartUpdate
from app.exception import NotMoreProductsException

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