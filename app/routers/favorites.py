from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated, List
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
async def get_favorites(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Favorites)
        .where(Favorites.user_id == current_user['id'])
    )

    favorites = result.scalars().all()
    return favorites


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_favorites(
        product_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    try:
        new_favorite = Favorites(
            user_id=current_user['id'],
            product_id=product_id
        )

        db.add(new_favorite)
        await db.commit()
        await db.refresh(new_favorite)
        return new_favorite

    except IntegrityError as e:
        await db.rollback()
        if "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот товар уже в избранном"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при добавлении в избранное: {str(e)}"
        )
#
#
# @router.delete('/', response_model=Favorites, status_code=status.HTTP_204_NO_CONTENT)
# async def del_favorite_product(db: Annotated[AsyncSession, Depends(get_db)], favorite: Favorites):
#     favorite = await db.scalar(select(Favorites)
#                                .where(Favorites.user_id == favorite.user_id)
#                                .where(Favorites.product_id == favorite.product_id))
#     if not favorite:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Товар не найден в избранном"
#         )
#
#     try:
#         await db.delete(favorite)
#         await db.commit()
#
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Ошибка при удалении: {str(e)}"
#         )
