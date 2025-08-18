from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.backend.db_depends import get_db
from app.models import Product


async def check_stock(product_id: int,
                      db: AsyncSession = Depends(get_db)):
    stock_product = await db.scalar(
        select(Product.stock)
        .where(Product.id == product_id)
    )
    if not stock_product:
        raise ValueError('Товар отсутствует на складе')

    return stock_product
