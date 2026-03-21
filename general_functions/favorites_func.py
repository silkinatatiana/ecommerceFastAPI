from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_depends import get_db
from models import Favorites


async def get_favorite_product_ids(
    user_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        favorite_query = select(Favorites.product_id).where(
            Favorites.user_id == user_id
        )
        favorite_result = await db.execute(favorite_query)
        favorite_product_ids = favorite_result.scalars().all()
        return favorite_product_ids

    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не удалось получить список избранных товаров",
        ) from None
