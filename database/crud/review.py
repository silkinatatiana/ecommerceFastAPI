from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Review


@handle_db_errors
async def get_reviews(db: AsyncSession,
                      review_id: int = None,
                      product_id: int = None
):
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


@handle_db_errors
async def create_new_review(db: AsyncSession,
                            user_id: int | None,
                            product_id: int,
                            comment: str,
                            grade: int,
                            photo_urls: list = None
):
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


@handle_db_errors
async def delete_review(db: AsyncSession,
                        review_id: int = None
):
    query = (delete(Review).where(Review.id == review_id))
    result = await db.execute(query)
    await db.commit()

    if result.rowcount == 0:
        return {'message': 'Комментарий удален'}
    return None
