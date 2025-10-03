from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Favorites


@handle_db_errors
async def create_favorite(db: AsyncSession,
                          user_id: int,
                          product_id: int
):
    new_favorite = Favorites(
        user_id=user_id,
        product_id=product_id
    )

    db.add(new_favorite)
    await db.commit()
    await db.refresh(new_favorite)


@handle_db_errors
async def get_favorite(db: AsyncSession,
                       user_id: int,
                       product_id: int = None
):
    query = select(Favorites)

    if user_id:
        query = query.where(Favorites.user_id == user_id)

    if product_id:
        query = query.where(Favorites.product_id == product_id)

    if product_id:
        result = await db.scalar(query)

    else:
        favorites = await db.execute(query)
        result = favorites.scalars().all()

    return result


@handle_db_errors
async def delete_favorite(db: AsyncSession,
                          user_id: int,
                          product_id: int = None
):
    query = (delete(Favorites).where(
            Favorites.user_id == user_id,
            Favorites.product_id == product_id)
    )
    result = await db.execute(query)
    await db.commit()

    if result.rowcount == 0:
        return {'message': 'Товар удален из избранного'}
    return None
