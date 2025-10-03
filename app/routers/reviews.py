from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException, Cookie
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.crud.products import get_product
from database.crud.review import get_reviews, create_new_review, delete_review
from database.crud.users import get_user
from database.db_depends import get_db
from functions.auth_func import get_user_id_by_token
from schemas import CreateReviews
from models import *

router = APIRouter(prefix='/reviews', tags=['reviews'])
templates = Jinja2Templates(directory='app/templates/')


@router.get('/', response_model=list[CreateReviews])
async def all_reviews(db: AsyncSession = Depends(get_db)):
    reviews = await get_reviews(db=db)
    return reviews or []


@router.get('/{product_id}', response_model=list[CreateReviews])
async def product_reviews(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_id: int
):
    product = await get_product(db=db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='NOT FOUND'
        )

    reviews = await get_reviews(product_id=product_id, db=db)
    return reviews


@router.post("/create_by/{product_id}")
async def create_review(
        review_data: CreateReviews,
        product_id: int,
        token: str = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db),
):
    user_id = None
    if token:
        try:
            user_id = get_user_id_by_token(token)
        except HTTPException:
            user_id = None

    if review_data.photo_urls and len(review_data.photo_urls) > 5:
        raise HTTPException(400, "Можно прикрепить не более 5 фото")

    result = await create_new_review(user_id=user_id,
                                     product_id=product_id,
                                     comment=review_data.comment,
                                     grade=review_data.grade,
                                     photo_urls=review_data.photo_urls,
                                     db=db)
    return result


@router.delete('/{review_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_review_by_id(review_id: int,
                              db: Annotated[AsyncSession, Depends(get_db)],
                              token: str = Cookie(None, alias='token')
):
    try:
        if not token:
            return RedirectResponse(url='/auth/create', status_code=status.HTTP_303_SEE_OTHER)

        user_id = get_user_id_by_token(token)

        current_user = await get_user(user_id=user_id, db=db)

        if not current_user.get('is_admin'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Admin access required'
            )

        review = await delete_review(review_id=review_id, db=db)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )
        return review

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось удалить комментарий: {str(e)}"
        )


