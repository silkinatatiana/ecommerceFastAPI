
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database.crud.decorators import handle_db_errors
from models.views import Views


@handle_db_errors
async def get_views_by_product_user(db: AsyncSession, user_id: int, product_id: int):
    if user_id and product_id:
        views = await db.scalar(
            select(Views).where(
                Views.user_id == user_id, Views.product_id == product_id
            )
        )
        return views


@handle_db_errors
async def get_all_views_by_user(db: AsyncSession, user_id: int) -> list[Views]:
    result = await db.scalars(
        select(Views).where(Views.user_id == user_id).order_by(Views.count_views.desc())
    )
    return result.all()


@handle_db_errors
async def create_views_product(db: AsyncSession, user_id: int, product_id: int):
    view = Views(user_id=user_id, product_id=product_id)

    db.add(view)
    await db.commit()
    await db.refresh(view)

    return view


@handle_db_errors
async def update_views_by_product_user(db: AsyncSession, user_id: int, product_id: int):
    view = await get_views_by_product_user(
        user_id=user_id, product_id=product_id, db=db
    )

    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Нет связки по пользователю и продукту",
        )

    query = (
        update(Views)
        .where(Views.user_id == user_id, Views.product_id == product_id)
        .values(count_views=view.count_views + 1)
    )
    await db.execute(query)
    await db.commit()
