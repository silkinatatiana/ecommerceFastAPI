from fastapi import APIRouter, Depends, status, HTTPException, Body, File, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from app.models import *
from app.models import Review
from app.routers.auth import get_current_user
from app.schemas import CreateReviews

router = APIRouter(prefix='/reviews', tags=['reviews'])
templates = Jinja2Templates(directory='app/templates/')

@router.get('/', response_model=list[CreateReviews])
async def all_reviews(db: Annotated[AsyncSession, Depends(get_db)]):
    reviews = await db.scalars(select(Review))
    return reviews.all() or []


@router.get('/{product_id}', response_model=list[CreateReviews])
async def product_reviews(
        db: Annotated[AsyncSession, Depends(get_db)],
        product_id: int
):
    product = await db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Product not found'
        )

    reviews = await db.scalars(
        select(Review)
        .where(Review.product_id == product.id)
    )
    return reviews.all()


@router.post("/products/{product_id}/reviews")
async def create_review(
    product_id: int,
    comment: str = Form(...),
    grade: int = Form(..., ge=1, le=5),
    photo_urls: Optional[List[str]] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if photo_urls and len(photo_urls) > 5:
        raise HTTPException(400, "Можно прикрепить не более 5 фото")

    review = Review(
        user_id=1, # в аргументы функции нужно будет передать реального пользователя и сюда его id
        product_id=product_id,
        comment=comment,
        grade=grade,
        photo_urls=photo_urls or None
    )
    db.add(review)
    await db.commit()
    return {"message": "Отзыв сохранен"}

@router.delete('/{review_id}', status_code=status.HTTP_200_OK)
async def delete_review(
        review_id: int,
        db: Annotated[AsyncSession, Depends(get_db)] # в аргументы функции нужно будет передать реального пользователя (current_user: Annotated[dict, Depends(get_current_user)] )
):
    review = await db.scalar(select(Review).where(Review.id == review_id))
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Review not found'
        )

    # if not current_user.get('is_admin'):
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail='Admin access required'
    #     )

    await db.commit()
    return {'message': 'Review deleted successfully'}

@router.get('/product/{product_id}/reviews', response_class=HTMLResponse)
async def product_reviews(request: Request, product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    reviews = await db.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .options(joinedload(Review.user))
    )
    
    return templates.TemplateResponse("products/reviews.html", {
        "request": request,
        "reviews": [{
            "author": r.user.username if r.user else "Аноним",
            "date": r.comment_date.strftime("%d.%m.%Y"),
            "rating": r.grade,
            "text": r.comment,
            "photo_urls": r.photo_urls if r.photo_urls else []
        } for r in reviews.scalars()]
    })
