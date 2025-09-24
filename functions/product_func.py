from fastapi import Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Product
from database.db_depends import get_db


async def check_stock(product_id: int,
                      db: AsyncSession = Depends(get_db)):
    stock_product = await db.scalar(
        select(Product.stock)
        .where(Product.id == product_id)
    )
    if not stock_product:
        raise ValueError('Товар отсутствует на складе')

    return stock_product


async def update_stock(product_id: int,
                       count: int,
                       add: bool = False,
                       db: AsyncSession = Depends(get_db)):
    if not add:
        current_count = await check_stock(product_id=product_id, db=db)

        if current_count is None:
            raise ValueError(f"Товар с ID {product_id} не найден")

        if current_count - count < 0:
            raise ValueError(f'К заказу доступно {current_count} ед. товара')

        update_query = (update(Product).where(Product.id == product_id)
                        .values(stock=Product.stock - count))
    else:
        update_query = (update(Product).where(Product.id == product_id)
                        .values(stock=Product.stock + count))

    await db.execute(update_query)
    await db.commit()
    return {'message': 'Количество товара на складе обновлено'}

