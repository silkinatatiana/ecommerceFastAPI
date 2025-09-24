from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Favorites


async def create_favorite(user_id: int,
                          product_id: int,
                          db: AsyncSession):
    try:
        new_favorite = Favorites(
            user_id=user_id,
            product_id=product_id
        )

        db.add(new_favorite)
        await db.commit()
        await db.refresh(new_favorite)

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def get_favorite(db: AsyncSession,
                       user_id: int,
                       product_id: int = None
):
    try:
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

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def delete_favorite(db: AsyncSession,
                          user_id: int,
                          product_id: int = None
):
    try:
        stmt = (
            delete(Favorites).where(
                Favorites.user_id == user_id,
                Favorites.product_id == product_id,
            )
        )
        result = await db.execute(stmt)
        await db.commit()

        if result.rowcount == 0:
            return {'message': 'Товар удален из избранного'}
        return None

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )
