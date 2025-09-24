from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models import Review


async def get_reviews(
        db: AsyncSession,
        review_id: int = None,
        product_id: int = None):
    try:
        query = select(Review)

        if review_id:
            query = query.where(Review.id == review_id)

        if product_id:
            query = query.where(Review.product_id == product_id)

        if review_id:
            result = await db.scalar(query)

        else:
            reviews = await db.execute(query)
            result = reviews.scalars().all()

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


async def create_new_review(user_id: int,
                            product_id: int,
                            comment: str,
                            grade: int,
                            db: AsyncSession,
                            photo_urls: list = None):
    try:
        review = Review(user_id=user_id,
                        product_id=product_id,
                        comment=comment,
                        grade=grade,
                        photo_urls=photo_urls or []
        )
        db.add(review)
        await db.commit()
        await db.refresh(review)
        return {
            "message": "Отзыв сохранен",
            "review_id": review.id,
            "product_id": review.product_id
        }

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


async def delete_review(db: AsyncSession,
                          review_id: int = None
):
    try:
        query = (delete(Review).where(Review.id == review_id))
        result = await db.execute(query)
        await db.commit()

        if result.rowcount == 0:
            return {'message': 'Комментарий удален'}
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
