from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Product, Favorites
from schemas import CreateProduct


@handle_db_errors
async def create_new_product(db: AsyncSession,
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

    return product


@handle_db_errors
async def get_product(db: AsyncSession,
                      category_ids: list = None,
                      product_id: int = None,
                      product_ids: list = None,
                      func_count: bool = False,
                      colors: list = None,
                      built_in_memory: list = None,
                      order_dy_: int | str = None
):
    query = select(Product)

    if func_count:
        query = select(func.count()).select_from(Product)

    if product_id:
        query = query.where(Product.id == product_id)

    if product_ids:
        query = query.where(Product.id.in_product_ids)

    if category_ids:
        query = query.where(Product.category_id.in_(category_ids))

    if colors:
        query = query.where(Product.color.in_(colors))

    if built_in_memory:
        query = query.where(Product.built_in_memory_capacity.in_(built_in_memory))

    if order_dy_:
        query = query.order_by(order_dy_)

    if func_count or product_id:
        result = await db.scalar(query)
        return result

    result = await db.execute(query)
    products = result.scalars().all()
    return products or []


@handle_db_errors
async def get_products_with_filters(
    db: AsyncSession,
    category_id: int,
    page: int = 1,
    per_page: int = 3,
    colors: Optional[str] = None,
    built_in_memory: Optional[str] = None,
    user_id: Optional[int] = None,
    favorites: Optional[List[str]] = None,
) -> tuple[List[Product], int]:

    base_query = select(Product).where(Product.category_id == category_id).order_by(Product.id)
    count_query = select(func.count()).select_from(Product).where(Product.category_id == category_id)

    if colors:
        colors_list = [c.strip() for c in colors.split(",") if c.strip()]
        if colors_list:
            color_condition = Product.color.in_(colors_list)
            base_query = base_query.where(color_condition)
            count_query = count_query.where(color_condition)

    if built_in_memory:
        memory_list = [m.strip() for m in built_in_memory.split(",") if m.strip()]
        if memory_list:
            memory_condition = Product.built_in_memory_capacity.in_(memory_list)
            base_query = base_query.where(memory_condition)
            count_query = count_query.where(memory_condition)

    if favorites is not None and user_id:
        favorite_ids_query = select(Favorites.product_id).where(Favorites.user_id == user_id)
        favorite_ids = (await db.scalars(favorite_ids_query)).all()
        if favorite_ids:
            base_query = base_query.where(Product.id.in_(favorite_ids))
            count_query = count_query.where(Product.id.in_(favorite_ids))
        else:
            base_query = base_query.where(False)
            count_query = count_query.where(False)

    total_count = await db.scalar(count_query) or 0

    offset = (page - 1) * per_page
    paginated_query = base_query.offset(offset).limit(per_page)
    products = (await db.scalars(paginated_query)).all()

    return products, total_count



