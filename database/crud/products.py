from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Product
from schemas import CreateProduct


@handle_db_errors
async def create_product(db: AsyncSession,
                         product_data: CreateProduct,
                         supplier_id: int,
):
    product = Product(
        **product_data.dict(exclude_unset=True),
        supplier_id=supplier_id
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)


@handle_db_errors
async def get_product(db: AsyncSession,
                      category_ids: int = None,
                      product_ids: int = None,
                      func_count: bool = False,
                      colors: list = None,
                      built_in_memory: list = None
):
    query = select(Product)

    if func_count:
        query = select(func.count()).select_from(Product)

    if product_ids:
        query = query.where(Product.id.in_product_ids)

    if category_ids:
        query = query.where(Product.category_id.in_(category_ids))

    if colors:
        query = query.where(Product.color.in_(colors))

    if built_in_memory:
        query = query.where(Product.built_in_memory_capacity.in_(built_in_memory))

    if func_count:
        result = await db.scalar(query)
        return result

    result = await db.execute(query)
    products = result.scalars().all()
    return products or []




