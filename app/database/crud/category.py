from fastapi import HTTPException, status
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category


async def create_new_category(category_name: str,
                              db: AsyncSession):
    try:
        new_category = Category(name=category_name)
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return f"Категория '{category_name}' успешно создана"

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def get_category(db: AsyncSession,
                       category_id: int = None):
    try:
        query = select(Category)

        if category_id:
            query = query.where(Category.id == category_id)

        if category_id:
            result = await db.scalar(query)

        else:
            categories = await db.execute(query)
            result = categories.scalars().all()

        return result

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def update_category_name(category_id: int,
                               category_name: str,
                               db: AsyncSession
):
    try:
        query = update(Category).where(Category.id == category_id).values(name=category_name)
        result = await db.execute(query)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )


async def delete_category_by_id(category_id: int,
                               db: AsyncSession
):
    try:
        query = delete(Category).where(Category.id == category_id)
        result = await db.execute(query)

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        await db.commit()

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных: {str(e)}"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось выполнить запрос в БД: {str(e)}"
        )