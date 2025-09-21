from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.category import get_category, create_new_category, update_category_name, delete_category_by_id
from app.functions.auth_func import get_current_user
from app.database.db_depends import get_db
from app.schemas import CreateCategory

router = APIRouter(prefix='/categories', tags=['categories'])
templates = Jinja2Templates(directory="app/templates")


@router.get('/')
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    categories = await get_category(db=db)
    return categories


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_category(
    create_data: CreateCategory,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    new_category = await create_new_category(category_name=create_data.name, db=db)
    return new_category


@router.put('/')
async def update_category(db: Annotated[AsyncSession, Depends(get_db)],
                          category_id: int,
                          new_category_data: CreateCategory,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        await update_category_name(category_id=category_id,
                                   category_name=new_category_data.name,
                                   db=db)
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category update is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )


@router.delete('/', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)],
                          category_id: int,
                          get_user: Annotated[dict, Depends(get_current_user)]
):
    if get_user.get('is_admin'):
        await delete_category_by_id(category_id=category_id, db=db)

        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )
