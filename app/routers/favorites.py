from typing import Optional
import jwt
from fastapi import APIRouter, Depends, status, HTTPException, Request, Cookie
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi.templating import Jinja2Templates

from app.routers.auth import get_current_user
from app.backend.db_depends import get_db
from app.models.favorites import Favorites
from app.models.users import User
from app.routers.auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/favorites", tags=["favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/')
async def get_favorites(
        user_id: int,
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorites)
        .where(Favorites.user_id == user_id)
    )

    favorites = result.scalars().all()
    return favorites

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_favorites(
        product_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        new_favorite = Favorites(
            user_id=user_id,
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


@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def del_favorite_product(product_id: int,
                               user_id: int,
                               db: AsyncSession = Depends(get_db)):
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Товар не найден в избранном'
            )
        return None

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при удалении из избранного: {str(e)}'
        )


@router.post('/toggle/{product_id}')
async def toggle_favorite(
        request: Request,
        product_id: int,
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user_id = payload.get("id")
    existing_favorite = await db.execute(
        select(Favorites)
        .where(
            Favorites.user_id == user_id,
            Favorites.product_id == product_id
        )
    )
    existing_favorite = existing_favorite.scalar_one_or_none()

    if existing_favorite:
        await del_favorite_product(product_id, user_id, db)
    else:
        await create_favorites(product_id, user_id, db)
