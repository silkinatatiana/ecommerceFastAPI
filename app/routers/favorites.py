from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi.templating import Jinja2Templates

from app.routers.auth import get_current_user
from app.backend.db_depends import get_db
from app.models.favorites import Favorites
from app.models.users import User
from app.models.products import Product

router = APIRouter(prefix="/favorites", tags=["favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/')
async def get_favorites(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    result = await db.execute(
        select(Favorites).where(Favorites.user_id == user_id)
        .options(selectinload(Favorites.products))
    )

    favorites = result.scalars().all()
    fav_products = [fav.products for fav in favorites]

    return fav_products


@router.post('/', response_model=Favorites, status_code=status.HTTP_201_CREATED)
async def create_favorites(user_id: int, product_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не зарегистрирован")

    product = await db.scalar(select(Product).where(Product.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")

    existing_favorite = await db.scalar(
        select(Favorites)
        .where(Favorites.user_id == user_id)
        .where(Favorites.product_id == product_id)
    )

    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Товар уже в избранном"
        )

    try:
        new_favorite = Favorites(
            user_id=user_id,
            product_id=product_id
        )

        db.add(new_favorite)
        await db.commit()
        await db.refresh(new_favorite)
        return new_favorite
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка при добавлении в избранное"
        )


@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def del_favorite_product(db: Annotated[AsyncSession, Depends(get_db)], product_id: int, user_id: int):
    favorite = await db.scalar(select(Favorites)
                               .where(Favorites.user_id == user_id)
                               .where(Favorites.product_id == product_id))
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден в избранном"
        )

    try:
        await db.delete(favorite)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении: {str(e)}"
        )
