from fastapi import HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.crud.decorators import handle_db_errors
from models import Category


@handle_db_errors
async def create_new_category(db: AsyncSession,
                              category_name: str
):
    new_category = Category(name=category_name)
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return f"Категория '{category_name}' успешно создана"


@handle_db_errors
async def get_category(db: AsyncSession,
                       category_id: int = None
):
    query = select(Category)

    if category_id:
        query = query.where(Category.id == category_id)

    if category_id:
        result = await db.scalar(query)

    else:
        categories = await db.execute(query)
        result = categories.scalars().all()

    return result


@handle_db_errors
async def update_category_name(db: AsyncSession,
                               category_id: int,
                               category_name: str
):
    query = update(Category).where(Category.id == category_id).values(name=category_name)
    result = await db.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    await db.commit()


@handle_db_errors
async def delete_category_by_id(db: AsyncSession,
                                category_id: int

):
    query = delete(Category).where(Category.id == category_id)
    result = await db.execute(query)

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    await db.commit()
