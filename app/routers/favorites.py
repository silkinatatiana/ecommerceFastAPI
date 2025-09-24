from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Cookie
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import jwt

from database.crud.favorites import get_favorite, create_favorite, delete_favorite
from database.db_depends import get_db
from functions.auth_func import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/favorites", tags=["favorites"])
templates = Jinja2Templates(directory="app/templates")


@router.get('/')
async def get_favorites(
        user_id: int,
        db: AsyncSession = Depends(get_db),
):
    favorites = await get_favorite(user_id=user_id, db=db)
    return favorites


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_favorites(
        product_id: int,
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        new_favorite = await create_favorite(user_id=user_id,
                                             product_id=product_id,
                                             db=db)
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
        result = await delete_favorite(user_id=user_id,
                                       product_id=product_id,
                                       db=db)
        return result

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при удалении из избранного: {str(e)}'
        )


@router.post('/toggle/{product_id}')
async def toggle_favorite(
        product_id: int,
        token: Optional[str] = Cookie(None, alias='token'),
        db: AsyncSession = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")

        existing_favorite = await get_favorite(product_id=product_id, user_id=user_id, db=db)
        if existing_favorite:
            await delete_favorite(product_id=product_id, user_id=user_id, db=db)
        else:
            await create_favorite(product_id=product_id, user_id=user_id, db=db)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Ошибка при переключении избранного: {str(e)}'
        )