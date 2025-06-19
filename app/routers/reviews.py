from fastapi import APIRouter, Depends, status, HTTPException, Body
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from sqlalchemy import select, update, func
from app.models import *
from app.routers.auth import get_current_user
from app.schemas import CreateReviews

router = APIRouter(prefix='/reviews', tags=['reviews'])


@router.get('/', response_model=list[CreateReviews])
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review).where(Review.is_active == True))
    return reviews.all() or []


@router.get('/{product_slug}', response_model=list[CreateReviews])
async def product_reviews(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_slug: str
):
    product = await db.scalar(select(Product).where(Product.slug == product_slug))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found'
        )

    reviews = await db.scalars(
        select(Review)
        .where(Review.product_id == product.id)
        .where(Review.is_active == True)
    )
    return reviews.all()


@router.post('/{product_name}', status_code=status.HTTP_201_CREATED)
async def add_review(
        product_name: str,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[dict, Depends(get_current_user)],
        review_data: CreateReviews = Body(...)
):
    if not current_user.get('is_customer'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Only customers can leave reviews'
        )

    product = await db.scalar(select(Product).where(Product.name == product_name))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found'
        )

    new_review = Review(
        user_id=current_user['id'],
        product_id=product.id,
        comment=review_data.comment,
        grade=review_data.grade
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    await update_product_rating(db, product.id)

    return {'review_id': new_review.id}


async def update_product_rating(db: AsyncSession, product_id: int):
    await db.execute(
        update(Product)
        .where(Product.id == product_id)
        .values(rating=select(func.avg(Review.grade))
                .where(Review.product_id == product_id)
                .where(Review.is_active == True))
    )
    await db.commit()


@router.delete('/{review_id}', status_code=status.HTTP_200_OK)
async def delete_review(
        review_id: int,
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: Annotated[dict, Depends(get_current_user)]
):
    review = await db.scalar(select(Review).where(Review.id == review_id))
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Review not found'
        )

    if not current_user.get('is_admin'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Admin access required'
        )

    review.is_active = False
    await db.commit()
    await update_product_rating(db, review.product_id)

    return {'message': 'Review deleted successfully'}
