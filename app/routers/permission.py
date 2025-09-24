from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from database.db_depends import get_db
from models import User
from .auth import get_current_user

templates = Jinja2Templates(directory='app/templates/')
router = APIRouter(prefix='/permission', tags=['permission'])


@router.patch('/')
async def supplier_permission(db: Annotated[AsyncSession, Depends(get_db)],
                              get_user: Annotated[dict, Depends(get_current_user)],
                              user_id: int):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Пользователь не найден')

        if user.role == 'seller':
            await db.execute(update(User).where(User.id == user_id).values(is_supplier=False, is_customer=True))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is no longer supplier'
            }
        else:
            await db.execute(update(User).where(User.id == user_id).values(is_supplier=True, is_customer=False))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User is now supplier'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission"
        )


@router.delete('/delete')
async def delete_user(db: Annotated[AsyncSession, Depends(get_db)], get_user: Annotated[dict, Depends(get_current_user)], user_id: int):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='NOT FOUND'
            )

        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can't delete admin user"
            )

        else:
            return {
                'status_code': status.HTTP_200_OK,
                'detail': 'User has already been deleted'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have admin permission"
        )
