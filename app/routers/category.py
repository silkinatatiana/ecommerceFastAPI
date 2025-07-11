from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from sqlalchemy import insert, select, update
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx

from app.backend.db_depends import get_db
from app.schemas import CreateCategory
from app.models.category import Category

router = APIRouter(prefix='/categories', tags=['categories'])
templates = Jinja2Templates(directory="app/templates")


@router.get('/')
async def get_all_categories(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories

@router.post('/')
async def create_category(
    create_data: CreateCategory,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get('is_admin'):
        raise HTTPException(status_code=403, detail="Требуются права администратора")

    new_category = Category(
        name=create_data.name,
        slug=slugify(create_data.name),
        is_active=True
    )
    
    await db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


@router.put('/')
async def update_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int,
                          update_category: CreateCategory, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )

        category.name = update_category.name
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category update is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )


@router.delete('/')
async def delete_category(db: Annotated[AsyncSession, Depends(get_db)], category_id: int,
                          get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin'):
        category = await db.scalar(select(Category).where(Category.id == category_id))
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='There is no category found'
            )
        category.is_active = False
        await db.commit()
        return {
            'status_code': status.HTTP_200_OK,
            'transaction': 'Category delete is successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='You must be admin user for this'
        )
